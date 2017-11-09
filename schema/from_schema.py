import json
from collections import namedtuple

from fields import *

def _to_namedtuple(mydict):
    return namedtuple('structure', mydict.keys())(**mydict)


def _get_json(filename):
    with open(filename) as json_input:
        code = json.load(json_input)
        return code

def _json_to_code(filename):
    data = _get_json(filename)
    defined_classes = {}
    code_for_classes = [_class_from_schema(name, _to_namedtuple(structure_dict), defined_classes = defined_classes) for (name, structure_dict) in data.items()]
    return '\n\n'.join(list(defined_classes.values()) + code_for_classes)


def _class_from_schema(name, class_schema, defined_classes):
    def get_params_as_strings(schema):
        return ['%s = %s' % (key, val) for key, val in schema.items() if key is key not in ('type')]

    def string_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'String', ', '.join(get_params_as_strings(schema)))

    def number_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'Number', ', '.join(get_params_as_strings(schema)))

    def integer_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'Integer', ', '.join(get_params_as_strings(schema)))

    def float_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'Float', ', '.join(get_params_as_strings(schema)))

    def structfield_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'StructureReference', ', '.join(get_params_as_strings(schema)))

    def array_gen(field, schema):
        return '    %s = %s(%s)\n' % (field, 'Array', ', '.join(get_params_as_strings(schema)))

    generators = {
        'string': string_gen,
        'number': number_gen,
        'integer': integer_gen,
        'float': float_gen,
        'object': structfield_gen,
        'array': array_gen
    }


    def field_definition(field, field_type, schema):
        if field_type in generators:
            csname, params_string = generators[field_type](field, schema)
            return '    %s = %s(%s)\n' % (field, csname, params_string)
        if field_type in globals():
            kwparams = get_params_as_strings(schema)
            return '    %s = %s(%s)\n' % (field, field_type, ', '.join(kwparams))


    def build_code_for_fields(class_schema, defined_classes):
        code = ''
        for field, schema in class_schema.properties.items():
            field_schema = _to_namedtuple(schema)
            if isinstance(field_schema.type, str):
                code += field_definition(field, field_schema.type, schema)
            elif isinstance(field_schema.type, list):
                class_name = ''.join(field_schema.type)
                if class_name not in globals():
                    defined_classes[class_name] = 'class %s(%s): pass\n\n' % (class_name, ', '.join(field_schema.type))
                code += field_definition(field, class_name, schema)
        return code

    code = 'class %s(Structure):\n' % name
    if hasattr(class_schema, 'description'):
        code += '    \'\'\'%s\'\'\'\n' % class_schema.description

    return code + build_code_for_fields(class_schema, defined_classes)



code = _json_to_code('jsonschema.json')
print(code)
exec(code)
