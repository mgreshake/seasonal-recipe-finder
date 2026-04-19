import re

import pytest

from layouts import FormLayout, HorizontalBoxLayout, Margins, VerticalBoxLayout
from widgets import ALIGNMENTS, Label, TextField


class TestHorizontalBoxLayout:

    @pytest.fixture(autouse=True)
    def _empty_horizontal_box_layout(self, window):
        self.layout = HorizontalBoxLayout()

    def test_create_center_aligned_layout(self):
        alignment = "center"
        layout = HorizontalBoxLayout(alignment)
        assert layout.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            HorizontalBoxLayout(alignment="middle")

    def test_create_layout_with_fixed_spacing(self):
        spacing = 10
        layout = HorizontalBoxLayout(spacing=spacing)
        assert layout.spacing == spacing

    def test_create_layout_with_fixed_left_and_right_margin(self):
        margins = Margins(left=10, right=10)
        layout = HorizontalBoxLayout(margins=margins)
        assert layout.margins == (10, 0, 10, 0)

    def test_add_widget(self):
        label = Label("This is a test")
        self.layout.add_item(label)
        assert self.layout[0] == label

    def test_add_nested_layout(self):
        layout = VerticalBoxLayout()
        self.layout.add_item(layout)
        assert self.layout[0] == layout

    def test_invalid_item_type_raises_error_on_insertion(self):
        message = "Invalid item type found: NoneType. Must be 'Widget' or 'Layout'."
        with pytest.raises(TypeError, match=message):
            self.layout.add_item(None)


class TestVerticalBoxLayout:

    @pytest.fixture(autouse=True)
    def _empty_vertical_box_layout(self, window):
        self.layout = VerticalBoxLayout()

    def test_create_center_aligned_layout(self):
        alignment = "center"
        layout = VerticalBoxLayout(alignment)
        assert layout.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            VerticalBoxLayout(alignment="middle")

    def test_create_layout_with_fixed_spacing(self):
        spacing = 10
        layout = VerticalBoxLayout(spacing=spacing)
        assert layout.spacing == spacing

    def test_create_layout_with_fixed_left_and_right_margin(self):
        margins = Margins(left=10, right=10)
        layout = VerticalBoxLayout(margins=margins)
        assert layout.margins == (10, 0, 10, 0)

    def test_add_widget(self):
        label = Label("This is a test")
        self.layout.add_item(label)
        assert self.layout[0] == label

    def test_add_nested_layout(self):
        layout = HorizontalBoxLayout()
        self.layout.add_item(layout)
        assert self.layout[0] == layout

    def test_invalid_item_type_raises_error_on_insertion(self):
        message = "Invalid item type found: NoneType. Must be 'Widget' or 'Layout'."
        with pytest.raises(TypeError, match=message):
            self.layout.add_item(None)


class TestFormLayout:

    @pytest.fixture(autouse=True)
    def _empty_form_layout(self, window):
        self.layout = FormLayout()

    def test_create_center_aligned_layout(self):
        alignment = "center"
        layout = FormLayout(alignment)
        assert layout.alignment == alignment

    def test_invalid_alignment_raises_error_on_creation(self):
        assert "middle" not in ALIGNMENTS

        message = "Invalid key found: middle. Possible options are ['left', 'center', 'right']."
        with pytest.raises(KeyError, match=re.escape(message)):
            FormLayout(alignment="middle")

    def test_create_layout_with_fixed_spacing(self):
        horizontal_spacing, vertical_spacing = 10, 10
        layout = FormLayout(horizontal_spacing=horizontal_spacing, vertical_spacing=vertical_spacing)
        assert layout.horizontal_spacing == horizontal_spacing
        assert layout.vertical_spacing == vertical_spacing

    def test_create_layout_with_fixed_left_and_right_margin(self):
        margins = Margins(left=10, right=10)
        layout = FormLayout(margins=margins)
        assert layout.margins == (10, 0, 10, 0)

    def test_add_widget(self):
        label = Label("Test:")
        text_field = TextField()
        self.layout.add_item(label, text_field)
        assert self.layout[0] == (label, text_field)

    def test_add_nested_layout(self):
        label = Label("Test:")
        layout = HorizontalBoxLayout()
        self.layout.add_item(label, layout)
        assert self.layout[0] == (label, layout)
