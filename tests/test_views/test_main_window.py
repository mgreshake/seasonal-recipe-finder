import copy
import filecmp
import os
import pytest

from database import Document
from views.main_window import MainWindow
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
    recipes = [
        {
            "name": "Fruit Salad",
            "portions": 4,
            "ingredients": [
                {"quantity": 3.0, "unit": 0, "id": 0},
                {"quantity": 4.0, "unit": 0, "id": 1},
                {"quantity": 50.0, "unit": 1, "id": 2},
            ],
            "preparation": "Put all together.",
        },
        {
            "name": "Banana Smoothie",
            "portions": 2,
            "ingredients": [
                {"quantity": 2.0, "unit": 0, "id": 1},
                {"quantity": 2.0, "unit": 7, "id": 2},
                {"quantity": 400.0, "unit": 5, "id": 3},
            ],
            "preparation": "Slice, mix, done.",
        },
    ]
    database.insert_document("recipe", recipes[0], 0)
    database.insert_document("recipe", recipes[1], 1)
    yield database.recipe
    database.drop_table("recipe", force=True)


class TestMainWindow:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_ingredients, table_with_recipes, date_patch):
        self.ingredient_table = table_with_ingredients
        self.recipe_table = table_with_recipes
        self.window = MainWindow()

    def test_create_window(self):
        assert self.window._recipe_name_field.content == ""
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._recipe_list.entries == [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        assert self.window._portion_field.content == ""
        assert self.window._recipe_view.content == ""

        self.window.close()

    def test_show_preparation_when_recipe_is_selected(self):
        assert self.window._portion_field.content == ""
        assert self.window._recipe_view.content == ""

        self.window._recipe_list.select(1)
        recipe_text = "Ingredients:\n\n2 Banana\n2 TL Sugar\n400 ml Milk\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._portion_field.content == "2"
        assert self.window._recipe_view.content == recipe_text

        self.window.close()

    def test_show_placeholder_if_recipe_contains_unknown_ingredient(self):
        self.ingredient_table.remove_documents([3])
        assert not self.ingredient_table.search(f"name == 'Milk'")

        self.window._recipe_list.select(1)
        recipe_text = "Ingredients:\n\n2 Banana\n2 TL Sugar\n400 ml Unknown\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._portion_field.content == "2"
        assert self.window._recipe_view.content == recipe_text

        self.ingredient_table.insert_document({"name": "Milk", "season": [0, 0], "storage": [0, 0], "origin": 0}, 3)
        self.window.close()

    def test_adjust_quantities_when_portions_change(self):
        self.window._recipe_list.select(1)
        recipe_text = "Ingredients:\n\n2 Banana\n2 TL Sugar\n400 ml Milk\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._portion_field.content == "2"
        assert self.window._recipe_view.content == recipe_text

        self.window._portion_field.fill("4")
        recipe_text = "Ingredients:\n\n4 Banana\n4 TL Sugar\n800 ml Milk\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._recipe_view.content == recipe_text

        self.window.close()

    def test_preparation_remains_untouched_if_portion_field_is_empty(self):
        self.window._recipe_list.select(1)
        recipe_text = "Ingredients:\n\n2 Banana\n2 TL Sugar\n400 ml Milk\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._portion_field.content == "2"
        assert self.window._recipe_view.content == recipe_text

        self.window._portion_field.fill("")
        assert self.window._recipe_view.content == recipe_text

        self.window.close()

    def test_clear_preparation_when_recipe_is_deselected(self):
        self.window._recipe_list.select(1)
        recipe_text = "Ingredients:\n\n2 Banana\n2 TL Sugar\n400 ml Milk\n\n\nPreparation:\n\nSlice, mix, done."
        assert self.window._portion_field.content == "2"
        assert self.window._recipe_view.content == recipe_text

        self.window._recipe_list.deselect()
        assert self.window._portion_field.content == ""
        assert self.window._recipe_view.content == ""

        self.window.close()


class TestSearchRecipes:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_ingredients, table_with_recipes, date_patch):
        self.window = MainWindow()

    def test_filter_recipes_by_name(self):
        assert self.window._ingredient_combo_box.selected_entry == ("", None)
        assert self.window._recipe_list.entries == [("Fruit Salad", 0), ("Banana Smoothie", 1)]

        self.window._recipe_name_field.fill("banana")
        self.window._search_recipe_button.click()
        assert self.window._recipe_list.entries == [("Banana Smoothie", 1)]

        self.window.close()

    def test_filter_recipes_by_ingredient(self):
        assert self.window._recipe_name_field.content == ""
        assert self.window._recipe_list.entries == [("Fruit Salad", 0), ("Banana Smoothie", 1)]

        self.window._ingredient_combo_box.select(0)
        self.window._search_recipe_button.click()
        assert self.window._recipe_list.entries == [("Fruit Salad", 0)]

        self.window.close()

    def test_filter_recipes_by_name_and_ingredient(self):
        assert self.window._recipe_list.entries == [("Fruit Salad", 0), ("Banana Smoothie", 1)]

        self.window._recipe_name_field.fill("banana")
        self.window._ingredient_combo_box.select(0)
        self.window._search_recipe_button.click()
        assert self.window._recipe_list.is_empty()

        self.window.close()

    def test_show_all_recipes(self):
        self.window._ingredient_combo_box.select(0)
        self.window._search_recipe_button.click()
        assert self.window._recipe_list.entries == [("Fruit Salad", 0)]

        self.window._recipe_name_field.fill("")
        self.window._ingredient_combo_box.text_field.fill("")
        self.window._search_recipe_button.click()
        assert self.window._recipe_list.entries == [("Fruit Salad", 0), ("Banana Smoothie", 1)]

        self.window.close()


