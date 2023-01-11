from collections import deque
from copy import deepcopy
from typing import Iterable

from typedpy.structures import (
    FieldMeta,
    ImmutableMixin,
    Field,
    Structure,
    TypedPyDefaults,
)
from typedpy.structures.consts import DISABLE_PROTECTION


class _CollectionMeta(FieldMeta):
    def __getitem__(cls, item):
        def validate_and_get_field(val):
            return FieldMeta.__getitem__(cls, val)

        if isinstance(item, tuple):
            items = [validate_and_get_field(it) for it in item]
            return cls(items=items)  # pylint: disable=E1120, E1123
        return cls(items=validate_and_get_field(item))  # pylint: disable=E1120, E1123


class SizedCollection:
    def __init__(self, *args, minItems=None, maxItems=None, **kwargs):
        self.minItems = minItems
        self.maxItems = maxItems
        super().__init__(*args, **kwargs)

    def validate_size(self, items, name):
        if self.minItems is not None and len(items) < self.minItems:
            raise ValueError(
                f"{name}: Expected length of at least {self.minItems}; Got {items}"
            )
        if self.maxItems is not None and len(items) > self.maxItems:
            raise ValueError(
                f"{name}: Expected length of at most {self.maxItems}; Got {items}"
            )

    # This is needed to hack the type check of typing.Optional, to allow the following syntax:
    #   x: Optional[Array[Integer]]
    def __call__(self, *args, **kwargs):
        return self


class _IteratorProxyMixin:
    class ListIteratorProxy:
        def __init__(self, the_list):
            self.the_list = the_list
            self.index = 0

        def __next__(self):
            if len(self.the_list) > self.index:
                self.index += 1
                return self.the_list[self.index - 1]
            raise StopIteration


