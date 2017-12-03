import json

from typedpy import *


class Person(Structure):
    _required = ['ssid']
    name = String(pattern='[A-Za-z]+$', maxLength=8)
    ssid = String(minLength = 3, pattern = '[A-Za-z]+$')
    num = Integer(maximum=30, minimum=10, multiplesOf="dd", exclusiveMaximum=False)
    aaa = String
    #embedding "inline" structures as fields
    #equivalent to :
    # foo: {
    #     type: object,
    #     properties: {
    #          a: {
    #              type: string
    #          },
    #          b: {
    #            type: object,
    #            properties: {
    #                 c: {
    #                   type: number,
    #                   minimum: 10
    #                 },
    #                 d: {
    #                   type: number,
    #                   maximum: 10
    #                 },
    #            }
    #          }
    #     }
    # }
    foo = StructureReference(a=String(), b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))

# Inherited Structure. Note:
# - adding a new attribute "children"
# - overriding attribute "num" from Person to a new type
# - expecting the required fields to be: ssid (from Person), children, num
# - attributes ssid, foo, name are inherited from num
class OldPerson(Person):
    children = PositiveInt()
    num = PositiveInt()


class Trade(Structure):
    _additionalProperties = True
    _required = ['tradable', 'quantity', 'price']
    tradable = String()
    counterparty1 = String()
    counterparty2 = String()
    quantity = AnyOf([PositiveInt(), Enum(values=['asds', 'ddd', 'cxczx'])])
    price = PositiveFloat()
    category = EnumString(values = ['a','b'])

    #class referece: to another Structure
    person = Person

    #array support, similar to json schema
    children = Array(uniqueItems=True, minItems= 3, items = [String(), Number(maximum=10)])


op = OldPerson(children = 1, num=1, ssid = "aaa")
print(Person)


p = Person(name="fo", ssid="fff", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
p.foo.b.c = 15
t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = ['aa', 3, 2])
t.person = p
print (t.person.name)
print(Person.name)
print(p)
t.children[1] = 8
print(t)

class Foo(Person):
    def __init__(self, *args, x, y, **kwargs):
        self.x = x
        self.y = y
        super().__init__(*args, **kwargs)

    def multiply(self):
        return self.x*self.y*self.num


foo = Foo(ssid = "abc", num = 10, x = 2, y = 3)
print(foo.multiply())

import pprint
pp = pprint.PrettyPrinter(indent=4)

class SimpleStruct(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)

class Example(Structure):
    i = Integer(maximum=10)
    s = String(maxLength=5)
    a = Array[Integer(multiplesOf=5), Number]
    foo = StructureReference(a1 = Integer(), a2=Float())
    ss = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1,2,3])


schema, definitions = structure_to_schema(Example, {})
schema['definitions'] = definitions
print(json.dumps(schema, indent=4))
del schema['definitions']
print("\n**************************\n")

print(schema_definitions_to_code(definitions))
print("\n\n")
print(schema_to_struct_code('Duba', schema, definitions))