class TestAddRecipe:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_ingredients, table_with_recipes, date_patch):
        self.ingredient_table = table_with_ingredients
        self.recipe_table = table_with_recipes
        self.window = MainWindow()

    def test_open_input_mask_when_new_recipe_is_added(self):
        recipe_name = "Candy Apples"
        assert not self.recipe_table.search(f"name == '{recipe_name}'")

        self.window._recipe_window.run = self.window._recipe_window.show
        self.window._recipe_name_field.fill(recipe_name)
        self.window._add_recipe_button.click()
        assert self.window._recipe_window.is_visible()
        assert self.window._recipe_window._name_field.content == recipe_name

        self.window._recipe_window.close()
        self.window.close()

    def test_add_new_recipe_from_input_mask_to_list(self):
        recipe_name = "Candy Apples"
        ingredient_name = "Red Food Coloring"
        assert not self.recipe_table.search(f"name == '{recipe_name}'")
        assert not self.ingredient_table.search(f"name == '{ingredient_name}'")
        assert recipe_name not in self.window._recipe_list.entries.labels
        assert ingredient_name not in self.window._ingredient_combo_box.entries.labels

        def fill_recipe_window():
            self.window._recipe_window._name_field.fill(recipe_name)
            self.window._recipe_window._portion_field.fill("4")
            self.window._recipe_window._quantity_field.fill("3")
            self.window._recipe_window._quantity_unit_dropdown.select(8)
            self.window._recipe_window._add_ingredient_button.click()
            self.window._recipe_window._ingredient_list.append(("Apple", {"quantity": 4.0, "unit": 0, "id": 0}))
            self.window._recipe_window._ingredient_list.append(("Sugar", {"quantity": 600.0, "unit": 1, "id": 2}))
            self.window._recipe_window._preparation_field.fill("Made with love.")
            self.window._recipe_window._confirm_button.click()
            return Result.CONFIRMED

        def fill_ingredient_window():
            self.window._recipe_window._ingredient_window._name_field.fill(ingredient_name)
            self.window._recipe_window._ingredient_window._confirm_button.click()
            return Result.CONFIRMED

        self.window._recipe_window.run = fill_recipe_window
        self.window._recipe_window._ingredient_window.run = fill_ingredient_window
        self.window._add_recipe_button.click()
        assert recipe_name in self.window._recipe_list.entries.labels
        assert ingredient_name in self.window._ingredient_combo_box.entries.labels
        assert self.window._recipe_list.selected_entry.label == "Candy Apples"
        assert self.window._ingredient_combo_box.selected_entry == ("", None)

        results = self.recipe_table.search(f"name == '{recipe_name}'")
        self.recipe_table.remove_documents(map(Document.id.fget, results))
        results = self.ingredient_table.search(f"name == '{ingredient_name}'")
        self.ingredient_table.remove_documents(map(Document.id.fget, results))
        self.window.close()

    def test_add_nothing_to_list_if_input_mask_is_cancelled(self):
        recipe_name = "Candy Apples"
        assert not self.recipe_table.search(f"name == '{recipe_name}'")
        assert recipe_name not in self.window._recipe_list.entries.labels

        def cancel_recipe_window():
            self.window._recipe_window._cancel_button.click()
            return Result.CANCELLED

        self.window._recipe_window.run = cancel_recipe_window
        self.window._add_recipe_button.click()
        assert recipe_name not in self.window._recipe_list.entries.labels

        self.window.close()

    def test_add_nothing_to_list_if_input_mask_is_closed(self):
        recipe_name = "Candy Apples"
        assert not self.recipe_table.search(f"name == '{recipe_name}'")
        assert recipe_name not in self.window._recipe_list.entries.labels

        def close_recipe_window():
            self.window._recipe_window.close()
            return Result.CANCELLED

        self.window._recipe_window.run = close_recipe_window
        self.window._add_recipe_button.click()
        assert recipe_name not in self.window._recipe_list.entries.labels

        self.window.close()


