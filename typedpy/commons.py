def wrap_val(v):
    return "'{}'".format(v) if isinstance(v, str) else v


def _is_dunder(name):
    """Returns True if a __dunder__ name, False otherwise."""
    return (
        len(name) > 4
        and name[:2] == name[-2:] == "__"
        and name[2] != "_"
        and name[-3] != "_"
    )


def _is_sunder(name):
    """Returns True if a _sunder name, False otherwise."""
    return len(name) > 2 and name[0] == "_" and name[1:2] != "_"
