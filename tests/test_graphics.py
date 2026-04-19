import pytest

from graphics import EmptySpace, HorizontalLine, VerticalLine


class TestHorizontalLine:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_draw_line(self):
        length = 200
        line = HorizontalLine(length, self.window)
        assert line.length == length

    def test_adjust_linewidth(self):
        linewidth = 3
        line = HorizontalLine(200, self.window, linewidth)
        assert line.linewidth == linewidth


class TestVerticalLine:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_draw_line(self):
        length = 200
        line = VerticalLine(length, self.window)
        assert line.length == length

    def test_adjust_linewidth(self):
        linewidth = 3
        line = VerticalLine(200, self.window, linewidth)
        assert line.linewidth == linewidth


class TestEmptySpace:

    @pytest.fixture(autouse=True)
    def _empty_window(self, window):
        self.window = window

    def test_create_space_with_fixed_size(self):
        width, height = 120, 30
        space = EmptySpace(self.window, width, height)
        assert space.size == (width, height)