class TestEditRecipe:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_ingredients, table_with_recipes, date_patch):
        self.ingredient_table = table_with_ingredients
        self.recipe_table = table_with_recipes
        self.window = MainWindow()

    def test_open_input_mask_when_recipe_is_edited(self):
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.selected_entry == ("Banana Smoothie", 1)

        self.window._recipe_window.run = self.window._recipe_window.show
        self.window._edit_recipe_button.click()
        assert self.window._recipe_window.is_visible()

        self.window._recipe_window.close()
        self.window.close()

    def test_update_selected_recipe_in_database(self):
        new_recipe_name = "Spinach Smoothie"
        new_ingredient_name = "Spinach"
        self.window._recipe_list.select(1)
        assert new_recipe_name not in self.window._recipe_list.entries.labels
        assert new_ingredient_name not in self.window._ingredient_combo_box.entries.labels
        assert self.window._recipe_list.selected_entry == ("Banana Smoothie", 1)

        def fill_recipe_window():
            self.window._recipe_window._name_field.fill(new_recipe_name)
            self.window._recipe_window._ingredient_list.select(0)
            self.window._recipe_window._edit_ingredient_button.click()
            self.window._recipe_window._confirm_button.click()
            return Result.CONFIRMED

        def fill_ingredient_window():
            self.window._recipe_window._ingredient_window._name_field.fill(new_ingredient_name)
            self.window._recipe_window._ingredient_window._confirm_button.click()
            return Result.CONFIRMED

        self.window._recipe_window.run = fill_recipe_window
        self.window._recipe_window._ingredient_window.run = fill_ingredient_window
        self.window._edit_recipe_button.click()
        assert new_ingredient_name in self.window._ingredient_combo_box.entries.labels
        assert self.window._recipe_list.selected_entry == (new_recipe_name, 1)
        assert self.window._ingredient_combo_box.selected_entry == ("", None)

        document_id = self.window._recipe_list.selected_entry.data
        self.recipe_table.update_documents([document_id], {"name": "Banana Smoothie"})
        document_id = self.recipe_table.get_documents([document_id])[0]["ingredients"][0]["id"]
        self.ingredient_table.update_documents([document_id], {"name": "Banana"})
        self.window.close()

    def test_update_nothing_in_database_if_input_mask_is_cancelled(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        def cancel_recipe_window():
            self.window._recipe_window._cancel_button.click()
            return Result.CANCELLED

        self.window._recipe_window.run = cancel_recipe_window
        self.window._edit_recipe_button.click()
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        self.window.close()

    def test_update_nothing_in_database_if_input_mask_is_closed(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        def close_recipe_window():
            self.window._recipe_window.close()
            return Result.CANCELLED

        self.window._recipe_window.run = close_recipe_window
        self.window._edit_recipe_button.click()
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        self.window.close()

    def test_update_nothing_in_database_if_no_recipe_is_selected(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_index < 0

        self.window._edit_recipe_button.click()
        assert self.window._recipe_list.entries == recipes

        self.window.close()


class TestDeleteRecipe:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_recipes, date_patch):
        self.table = table_with_recipes
        self.window = MainWindow()

    def test_open_dialog_when_recipe_is_deleted(self):
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.selected_entry == ("Banana Smoothie", 1)

        self.window._delete_recipe_dialog.run = self.window._delete_recipe_dialog.show
        self.window._delete_recipe_button.click()
        assert self.window._delete_recipe_dialog.is_visible()

        self.window._delete_recipe_dialog.close()
        self.window.close()

    def test_delete_selected_recipe_from_database(self):
        recipe_name = "Banana Smoothie"
        self.window._recipe_list.select(1)
        assert recipe_name in self.window._recipe_list.entries.labels
        assert self.window._recipe_list.selected_entry == (recipe_name, 1)

        def confirm_delete_recipe_dialog():
            self.window._delete_recipe_dialog.confirm()
            return Result.CONFIRMED

        self.window._delete_recipe_dialog.run = confirm_delete_recipe_dialog
        self.window._delete_recipe_button.click()
        assert recipe_name not in self.window._recipe_list.entries.labels
        assert self.window._recipe_list.selected_entry == ("Fruit Salad", 0)

        self.table.insert_document({
            "name": "Banana Smoothie",
            "portions": 2,
            "ingredients": [
                {"quantity": 2.0, "unit": 0, "id": 1},
                {"quantity": 2.0, "unit": 7, "id": 2},
                {"quantity": 400.0, "unit": 5, "id": 3},
            ],
            "preparation": "Slice, mix, done.",
        }, 1)
        self.window.close()

    def test_delete_nothing_from_database_if_dialog_is_cancelled(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        def cancel_delete_recipe_dialog():
            self.window._delete_recipe_dialog.cancel()
            return Result.CANCELLED

        self.window._delete_recipe_dialog.run = cancel_delete_recipe_dialog
        self.window._delete_recipe_button.click()
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        self.window.close()

    def test_delete_nothing_from_database_if_dialog_is_closed(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        self.window._recipe_list.select(1)
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        def close_delete_recipe_dialog():
            self.window._delete_recipe_dialog.close()
            return Result.CANCELLED

        self.window._delete_recipe_dialog.run = close_delete_recipe_dialog
        self.window._delete_recipe_button.click()
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_entry == recipes[1]

        self.window.close()

    def test_delete_nothing_from_database_if_no_recipe_is_selected(self):
        recipes = [("Fruit Salad", 0), ("Banana Smoothie", 1)]
        assert self.window._recipe_list.entries == recipes
        assert self.window._recipe_list.selected_index < 0

        self.window._delete_recipe_button.click()
        assert self.window._recipe_list.entries == recipes

        self.window.close()


class TestExportDatabase:

    @pytest.fixture(autouse=True)
    def _main_window(self, table_with_ingredients, table_with_recipes, date_patch):
        self.ingredient_table = table_with_ingredients
        self.recipe_table = table_with_recipes
        self.window = MainWindow()

    def test_open_message_box_when_database_is_exported(self):
        assert not self.ingredient_table.is_empty()
        assert not self.recipe_table.is_empty()

        self.window._export_done_message_box.run = self.window._export_done_message_box.show
        self.window._export_database_button.click()
        assert self.window._export_done_message_box.is_visible()

        self.window._export_done_message_box.close()
        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.window.close()

    def test_export_database_to_json(self):
        assert not self.ingredient_table.is_empty()
        assert not self.recipe_table.is_empty()

        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert filecmp.cmp("ingredients.json", "tests/resources/ingredients.json")
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.window.close()

    def test_export_nothing_if_table_is_empty(self):
        documents = self.recipe_table.get_documents([0, 1])
        self.recipe_table.remove_documents([0, 1])
        assert self.recipe_table.is_empty()

        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert not os.path.exists("recipes.json")

        os.remove("ingredients.json")
        self.recipe_table.insert_document(documents[0].fields, 0)
        self.recipe_table.insert_document(documents[1].fields, 1)
        self.window.close()

    def test_existing_file_triggers_dialog_on_export(self):
        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert os.path.exists("recipes.json")

        self.window._existing_file_dialog.run = self.window._existing_file_dialog.show
        self.window._export_database_button.click()
        assert self.window._existing_file_dialog.is_visible()

        self.window._existing_file_dialog.close()
        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.window.close()

    def test_overwrite_file_if_dialog_is_confirmed(self):
        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        def confirm_existing_file_dialog():
            self.window._existing_file_dialog.confirm()
            return Result.CONFIRMED

        documents = self.recipe_table.get_documents([1])
        self.recipe_table.remove_documents([1])
        self.window._existing_file_dialog.run = confirm_existing_file_dialog
        self.window._export_database_button.click()
        assert not filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.recipe_table.insert_document(documents[0].fields, 1)
        self.window.close()

    def test_export_nothing_if_dialog_is_cancelled(self):
        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        def cancel_existing_file_dialog():
            self.window._existing_file_dialog.cancel()
            return Result.CANCELLED

        documents = self.recipe_table.get_documents([1])
        self.recipe_table.remove_documents([1])
        self.window._existing_file_dialog.run = cancel_existing_file_dialog
        self.window._export_database_button.click()
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.recipe_table.insert_document(documents[0].fields, 1)
        self.window.close()

    def test_export_nothing_if_dialog_is_closed(self):
        self.window._export_done_message_box.run = self.window._export_done_message_box.close
        self.window._export_database_button.click()
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        def close_existing_file_dialog():
            self.window._existing_file_dialog.close()
            return Result.CANCELLED

        documents = self.recipe_table.get_documents([1])
        self.recipe_table.remove_documents([1])
        self.window._existing_file_dialog.run = close_existing_file_dialog
        self.window._export_database_button.click()
        assert filecmp.cmp("recipes.json", "tests/resources/recipes.json")

        os.remove("ingredients.json")
        os.remove("recipes.json")
        self.recipe_table.insert_document(documents[0].fields, 1)
        self.window.close()
