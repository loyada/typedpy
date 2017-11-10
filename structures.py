from collections import OrderedDict
from inspect import Signature, Parameter


# support:
# json schema draft 4,
# Structure inheritance,
# fields of class reference
# embedded structures

def make_signature(names, required, additionalProperties, bases_params_by_name):
    nonDefaultArgsForClass = OrderedDict([(name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD)) for name in names if name in required])
    nonDefaultArgsForBases = OrderedDict([(name, param) for (name, param) in bases_params_by_name.items() if name in required])
    nonDefaultArgs = list({**nonDefaultArgsForBases, **nonDefaultArgsForClass}.values())

    defaultArgsForClass = OrderedDict([(name, Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None))
                                        for name in names if name not in required])
    defaultArgsForBases = OrderedDict([(name, param) for (name, param) in bases_params_by_name.items() if name not in required])
    defaultArgs = list({**defaultArgsForBases, **defaultArgsForClass}.values())
    additionalArgs = [Parameter("kwargs", Parameter.VAR_KEYWORD)] if additionalProperties else []

    return Signature(nonDefaultArgs + defaultArgs + additionalArgs)


class Field(object):
    def __init__(self, name=None):
        self._name = name

    def __set__(self, instance, value):
        instance.__dict__[self._name] = value

    def __str__(self):
        name = self.__class__.__name__
        props = []
        for k,v in self.__dict__.items():
            if v is not None and not k.startswith('_'):
                strv = "'{}'".format(v) if isinstance(v, str) else str(v)
                props.append('{} = {}'.format(k, strv))

        propst = '. Properties: {}'.format(', '.join(props)) if props  else ''
        return '<{}{}>'.format(name, propst)


class StructMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        return OrderedDict()

    def __new__(cls, name, bases, cls_dict):
        bases_params = OrderedDict()
        bases_required = []
        baseStructures = [base for base in bases if issubclass(base, Structure) and base is not Structure]
        for base in baseStructures:
            for k, param in base.__signature__.parameters.items():
                if k not in bases_params:
                    if param.default is not None and param.kind!=Parameter.VAR_KEYWORD:
                        bases_required.append(k)
                    bases_params[k] = param
            additionalProps = base.__dict__.get('_additionalProperties', True)
            if additionalProps and bases_params["kwargs"].kind==Parameter.VAR_KEYWORD:
                del bases_params["kwargs"]

        fields = [key for key, val in cls_dict.items() if isinstance(val, Field)]
        for field_name in fields:
            cls_dict[field_name]._name = field_name
        clsobj = super().__new__(cls, name, bases, dict(cls_dict))
        clsobj._fields = fields
        default_required = list(set(bases_required + fields)) if bases_params else fields
        required = cls_dict.get('_required', default_required)
        additionalProps = cls_dict.get('_additionalProperties', True)
        sig = make_signature(clsobj._fields, required, additionalProps, bases_params)
        setattr(clsobj, '__signature__', sig)
        return clsobj

    def __str__(self):
        name = self.__name__
        props = []
        for k,v in self.__dict__.items():
            if v is not None and not k.startswith('_'):
                strv = "'{}'".format(v) if isinstance(v, str) else str(v)
                props.append('{} = {}'.format(k, strv))
        return '<Structure: {}. Properties: {}>'.format(name, ', '.join(props))


class Structure(metaclass=StructMeta):
    _fields = []

    def __init__(self, *args, **kwargs):
        bound = self.__signature__.bind(*args, **kwargs)
        for name, val in bound.arguments.items():
            setattr(self, name, val)

    def __str__(self):
        name = self.__class__.__name__
        props = []
        for k, v in self.__dict__.items():
            if v is not None and not k.startswith('_'):
                strv = "'{}'".format(v) if isinstance(v, str) else str(v)
                props.append('{} = {}'.format(k, strv))
        return '<Instance of {}. Properties: {}>'.format(name, ', '.join(props))
