import os
import re

import pytest

from utils.collections import ListEntries, ListEntry
from widgets import ALIGNMENTS, Button, ComboBox, DropdownList, INPUT_POLICY, Icon, Label, ListBox, TextBox, TextField


class TestLabel:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_label(self):
        content = "This is a test"
        label = Label(content, self.window)
        assert label.text == content

    def test_create_center_aligned_label(self):
        alignment = "center"
        label = Label("This is a test", self.window, alignment)
        assert label.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            Label("This is a test", self.window, alignment="middle")

    def test_create_label_with_fixed_size(self):
        width, height = 120, 30
        label = Label("This is a test", self.window, width=width, height=height)
        assert label.size == (width, height)


class TestIcon:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_icon_from_image(self):
        Icon("tests/resources/icon.png", self.window)

    def test_create_icon_from_standard_pixel_map(self):
        Icon(9, self.window)

    def test_unknown_source_type_raises_error_on_creation(self):
        message = "Unknown source type found: float. Must be image path or standard pixel map."
        with pytest.raises(TypeError, match=message):
            Icon(0.0, self.window)

    def test_invalid_image_path_raises_error_on_creation(self):
        image_path = "resources/error.png"
        assert not os.path.exists(image_path)

        message = f"Invalid source found: {image_path}"
        with pytest.raises(ValueError, match=message):
            Icon(image_path, self.window)

    def test_create_icon_with_fixed_size(self):
        width, height = 64, 64
        icon = Icon(9, self.window, width, height)
        assert icon.size == (width, height)


class TestButton:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_button(self):
        text = "Test"
        button = Button(text, self.window)
        assert button.label == text

    def test_create_button_with_icon(self):
        icon = Icon("tests/resources/icon.png")
        button = Button(icon, self.window)
        assert button.label == icon

    def test_create_button_with_fixed_size(self):
        width, height = 120, 30
        button = Button("Test", self.window, width=width, height=height)
        assert button.size == (width, height)

    def test_trigger_callback_when_button_is_clicked(self):
        assert self.window.is_visible()

        button = Button("Test", self.window, callback=self.window.hide)
        button.click()
        assert not self.window.is_visible()

        self.window.show()


class TestTextField:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_text_field(self):
        text_field = TextField(self.window)
        assert text_field.content == ""

    def test_create_text_field_with_content(self):
        content = "This is a test"
        text_field = TextField(self.window, content)
        assert text_field.content == content

    def test_create_text_field_with_center_aligned_input(self):
        alignment = "center"
        text_field = TextField(self.window, "This is a test", alignment)
        assert text_field.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            TextField(self.window, "This is a test", alignment="middle")

    def test_create_text_field_with_fixed_size(self):
        width, height = 120, 30
        text_field = TextField(self.window, width=width, height=height)
        assert text_field.size == (width, height)

    @pytest.mark.parametrize(
        "policy, input, accepted",
        [
            ("word", "foobar", True), ("word", "This is a test", False), ("word", "foobar2000", False),
            ("count", "42", True), ("count", "01234", False), ("count", "-42", False),
            ("integer", "01234", True), ("integer", "-42", True), ("integer", "3.141", False),
            ("decimal", "3.141", True), ("decimal", "3,141", True), ("decimal", "-3.", True), ("decimal", ".141", True),
            ("number", "-42", True), ("number", "3.141", True), ("number", "foobar", False)
        ],
    )
    def test_accept_only_specific_input(self, policy, input, accepted):
        text_field = TextField(self.window, input, policy=policy)
        assert text_field.has_valid_content() == accepted

    def test_invalid_policy_raises_error_on_creation(self):
        assert "text" not in INPUT_POLICY

        message = "Invalid key found: text. Possible options are ['word', 'number', 'integer', 'decimal', 'count']."
        with pytest.raises(KeyError, match=re.escape(message)):
            TextField(self.window, policy="text")

    def test_trigger_callback_when_input_changes(self):
        text_field = TextField(self.window, callback=self.window.hide)
        assert self.window.is_visible()

        text_field.fill("This is a test")
        assert not self.window.is_visible()

        self.window.show()

    def test_fill_text_field(self):
        content = "This is a test"
        text_field = TextField(self.window)
        assert text_field.content != content

        text_field.fill(content)
        assert text_field.content == content


class TestTextBox:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_text_box(self):
        text_box = TextBox(self.window)
        assert text_box.content == ""

    def test_create_text_box_with_content(self):
        content = "This is a test"
        text_box = TextBox(self.window, content)
        assert text_box.content == content

    def test_create_text_box_with_center_aligned_input(self):
        alignment = "center"
        text_box = TextBox(self.window, "This is a test", alignment)
        assert text_box.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            TextBox(self.window, "This is a test", alignment="middle")

    def test_create_non_editable_text_box(self):
        text_box = TextBox(self.window, is_editable=False)
        assert not text_box.is_editable

    def test_create_text_box_with_fixed_size(self):
        width, height = 120, 120
        text_box = TextBox(self.window, width=width, height=height)
        assert text_box.size == (width, height)

    def test_fill_text_box(self):
        content = "This is a test"
        text_box = TextBox(self.window)
        assert text_box.content != content

        text_box.fill(content)
        assert text_box.content == content


