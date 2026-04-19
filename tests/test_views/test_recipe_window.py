import pytest

from database import Document
from utils.collections import ListEntry
from views.main_window import MainWindow
from views.recipe_window import Recipe, RecipeWindow
from windows import Result


@pytest.fixture(scope="module")
def table_with_ingredients(database):
    database.insert_document("ingredient", {"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}, 0)
    database.insert_document("ingredient", {"name": "Banana", "season": [1, 12], "storage": [0, 0], "origin": 3}, 1)
    database.insert_document("ingredient", {"name": "Sugar", "season": [0, 0],  "storage": [0, 0],  "origin": 0}, 2)
    database.insert_document("ingredient", {"name": "Milk", "season": [0, 0], "storage": [0, 0], "origin": 0}, 3)
    yield database.ingredient
    database.drop_table("ingredient", force=True)


@pytest.fixture(scope="module")
def table_with_recipes(database):
    recipe = {
        "name": "Fruit Salad",
        "portions": 4,
        "ingredients": [
            {"quantity": 3.0, "unit": 0, "id": 0},
            {"quantity": 4.0, "unit": 0, "id": 1},
            {"quantity": 50.0, "unit": 1, "id": 2},
        ],
        "preparation": "Put all together.",
    }
    database.insert_document("recipe", recipe, 0)
    yield database.recipe
    database.drop_table("recipe", force=True)


@pytest.fixture(scope="module")
def main_window():
    window = MainWindow()
    yield window
    window.close()


class TestRecipeWindow:

    @pytest.fixture(autouse=True)
    def _recipe_window(self, table_with_ingredients, table_with_recipes, main_window):
        self.table = table_with_recipes
        self.window = RecipeWindow(main_window)

    def test_create_empty_form(self):
        assert self.window._name_field.content == ""
        assert self.window._portion_field.content == "1"
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._ingredient_list.is_empty()
        assert self.window._preparation_field.content == ""
        assert self.window._document_id is None

        self.window.close()

    def test_apply_existing_recipe_to_form(self):
        document_id = 0
        assert self.table.contains_document(document_id)

        self.window.fill(document_id)
        assert self.window._name_field.content == "Fruit Salad"
        assert self.window._portion_field.content == "4"
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._ingredient_list.entries == [
            ("3 Apple", {"quantity": 3.0, "unit": 0, "id": 0}),
            ("4 Banana", {"quantity": 4.0, "unit": 0, "id": 1}),
            ("50 g Sugar", {"quantity": 50.0, "unit": 1, "id": 2}),
        ]
        assert self.window._preparation_field.content == "Put all together."
        assert self.window._document_id == document_id

        self.window.close()

    def test_unknown_recipe_raises_warning_on_request(self):
        document_id = 1
        assert not self.table.contains_document(document_id)

        message = f"No document with ID {document_id} found. New recipe will be created."
        with pytest.warns(UserWarning, match=message):
            self.window.fill(document_id)

        self.window.close()

    def test_form_remains_empty_if_recipe_is_unknown(self):
        document_id = 1
        assert not self.table.contains_document(document_id)

        self.window.fill(document_id)
        assert self.window._name_field.content == ""
        assert self.window._portion_field.content == "1"
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._ingredient_list.is_empty()
        assert self.window._preparation_field.content == ""
        assert self.window._document_id is None

        self.window.close()

    def test_apply_new_recipe_to_form(self):
        recipe = Recipe(
            name="Banana Smoothie",
            portions=2,
            ingredients=[
                {"quantity": 2.0, "unit": 0, "id": 1},
                {"quantity": 2.0, "unit": 7, "id": 2},
                {"quantity": 400.0, "unit": 5, "id": 3},
            ],
            preparation = "Slice, mix, done.",
        )
        assert not self.table.search(f"name == '{recipe.name}'")

        self.window.fill(recipe)
        assert self.window._name_field.content == "Banana Smoothie"
        assert self.window._portion_field.content == "2"
        assert self.window._ingredient_list.entries == [
            ("2 Banana", {"quantity": 2.0, "unit": 0, "id": 1}),
            ("2 TL Sugar", {"quantity": 2.0, "unit": 7, "id": 2}),
            ("400 ml Milk", {"quantity": 400.0, "unit": 5, "id": 3}),
        ]
        assert self.window._preparation_field.content == "Slice, mix, done."
        assert self.window._document_id is None

        self.window.close()

    def test_update_ingredient_selection_when_list_entry_is_selected(self):
        self.window.fill(0)
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert not self.window._ingredient_list.is_empty()

        self.window._ingredient_list.select(2)
        assert self.window._quantity_field.content == "50"
        assert self.window._quantity_unit_dropdown.selected_entry == ("g", 1)
        assert self.window._ingredient_combo_box.selected_entry == ("Sugar", 2)

        self.window.close()

    def test_clear_ingredient_selection_when_list_entry_is_deselected(self):
        self.window.fill(0)
        self.window._ingredient_list.select(2)
        assert self.window._quantity_field.content == "50"
        assert self.window._quantity_unit_dropdown.selected_entry == ("g", 1)
        assert self.window._ingredient_combo_box.selected_entry == ("Sugar", 2)

        self.window._ingredient_list.deselect()
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)

        self.window.close()

    def test_clear_form(self):
        self.window.fill(0)
        self.window._ingredient_list.select(2)
        assert self.window._name_field.content == "Fruit Salad"
        assert self.window._portion_field.content == "4"
        assert self.window._quantity_field.content == "50"
        assert self.window._quantity_unit_dropdown.selected_entry == ("g", 1)
        assert self.window._ingredient_combo_box.selected_entry == ("Sugar", 2)
        assert self.window._ingredient_list.entries == [
            ("3 Apple", {"quantity": 3.0, "unit": 0, "id": 0}),
            ("4 Banana", {"quantity": 4.0, "unit": 0, "id": 1}),
            ("50 g Sugar", {"quantity": 50.0, "unit": 1, "id": 2}),
        ]
        assert self.window._preparation_field.content == "Put all together."
        assert self.window._document_id is not None

        self.window.clear()
        assert self.window._name_field.content == ""
        assert self.window._portion_field.content == "1"
        assert self.window._quantity_field.content == ""
        assert self.window._quantity_unit_dropdown.selected_entry == ("", 0)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._ingredient_list.is_empty()
        assert self.window._preparation_field.content == ""
        assert self.window._document_id is None

        self.window.close()

    def test_write_new_recipe_to_database(self):
        recipe = Recipe(
            name="Banana Smoothie",
            portions=2,
            ingredients=[
                {"quantity": 2.0, "unit": 0, "id": 1},
                {"quantity": 2.0, "unit": 7, "id": 2},
                {"quantity": 400.0, "unit": 5, "id": 3},
            ],
            preparation = "Slice, mix, done.",
        )
        assert not self.table.search(f"name == '{recipe.name}'")

        self.window.fill(recipe)
        self.window._confirm_button.click()
        results = self.table.search(f"name == '{recipe.name}'")
        assert results == [{
            "name": "Banana Smoothie",
            "portions": 2,
            "ingredients": [
                {"quantity": 2.0, "unit": 0, "id": 1},
                {"quantity": 2.0, "unit": 7, "id": 2},
                {"quantity": 400.0, "unit": 5, "id": 3},
            ],
            "preparation": "Slice, mix, done.",
        }]

        self.table.remove_documents(map(Document.id.fget, results))
        self.window.close()

    def test_update_existing_recipe_in_database(self):
        document_id = 0
        assert self.table.contains_document(document_id)

        self.window.fill(document_id)
        self.window._portion_field.fill("3")
        self.window._confirm_button.click()
        results = self.table.get_documents([document_id])
        assert results == [{
            "name": "Fruit Salad",
            "portions": 3,
            "ingredients": [
                {"quantity": 3.0, "unit": 0, "id": 0},
                {"quantity": 4.0, "unit": 0, "id": 1},
                {"quantity": 50.0, "unit": 1, "id": 2},
            ],
            "preparation": "Put all together.",
        }]

        self.table.update_documents([document_id], {"portions": 4})
        self.window.close()

    def test_missing_name_triggers_message_box_on_confirmation(self):
        assert self.window._name_field.content == ""

        self.window._missing_name_message_box.run = self.window._missing_name_message_box.show
        self.window._confirm_button.click()
        assert self.window._missing_name_message_box.is_visible()

        self.window._missing_name_message_box.close()
        self.window.close()

    def test_missing_ingredients_triggers_message_box_on_confirmation(self):
        self.window._name_field.fill("Fruit Salad")
        self.window._ingredient_list.append(ListEntry("Apple"))
        assert self.window._ingredient_list.count < 2

        self.window._missing_ingredients_message_box.run = self.window._missing_ingredients_message_box.show
        self.window._confirm_button.click()
        assert self.window._missing_ingredients_message_box.is_visible()

        self.window._missing_ingredients_message_box.close()
        self.window.close()

    def test_existing_name_triggers_message_box_on_confirmation(self):
        recipe_name = "Fruit Salad"
        self.window._ingredient_list.append(ListEntry("Apple"))
        self.window._ingredient_list.append(ListEntry("Banana"))
        assert self.table.search(f"name == '{recipe_name}'")
        assert self.window._ingredient_list.count >= 2

        self.window._existing_name_message_box.run = self.window._existing_name_message_box.show
        self.window._name_field.fill(recipe_name)
        self.window._confirm_button.click()
        assert self.window._existing_name_message_box.is_visible()

        self.window._existing_name_message_box.close()
        self.window.close()


class TestAddIngredient:

    @pytest.fixture(autouse=True)
    def _recipe_window(self, table_with_ingredients, main_window):
        self.table = table_with_ingredients
        self.window = RecipeWindow(main_window)

    def test_add_existing_ingredient_from_selection_to_list(self):
        assert self.table.search(f"name == 'Sugar'")
        assert self.window._ingredient_list.is_empty()

        self.window._quantity_field.fill("50")
        self.window._quantity_unit_dropdown.select(1)
        self.window._ingredient_combo_box.select(3)
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.entries == [("50 g Sugar", {"quantity": 50.0, "unit": 1, "id": 2})]

        self.window.close()

    def test_update_list_entry_if_ingredient_is_already_listed(self):
        self.window._quantity_field.fill("50")
        self.window._quantity_unit_dropdown.select(1)
        self.window._ingredient_combo_box.select(3)
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.entries == [("50 g Sugar", {"quantity": 50.0, "unit": 1, "id": 2})]

        self.window._quantity_field.fill("100")
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.entries == [("100 g Sugar", {"quantity": 100.0, "unit": 1, "id": 2})]

        self.window.close()

    def test_insert_ingredient_before_selected_list_entry(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_index == 0

        self.window._quantity_field.fill("50")
        self.window._quantity_unit_dropdown.select(1)
        self.window._ingredient_combo_box.text_field.fill("Sugar")
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.entries == [
            ("50 g Sugar", {"quantity": 50.0, "unit": 1, "id": 2}),
            ("Apple", {"quantity": 0.0, "unit": 0, "id": 0}),
        ]

        self.window.close()

    def test_open_input_mask_when_new_ingredient_is_added(self):
        ingredient_name = "Orange"
        assert not self.table.search(f"name == '{ingredient_name}'")

        self.window._ingredient_window.run = self.window._ingredient_window.show
        self.window._ingredient_combo_box.text_field.fill(ingredient_name)
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_window.is_visible()
        assert self.window._ingredient_window._name_field.content == ingredient_name

        self.window._ingredient_window.close()
        self.window.close()

    def test_add_new_ingredient_from_input_mask_to_list(self):
        ingredient_name = "Orange"
        assert not self.table.search(f"name == '{ingredient_name}'")
        assert ingredient_name not in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.is_empty()

        def fill_ingredient_window():
            self.window._ingredient_window._name_field.fill(ingredient_name)
            self.window._ingredient_window._origin_dropdown.select(2)
            self.window._ingredient_window._confirm_button.click()
            return Result.CONFIRMED

        self.window._ingredient_window.run = fill_ingredient_window
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_combo_box.text_field.content == ingredient_name
        assert ingredient_name in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.entries.labels == [ingredient_name]

        results = self.table.search(f"name == '{ingredient_name}'")
        self.table.remove_documents(map(Document.id.fget, results))
        self.window.close()

    def test_add_nothing_to_list_if_input_mask_is_cancelled(self):
        assert not self.table.search(f"name == 'Orange'")
        assert self.window._ingredient_list.is_empty()

        def cancel_ingredient_window():
            self.window._ingredient_window._cancel_button.click()
            return Result.CANCELLED

        self.window._ingredient_window.run = cancel_ingredient_window
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.is_empty()

        self.window.close()

    def test_add_nothing_to_list_if_input_mask_is_closed(self):
        assert not self.table.search(f"name == 'Orange'")
        assert self.window._ingredient_list.is_empty()

        def close_ingredient_window():
            self.window._ingredient_window.close()
            return Result.CANCELLED

        self.window._ingredient_window.run = close_ingredient_window
        self.window._add_ingredient_button.click()
        assert self.window._ingredient_list.is_empty()

        self.window.close()


class TestRemoveIngredient:

    @pytest.fixture(autouse=True)
    def _recipe_window(self, main_window):
        self.window = RecipeWindow(main_window)

    def test_remove_selected_ingredient_from_list(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        self.window._remove_ingredient_button.click()
        assert self.window._ingredient_list.is_empty()
        assert self.window._ingredient_list.selected_entry is None

        self.window.close()

    def test_remove_nothing_from_list_if_no_ingredient_is_selected(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_index < 0

        self.window._remove_ingredient_button.click()
        assert self.window._ingredient_list.entries == ([ingredient_entry])

        self.window.close()


class TestEditIngredient:

    @pytest.fixture(autouse=True)
    def _recipe_window(self, table_with_ingredients, main_window):
        self.table = table_with_ingredients
        self.window = RecipeWindow(main_window)

    def test_open_input_mask_when_ingredient_is_edited(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        self.window._ingredient_window.run = self.window._ingredient_window.show
        self.window._edit_ingredient_button.click()
        assert self.window._ingredient_window.is_visible()

        self.window._ingredient_window.close()
        self.window.close()

    def test_update_selected_ingredient_in_database(self):
        new_ingredient_name = "Pineapple"
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert new_ingredient_name not in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def fill_ingredient_window():
            self.window._ingredient_window._name_field.fill(new_ingredient_name)
            self.window._ingredient_window._confirm_button.click()
            return Result.CONFIRMED

        self.window._ingredient_window.run = fill_ingredient_window
        self.window._edit_ingredient_button.click()
        results = self.table.get_documents([ingredient_entry.data["id"]])
        assert results == [{"name": "Pineapple", "season": [8, 11], "storage": [12, 5], "origin": 1}]
        assert self.window._ingredient_combo_box.text_field.content == new_ingredient_name
        assert new_ingredient_name in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.selected_entry.label == new_ingredient_name

        self.table.update_documents([ingredient_entry.data["id"]], {"name": "Apple"})
        self.window.close()

    def test_update_nothing_in_database_if_input_mask_is_cancelled(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def cancel_ingredient_window():
            self.window._ingredient_window._cancel_button.click()
            return Result.CANCELLED

        self.window._ingredient_window.run = cancel_ingredient_window
        self.window._edit_ingredient_button.click()
        results = self.table.search(f"name == '{ingredient_entry.label}'")
        assert results == [{"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}]
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        self.window.close()

    def test_update_nothing_in_database_if_input_mask_is_closed(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def close_ingredient_window():
            self.window._ingredient_window.close()
            return Result.CANCELLED

        self.window._ingredient_window.run = close_ingredient_window
        self.window._edit_ingredient_button.click()
        results = self.table.search(f"name == '{ingredient_entry.label}'")
        assert results == [{"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}]
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        self.window.close()

    def test_update_nothing_in_database_if_no_ingredient_is_selected(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_index < 0

        self.window._edit_ingredient_button.click()
        results = self.table.search(f"name == '{ingredient_entry.label}'")
        assert results == [{"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}]
        assert self.window._ingredient_list.entries == ([ingredient_entry])

        self.window.close()


class TestDeleteIngredient:

    @pytest.fixture(autouse=True)
    def _recipe_window(self, table_with_ingredients, table_with_recipes, main_window):
        self.ingredient_table = table_with_ingredients
        self.recipe_table = table_with_recipes
        self.window = RecipeWindow(main_window)

    def test_open_dialog_when_ingredient_is_deleted(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        self.window._delete_ingredient_dialog.run = self.window._delete_ingredient_dialog.show
        self.window._delete_ingredient_button.click()
        assert self.window._delete_ingredient_dialog.is_visible()

        self.window._delete_ingredient_dialog.close()
        self.window.close()

    def test_delete_selected_ingredient_from_database(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert ingredient_entry.label in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def confirm_delete_ingredient_dialog():
            self.window._delete_ingredient_dialog.confirm()
            return Result.CONFIRMED

        self.window._delete_ingredient_dialog.run = confirm_delete_ingredient_dialog
        self.window._delete_ingredient_button.click()
        assert not self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_combo_box.text_field.content == ""
        assert ingredient_entry.label not in self.window._ingredient_combo_box.entries.labels
        assert self.window._ingredient_list.is_empty()
        assert self.window._ingredient_list.selected_entry is None

        self.ingredient_table.insert_document({"name": "Apple", "season": [8, 11], "storage": [12, 5], "origin": 1}, 0)
        self.window.close()

    def test_delete_nothing_from_database_if_dialog_is_cancelled(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def cancel_delete_ingredient_dialog():
            self.window._delete_ingredient_dialog.cancel()
            return Result.CANCELLED

        self.window._delete_ingredient_dialog.run = cancel_delete_ingredient_dialog
        self.window._delete_ingredient_button.click()
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])

        self.window.close()

    def test_delete_nothing_from_database_if_dialog_is_closed(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        self.window._ingredient_list.select(0)
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_entry == ingredient_entry

        def close_delete_ingredient_dialog():
            self.window._delete_ingredient_dialog.close()
            return Result.CANCELLED

        self.window._delete_ingredient_dialog.run = close_delete_ingredient_dialog
        self.window._delete_ingredient_button.click()
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])

        self.window.close()

    def test_delete_nothing_from_database_if_no_ingredient_is_selected(self):
        ingredient_entry = ListEntry("Apple", {"quantity": 0.0, "unit": 0, "id": 0})
        self.window._ingredient_list.append(ingredient_entry)
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])
        assert self.window._ingredient_list.selected_index < 0

        self.window._delete_ingredient_button.click()
        assert self.ingredient_table.search(f"name == '{ingredient_entry.label}'")
        assert self.window._ingredient_list.entries == ([ingredient_entry])

        self.window.close()
