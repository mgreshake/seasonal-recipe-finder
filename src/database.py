from __future__ import annotations

import operator
import os
import re
import uuid
import warnings
from collections.abc import Callable, Container, Iterable, Iterator, Mapping
from functools import reduce
from typing import Any, Literal, TypeAlias

from tinydb import TinyDB
from tinydb import Query as TinyQuery
from tinydb.table import Table as TinyTable
from tinydb.table import Document as TinyDocument


class DatabaseMeta(type):
    """Meta class to implement singleton pattern for database interface."""

    _instances: dict[DatabaseMeta, Database] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Database:
        """Return database instance or creates new one if not existing.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Database: Singleton instance of database.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls) -> None:
        """Delete singleton instance of database."""
        try:
            del cls._instances[cls]
        except KeyError:
            pass


class Database(metaclass=DatabaseMeta):
    """Interface for database that stores information in tables and documents."""

    def __init__(self, path: str) -> None:
        """Open database file or create new one if not existing.

        Args:
            path (str): Path to database file.
        """
        if not os.path.exists(path):
            warnings.warn(f"{path} does not exist. Empty database is created.")

        self._database: TinyDB = TinyDB(path)

        for name in self._database.tables():
            self.create_table(name)

    def __getattr__(self, name: str) -> Any:
        """Return attribute matching given name.

        Args:
            name (str): Name of attribute to be returned.

        Returns:
            Any: Requested attribute.

        Raises:
            AttributeError: If attribute is not available.
        """
        try:
            return self.__getattribute__(name)
        except AttributeError:
            raise AttributeError(f"Unknown table found: {name}")

    def __iter__(self) -> Iterator[Table]:
        """Iterate through all tables in database.

        Returns:
            Iterator[Table]: Available table instances.
        """
        return (attr for name, attr in vars(self).items() if not name.startswith("_"))

    def is_empty(self) -> bool:
        """Check if database contains tables with documents.

        Returns:
            bool: `True` if database is empty, `False` otherwise.
        """
        return len(self._database.tables()) == 0

    def create_table(self, name: str, suppress_warning: bool = False) -> None:
        """Add table to database if not existing.

        Args:
            name (str): Name of table to be created.
            suppress_warning (`bool`, optional): Flag whether warning for already existing table should be suppressed.
        """
        if not hasattr(self, name):
            table = Table(self._database.table(name))
            setattr(self, name, table)
        elif not suppress_warning:
            warnings.warn(f"{name} already exists. Table is not created.")

    def get_tables(self) -> set[str]:
        """Return names of all tables in database.

        Returns:
            set[str]: Names of available tables.
        """
        return set(table.name for table in self)

    def drop_table(self, name: str, force: bool = False) -> None:
        """Remove table from database if empty.

        Args:
            name (str): Name of table to be removed.
            force (`bool`, optional). Flag whether table will be removed even if filled.
        """
        if getattr(self, name).is_empty() or force:
            self._database.drop_table(name)
            delattr(self, name)
        else:
            warnings.warn(f"{name} is not empty. Table is not dropped.")

    def insert_document(self, table: str, document: Mapping[str, Any], document_id: int | None = None) -> int:
        """Add document to database.

        If table does not exist, a new table is created.

        Args:
            table (str): Name of table where document is added.
            document (Mapping[str, Any]): Document to be added.
            document_id (`int`, optional): ID of document to be added. Generates unique ID if `None`.

        Returns:
            int: ID of added document.
        """
        if not hasattr(self, table):
            self.create_table(table)
        return getattr(self, table).insert_document(document, document_id)

    def count_documents(self) -> int:
        """Count total number of documents in database.

        Returns:
            int: Total number of documents.
        """
        if self.is_empty():
            return 0
        results = (table.count_documents() for table in self)
        return reduce(operator.__add__, results)

    def contains_document(self, document_id: int) -> bool:
        """Check if document with given ID exists in database.

        Args:
            document_id: ID of document to be searched.

        Returns:
            bool: `True` if document exists, `False` otherwise.
        """
        if self.is_empty():
            return False
        results = (table.contains_document(document_id) for table in self)
        return reduce(operator.__or__, results)

    def get_documents(self, document_ids: list[int] | None = None) -> list[Document]:
        """Return all documents in database matching given IDs.

        If no IDs are passed, all documents from the database are returned.

        Args:
            document_ids (`list[int]`, optional): IDs of documents to be returned.

        Returns:
            list[Document]: Requested documents.
        """
        if self.is_empty():
            return []
        results = (table.get_documents(document_ids) for table in self)
        return reduce(operator.__add__, results)


class Table:
    """Interface for table that contains documents."""

    def __init__(self, table: TinyTable) -> None:
        """Wrap table from TinyDB into separate object.

        Args:
            table (TinyTable): Table to be wrapped.
        """
        self._table: TinyTable = table

    @property
    def name(self) -> str:
        """str: Table name."""
        return self._table.name

    def is_empty(self) -> bool:
        """Check if table contains documents.

        Returns:
            bool: `True` if table is empty, `False` otherwise.
        """
        return len(self._table) == 0

    def insert_document(self, document: Mapping[str, Any], document_id: int | None = None) -> int:
        """Add document to table.

        Args:
            document (Mapping[str, Any]): Document to be added.
            document_id (`int`, optional): ID of document to be added. Generates unique ID if `None`.

        Returns:
            int: ID of added document.
        """
        if document_id is None:
            document_id = self._generate_document_id()
        return self._table.insert(TinyDocument(document, doc_id=document_id))

    @staticmethod
    def _generate_document_id() -> int:
        """Generate unique document ID based on UUID.

        Returns:
            int: Document ID.
        """
        return uuid.uuid1().int >> 64

    def count_documents(self) -> int:
        """Count total number of documents in table.

        Returns:
            int: Total number of documents.
        """
        return len(self._table)

    def contains_document(self, document_id: int) -> bool:
        """Check if document with given ID exists in table.

        Args:
            document_id: ID of document to be searched.

        Returns:
            bool: `True` if document exists, `False` otherwise.
        """
        return self._table.contains(doc_id=document_id)

    def get_documents(self, document_ids: list[int] | None = None) -> list[Document]:
        """Return all documents in table matching given IDs.

        If no IDs are passed, all documents from the table are returned.

        Args:
            document_ids (`list[int]`, optional): IDs of documents to be returned.

        Returns:
            list[Document]: Requested documents.
        """
        if not document_ids:
            return self._table.all()
        return [Document(document) for document in self._table.get(doc_ids=document_ids)]

    def update_documents(self, document_ids: Iterable[int], fields: Mapping[str, Any]) -> None:
        """Update all documents in table matching given IDs.

        Fields that do not exist in documents are added.

        Args:
            document_ids (Iterable[int]): IDs of documents to be updated.
            fields (Mapping[str, Any]): Fields of documents with values to be updated.
        """
        filtered_document_ids = self._filter_existing_document_ids(document_ids)
        self._table.update(fields, doc_ids=filtered_document_ids)

    def remove_documents(self, document_ids: Iterable[int]) -> None:
        """Remove all documents from table matching given IDs.

        Args:
            document_ids (Iterable[int]): IDs of documents to be removed.
        """
        filtered_document_ids = self._filter_existing_document_ids(document_ids)
        self._table.remove(doc_ids=filtered_document_ids)

    def _filter_existing_document_ids(self, document_ids: Iterable[int]) -> Iterator[int]:
        """Filter for existing document IDs and reports missing ones.

        Args:
            document_ids (Iterable[int]): Document IDs to be filtered.

        Yields:
            int: Existing document IDs.
        """
        missing_document_ids = set()

        for document_id in document_ids:
            if self.contains_document(document_id):
                yield document_id
            else:
                missing_document_ids.add(document_id)

        if missing_document_ids:
            warnings.warn(f"Unknown document IDs found: {', '.join(map(str, missing_document_ids))}")

    def search(self, condition: str = "", sort_by: SortOptions | None = None) -> list[Document]:
        """Search for all documents in table matching given condition.

        If no condition is passed, all documents from the table are returned.

        Args:
            condition (`str`, optional): Condition to be matched.
            sort_by (`SortOptions`, optional): Fields, possibly with sort order, according to which documents are
                sorted. Priority of arguments is in descending order. Documents are not sorted by default.

        Returns:
            list[Document]: Queried documents.
        """
        query = _Query(self, condition)

        query.evaluate()
        if sort_by is not None:
            query.sort(sort_by)

        return query.results


class Document:
    """Interface for document that contains data."""

    def __init__(self, document: TinyDocument) -> None:
        """Wrap document from TinyDB into separate object.

        Args:
            document (TinyDocument): Document to be wrapped.
        """
        self._document: TinyDocument = document

    def __getitem__(self, field: str) -> Any:
        """Return value of specified field.

        Args:
            field (str): Field name.

        Returns:
            Any: Value of requested field.
        """
        return self._document[field]

    def __eq__(self, other: Mapping[str, Any]) -> bool:
        """Compare document with given mapping.

        Args:
            other (Mapping[str, Any]): Mapping to be compared.

        Returns:
            bool: `True` if mapping is equal to document, `False` otherwise.
        """
        return self._document == other

    def __str__(self) -> str:
        """Return string representation of document.

        Returns:
            str: Content of document.
        """
        return str(self._document)

    @property
    def id(self) -> int:
        """int: Document ID."""
        return self._document.doc_id

    @property
    def fields(self) -> Mapping[str, Any]:
        """Mapping[str, Any]: Document fields."""
        return self._document


SortCriterion: TypeAlias = str | Callable[[Document], Any]

SortOrder: TypeAlias = Literal["asc", "desc"]

SortOptions: TypeAlias = SortCriterion | Iterable[SortCriterion] | Mapping[SortCriterion, SortOrder]


class _Query:
    """Interface for query that searches table for documents."""

    def __init__(self, table: Table, condition: str = "") -> None:
        """Set table and parses condition.

        Args:
            table (Table): Table to be searched.
            condition (`str`, optional): Condition to be matched. Search for all documents by default.
        """
        self._table: Table = table
        self._query: str = f"self._table.search({self._parse(condition)})" if condition else "self._table.all()"
        self._results: list[TinyDocument] | None = None
        self._order: list[int] | None = None

    @staticmethod
    def _parse(condition: str) -> str:
        """Parse condition into valid TinyDB query."""
        if match := re.match(r"\((.+)\) ([&|]) \((.+)\)", condition):
            return f"({_Query._parse(match.group(1))}) {match.group(2)} ({_Query._parse(match.group(3))})"
        elif match := re.match(r"(\w+)\.contains\((.+)\)", condition):
            return f"Query().{match.group(1)}.test(lambda x: contains(x, {match.group(2)}))"
        elif match := re.match(r"(\w+)\.(.+)", condition):
            return f"Query().{match.group(1)}.any({_Query._parse(match.group(2))})"
        else:
            return f"Query().{condition}"

    def __getattr__(self, name: str) -> Any:
        """Return attribute matching given name. Raise warning if query results are not available yet.

        Args:
            name (str): Name of attribute to be returned.

        Returns:
            Any: Requested attribute.
        """
        attr = self.__getattribute__(name)
        if name == "_results" and attr is None:
            warnings.warn("No query results available. Invoke 'evaluate' method first.")
            return []
        return attr

    @property
    def results(self) -> list[Document]:
        """list[Document]: Query results if available."""
        indices = range(len(self._results)) if self._order is None else self._order
        return [Document(self._results[index]) for index in indices]

    def evaluate(self) -> None:
        """Evaluate query and store results.

        Raises:
            InvalidQueryError: If malformed query is tried to evaluate.
        """
        try:
            namespace = {"__builtins__": None, "self": self._table, "Query": TinyQuery, "contains": self._contains}
            self._results = eval(self._query, namespace)
        except Exception as error:
            raise InvalidQueryError(error)
 
    @staticmethod
    def _contains(container: Container, item: Any) -> bool:
        """Check if item is part of container. Strings are normalized before."""
        if isinstance(container, str):
            container = container.strip().lower()
            item = item.strip().lower()
        return container.__contains__(item)

    def sort(self, fields: SortOptions) -> None:
        """Sort results by specified criteria.

        If no sort order is passed, results are sorted in ascending order.

        Args:
            fields (SortOptions): Either field name, custom function, sequence of criteria or mapping of criteria with
                sort order.
        """
        def get_sorting_key(index: int) -> tuple[bool, Any]:
            document = Document(self._results[index])
            value = field(document) if isinstance(field, Callable) else document[field]
            return (value is None) != is_descending_order, value

        if isinstance(fields, str | Callable):
            fields = {fields: "asc"}
        elif isinstance(fields, Iterable) and not isinstance(fields, Mapping):
            fields = {field: "asc" for field in fields}

        indices = range(len(self._results))

        for field, order in reversed(fields.items()):
            is_descending_order = order == "desc"
            indices = sorted(indices, key=lambda index: get_sorting_key(index), reverse=is_descending_order)

        self._order = indices


class InvalidQueryError(Exception):
    """Exception that is raised when an invalid query is passed."""

    def __init__(self, error: Exception) -> None:
        """Pass message of raised error to exception.

        Args:
            error (Exception): Error raised during execution of query.
        """
        super().__init__(f"{type(error).__name__} raised while executing query: {error.args[0]}")
