from datetime import datetime
from typing import Optional

from typedpy import create_pyi


class Base:
    base1: int = 5
    base2: list
    base3 = {"x": 1}


class JobController(Base):
    CONST_ID = 5
    CONST_ID_WITH_ANNOTATION: str

    def __init__(self, urls: dict[str, dict]):
        self.urls = urls

    def execute(self, job_id: str):
        pass

    def aaa(self, a: list[datetime] = list, o: Optional[str] = None):
        pass


if __name__ == "__main__":
    create_pyi(__file__, locals())
