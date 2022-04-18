from examples.api_example import Foo
from typedpy import Omit, create_pyi

from examples.subpackage.apis import Vehicle

class FooOmitSubPackage(Omit[Foo, ("a", "b")]):
    x: int


if __name__ == "__main__":
    create_pyi(__file__, locals())
