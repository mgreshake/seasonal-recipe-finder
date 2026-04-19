import os
import warnings

import pytest

from database import Database, InvalidQueryError


@pytest.fixture(scope="class")
def database_with_empty_table(database):
    database.create_table("test_table")
    yield database
    database.drop_table("test_table")


@pytest.fixture(scope="class")
def database_with_documents(database):
    database.insert_document("test_table", {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]})
    database.insert_document("test_table", {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]})
    database.insert_document("test_table", {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]})
    yield database
    database.drop_table("test_table", force=True)


class TestDatabase:

    def test_create_empty_database(self):
        path = "test_database.json"
        assert not os.path.exists(path)

        Database(path)
        assert os.path.exists(path)

        Database.clear()
        os.remove(path)

    def test_missing_database_raises_warning_on_creation(self):
        path = "test_database.json"
        assert not os.path.exists(path)

        message = f"{path} does not exist. Empty database is created."
        with pytest.warns(UserWarning, match=message):
            Database(path)

        Database.clear()
        os.remove(path)

    def test_create_singleton_instance(self, database):
        path = "test_database.json"
        assert os.path.exists(path)

        database_2 = Database(path)
        assert id(database) == id(database_2)

    def test_check_if_database_is_empty(self, database):
        assert database.is_empty()


class TestTables:

    @pytest.fixture(autouse=True)
    def _empty_database(self, database):
        self.database = database

    def test_return_no_tables_from_empty_database(self):
        assert self.database.is_empty()
        assert self.database.get_tables() == set()

    def test_create_empty_table(self):
        name = "test_table"
        assert name not in self.database.get_tables()

        self.database.create_table(name)
        assert name in self.database.get_tables()

        delattr(self.database, name)

    def test_existing_table_raises_warning_on_creation(self):
        name = "test_table"
        self.database.create_table(name)
        assert name in self.database.get_tables()

        message = f"{name} already exists. Table is not created."
        with pytest.warns(UserWarning, match=message):
            self.database.create_table(name)

        delattr(self.database, name)

    def test_suppress_warning_for_existing_table(self):
        name = "test_table"
        self.database.create_table(name)
        assert name in self.database.get_tables()

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.database.create_table(name, suppress_warning=True)

        delattr(self.database, name)

    def test_check_if_table_is_empty(self):
        name = "test_table"
        self.database.create_table(name)
        assert getattr(self.database, name).is_empty()

        delattr(self.database, name)

    def test_drop_empty_table(self):
        name = "test_table"
        self.database.create_table(name)
        assert getattr(self.database, name).is_empty()

        self.database.drop_table(name)
        assert name not in self.database.get_tables()

    def test_return_all_tables_from_database(self):
        self.database.create_table("test_table_1")
        self.database.create_table("test_table_2")
        assert self.database.get_tables() == {"test_table_1", "test_table_2"}

        for name in self.database.get_tables():
            self.database.drop_table(name)

    def test_missing_table_raises_error_on_access(self):
        name = "test_table"
        assert name not in self.database.get_tables()

        message = f"Unknown table found: {name}"
        with pytest.raises(AttributeError, match=message):
            getattr(self.database, name).is_empty()


