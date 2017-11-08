# typed-py

Typesafe Python structures



## Example 1
```python
class Person(Structure):
    name = String(pattern='[A-Za-z]+$', maxLength=8)
    ssid = String(minLength = 3, pattern = '[A-Za-z]+$')
    num = Integer(maximum=30, minimum=10, multiplesOf=5, exclusiveMaximum=False)
    foo = StructureReference(a=String(), b = StructureReference(c = Number(minimum=10), d = Number(maximum=10)))
    

Person(name="fo d", ssid="fff", num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
{ValueError}name: Does not match regular expression: [A-Za-z]+$

Person(name="fo", ssid=4, num=25, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
{TypeError}ssid: Expected a string


Person(name="fo", ssid="aaa", num=33, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})
{ValueError}num: Expected a maxmimum of 30

Person(name="fo", ssid="aaa", num=10, foo = {'a': 'aaa', 'b': {'c': 0, 'd': 1}})
{ValueError}c: Expected a minimum of 10


Person(name="fo", ssid="aaa", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
{TypeError}c: Expected a number

Person(ssid="aaa", num=10, foo = {'a': 'aaa', 'b': {'c': "", 'd': 1}})
{TypeError}missing a required argument: 'name'

p = Person(name ="aaa", ssid="aaa", num=10, foo = {'a': 'aaa', 'b': {'c': 10, 'd': 1}})

p.num
10

p.num-=1
ValueError: num: Expected a minimum of 10

p.foo.b.d 
1

p.foo.b = {'d': 1}
TypeError: missing a required argument: 'c'

p.foo.b.d = 99
ValueError: d: Expected a maxmimum of 10

```


## Example 2
```python
class Trade(Structure):
    _additionalProperties = True
    _required = ['tradable', 'quantity', 'price']
    tradable = String()
    counterparty1 = String()
    counterparty2 = String()
    quantity = AnyOf([PositiveInt(), Enum(values=['asds', 'ddd', 'cxczx'])])
    price = PositiveFloat()
    category = EnumString(values = ['a','b'])
    person = ClassReference(Person)
    children = Array(uniqueItems=True, minItems= 3, items = [String(), Number(maximum=10)])

t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = [ 3, 2])
ValueError: children: Expected length of at least 3

t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = [ 1,3, 2])
TypeError: children_0: Expected a string

t = Trade(tradable="foo", quantity='ddd', price=10.0, category= 'a', children = [ "a",3, 2])
t.children[1]
3

t.children[1] = None
TypeError: children_1: Expected a number

t.children[1] = 3
t.children[1]
3

t.person = p
t.person.name
fo  

t.person.name = None
TypeError: name: Expected a string

# quantity can also be a positive int
t.quantity = 30
t.quantity
30
```