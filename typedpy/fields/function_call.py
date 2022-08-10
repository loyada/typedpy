from typedpy.structures import Structure, Field
from typedpy.commons import wrap_val
from .array import Array
from .strings import String


class Function(Field):
    """
    A function or method. Note that this can't be any callable (it can't be a class,
     for example), but a real function
    """

    _bound_method_type = type(Field().__init__)

    def __set__(self, instance, value):
        def is_function(f):
            return type(f) in {
                type(lambda x: x),
                type(open),
                Function._bound_method_type,
            }

        def err_prefix():
            return f"{self._name}: Got {wrap_val(value)}; " if self._name else ""

        if not is_function(value):
            raise TypeError(f"{err_prefix()}Expected a function")
        super().__set__(instance, value)


class FunctionCall(Structure):
    """
    Structure that represents a function call for the purpose of serialization mappers: \
    Includes the function to be called, and a list of keys of positional string arguments.
    This is not a generic function call.

    Arguments:
        func(Function):
            the function to be called. Note this must be a real function, not any callable.
        args(Array[String]): optional
            the keys of the arguments to be used as positional arguments for the function call
    """

    func = Function
    args = Array[String]
    _required = ["func"]
