---
name: typedpy-dev
description: How to develop, test, document, and release typedpy (github.com/loyada/typedpy) -- the Field/Structure architecture, the four places a new Field type must be wired in, testing and CI conventions, known pre-existing quirks, and the release process. Use this whenever working on typedpy's own source (not just using typedpy as a library) -- adding or changing a Field type, touching serialization/fast_serialization/json_schema/stubs, writing tests for typedpy itself, debugging CI, or cutting a release.
---

# Developing typedpy

typedpy is a pure-Python, dependency-free (`install_requires=[]`) library for type-safe,
validated data structures, broadly comparable to Pydantic/dataclasses but with deep
immutability, versioned serialization, JSON Schema generation, and `.pyi` stub generation.
Supports Python 3.9-3.14.

## Packaging

Packaging lives in `pyproject.toml` (PEP 621, `setuptools` backend -- **not** Poetry,
despite the project's own issue titles sometimes mentioning it). There is no `setup.py`.
Build with `python -m build`; it produces `dist/*.whl` and `dist/*.tar.gz`. Verify with
`twine check dist/*` before anything else. See "Releasing" below for the full flow.

## The Field contract

Every field type is a descriptor: `typedpy/structures/structures.py` defines `Field`
(`__get__`/`__set__`, `_name` assigned at class-creation time, `_try_default_value`) and
`TypedField` (adds `_validate`/`get_type` for a field wrapping one concrete type, e.g.
`ClassReference`). A field subclass typically lives in its own file under `typedpy/fields/`
and is re-exported via `typedpy/fields/__init__.py` (then `typedpy/__init__.py`'s
`from .fields import *` makes it public). `Constant` (in `typedpy/commons.py`) is a
related-but-distinct concept: it has **no** descriptor protocol, so reading it off a class
(`SomeClass.some_constant`) returns the raw `Constant` object itself, not a value -- this
matters when writing code that needs to tell "a real field" apart from "a constant."

## Adding a new field type: four places to wire it in

This is the pattern a new field type almost always needs, beyond the field class itself.
`typedpy/fields/discriminated_union.py` is the most recent and most complete worked example
-- read it alongside this list:

1. **`typedpy/serialization/serialization.py`**: add a branch in `deserialize_single_field`
   for how to turn raw input into a value (do this *before* the generic
   `isinstance(field, SerializableField)` branch if your field needs more context than a
   bare `deserialize(self, value)` call gives -- e.g. mapper/camelCase/keep_undefined).
   Add a branch in `serialize_val` if the generic `SerializableField` dispatch
   (`field_definition.serialize(val)`) isn't right either -- e.g. if serialization needs to
   dispatch by the *runtime* type of the value rather than by the field definition.
2. **`typedpy/serialization/fast_serialization.py`**: add a branch in `_get_serialize` if
   the field needs special handling for `FastSerializable` classes (the generic path calls
   `obj.serialize(val)` where `obj` is the field itself -- not polymorphic by the value's
   actual class; `DiscriminatedUnion`'s branch there shows how to build a closure that calls
   `val.serialize()` instead, and how to eagerly verify/create fast serializers for every
   possible concrete type up front).
3. **`typedpy/json_schema/json_schema_mapping.py`**: register the field class in
   `get_mapper`'s `field_type_to_mapper` dict, pointing at a new `Mapper` subclass (see
   `OneOfMapper`/`AnyOfMapper`/`DiscriminatedUnionMapper` for the shape -- `to_schema(self,
   definitions, serialization_mapper)` returning a schema dict). `_map_class_reference` is
   the existing helper for "turn a Structure class into a schema + `$ref`, registered into
   `definitions`."
4. **`typedpy/stubs/type_info_getter.py`**: add a branch in `get_type_info` for how the
   field's declared type renders in generated `.pyi` stubs (see `_get_anyof_typing` /
   `_get_discriminated_union_typing` for the `Union[...]` pattern -- wrap each possible
   concrete type in `ClassReference(...)` and recurse into `get_type_info`, which handles
   import tracking via `additional_classes` automatically).

