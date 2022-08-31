from .structures import Structure


class AbstractStructure(Structure):
    """
    Defines a Structure class that cannot be instantiated because it is abstract.
     To instantiate, you are required to extend it.
    """

    def __init__(self, *args, **kwargs):
        found = False
        for clz in self.__class__.__bases__:
            if clz is AbstractStructure:
                found = True
                break
        if found:
            raise TypeError("Not allowed to instantiate an abstract Structure")
        super().__init__(*args, **kwargs)
