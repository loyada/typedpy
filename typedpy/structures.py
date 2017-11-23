"""
The Skeleton classes to support strictly defined structures:
Structure, Field, StructureReference, ClassReference, TypedField
"""
from collections import OrderedDict
from inspect import Signature, Parameter


# support:
# json schema draft 4,
# Structure inheritance,
# fields of class reference
# embedded structures

def make_signature(names, required, additional_properties, bases_params_by_name):
    """
    Make a signature that will be used for the constructor of the Structure
    :param names: names of the properties
    :param required: list of required properties
    :param additional_properties: are additional properties allowed?
    :param bases_params_by_name: parameters taken from base classes (i.e. MRO)
           in case of inheritance
    :return: the signature
    """
    non_default_args_for_class = OrderedDict(
        [(name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD)) for name in names if
         name in required])
    non_default_args_for_bases = OrderedDict(
        [(name, param) for (name, param) in bases_params_by_name.items() if
         name in required])
    non_default_args = list({**non_default_args_for_bases,
                             **non_default_args_for_class}.values())

    default_args_for_class = OrderedDict(
        [(name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None))
         for name in names if name not in required])
    default_args_for_bases = OrderedDict([(name, param) for (name, param)
                                          in bases_params_by_name.items() if name not in required])
    default_args = list({**default_args_for_bases, **default_args_for_class}.values())
    additional_args = [Parameter("kwargs", Parameter.VAR_KEYWORD)] if \
        additional_properties else []

    return Signature(non_default_args + default_args + additional_args)


def get_base_info(bases):
    """
    Extract the parameters from all the base classes to support inheritance of Structures.
    :param bases: list of base classes
    :return:  a tuple of: (the parameters from the base classes, a list of the names of
              the required ones)
    """
    bases_params = OrderedDict()
    bases_required = []
    base_structures = [base for base in bases if
                       issubclass(base, Structure) and base is not Structure]
    for base in base_structures:
        for k, param in getattr(base, '__signature__').parameters.items():
            if k not in bases_params:
                if param.default is not None and param.kind != Parameter.VAR_KEYWORD:
                    bases_required.append(k)
                bases_params[k] = param
        additional_props = base.__dict__.get('_additionalProperties', True)
        if additional_props and bases_params["kwargs"].kind == Parameter.VAR_KEYWORD:
            del bases_params["kwargs"]

    return (bases_params, bases_required)


class Field(object):
    """
    Base class for a field(i.e. property) in a structure.
    """

    def __init__(self, name=None, immutable=None):
        self._name = name
        if immutable is not None:
            self._immutable = immutable

    def __set__(self, instance, value):
        if (getattr(self, '_immutable', False) or getattr(instance, '_immutable', False)) \
                and  self._name in instance.__dict__:
            raise ValueError("{}: Field is immutable".format(self._name))
        instance.__dict__[self._name] = value

    def __str__(self):
        def as_str(val):
            """
            convert to string or a list of strings
            :param val: a Field or a list of Fields
            :return: a string representation
            """
            if hasattr(val, '__iter__'):
                return '[{}]'.format(', '.join([str(v) for v in val]))
            return str(val)
        name = self.__class__.__name__
        props = []
        for k, val in sorted(self.__dict__.items()):
            if val is not None and not k.startswith('_'):
                strv = "'{}'".format(val) if isinstance(val, str) else as_str(val)
                props.append('{} = {}'.format(k, strv))

        propst = '. Properties: {}'.format(', '.join(props)) if props else ''
        return '<{}{}>'.format(name, propst)


class StructMeta(type):
    """
    Metaclass for Structure. Manipulates it to ensure the fields are set up correctly.
    """
    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, cls_dict):
        bases_params, bases_required = get_base_info(bases)
        for key, val in cls_dict.items():
            if not key.startswith('_') and not isinstance(val, Field) and Field in val.__mro__:
                cls_dict[key] = val()
        for key, val in cls_dict.items():
            if isinstance(val, StructMeta) and not isinstance(val, Field):
                cls_dict[key] = ClassReference(val)
        fields = [key for key, val in cls_dict.items() if isinstance(val, Field)]
        for field_name in fields:
            setattr(cls_dict[field_name], '_name', field_name)
        clsobj = super().__new__(mcs, name, bases, dict(cls_dict))
        clsobj._fields = fields
        default_required = list(set(bases_required + fields)) if bases_params else fields
        required = cls_dict.get('_required', default_required)
        additional_props = cls_dict.get('_additionalProperties', True)
        sig = make_signature(clsobj._fields, required, additional_props, bases_params)
        setattr(clsobj, '__signature__', sig)
        return clsobj

    def __str__(cls):
        name = cls.__name__
        props = []
        for k, val in sorted(cls.__dict__.items()):
            if val is not None and not k.startswith('_'):
                strv = "'{}'".format(val) if isinstance(val, str) else str(val)
                props.append('{} = {}'.format(k, strv))
        return '<Structure: {}. Properties: {}>'.format(name, ', '.join(props))


class Structure(metaclass=StructMeta):
    """
    The main class to support strictly defined structures. Note it is manipulated by StructMeta.
    """
    _fields = []

    def __init__(self, *args, **kwargs):
        bound = getattr(self, '__signature__').bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            setattr(self, name, val)

    def __str__(self):
        name = self.__class__.__name__
        if name.startswith('StructureReference_') and self.__class__.__bases__ == (Structure,):
            name = 'Structure'
        props = []
        for k, val in sorted(self.__dict__.items()):
            strv = "'{}'".format(val) if isinstance(val, str) else str(val)
            props.append('{} = {}'.format(k, strv))
        return '<Instance of {}. Properties: {}>'.format(name, ', '.join(props))

    def __eq__(self, other):
        return str(self) == str(other)

    def __delitem__(self, key):
        if isinstance(getattr(self, '_required'), list) and \
            key in getattr(self, '_required'):
            raise ValueError("{} is manadoty".format(key))
        del self.__dict__[key]



class ImmutableStructure(Structure):
    """
    A structure in which non of the fields can be updated post creation
    """
    _immutable = True


class StructureReference(Field):
    """
    An embedded structure within other structure. Allows to create hierarchy.
    """
    counter = 0

    def __init__(self, **kwargs):
        classname = "StructureReference_" + str(StructureReference.counter)
        StructureReference.counter += 1

        self._newclass = type(classname, (Structure,), kwargs)
        super().__init__(kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError("{}: Expected a dictionary".format(self._name))
        newval = self._newclass(**value)
        super().__set__(instance, newval)

    def __str__(self):
        props = []
        for k, val in sorted(self._newclass.__dict__.items()):
            if val is not None and not k.startswith('_'):
                props.append('{} = {}'.format(k, str(val)))

        propst = '. Properties: {}'.format(', '.join(props)) if props  else ''
        return '<Structure{}>'.format(propst)


class TypedField(Field):
    """
    A strictly typed field
    """
    _ty = object

    def __set__(self, instance, value):
        if not isinstance(value, self._ty):
            raise TypeError("%s: Expected %s" % (self._name, self._ty))
        super().__set__(instance, value)


class ClassReference(TypedField):
    """
    A field that is a reference to another Structure instance
    """
    def __init__(self, cls):
        self._ty = cls
        super().__init__(cls)

    def __str__(self):
        return "<ClassReference: {}>".format(self._ty.__name__)
