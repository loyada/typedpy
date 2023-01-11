from typedpy.structures import Field, Structure


class StructureReference(Field):
    """
    A Field that is an embedded structure within other structure. Allows to create hierarchy.
    This is useful if you want to inline your Structure, as opposed to create an explicit
    class for it.
    All the arguments are passed as attributes of the structure. Example:

    .. code-block:: python

        StructureReference(
            _additionalProperties = False,
            id = String,
            name = String
            age = AnyOf[PositiveInt, PositiveFloat]
        )


    Important: Since Typedpy dynamically creates an internal class for it, this
    field cannot be pickled!
    """

    counter = 0

    def __init__(self, **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter += 1

        self._newclass = type(classname, (Structure,), kwargs)
        super().__init__(kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, (dict, Structure)):
            raise TypeError(
                f"{self._name}: Expected a dictionary or Structure; got {value}"
            )
        extracted_values = (
            {k: v for (k, v) in value.__dict__.items() if k != "_instantiated"}
            if isinstance(value, (Structure,))
            else value
        )
        newval = self._newclass(**extracted_values)
        super().__set__(instance, newval)

    def __serialize__(self, value):
        raise TypeError(f"{self._name}: StructuredReference Cannot be pickled")

    def __str__(self):
        props = []
        for k, val in sorted(self._newclass.__dict__.items()):
            if val is not None and not k.startswith("_"):
                props.append(f"{k} = {str(val)}")

        propst = f". Properties: {', '.join(props)}" if props else ""
        return f"<Structure{propst}>"

    def serialize(self, value):
        # This is not optimized, since it is a legacy field type
        res = {
            name: getattr(self._newclass, name).serialize(getattr(value, name, None))
            for name, field in self._newclass.get_all_fields_by_name().items()
        }
        return res
