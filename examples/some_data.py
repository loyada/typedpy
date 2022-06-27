from dataclasses import dataclass
from typing import Optional, TypedDict


@dataclass
class SomeData:
    a: int
    s: str
    s_opt: Optional[str]


FROZEN = frozenset([1, 2, 3])

Point2D = TypedDict("Point2D", x=int, y=int, label=str)
