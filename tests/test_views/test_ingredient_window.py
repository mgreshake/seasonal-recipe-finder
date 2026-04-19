import pytest

from database import Document
from views.ingredient_window import Ingredient, IngredientWindow
from views.main_window import MainWindow


@pytest.fixture(scope="module")
def table_with_ingredient(database):
    database.insert_document("ingredient", {"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}, 0)
    yield database.ingredient
    database.drop_table("ingredient", force=True)


@pytest.fixture(scope="module")
def main_window():
    window = MainWindow()
    yield window
    window.close()


class TestIngredientWindow:

    @pytest.fixture(autouse=True)
    def _ingredient_window(self, table_with_ingredient, main_window):
        self.table = table_with_ingredient
        self.window = IngredientWindow(main_window)

    def test_create_empty_form(self):
        assert self.window._name_field.content == ""
        assert self.window._season_from_dropdown.selected_entry == ("", 0)
        assert self.window._season_to_dropdown.selected_entry == ("", 0)
        assert self.window._storage_from_dropdown.selected_entry == ("", 0)
        assert self.window._storage_to_dropdown.selected_entry == ("", 0)
        assert self.window._origin_dropdown.selected_entry == ("", 0)
        assert self.window._document_id is None

        self.window.close()

    def test_apply_existing_ingredient_to_form(self):
        document_id = 0
        assert self.table.contains_document(document_id)

        self.window.fill(document_id)
        assert self.window._name_field.content == "Apple"
        assert self.window._season_from_dropdown.selected_entry == ("August", 8)
        assert self.window._season_to_dropdown.selected_entry == ("November", 11)
        assert self.window._storage_from_dropdown.selected_entry == ("Dezember", 12)
        assert self.window._storage_to_dropdown.selected_entry == ("Mai", 5)
        assert self.window._origin_dropdown.selected_entry == ("regional", 1)
        assert self.window._document_id == document_id

        self.window.close()

    def test_unknown_ingredient_raises_warning_on_request(self):
        document_id = 1
        assert not self.table.contains_document(document_id)

        message = f"No document with ID {document_id} found. New ingredient will be created."
        with pytest.warns(UserWarning, match=message):
            self.window.fill(document_id)

        self.window.close()

    def test_form_remains_empty_if_ingredient_is_unknown(self):
        document_id = 1
        assert not self.table.contains_document(document_id)

        self.window.fill(document_id)
        assert self.window._name_field.content == ""
        assert self.window._season_from_dropdown.selected_entry == ("", 0)
        assert self.window._season_to_dropdown.selected_entry == ("", 0)
        assert self.window._storage_from_dropdown.selected_entry == ("", 0)
        assert self.window._storage_to_dropdown.selected_entry == ("", 0)
        assert self.window._origin_dropdown.selected_entry == ("", 0)
        assert self.window._document_id is None

        self.window.close()

    def test_apply_new_ingredient_to_form(self):
        ingredient = Ingredient(name="Orange", origin=2)
        assert not self.table.search(f"name == '{ingredient.name}'")

        self.window.fill(ingredient)
        assert self.window._name_field.content == "Orange"
        assert self.window._season_from_dropdown.selected_entry == ("", 0)
        assert self.window._season_to_dropdown.selected_entry == ("", 0)
        assert self.window._storage_from_dropdown.selected_entry == ("", 0)
        assert self.window._storage_to_dropdown.selected_entry == ("", 0)
        assert self.window._origin_dropdown.selected_entry == ("kontinental", 2)
        assert self.window._document_id is None

        self.window.close()

    def test_clear_form(self):
        self.window.fill(0)
        assert self.window._name_field.content == "Apple"
        assert self.window._season_from_dropdown.selected_entry == ("August", 8)
        assert self.window._season_to_dropdown.selected_entry == ("November", 11)
        assert self.window._storage_from_dropdown.selected_entry == ("Dezember", 12)
        assert self.window._storage_to_dropdown.selected_entry == ("Mai", 5)
        assert self.window._origin_dropdown.selected_entry == ("regional", 1)
        assert self.window._document_id is not None

        self.window.clear()
        assert self.window._name_field.content == ""
        assert self.window._season_from_dropdown.selected_entry == ("", 0)
        assert self.window._season_to_dropdown.selected_entry == ("", 0)
        assert self.window._storage_from_dropdown.selected_entry == ("", 0)
        assert self.window._storage_to_dropdown.selected_entry == ("", 0)
        assert self.window._origin_dropdown.selected_entry == ("", 0)
        assert self.window._document_id is None

        self.window.close()

    def test_synchronize_dropdowns(self):
        assert self.window._season_to_dropdown.selected_index == 0
        assert self.window._storage_from_dropdown.selected_index == 0

        self.window._season_from_dropdown.select(1)
        self.window._storage_to_dropdown.select(2)
        assert self.window._season_to_dropdown.selected_index == 1
        assert self.window._storage_from_dropdown.selected_index == 2

        self.window._season_from_dropdown.select(2)
        self.window._storage_to_dropdown.select(3)
        assert self.window._season_to_dropdown.selected_index == 1
        assert self.window._storage_from_dropdown.selected_index == 2

        self.window._season_from_dropdown.select(0)
        self.window._storage_to_dropdown.select(0)
        assert self.window._season_to_dropdown.selected_index == 0
        assert self.window._storage_from_dropdown.selected_index == 0

        self.window.close()

    def test_write_new_ingredient_to_database(self):
        ingredient = Ingredient(name="Orange", origin=2)
        assert not self.table.search(f"name == '{ingredient.name}'")

        self.window.fill(ingredient)
        self.window._confirm_button.click()
        results = self.table.search(f"name == '{ingredient.name}'")
        assert results == [{"name": "Orange", "season": [0, 0], "storage": [0, 0], "origin": 2}]

        self.table.remove_documents(map(Document.id.fget, results))
        self.window.close()

    def test_update_existing_ingredient_in_database(self):
        document_id = 0
        assert self.table.contains_document(document_id)

        self.window.fill(document_id)
        self.window._storage_to_dropdown.select(3)
        self.window._confirm_button.click()
        results = self.table.get_documents([document_id])
        assert results == [{"name": "Apple", "season": [8, 11], "storage": [12, 3], "origin": 1}]

        self.table.update_documents([document_id], {"storage": [12, 5]})
        self.window.close()

    def test_missing_name_triggers_message_box_on_confirmation(self):
        assert self.window._name_field.content == ""

        self.window._missing_name_message_box.run = self.window._missing_name_message_box.show
        self.window._confirm_button.click()
        assert self.window._missing_name_message_box.is_visible()

        self.window._missing_name_message_box.close()
        self.window.close()

    def test_existing_name_triggers_message_box_on_confirmation(self):
        ingredient_name = "Apple"
        assert self.table.search(f"name == '{ingredient_name}'")

        self.window._existing_name_message_box.run = self.window._existing_name_message_box.show
        self.window._name_field.fill(ingredient_name)
        self.window._confirm_button.click()
        assert self.window._existing_name_message_box.is_visible()

        self.window._existing_name_message_box.close()
        self.window.close()

    def test_close_window_without_changes_on_cancellation(self):
        document_id = 0
        assert self.table.contains_document(document_id)

        self.window.fill(document_id)
        self.window._storage_to_dropdown.select(3)
        self.window._cancel_button.click()
        results = self.table.get_documents([document_id])
        assert results == [{"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}]

        self.window.close()
