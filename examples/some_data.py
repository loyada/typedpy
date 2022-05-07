from dataclasses import dataclass
from typing import Optional


@dataclass
class SomeData:
    a: int
    s: str
    s_opt: Optional[str]
