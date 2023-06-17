import datetime
from collections import deque

import typing


def convert_basic_types(v):
    from typedpy.fields import (
        Integer,
        Float,
        String,
        Map,
        Array,
        Tuple,
        Set,
        Boolean,
        ImmutableSet,
        AnyOf,
        Anything,
        Deque,
    )
    from typedpy.extfields import DateField, DateTime, TimeField

    type_mapping = {
        deque: Deque,
        int: Integer,
        str: String,
        float: Float,
        dict: Map,
        set: Set,
        list: Array,
        tuple: Tuple,
        bool: Boolean,
        frozenset: ImmutableSet,
        datetime.date: DateField,
        datetime.datetime: DateTime,
        datetime.time: TimeField,
        typing.Union: AnyOf,
        typing.Any: Anything,
    }
    return type_mapping.get(v, None)