class TestListBox:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_list_box(self):
        entries = ListEntries(["Test", "Another Test"])
        list_box = ListBox(self.window, entries)
        assert list_box.entries == entries

    def test_create_list_box_with_linked_data(self):
        entries = ListEntries({"Test": 1, "Another Test": 2})
        list_box = ListBox(self.window, entries)
        assert list_box.entries == entries

    def test_create_list_box_with_fixed_size(self):
        width, height = 120, 120
        list_box = ListBox(self.window, width=width, height=height)
        assert list_box.size == (width, height)

    def test_check_if_list_box_is_empty(self):
        list_box = ListBox(self.window)
        assert list_box.is_empty()

    def test_count_entries_in_list_box(self):
        list_box = ListBox(self.window, ["Test", "Another Test"])
        assert list_box.count == 2

    def test_select_entry(self):
        index = 1
        list_box = ListBox(self.window, ["Test", "Another Test"])
        assert list_box.selected_index != index

        list_box.select(index)
        assert list_box.selected_index == index
        assert list_box.selected_entry == ListEntry("Another Test")

    def test_invalid_index_raises_error_on_selection(self):
        list_box = ListBox(self.window, ["Test", "Another Test"])
        message = "Entry with index 2 does not exist"
        with pytest.raises(IndexError, match=message):
            list_box.select(2)

    def test_select_first_entry_by_default(self):
        default_index = 0
        list_box = ListBox(self.window, ["Test"], default_index)
        assert list_box.selected_index == default_index
        assert list_box.selected_entry == ListEntry("Test")

    def test_trigger_callback_when_entry_is_selected(self):
        list_box = ListBox(self.window, ["Test"], callback=self.window.hide)
        assert self.window.is_visible()

        list_box.select(0)
        assert not self.window.is_visible()

        self.window.show()

    def test_deselect_entry(self):
        index = 1
        list_box = ListBox(self.window, ["Test", "Another Test"], index)
        assert list_box.selected_index == index
        assert list_box.selected_entry == ListEntry("Another Test")

        list_box.deselect()
        assert list_box.selected_index == -1
        assert list_box.selected_entry is None

    def test_append_entry(self):
        list_box = ListBox(self.window, ["Test"])
        list_box.append(ListEntry("Another Test"))
        assert list_box.entries == ListEntries(["Test", "Another Test"])

    def test_insert_entry(self):
        list_box = ListBox(self.window, ["Test"])
        list_box.insert(0, ListEntry("Another Test"))
        assert list_box.entries == ListEntries(["Another Test", "Test"])

    def test_invalid_index_raises_error_on_insertion(self):
        list_box = ListBox(self.window, ["Test"])
        message = "Entry cannot be inserted at index 2"
        with pytest.raises(IndexError, match=message):
            list_box.insert(2, ListEntry("Another Test"))

    def test_remove_entry(self):
        list_box = ListBox(self.window, ["Test", "Another Test"])
        list_box.remove(0)
        assert list_box.entries == ListEntries(["Another Test"])

    def test_invalid_index_raises_error_on_deletion(self):
        list_box = ListBox(self.window, ["Test", "Another Test"])
        message = "Entry with index 2 does not exist"
        with pytest.raises(IndexError, match=message):
            list_box.remove(2)

    def test_update_entry(self):
        list_box = ListBox(self.window, ["Test"])
        list_box.update(0, ListEntry("Another Test"))
        assert list_box.entries == ListEntries(["Another Test"])

    def test_invalid_index_raises_error_on_update(self):
        list_box = ListBox(self.window, ["Test"])
        message = "Entry with index 2 does not exist"
        with pytest.raises(IndexError, match=message):
            list_box.update(2, ListEntry("Another Test"))

    def test_clear_list_box(self):
        list_box = ListBox(self.window, ["Test", "Another Test"], default_index=1)
        list_box.clear()
        assert list_box.is_empty()
        assert list_box.selected_index < 0

    def test_replace_entries(self):
        entries = ListEntries(["Test"])
        list_box = ListBox(self.window, ["Test", "Another Test"], default_index=1)
        assert list_box.entries != entries
        assert list_box.selected_index == 1

        list_box.entries = entries
        assert list_box.entries == entries
        assert list_box.selected_index < 0