Also check `typedpy/structures/structures.py`'s `_get_all_fields_by_name`/
`get_all_fields_by_name` if the field needs special handling during class construction, and
`typedpy/stubs/type_info_getter.py`'s `get_all_type_info` if it needs to be excluded from
generated stubs the way `Constant` fields are.

**Don't assume a clean architectural boundary exists to preserve.** `typedpy/fields/*.py`
already has real coupling into `typedpy/structures`, and `serialization.py` already reaches
into field-internal attributes (e.g. `field._ty` for `ClassReference`, `field._by_owner` for
`DiscriminatedUnion`). Follow that existing pattern rather than inventing a cleaner one --
e.g. prefer a dedicated branch in `serialize_val`/`deserialize_single_field` that reaches
into the field's attributes, over having the field itself import from
`typedpy.serialization` (fields currently have zero dependency on serialization; keep it
that way, using a deferred/function-local import in the rare case it's unavoidable).

## Structures and Constants

`AbstractStructure` blocks direct instantiation (only subclasses can be instantiated) --
use it for a base class that's meant to be specialized, like a discriminated union's base.
A common pattern: a base class declares a field normally (e.g. `subject: Enum[EventSubject]`),
and each subclass fixes it via `subject = Constant(EventSubject.foo)`. This is already
fully supported end-to-end (validation, serialization incl. fast serialization,
deserialization skips/ignores constants in input, JSON Schema emits `enum: [value]`, stubs
skip it) -- see `docs/structures.rst`'s "Defining inherited fields as constants" section
and `tests/test_constant_field.py`.

## Testing conventions

- One test file per feature area (`tests/test_<feature>.py`), fixtures as module-level
  classes, `pytest.raises(...)` + plain `str(excinfo.value)` substring assertions for error
  cases (not a dedicated error-formatting helper, despite `get_simplified_error` existing in
  `typedpy/errors.py` -- it's used in some older test files but isn't the dominant pattern).
- Run the file you're working on directly during iteration; run the full suite
  (`pytest tests/`) before considering anything done.
- **Four tests always fail outside real CI**: `tests/test_create_pyi.py::test_create_stub_using_script[...]`
  (4 parametrized cases). They spawn a subprocess that needs `typedpy` importable, which
  fails in most sandboxes (`ModuleNotFoundError: No module named 'typedpy'`) because the
  package isn't pip-installed there. This is a sandbox limitation, not a real failure --
  confirmed clean in actual GitHub Actions CI. Don't chase it; do verify your own changes
  don't add *new* failures beyond these four.
- If you can't get a given Python version's venv working locally (e.g. missing
  `pythonX.Y-distutils`/ensurepip, no `sudo`), you can often still get a real signal by
  running the test *logic* as plain `assert` statements under a bare `pythonX.Y` binary --
  typedpy has zero runtime dependencies, so this is a faithful (if manual) check. Real CI is
  still the authoritative confirmation.

## CI and tox

- `tox.ini`'s default `[testenv]` is now just `pip install .` + `pytest` -- lint and
  coverage are **not** run inside the per-Python-version matrix (that used to happen and was
  redundant 6x over). `tox -e lint` runs `black --check` + `pylint`; `tox -e coverage` runs
  coverage with `--fail-under=85`.
- **`.github/workflows/main.yml` runs pytest/coverage directly, not through `tox`, in the
  `build` and `coverage` jobs.** This is deliberate: `tox`'s subprocess command runner
  silently swallows the stderr output that `pytest-github-actions-annotate-failures` writes
  (confirmed by comparing the same command run directly vs. through `tox -e <env> -- ...` --
  the `::error` annotation line is missing even from tox's own per-command log file, not
  just from the terminal). If you ever need to add a new tox env that should also annotate
  failures in CI, don't route it through `tox` in the workflow -- install deps and invoke
  `pytest` as a plain shell step instead. The `lint` job is unaffected (no pytest involved)
  and still legitimately uses `tox -e lint`.
- Local verification quirk, not a real CI issue: a bare `pytest` (no path argument) run from
  this repo can pick up unrelated stray directories if they exist locally (an old `.tox/`,
  `.venv/`, `build/`, or similar containing vendored test-looking files, e.g. pip's bundled
  colorama tests) -- these are gitignored and don't exist in a fresh CI checkout. If a local
  bare-`pytest` run shows unfamiliar failures with paths like
  `lib/python3.x/site-packages/...`, that's local environment pollution, not a real
  regression -- verify against a clean export (`git archive HEAD | tar -x -C /tmp/clean &&
  cd /tmp/clean && pip install . && pytest`) instead of trusting the dirty tree.
- **black-version drift**: if `black --check` suddenly flags many unrelated files, it's
  almost always because the installed `black` is a newer version than whatever last
  formatted the repo, not a real problem with your change. Running plain `black typedpy`
  fixes it in one shot; this has happened multiple times across unrelated PRs to this repo.
- **Expected, not a bug**: `pylint` reports many `cyclic-import` (R0401) warnings across
  `typedpy/fields/*` <-> `typedpy/structures/*`. This is a pre-existing, accepted pattern in
  this codebase (consistent circular references at the module level that Python tolerates
  fine at runtime) -- don't try to "fix" it unless specifically asked. The real gate is
  `pylint`'s `fail-under = 9.7` in `setup.cfg`.

## Documentation

Sphinx, source in `docs/*.rst`. `docs/fields.rst` has `.. autoclass::` reference entries for
every field type, grouped by category (Numerical / String/Enum / Collections / Re-use /
Immutability) -- a new field usually belongs in "Re-use" if it's union-like, next to
`AnyOf`/`OneOf`/`NotField`. `docs/structures.rst` has the narrative/tutorial content; prefer
extending an existing relevant section with a worked example over creating a new one from
scratch, and link to the `fields.rst` reference via `:class:`SomeField`` rather than
duplicating the `.. autoclass::` directive (Sphinx will warn/error on a duplicate object
description). Build locally with `python -m sphinx -b html docs/ /tmp/out` (the `tox -e
docs` env exists but isn't wired into CI) and check for *new* warnings compared to a
baseline -- there are some pre-existing ones (unrelated docstring formatting issues, theme
config) that aren't worth chasing.

## Git conventions

Branch naming is `<kind>/<issue-number>-<short-desc>` when there's a GitHub issue
(`fix/295-...`, `feature/297-...`, `ci/299-...`, `build/288-...`), or `release/X.Y.Z` for a
version bump. PR titles tend to be short and plain (often just the version number for a
release PR). Commit messages explain *why*, not just *what*.

## Releasing

1. On a `release/X.Y.Z` branch, bump `version` (and the `Download` URL under
   `[project.urls]`) in `pyproject.toml` -- this is the **only** place the version lives
   now.
2. `rm -rf dist build *.egg-info && python -m build`, then `twine check dist/*`. Also smoke
   test: `pip install --force-reinstall --no-deps .` and confirm `import typedpy` plus the
   two console scripts (`create-stub`, `create-stubs-for-dir`) still work.
3. Run the full test suite once more before opening the PR.
4. After merge, tag the merge commit (`git tag -a vX.Y.Z -m "X.Y.Z" <merge-sha> && git push
   origin vX.Y.Z`), then rebuild from the merged commit (don't reuse the pre-merge build --
   rebuild to be sure the artifact matches what's actually on `master`).
5. **The actual `twine upload dist/*` is run by the repo owner, not automated** -- no PyPI
   credentials should ever be assumed to exist in a dev environment. Hand over the built,
   verified `dist/*` files and the exact command.
6. **Known gotcha**: an old system `twine`/`pkginfo` can fail with the misleading error
   `InvalidDistribution: Metadata is missing required fields: Name, Version` on a package
   that a recent `setuptools` built -- this is `pkginfo` being too old to parse
   `Metadata-Version: 2.4`, not a real problem with the package (confirmed by checking with
   a newer `twine`/`pkginfo`, which parses the identical files fine). Fix: `pip install
   --user --upgrade twine pkginfo` in whatever environment runs the upload.