class TestDocuments:

    @pytest.fixture(autouse=True)
    def _database_with_empty_table(self, database_with_empty_table):
        self.database = database_with_empty_table

    def test_return_no_documents_from_empty_database(self):
        assert self.database.is_empty()
        assert self.database.get_documents() == []

    def test_add_document_to_existing_table(self):
        table = "test_table"
        assert table in self.database.get_tables()

        document = {"dummy": "foo"}
        document_id = self.database.insert_document(table, document)
        assert self.database.get_documents([document_id]) == [document]

        getattr(self.database, table)._table.remove(doc_ids=[document_id])

    def test_check_if_table_contains_specific_document(self):
        table = "test_table"
        document_id = self.database.insert_document(table, {"dummy": "foo"})
        assert self.database.contains_document(document_id)

        getattr(self.database, table)._table.remove(doc_ids=[document_id])

    def test_remove_document_from_table(self):
        table = "test_table"
        document_id = self.database.insert_document(table, {"dummy": "foo"})
        assert self.database.contains_document(document_id)

        getattr(self.database, table).remove_documents([document_id])
        assert not self.database.contains_document(document_id)

    def test_missing_document_raises_warning_on_deletion(self):
        document_id = 0
        assert not self.database.contains_document(document_id)

        message = f"Unknown document IDs found: {document_id}"
        with pytest.warns(UserWarning, match=message):
            self.database.test_table.remove_documents([document_id])

    def test_add_document_with_fixed_id(self):
        table = "test_table"
        document_id = 1
        assert not self.database.contains_document(document_id)

        document = {"dummy": "foo"}
        self.database.insert_document(table, document, document_id)
        assert self.database.get_documents([document_id]) == [document]

        getattr(self.database, table).remove_documents([document_id])

    def test_duplicate_document_id_raises_error_on_insertion(self):
        table = "test_table"
        document_id = 1
        self.database.insert_document(table, {"dummy": "foo"}, document_id)
        assert self.database.contains_document(document_id)

        message = f"Document with ID {document_id} already exists"
        with pytest.raises(ValueError, match=message):
            self.database.insert_document(table, {"dummy": "bar"}, document_id)

        getattr(self.database, table).remove_documents([document_id])

    def test_count_documents_in_table(self):
        table = "test_table"
        assert getattr(self.database, table).is_empty()

        document_id = self.database.insert_document(table, {"dummy": "foo"})
        assert self.database.count_documents() == 1

        getattr(self.database, table).remove_documents([document_id])

    def test_return_specific_documents_from_table(self):
        table = "test_table"
        documents = [{"dummy": "foo"}, {"dummy": "bar"}, {"dummy": None}]
        document_ids = [self.database.insert_document(table, document) for document in documents]
        assert self.database.get_documents(document_ids[:2]) == documents[:2]

        getattr(self.database, table).remove_documents(document_ids)

    def test_filled_table_raises_warning_on_deletion(self):
        table = "test_table"
        document_id = self.database.insert_document(table, {"dummy": "foo"})
        assert not getattr(self.database, table).is_empty()

        message = f"{table} is not empty. Table is not dropped."
        with pytest.warns(UserWarning, match=message):
            self.database.drop_table(table)

        getattr(self.database, table).remove_documents([document_id])

    def test_force_deletion_of_filled_table(self):
        table = "test_table"
        self.database.insert_document(table, {"dummy": "foo"})
        assert not getattr(self.database, table).is_empty()

        self.database.drop_table(table, force=True)
        assert table not in self.database.get_tables()

        self.database.create_table(table)

    def test_add_document_to_new_table(self):
        table = "test_table_2"
        assert table not in self.database.get_tables()

        document = {"dummy": "foo"}
        document_id = self.database.insert_document(table, document)
        assert self.database.get_documents([document_id]) == [document]

        self.database.drop_table(table, force=True)

    def test_return_all_documents_from_database(self):
        documents = [{"dummy": "foo"}, {"dummy_2": [{"a": 42, "b": 73}]}]
        self.database.insert_document("test_table", documents[0])
        self.database.insert_document("test_table_2", documents[1])
        assert self.database.get_documents() == documents

        for table in self.database.get_tables():
            self.database.drop_table(table, force=True)
        self.database.create_table("test_table")

    def test_update_existing_field_in_document(self):
        table = "test_table"
        document_id = self.database.insert_document(table, {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]})
        assert self.database.contains_document(document_id)

        getattr(self.database, table).update_documents([document_id], {"dummy": "bar"})
        assert self.database.get_documents([document_id]) == [{"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]}]

        getattr(self.database, table).remove_documents([document_id])

    def test_add_new_field_to_document(self):
        table = "test_table"
        document_id = self.database.insert_document(table, {"dummy": "foo"})
        assert self.database.contains_document(document_id)

        getattr(self.database, table).update_documents([document_id], {"dummy_2": [{"a": 42, "b": 73}]})
        assert self.database.get_documents([document_id]) == [{"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]}]

        getattr(self.database, table).remove_documents([document_id])

    def test_missing_document_raises_warning_on_update(self):
        document_id = 0
        assert not self.database.contains_document(document_id)

        message = f"Unknown document IDs found: {document_id}"
        with pytest.warns(UserWarning, match=message):
            self.database.test_table.update_documents([document_id], {"dummy": "foo"})


class TestQueries:

    @pytest.fixture(autouse=True)
    def _table_with_documents(self, database_with_documents):
        self.table = database_with_documents.test_table

    @staticmethod
    def get_first_value(document):
        return document["dummy_2"][0]["a"]

    def test_query_all_documents_from_table(self):
        documents = [
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
        ]
        assert self.table.get_documents() == documents

        results = self.table.search()
        assert results == documents

    def test_query_documents_matching_value(self):
        results = self.table.search("dummy == 'foo'")
        assert results == [{"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]}]

    def test_query_documents_not_matching_value(self):
        results = self.table.search("dummy != 'bar'")
        assert results == [
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
        ]

    def test_query_documents_containing_value(self):
        results = self.table.search("dummy.contains('ba')")
        assert results == [
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
        ]

    def test_evaluate_condition_with_nested_field(self):
        results = self.table.search("dummy_2.a == 42")
        assert results == [
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
        ]

    def test_evaluate_conditions_with_logical_and(self):
        results = self.table.search("(dummy.contains('ba')) & (dummy_2.a == 42)")
        assert results == [{"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]}]

    def test_evaluate_conditions_with_logical_or(self):
        results = self.table.search("(dummy.contains('ba')) | (dummy_2.a == 42)")
        assert results == [
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
        ]

    def test_sort_results_by_field_name(self):
        results = self.table.search(sort_by="dummy")
        assert results == [
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
        ]

    def test_sort_results_by_custom_function(self):
        results = self.table.search(sort_by=self.get_first_value)
        assert results == [
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
        ]

    def test_sort_results_by_multiple_criteria(self):
        results = self.table.search(sort_by=[self.get_first_value, "dummy"])
        assert results == [
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
        ]

    def test_sort_results_in_descending_order(self):
        results = self.table.search(sort_by={"dummy": "desc"})
        assert results == [
            {"dummy": "foo", "dummy_2": [{"a": 42, "b": 73}]},
            {"dummy": "baz", "dummy_2": [{"a": 3.141, "b": None}]},
            {"dummy": "bar", "dummy_2": [{"a": 42, "b": 73}]},
        ]

    def test_invalid_query_raises_error_on_execution(self):
        message = "RuntimeError raised while executing query: Empty query was evaluated"
        with pytest.raises(InvalidQueryError, match=message):
            self.table.search("print('This is a test')")
