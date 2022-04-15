from typing import Union, Optional, Any
from typedpy import Structure
import enum

from typedpy import create_pyi


class State(enum.Enum):
    NY = "ny"
    NJ = "nj"
    AL = "al"
    FL = "fl"


class Sex(enum.Enum):
    male = 1
    female = 2