class TestDropdownList:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_dropdown_list(self):
        entries = ListEntries(["Test", "Another Test"])
        dropdown_list = DropdownList(entries, self.window)
        assert dropdown_list.entries == entries

    def test_create_dropdown_list_with_linked_data(self):
        entries = ListEntries({"Test": 1, "Another Test": 2})
        dropdown_list = DropdownList(entries, self.window)
        assert dropdown_list.entries == entries

    def test_create_dropdown_list_with_fixed_size(self):
        width, height = 120, 30
        dropdown_list = DropdownList([], self.window, width=width, height=height)
        assert dropdown_list.size == (width, height)

    def test_get_current_selection(self):
        dropdown_list = DropdownList(["Test", "Another Test"], self.window)
        assert dropdown_list.selected_index == 0
        assert dropdown_list.selected_entry == ListEntry("Test")

    def test_select_entry(self):
        index = 1
        dropdown_list = DropdownList(["Test", "Another Test"], self.window)
        assert dropdown_list.selected_index != index

        dropdown_list.select(index)
        assert dropdown_list.selected_index == index
        assert dropdown_list.selected_entry == ListEntry("Another Test")

    def test_invalid_index_raises_error_on_selection(self):
        dropdown_list = DropdownList(["Test", "Another Test"], self.window)
        message = "Entry with index 2 does not exist"
        with pytest.raises(IndexError, match=message):
            dropdown_list.select(2)

    def test_select_second_entry_by_default(self):
        default_index = 1
        dropdown_list = DropdownList(["Test", "Another Test"], self.window, default_index)
        assert dropdown_list.selected_index == default_index
        assert dropdown_list.selected_entry == ListEntry("Another Test")

    def test_trigger_callback_when_entry_is_selected(self):
        dropdown_list = DropdownList(["Test", "Another Test"], self.window, callback=self.window.hide)
        assert self.window.is_visible()

        dropdown_list.select(1)
        assert not self.window.is_visible()

        self.window.show()

    def test_replace_entries(self):
        entries = ListEntries(["Test"])
        dropdown_list = DropdownList(["Test", "Another Test"], self.window, default_index=1)
        assert dropdown_list.entries != entries
        assert dropdown_list.selected_index == 1

        dropdown_list.entries = entries
        assert dropdown_list.entries == entries
        assert dropdown_list.selected_index == 0


class TestComboBox:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_combo_box(self):
        entries = ListEntries(["Test"])
        combo_box = ComboBox(entries, self.window)
        assert combo_box.entries == entries

    def test_create_combo_box_with_linked_data(self):
        entries = ListEntries({"Test": 1})
        combo_box = ComboBox(entries, self.window)
        assert combo_box.entries == entries

    def test_create_combo_box_with_text_input(self):
        text = "Another Test"
        combo_box = ComboBox({"Test": 1}, self.window, text)
        assert combo_box.text_field.content == text

    def test_create_combo_box_with_maximum_number_of_visible_entries(self):
        max_num_entries = 1
        combo_box = ComboBox(["Test", "Another Test"], self.window, max_num_entries=max_num_entries)
        assert combo_box.max_num_entries == max_num_entries

    def test_create_combo_box_with_fixed_size(self):
        width, height = 120, 25
        combo_box = ComboBox([], self.window, width=width, height=height)
        assert combo_box.size == (width, height)

    def test_get_current_selection(self):
        combo_box = ComboBox(["Test"], self.window)
        assert combo_box.selected_index < 0
        assert combo_box.selected_entry == ListEntry(("", None))

    def test_select_entry(self):
        index = 0
        combo_box = ComboBox(["Test"], self.window)
        assert combo_box.selected_index != index

        combo_box.select(index)
        assert combo_box.selected_index == index
        assert combo_box.selected_entry == ListEntry("Test")

    def test_invalid_index_raises_error_on_selection(self):
        combo_box = ComboBox(["Test"], self.window)
        message = "Entry with index 1 does not exist"
        with pytest.raises(IndexError, match=message):
            combo_box.select(1)

    def test_select_first_entry_by_default(self):
        default_index = 0
        combo_box = ComboBox(["Test"], self.window, default_index=default_index)
        assert combo_box.selected_index == default_index
        assert combo_box.selected_entry == ListEntry("Test")

    def test_ignore_default_index_if_text_is_passed(self):
        text = "Another Test"
        combo_box = ComboBox(["Test"], self.window, text, default_index=0)
        assert combo_box.selected_index < 0
        assert combo_box.selected_entry == ListEntry((text, None))

    def test_trigger_callback_when_entry_is_selected(self):
        combo_box = ComboBox(["Test"], self.window, callback=self.window.hide)
        assert self.window.is_visible()

        combo_box.select(0)
        assert not self.window.is_visible()

        self.window.show()

    def test_update_entries_when_text_input_changes(self):
        combo_box = ComboBox(["Test", "Another Test"], self.window, default_index=0)
        assert combo_box.selected_entry == ListEntry("Test")

        combo_box.text_field.fill("other")
        assert combo_box.selected_entry == ListEntry(("other", None))

        combo_box.select(0)
        assert combo_box.selected_entry == ListEntry("Another Test")

    def test_replace_entries(self):
        entries = ListEntries(["Test"])
        combo_box = ComboBox(["Test", "Another Test"], self.window, default_index=1)
        assert combo_box.entries != entries
        assert combo_box.selected_index == 1

        combo_box.entries = entries
        assert combo_box.entries == entries
        assert combo_box.selected_index == 0
