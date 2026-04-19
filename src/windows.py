from __future__ import annotations

from enum import Enum
from typing import Any, Literal, TypeAlias

from PyQt6.QtCore import QEventLoop, Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QDialog, QStyle

from layouts import HorizontalBoxLayout, Layout, VerticalBoxLayout
from widgets import Button, Command, Icon, Label, Size


MessageBoxType: TypeAlias = Literal["info", "warning", "error"]


class Result(Enum):
    CANCELLED = 0
    CONFIRMED = 1


class Window:
    """Interface for window that contains widgets."""

    def __init__(
        self,
        parent: Window | None = None,
        title: str = "",
        width: int = 400,
        height: int = 300,
        layout: Layout | None = None,
        confirm_callback: Command | None = None,
        cancel_callback: Command | None = None,
    ) -> None:
        """Create PyQt window with title and fixed size.

        Args:
            parent (`Window`, optional): Parent window instance.
            title (`str`, optional): Window title.
            width (`int`, optional): Width in pixels. Defaults to 400 pixels.
            height (`int`, optional): Height in pixels. Defaults to 300 pixels.
            layout (`Layout`, optional): Window layout.
            confirm_callback (`Command`, optional): Callback that triggers when window dialog is confirmed.
            cancel_callback (`Command`, optional): Callback that triggers when window dialog is cancelled.
        """
        self._instance: _QRespondingWidget = _QRespondingWidget(parent and parent._instance)
        self._is_closed: bool = False
        self._parent: Window | None = parent
        self._layout: Layout | None = layout

        self._instance.setWindowTitle(title)
        self._instance.setFixedSize(width, height)
        self._instance.closed.connect(self.on_closed)

        if layout is not None:
            self._instance.setLayout(layout._instance)

        if confirm_callback is not None:
            self._instance.confirmed[object].connect(confirm_callback)
        if cancel_callback is not None:
            self._instance.cancelled[object].connect(cancel_callback)

    @property
    def parent(self) -> Window | None:
        """Window | None: Parent window instance if available."""
        return self._parent

    @property
    def title(self) -> str:
        """str: Window title."""
        return self._instance.windowTitle()

    @property
    def size(self) -> Size:
        """Size: Width and height in pixels."""
        return Size(self._instance.width(), self._instance.height())

    @property
    def layout(self) -> Layout | None:
        """Layout | None: Layout instance if available."""
        return self._layout

    def exists(self) -> bool:
        """Check if window is still existing.

        Returns:
            bool: `False` if window is closed, `True` otherwise.
        """
        return not self._is_closed

    def is_visible(self) -> bool:
        """Check if window is visible.

        Returns:
            bool: `True` if window is currently visible, `False` otherwise.
        """
        return self._instance.isVisible()

    def show(self) -> None:
        """Show previously hidden window."""
        self._instance.show()

    def hide(self) -> None:
        """Hide window without destroying it."""
        self._instance.hide()

    def run(self) -> Result:
        """Show window while pausing parent loop.

        Returns:
            Result: `1` if window is confirmed, `0` otherwise.
        """
        self.on_started()

        loop = QEventLoop()
        self._instance.closed.connect(loop.quit)
        self._instance.setResult(QDialog.DialogCode.Rejected)
        self._instance.show()

        loop.exec()

        return Result(self._instance.result())

    def confirm(self, result: Any = None) -> None:
        """Confirm dialog and close window.

        Args:
            result (Any): Confirmation result. Expect no result by default.
        """
        self._instance.confirmed[object].emit(result)
        self._instance.setResult(QDialog.DialogCode.Accepted)
        self._instance.close()

    def cancel(self, result: Any = None) -> None:
        """Cancel dialog and close window.

        Args:
            result (Any): Cancellation result. Expect no result by default
        """
        self._instance.cancelled[object].emit(result)
        self._instance.setResult(QDialog.DialogCode.Rejected)
        self._instance.close()

    def close(self) -> None:
        """Close window."""
        self._instance.close()

    def on_started(self) -> None:
        """Mark window as alive."""
        self._is_closed = False

    def on_closed(self) -> None:
        """Mark window as closed."""
        self._is_closed = True


