
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

op.aaa = 3

p = Person(name="fo", ssid="fff", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
p.foo.b.c = 15
t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = ['aa', 3, 2])
t.person = p
print (t.person.name)
print(Person.name)
print(p)
t.children[1] = 8
print(t)
