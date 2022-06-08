import ast
import typing

from typedpy import Array, Map, Structure

INDENT = " " * 4


def get_imports(path):
    with open(path) as fh:
        root = ast.parse(fh.read(), path)

    for node in ast.iter_child_nodes(root):
        level = 0
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            level = node.level
        else:
            continue

        for n in node.names:
            yield (level, module, n.name.split("."), n.asname)


class FunctionInfo(Structure):
    name: str
    positional_args: Array[str]
    keyword: typing.Optional[str]
    keyword_only_args: Array[str]
    returns: str
    decorators: Array[str]

    _ignore_none = True


class ModelClass(Structure):
    name: str
    bases: Array[str]
    columns: Map[str, str]
    relationships: Map[str, str]
    functions: Array[FunctionInfo]

    @staticmethod
    def type_by_sqlalchemy_type(sqlalchemy_type: str) -> str:
        the_type = sqlalchemy_type.split(".")[-1]
        return {
            "BigInteger": "int",
            "Integer": "int",
            "Boolean": "bool",
            "String": "str",
            "DateTime": "datetime.datetime",
            "Date": "datetime.date",
            "Float": "float",
            "Interval": "datetime.timedelta",
            "Time": "datetime.time",
        }.get(the_type, "Any")


def _get_param_type(ast_type):
    if isinstance(ast_type, ast.Name):
        return ast_type.id
    elif isinstance(ast_type, ast.Subscript):
        value = ast_type.value.id
        if isinstance(ast_type.slice, ast.Tuple):
            args = [_get_param_type(x) for x in ast_type.slice.dims]
        else:
            args = [ast_type.slice.id]
        return f"{value}[{', '.join(args)}]"


def _extract_kw_args(args_info) -> str:
    if args_info.kwarg:
        return f"**{args_info.kwarg.arg}"
    return ""


def _extract_kwonly_arg(arg, default) -> str:
    the_type = f": {_get_param_type(arg.annotation)}" if arg.annotation else ""
    default_s = " = None" if default is not None else ""
    the_type = f": {_get_param_type(arg.annotation)}" if arg.annotation else ""
    return f"{arg.arg}{the_type}{default_s}"


def _extract_arg(arg):
    the_type = f": {_get_param_type(arg.annotation)}" if arg.annotation else ""
    return f"{arg.arg}{the_type}"


def method_to_src(func: FunctionInfo):
    res = []
    for d in func.decorators:
        res.append(f"@{d}")

    res.append(f"def {func.name}(")
    for a in func.positional_args:
        res.append(f"{INDENT}{a},")
    if func.keyword_only_args:
        res.append(f"{INDENT}*,")
        for a in func.keyword_only_args:
            res.append(f"{INDENT}{a},")
    if func.keyword:
        res.append(f"{INDENT}{func.keyword},")
    returns_s = f" -> {func.returns}" if func.returns else ""
    res.append(f"){returns_s}: ...")
    res.append("")
    return res


def functions_to_str(functions: typing.Iterable[FunctionInfo]) -> typing.Iterable[str]:
    res = []
    for func in functions:
        res.extend(method_to_src(func))
        res.append("")
        res.append("")

    return res


def models_to_src(models: typing.Iterable[ModelClass]) -> typing.Iterable[str]:
    res = []
    for model in models:
        bases = f"({', '.join(model.bases)})" if model.bases else ""
        res.append(f"class {model.name}{bases}:")
        column_with_type = [
            f"{INDENT}{field}: Union[Column, {the_type}]"
            for (field, the_type) in model.columns.items()
        ]
        fields_with_type = [
            f"{INDENT}{field}: {the_type}"
            for (field, the_type) in model.columns.items()
        ]
        for field in column_with_type:
            res.append(field)
        for rel in model.relationships:
            res.append(f"{INDENT}{rel}: Any")
        fields_arg_list = [f"{INDENT * 2}{f} = None," for f in fields_with_type]
        relationships_arg_list = [
            f"{INDENT * 3}{f} = None," for f in model.relationships
        ]
        res.append(f"{INDENT}def __init__(self,")
        res.extend(fields_arg_list)
        res.extend(relationships_arg_list)
        res.append(f"{INDENT}): ...")
        res.append("")
        if "Mappable" in bases:
            res.append(f"{INDENT}@classmethod")
            res.append(f"{INDENT}def from_structure(cls,")
            res.append(f"{INDENT*3}structure: Structure,")
            res.append(f"{INDENT*3}*,")
            res.append(f"{INDENT*3}ignore_props: list[str] = None,")
            res.extend(fields_arg_list)
            res.extend(relationships_arg_list)
            res.append(f"{INDENT}) -> {model.name}: ...")
            res.append("")
        for func in model.functions:
            res.extend([f"{INDENT}{line}" for line in method_to_src(func)])
            res.append("")
        res.append("")

    return res


def _get_function_info(node) -> FunctionInfo:
    decorators = [d.id for d in node.decorator_list]
    return_type = _get_param_type(node.returns) if node.returns else ""
    args = [_extract_arg(a) for a in node.args.args]
    keyword_args = _extract_kw_args(node.args)
    keyword_only_args = [
        _extract_kwonly_arg(a, d)
        for a, d in zip(node.args.kwonlyargs, node.args.kw_defaults)
    ]
    return FunctionInfo(
        name=node.name,
        positional_args=args,
        keyword=keyword_args,
        keyword_only_args=keyword_only_args,
        returns=return_type,
        decorators=decorators,
    )


def get_models(
    path,
) -> typing.Tuple[typing.Iterable[ModelClass], typing.Iterable[FunctionInfo]]:
    with open(path) as fh:
        root = ast.parse(fh.read(), path)

    classes = []
    functions = []
    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.FunctionDef):
            functions.append(_get_function_info(node))
        elif isinstance(node, ast.ClassDef):
            if node.bases:
                bases = [x.id for x in node.bases if isinstance(x, ast.Name)]
                if "Base" in bases:
                    bases.remove("Base")
                    class_name = node.name
                    body = node.body
                    methods = []
                    relationships = {}
                    columns = {}
                    for b in body:
                        if isinstance(b, ast.Assign) and isinstance(b.value, ast.Call):
                            field_name = b.targets[0].id
                            function_name = b.value.func.id
                            if function_name == "Column":
                                args = b.value.args
                                first = args[0]
                                column_type = (
                                    first.id
                                    if isinstance(first, ast.Name)
                                    else first.func.id
                                )
                                columns[
                                    field_name
                                ] = ModelClass.type_by_sqlalchemy_type(column_type)
                            if function_name == "relationship":
                                args = b.value.args
                                first = args[0]
                                entity_type = (
                                    first.id
                                    if isinstance(first, ast.Name)
                                    else first.value
                                )
                                relationships[field_name] = entity_type
                        if isinstance(b, ast.FunctionDef):
                            methods.append(_get_function_info(b))
                    classes.append(
                        ModelClass(
                            name=class_name,
                            bases=bases,
                            columns=columns,
                            relationships=relationships,
                            functions=methods,
                        )
                    )
    return classes, functions
