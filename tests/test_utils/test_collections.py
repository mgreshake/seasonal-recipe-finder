import re

import pytest

from utils.collections import Enum, ListEntries, ListEntry, LiteralDict


class TestEnum:

    def test_create_empty_enum(self):
        assert Enum() == {}

    def test_create_enum(self):
        items = {"foo": 0, "bar": 1}
        enum = Enum(items.keys())
        assert enum == items

    def test_create_enum_starting_from_different_value(self):
        items = {"foo": 1, "bar": 2}
        enum = Enum(items.keys(), start_value=1)
        assert enum == items

    def test_get_value_from_specific_item(self):
        enum = Enum(["foo", "bar"])
        assert enum["foo"] == 0

    def test_get_item_by_name(self):
        enum = Enum(["foo", "bar"])
        assert enum.foo == ("foo", 0)

    def test_unknown_name_raises_error_on_access(self):
        message = "No item with name 'baz' found."
        with pytest.raises(AttributeError, match=message):
            _ = Enum(["foo", "bar"]).baz

    def test_get_item_by_value(self):
        enum = Enum(["foo", "bar"])
        assert enum(0) == ("foo", 0)

    def test_unknown_value_raises_error_on_access(self):
        message = "No item with value '0' found."
        with pytest.raises(ValueError, match=message):
            Enum(["foo", "bar"], start_value=1)(0)

    def test_set_item_raises_error(self):
        message = "Enum is immutable. Item assignment is not supported."
        with pytest.raises(TypeError, match=message):
            Enum(["foo", "bar"])["baz"] = 2

    def test_delete_item_raises_error(self):
        message = "Enum is immutable. Item removal is not supported."
        with pytest.raises(TypeError, match=message):
            del Enum(["foo", "bar"])["foo"]


class TestLiteralDict:

    def test_create_empty_literal_dict(self):
        assert LiteralDict() == {}

    def test_create_literal_dict_from_mapping(self):
        mapping = {"foo": 1, "bar": 2}
        literal_dict = LiteralDict(mapping)
        assert literal_dict == mapping

    def test_create_literal_dict_from_keywords(self):
        mapping = {"foo": 1, "bar": 2}
        literal_dict = LiteralDict(**mapping)
        assert literal_dict == mapping

    def test_get_value_from_specific_literal(self):
        literal_dict = LiteralDict({"foo": 1, "bar": 2})
        assert literal_dict["foo"] == 1

    def test_unknown_literal_raises_error_on_access(self):
        message = "Invalid key found: baz. Possible options are ['foo', 'bar']."
        with pytest.raises(KeyError, match=re.escape(message)):
            _ = LiteralDict({"foo": 1, "bar": 2})["baz"]

    def test_set_literal_raises_error(self):
        message = "LiteralDict is immutable. Item assignment is not supported."
        with pytest.raises(TypeError, match=message):
            LiteralDict({"foo": 1, "bar": 2})["baz"] = 3

    def test_delete_literal_raises_error(self):
        message = "LiteralDict is immutable. Item removal is not supported."
        with pytest.raises(TypeError, match=message):
            del LiteralDict({"foo": 1, "bar": 2})["foo"]


class TestListEntries:

    def test_create_empty_list_entries(self):
        list_entries = ListEntries()
        assert list_entries.labels == []
        assert list_entries.data == []

    def test_create_list_entries_from_labels(self):
        labels = ["foo", "bar"]
        list_entries = ListEntries(labels)
        assert list_entries.labels == labels
        assert list_entries.data == labels

    def test_create_list_entries_from_pairs(self):
        entries = [("foo", 1), ("bar", 2)]
        list_entries = ListEntries(entries)
        assert list_entries.labels == ["foo", "bar"]
        assert list_entries.data == [1, 2]

    def test_create_list_entries_from_mapping(self):
        entries = {"foo": 1, "bar": 2}
        list_entries = ListEntries(entries)
        assert list_entries.labels == ["foo", "bar"]
        assert list_entries.data == [1, 2]

    def test_create_list_entries_from_keywords(self):
        entries = {"foo": 1, "bar": 2}
        list_entries = ListEntries(**entries)
        assert list_entries.labels == ["foo", "bar"]
        assert list_entries.data == [1, 2]

    def test_invalid_entries_raise_error_on_creation(self):
        message = "'42' cannot be parsed to list entries"
        with pytest.raises(TypeError, match=message):
            ListEntries(42)

    def test_get_entry_by_index(self):
        list_entries = ListEntries([("foo", 1), ("bar", 2)])
        assert list_entries[0] == ("foo", 1)

    def test_iterate_over_all_entries(self):
        entries = [("foo", 1), ("bar", 2)]
        list_entries = ListEntries(entries)
        assert [entry for entry in list_entries] == entries

    def test_get_number_of_entries(self):
        list_entries = ListEntries(["foo", "bar"])
        assert len(list_entries) == 2

    @pytest.mark.parametrize("other, result", [([("foo", 1), ("bar", 2)], True), ([("foo", 2), ("bar", 1)], False)])
    def test_compare_with_other_collection(self, other, result):
        list_entries = ListEntries([("foo", 1), ("bar", 2)])
        assert (list_entries == other) == result


class TestListEntry:

    def test_create_list_entry_from_label(self):
        list_entry = ListEntry("foo")
        assert list_entry.label == "foo"
        assert list_entry.data == "foo"

    def test_create_list_entry_from_label_and_data(self):
        list_entry = ListEntry("foo", 1)
        assert list_entry.label == "foo"
        assert list_entry.data == 1

    def test_create_list_entry_from_tuple(self):
        list_entry = ListEntry(("foo", 1))
        assert list_entry.label == "foo"
        assert list_entry.data == 1

    def test_convert_label_to_string(self):
        list_entry = ListEntry(1)
        assert list_entry.label == "1"
        assert list_entry.data == 1