class _ListStruct(list, ImmutableMixin, _IteratorProxyMixin):
    """
    This is a useful wrapper for the content of list in an Array field.
    It ensures that an update of the form:
     mystruct.my_array[i] = new_val
    Will not bypass the validation of the Array.
    """

    def __init__(self, array: Field, struct_instance: Structure, mylist, name: str):
        self._field_definition = array
        self._instance = struct_instance
        self._name = name
        super().__init__(self._get_defensive_copy_if_needed(mylist))

    def __setitem__(self, key, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.__setitem__(key, value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def __iter__(self):
        disable_protection = (
            getattr(self._instance, DISABLE_PROTECTION, False)
            or not TypedPyDefaults.defensive_copy_on_get
        )
        if not disable_protection and self._is_immutable():
            return _IteratorProxyMixin.ListIteratorProxy(self)
        return super().__iter__()

    def append(self, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.append(value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        super().append(value)

    def extend(self, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.extend(value)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def insert(self, index: int, value):
        self._raise_if_immutable()
        copied = self[:]
        copied.insert(index, value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def remove(self, ind):
        self._raise_if_immutable()
        copied = self[:]
        copied.remove(ind)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def copy(self):
        copied = super().copy()
        return deepcopy(copied) if self._is_immutable() else copied

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), [])

    def pop(self, index: int = -1):
        self._raise_if_immutable()
        copied = self[:]
        res = copied.pop(index)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def __getstate__(self):
        return {
            "the_instance": self._instance,
            "the_array": self._field_definition,
            "the_name": self._name,
            "the_values": self[:],
        }

    def __deepcopy__(self, memo):
        vals = [deepcopy(v) for v in self[:]]
        instance_id = id(self._instance)
        return _ListStruct(
            array=deepcopy(self._field_definition),
            struct_instance=memo.get(instance_id, self._instance),
            mylist=vals,
            name=self._name,
        )

    def __setstate__(self, state):
        self._name = state["the_name"]
        self._field_definition = state["the_array"]
        self._instance = state["the_instance"]
        super().__init__(state["the_values"])


class _DequeStruct(deque, ImmutableMixin, _IteratorProxyMixin):
    """
    This is a useful wrapper for the content of list in an Deque field.
    It ensures that an update of the form:
     mystruct.my_array[i] = new_val
    Will not bypass the validation of the Array.
    """

    def __init__(
        self,
        deq: Field = None,
        struct_instance: Structure = None,
        mydeque=None,
        name: str = None,
    ):
        self._field_definition = deq
        self._instance = struct_instance
        self._name = name
        if mydeque is not None:
            super().__init__(self._get_defensive_copy_if_needed(mydeque))

    def __setitem__(self, key, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied[key] = value
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def __iter__(self):
        disable_protection = (
            getattr(self._instance, DISABLE_PROTECTION, False)
            or not TypedPyDefaults.defensive_copy_on_get
        )
        if not disable_protection and self._is_immutable():
            return _ListStruct.ListIteratorProxy(self)
        return super().__iter__()

    def append(self, x):
        self._raise_if_immutable()
        copied = deque(self)
        copied.append(x)
        if self._field_definition:  # Python 3.6
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )
        super().append(x)

    def appendleft(self, x):
        self._raise_if_immutable()
        copied = deque(self)
        copied.appendleft(x)
        if self._field_definition:  # Python 3.6
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )
        super().append(x)

    def extend(self, iterable: Iterable):
        self._raise_if_immutable()
        copied = deque(self)
        copied.extend(iterable)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def extendleft(self, iterable: Iterable):
        self._raise_if_immutable()
        copied = deque(self)
        copied.extendleft(iterable)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

    def insert(self, i: int, x):
        self._raise_if_immutable()
        copied = deque(self)
        copied.insert(i, x)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def remove(self, value):
        self._raise_if_immutable()
        copied = deque(self)
        copied.remove(value)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def copy(self):
        copied = deque(self)
        return deepcopy(copied) if self._is_immutable() else copied

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), deque())

    def pop(self, *args, **kwargs):
        self._raise_if_immutable()
        copied = deque(self)
        res = copied.pop()
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def popleft(self):
        self._raise_if_immutable()
        copied = deque(self)
        res = copied.popleft()
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def rotate(self, n: int) -> None:  # pylint: disable=signature-differs
        self._raise_if_immutable()
        # no need to validate again
        super().rotate(n)

    def reverse(self) -> None:
        self._raise_if_immutable()
        # no need to validate again
        super().reverse()

    def __getstate__(self):
        return {
            "the_instance": self._instance,
            "field_def": self._field_definition,
            "the_name": self._name,
            "the_values": deque(self),
        }

    def __deepcopy__(self, memo):
        vals = [deepcopy(v) for v in self.copy()]
        instance_id = id(self._instance)
        return _DequeStruct(
            deq=deepcopy(self._field_definition),
            struct_instance=memo.get(instance_id, self._instance),
            mydeque=vals,
            name=self._name,
        )

    def __reduce__(self):
        res = super().__reduce__()
        return res[0], res[1], self.__getstate__(), res[3]

    def __setstate__(self, state):
        self._name = state["the_name"]
        self._field_definition = state["field_def"]
        self._instance = state["the_instance"]
        super().__init__(state["the_values"])


class _DictStruct(dict, ImmutableMixin):
    """
    This is a useful wrapper for the content of dict in an Map field.
    It ensures that an update of the form:
     mystruct.my_map[i] = new_val, or
     mystruct.my_map.update(some_dict)

    ...will not bypass the validation of the Map.
    """

    def __init__(self, the_map, struct_instance, mydict, name):
        self._field_definition = the_map
        self._instance = struct_instance
        self._name = name
        super().__init__(mydict)

    def __setitem__(self, key, value):
        super()._raise_if_immutable()
        copied = self.copy()
        copied.__setitem__(key, value)
        if getattr(self, "_instance", None):
            setattr(
                self._instance, getattr(self._field_definition, "_name", None), copied
            )

        super().__setitem__(key, value)

    def __getitem__(self, item):
        val = super().__getitem__(item)
        return self._get_defensive_copy_if_needed(val)

    def copy(self):
        copied = super().copy()
        return deepcopy(copied) if self._is_immutable() else copied

    def __deepcopy__(self, memo):
        new_dict = {deepcopy(k): deepcopy(v) for k, v in self.items()}
        instance_id = id(self._instance)
        return _DictStruct(
            the_map=self._field_definition,
            struct_instance=memo.get(instance_id, self._instance),
            mydict=new_dict,
            name=self._name,
        )

    def items(self):
        return ((k, self._get_defensive_copy_if_needed(v)) for k, v in super().items())

    def values(self):
        return (self._get_defensive_copy_if_needed(v) for v in super().values())

    def __delitem__(self, key):
        self._raise_if_immutable()
        copied = self.copy()
        del copied[key]
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)

    def update(self, *args, **kwargs):
        self._raise_if_immutable()
        copied = self.copy()
        res = copied.update(*args, **kwargs)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def pop(self, k):
        self._raise_if_immutable()
        copied = self.copy()
        res = copied.pop(k)
        setattr(self._instance, getattr(self._field_definition, "_name", None), copied)
        return res

    def clear(self) -> None:
        self._raise_if_immutable()
        setattr(self._instance, getattr(self._field_definition, "_name", None), {})

    def __getstate__(self):
        return {
            "_instance": self._instance,
            "_map": self._field_definition,
            "mydict": self.copy(),
            "_name": self._name,
        }

    def __setstate__(self, state):
        self._field_definition = state["_map"]
        self._instance = state["_instance"]
        self._name = state["_name"]
        super().__init__(state["mydict"])


class ContainNestedFieldMixin(Field):
    def _set_immutable(self, immutable: bool):
        items = getattr(self, "items", None)
        super()._set_immutable(immutable)
        if isinstance(items, Field):
            items._set_immutable(immutable)
        elif isinstance(items, (list, tuple)):
            for item in items:
                if isinstance(item, Field):
                    item._set_immutable(immutable)
