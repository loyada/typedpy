from pathlib import Path
import inspect
from .structures import TypedField, Structure

def create_pyi(calling_source_file, attrs: dict):
    full_path: Path = Path(calling_source_file)
    pyi_path = (full_path.parent / f"{full_path.stem}.pyi" ).resolve()

    out_src = ["from typedpy import Structure", ""]
    struct_classes = {k: v for k, v in attrs.items() if inspect.isclass(v) and issubclass(v, Structure)}

    for cls_name, cls in struct_classes.items():
        if cls.get_all_fields_by_name():
            out_src.append(f"class {cls_name}(Structure):")
            for field_name, field in cls.get_all_fields_by_name().items():
                if isinstance(field, TypedField):
                    ty = getattr(field, "_ty")
                    out_src.append(f"    {field_name}: {ty.__name__}")
            out_src.append("\n")

    out_s = "\n".join(out_src)
    with open(pyi_path, "w") as f:
        f.write(out_s)