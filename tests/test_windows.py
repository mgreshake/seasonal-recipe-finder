from typing import get_args

import pytest

from layouts import HorizontalBoxLayout
from windows import Dialog, MessageBox, MessageBoxType, Window


class TestWindow:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_empty_window(self):
        window = Window(self.window)
        assert window.exists()

        window._instance.close()

    def test_create_window_with_title(self):
        title = "Test Window"
        window = Window(self.window, title)
        assert window.title == title

        window._instance.close()

    def test_create_window_with_fixed_size(self):
        width, height = 640, 480
        window = Window(self.window, "Test Window", width, height)
        assert window.size == (width, height)

        window._instance.close()

    def test_create_window_with_layout(self):
        layout = HorizontalBoxLayout()
        window = Window(self.window, "Test Window", layout=layout)
        assert window.layout == layout

        window._instance.close()

    def test_check_if_window_is_visible(self):
        assert self.window.is_visible()

    def test_change_visibility(self):
        assert self.window.is_visible()

        self.window.hide()
        assert not self.window.is_visible()

        self.window.show()
        assert self.window.is_visible()

    def test_close_window(self):
        window = Window(self.window)
        assert window.exists()

        window.close()
        assert not window.exists()

    def test_confirm_window(self):
        def on_confirmed():
            self._is_confirmed = True

        self._is_confirmed = False
        window = Window(self.window, confirm_callback=on_confirmed)
        assert not self._is_confirmed
        assert window.exists()

        window.confirm()
        assert self._is_confirmed
        assert not window.exists()

        self._is_confirmed = False

    def test_cancel_window(self):
        def on_cancelled():
            self._is_cancelled = True

        self._is_cancelled = False
        window = Window(self.window, cancel_callback=on_cancelled)
        assert not self._is_cancelled
        assert window.exists()

        window.cancel()
        assert self._is_cancelled
        assert not window.exists()

        self._is_cancelled = False


class TestMessageBox:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_message_box(self):
        content = "This is a test"
        message_box = MessageBox(self.window, content)
        assert message_box.content == content

        message_box._instance.close()

    def test_invalid_type_raises_error_on_creation(self):
        assert "dialog" not in get_args(MessageBoxType)

        message = "Invalid message box type found: dialog. Must be 'info', 'warning' or 'error'."
        with pytest.raises(ValueError, match=message):
            MessageBox(self.window, "This is a test", type="dialog")

    def test_hide_message_box_raises_error(self):
        message_box = MessageBox(self.window, "This is a test")
        message_box.show()
        assert message_box.is_visible()

        message = "Message box cannot be hidden"
        with pytest.raises(AttributeError, match=message):
            message_box.hide()


class TestDialog:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_dialog(self):
        content = "This is a test"
        dialog = Dialog(self.window, content)
        assert dialog.content == content

        dialog._instance.close()

    def test_hide_dialog_raises_error(self):
        dialog = Dialog(self.window, "This is a test")
        dialog.show()
        assert dialog.is_visible()

        message = "Dialog cannot be hidden"
        with pytest.raises(AttributeError, match=message):
            dialog.hide()
