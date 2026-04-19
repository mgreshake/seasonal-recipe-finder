import datetime
import os

import pytest

from database import Database
from windows import Application


FAKE_DATE = datetime.date(2026, 3, 1)


class DateMock(datetime.date):
    @classmethod
    def today(cls):
        return FAKE_DATE


@pytest.fixture
def date_patch(monkeypatch):
    monkeypatch.setattr(datetime, "date", DateMock)


@pytest.fixture(scope="session")
def database():
    path = "test_database.json"
    yield Database(path)
    Database.clear()
    os.remove(path)


@pytest.fixture(scope="session")
def window():
    app = Application("Test Window", 640, 480)
    app.show()
    yield app
    app.close()
