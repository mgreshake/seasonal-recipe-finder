from __future__ import annotations

from collections import UserDict, UserList, namedtuple
from collections.abc import Collection, Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, cast, overload


_DictValueT = TypeVar("_DictValueT")

_EntryDataT = TypeVar("_EntryDataT")

_ListItemT = TypeVar("_ListItemT")


_EnumItem = namedtuple("_EnumItem", ["name", "value"])

_ListEntry = namedtuple("_ListEntry", ["label", "data"])


class Enum(UserDict):
    """Immutable enumeration based on bidirectional dictionary."""

    def __init__(self, collection: Collection[str] | None = None, start_value: int = 0) -> None:
        """Initialize enumeration of given items.

        Args:
            collection (Collection[str]): Items to be enumerated.
            start_value (`int`, optional): Value at which enumeration starts. Defaults to 0.
        """
        super().__init__()

        self._values: dict[int, str] = {}

        if collection:
            values = range(start_value, start_value + len(collection))
            for name, value in zip(collection, values):
                super().__setitem__(name, value)
            self._values.update(zip(values, collection))

    def __getattr__(self, name: str) -> _EnumItem:
        """Return item matching given name.

        Args:
            name (str): Name of item to be returned.

        Returns:
            _EnumItem: Requested item.

        Raises:
            AttributeError: If item with given name does not exist.
        """
        try:
            return _EnumItem(name, self[name])
        except KeyError:
            raise AttributeError(f"No item with name '{name}' found.")

    def __call__(self, value: int) -> _EnumItem:
        """Return item matching given value.

        Args:
            value (int): Value of item to be requested.

        Returns:
            _EnumItem: Requested item.

        Raises:
            ValueError: If item with given value does not exist.
        """
        try:
            return _EnumItem(self._values[value], value)
        except KeyError:
            raise ValueError(f"No item with value '{value}' found.")

    def __setitem__(self, key: str, item: _DictValueT) -> None:
        """Disable item assignment."""
        raise TypeError(f"{self.__class__.__name__} is immutable. Item assignment is not supported.")

    def __delitem__(self, key: str) -> None:
        """Disable item removal."""
        raise TypeError(f"{self.__class__.__name__} is immutable. Item removal is not supported.")


class LiteralDict(UserDict, Generic[_DictValueT]):
    """Immutable dictionary that has a fixed set of keys."""

    def __init__(self, mapping: Mapping[str, _DictValueT] | None = None, /, **kwargs: _DictValueT) -> None:
        """Define keys and values of dictionary.

        Args:
            mapping (`Mapping[str, _DictValueT]`, optional): Key-value pairs as mapping.
            **kwargs (_DictValueT): Key-value pairs as keyword arguments.
        """
        super().__init__()

        if mapping is not None:
            for key, value in mapping.items():
                super().__setitem__(key, value)

        if kwargs:
            for key, value in kwargs.items():
                super().__setitem__(key, value)

    def __getitem__(self, key: str) -> _DictValueT:
        """Return value of specified literal.

        Args:
            key (str): String literal.

        Returns:
            _DictValueT: Value of requested literal.

        Raises:
            KeyError: If requested literal is not supported.
        """
        try:
            return super().__getitem__(key)
        except KeyError:
            raise KeyError(f"Invalid key found: {key}. Possible options are {list(self)}.")

    def __setitem__(self, key: str, item: _DictValueT) -> None:
        """Disable item assignment."""
        raise TypeError(f"{self.__class__.__name__} is immutable. Item assignment is not supported.")

    def __delitem__(self, key: str) -> None:
        """Disable item removal."""
        raise TypeError(f"{self.__class__.__name__} is immutable. Item removal is not supported.")


class ListEntries(Generic[_EntryDataT]):
    """Collection of key-value pairs that represent labels and their corresponding data."""

    def __init__(self, collection: Iterable[Any] | None = None, /, **kwargs: _EntryDataT) -> None:
        """Initialize entries where keys are converted to strings. If sequence is passed, labels are set as data.

        Args:
            collection (`Iterable[Any]`, optional): Labels and corresponding data if available.
            **kwargs (_EntryDataT): List entries as key-value pairs.

        Raises:
            TypeError: If passed arguments are neither iterable nor `None`.
        """
        match collection:
            case None:
                entries = []
            case Mapping():
                entries = [ListEntry(key, collection[key]) for key in collection]
            case Iterable():
                entries = [ListEntry(item) for item in collection]
            case _:
                raise TypeError(f"'{collection}' cannot be parsed to list entries")

        self._entries: list[ListEntry[_EntryDataT]] = entries + [ListEntry(item) for item in kwargs.items()]

    def __getitem__(self, index: int) -> ListEntry[_EntryDataT]:
        """Return entry at specified index.

        Args:
            index (int): Index of list entry.

        Returns:
            ListEntry[_EntryDataT]: Entry at requested index.
        """
        return self._entries[index]

    def __iter__(self) -> Iterator[ListEntry[_EntryDataT]]:
        """Iterate over list entries.

        Yields:
            ListEntry[_EntryDataT]: Entry labels with corresponding data.
        """
        yield from self._entries

    def __len__(self) -> int:
        """Return number of list entries.

        Returns:
            int: Number of list entries.
        """
        return len(self._entries)

    def __eq__(self, other: Any) -> bool:
        """Compare list entries with other object.

        Args:
            other (Any): Object to be compared.

        Returns:
            bool: `True` if object is equal to entries, `False` otherwise.
        """
        return self._entries == other

    def __str__(self) -> str:
        """Return string representation of internal collection.

        Returns:
            str: Entry labels with corresponding data.
        """
        return str(self._entries)

    @property
    def labels(self) -> _List[str]:
        """list[str]: Labels of all entries."""
        return _List(entry.label for entry in self._entries)

    @property
    def data(self) -> _List[_EntryDataT]:
        """list[_EntryDataT]: Linked data of all entries."""
        return _List(entry.data for entry in self._entries)


class ListEntry(_ListEntry, Generic[_EntryDataT]):
    """Key-value pair consisting of label and corresponding data."""

    __slots__ = ()

    @overload
    def __new__(cls, entry: tuple[Any, _EntryDataT]) -> ListEntry[_EntryDataT]:
        ...

    @overload
    def __new__(cls, label: Any, data: _EntryDataT | None = None) -> ListEntry[_EntryDataT]:
        ...

    def __new__(cls, entry_or_label: Any, data: _EntryDataT | None = None) -> ListEntry[_EntryDataT]:
        """Convert label to string. If no data is passed, use label instead."""
        if cls._is_pair(entry_or_label):
            entry = str(entry_or_label[0]), entry_or_label[1]
        else:
            entry = str(entry_or_label), data if data is not None else entry_or_label

        return cast(ListEntry, super().__new__(cls, *entry))

    @staticmethod
    def _is_pair(value: Any) -> bool:
        """Check if value is tuple with two elements."""
        return isinstance(value, tuple) and len(value) == 2


class _List(UserList, Generic[_ListItemT]):
    """Custom list whose index function returns `-1` if item is not found instead of raising exception."""

    def index(self, item: _ListItemT, *args: Any) -> int:
        """Return index of first occurrence of specified item from list.

        Args:
            item (_ListItemT): Item for which index is requested.
            *args (Any): Variable length argument list.

        Returns:
            int: Index of requested item if it appears in list, `-1` otherwise.
        """
        try:
            return super().index(item, *args)
        except ValueError:
            return -1