class _QRespondingWidget(QDialog):
    """PyQt dialog that emits signal when it is confirmed, cancelled or closed."""

    confirmed = pyqtSignal(object)
    cancelled = pyqtSignal(object)
    closed = pyqtSignal()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closed.emit()


class Application(Window):
    """Interface for GUI application that consists of widgets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize PyQt application and creates main window.

        Args:
            *args (Any): Argument list for main window.
            **kwargs (Any): Keyword arguments for main window.
        """
        self._app: QApplication = QApplication([])
        super().__init__(None, *args, **kwargs)

    def run(self) -> None:
        """Execute application until main window is closed."""
        self._instance.show()
        self._app.exec()


class MessageBox(Window):
    """Interface for small window that requires interaction from user."""

    def __init__(self, parent: Window, text: str, type: MessageBoxType = "info") -> None:
        """Create PyQt window with text and button.

        Args:
            parent (Window): Parent window instance.
            text (str): Message box content.
            type (MessageBoxType): Message box type determining displayed icon. Possible options are `info`, `warning`
                and `error`. Defaults to `info`.

        Raises:
            ValueError: If message box type is not supported.
        """
        layout = VerticalBoxLayout(alignment="center", spacing=10, margins=(20, 20, 20, 20))
        super().__init__(parent, "", 450, 130, layout)

        self._content: str = text

        match type:
            case "info":
                icon = QStyle.StandardPixmap.SP_MessageBoxInformation
            case "warning":
                icon = QStyle.StandardPixmap.SP_MessageBoxWarning
            case "error":
                icon = QStyle.StandardPixmap.SP_MessageBoxCritical
            case _:
                raise ValueError(f"Invalid message box type found: {type}. Must be 'info', 'warning' or 'error'.")

        message = HorizontalBoxLayout(alignment="center", spacing=16)
        message.add_item(Icon(icon, width=64, height=64))
        message.add_item(Label(text, width=330))

        self.layout.add_item(message)
        self.layout.add_item(Button("Okay", callback=self.confirm, width=100))

    @property
    def content(self) -> str:
        """str: Message box content."""
        return self._content

    def hide(self) -> None:
        """Disable hiding message box."""
        raise AttributeError("Message box cannot be hidden")

    def on_started(self) -> None:
        """Lock all other GUI elements."""
        self._instance.setWindowModality(Qt.WindowModality.WindowModal)
        super().on_started()


class Dialog(Window):
    """Interface for small window that requires decision from user."""

    def __init__(self, parent: Window, text: str) -> None:
        """Creates PyQt window with text and buttons.

        Args:
            parent (Window): Parent window instance.
            text (str): Dialog content.
        """
        layout = VerticalBoxLayout(alignment="center", spacing=10, margins=(20, 20, 20, 20))
        super().__init__(parent, "", 450, 130, layout)

        self._content: str = text

        message = HorizontalBoxLayout(alignment="center", spacing=16)
        message.add_item(Icon(QStyle.StandardPixmap.SP_MessageBoxQuestion, width=64, height=64))
        message.add_item(Label(text, width=330))

        buttons = HorizontalBoxLayout("center", spacing=20)
        buttons.add_item(Button("Okay", callback=self.confirm, width=100))
        buttons.add_item(Button("Cancel", callback=self.cancel, width=100))

        self.layout.add_item(message)
        self.layout.add_item(buttons)

    @property
    def content(self) -> str:
        """str: Dialog content."""
        return self._content

    def hide(self) -> None:
        """Disable hiding dialog."""
        raise AttributeError("Dialog cannot be hidden")

    def on_started(self) -> None:
        """Lock all other GUI elements."""
        self._instance.setWindowModality(Qt.WindowModality.WindowModal)
        super().on_started()
