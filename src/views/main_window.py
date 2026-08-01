import datetime
import json
import math
import os

from database import Database, Document, Table
from graphics import EmptySpace, VerticalLine
from layouts import FormLayout, HorizontalBoxLayout, VerticalBoxLayout
from views.recipe_window import Recipe, RecipeWindow
from widgets import Button, ComboBox, Icon, Label, ListBox, TextBox, TextField, DropdownList
from windows import Application, Dialog, MessageBox, Result


SEASON_COEFFICIENT: float = 0.6
STORAGE_COEFFICIENT: float = 0.54
RARITY_COEFFICIENT: float = 0.25
ORIGIN_COEFFICIENT: float = 0.4


class MainWindow(Application):
    """Interface for searching and filtering recipes."""

    def __init__(self):
        """Create GUI elements, assign button triggers and search database for recipes."""
        layout = HorizontalBoxLayout(spacing=35, margins=(25, 25, 25, 25))
        super().__init__("Seasonal Recipe Finder", 900, 600, layout)

        self._database: Database = Database("database.json")

        self._database.create_table("recipe", suppress_warning=True)
        self._database.create_table("ingredient", suppress_warning=True)

        documents = self._database.recipe.search(sort_by={self.calc_sustainability_score: "desc", "name": "asc"})
        recipes = {document["name"]: document.id for document in documents}
        ingredients = {document["name"]: document.id for document in self._database.ingredient.search(sort_by="name")}

        search_recipe_icon = Icon("src/resources/magnifying-glass-solid.svg")
        add_recipe_icon = Icon("src/resources/plus-solid.svg")
        edit_recipe_icon = Icon("src/resources/pen-solid.svg")
        delete_recipe_icon = Icon("src/resources/trash-can-solid.svg")
        export_database_icon = Icon("src/resources/download-solid-full.svg")

        self._recipe_name_field: TextField = TextField()
        self._ingredient_combo_box: ComboBox = ComboBox(ingredients)

        self._recipe_list: ListBox = ListBox(entries=recipes, callback=self.fill_portion_field, width=355)
        self._search_recipe_button: Button = Button(
            search_recipe_icon,
            callback=self.search_database_for_recipes,
            height=28,
        )
        self._add_recipe_button: Button = Button(
            add_recipe_icon,
            callback=self.add_recipe_to_database,
            height=28,
        )
        self._edit_recipe_button: Button = Button(
            edit_recipe_icon,
            callback=self.update_recipe_in_database,
            height=28,
        )
        self._delete_recipe_button: Button = Button(
            delete_recipe_icon,
            callback=self.delete_recipe_from_database,
            height=28,
        )
        self._export_database_button: Button = Button(
            export_database_icon,
            callback=self.export_database_to_json,
            height=28,
        )

        self._portion_field: TextField = TextField(
            alignment="right",
            policy="count",
            callback=self.add_recipe_to_view,
            width=36,
        )
        self._language_dropdown: DropdownList = DropdownList(["EN"])
        self._recipe_view: TextBox = TextBox(is_editable=False, width=389)

        self._recipe_window: RecipeWindow = RecipeWindow(self, confirm_callback=self.update_recipe_list)
        self._delete_recipe_dialog: Dialog = Dialog(
            self,
            "Are you sure to delete recipe from database? This operation cannot be reverted.",
        )
        self._existing_file_dialog: Dialog = Dialog(
            self,
            "Export already exists. Are you sure to overwrite existing files?",
        )
        self._export_done_message_box: MessageBox = MessageBox(
            self,
            "Export database successfully.",
            type="info",
        )

        recipe_selection = FormLayout(horizontal_spacing=15)
        recipe_selection.add_item(Label("Recipe:"), self._recipe_name_field)
        recipe_selection.add_item(Label("Ingredients:"), self._ingredient_combo_box)

        recipe_buttons = VerticalBoxLayout()
        recipe_buttons.add_item(self._search_recipe_button)
        recipe_buttons.add_item(self._add_recipe_button)
        recipe_buttons.add_item(self._edit_recipe_button)
        recipe_buttons.add_item(self._delete_recipe_button)
        recipe_buttons.add_item(self._export_database_button)
        recipe_buttons.add_item(EmptySpace())

        recipe_panel = HorizontalBoxLayout()
        recipe_panel.add_item(self._recipe_list)
        recipe_panel.add_item(recipe_buttons)

        left_side = VerticalBoxLayout(spacing=15)
        left_side.add_item(recipe_selection)
        left_side.add_item(recipe_panel)

        separator = VerticalLine(550)

        header = HorizontalBoxLayout(spacing=15)
        header.add_item(Label("Portions:"))
        header.add_item(self._portion_field)
        header.add_item(EmptySpace(width=213))
        header.add_item(self._language_dropdown)

        right_side = VerticalBoxLayout(spacing=15)
        right_side.add_item(header)
        right_side.add_item(self._recipe_view)

        self.layout.add_item(left_side)
        self.layout.add_item(separator)
        self.layout.add_item(right_side)

    def calc_sustainability_score(self, document: Document) -> float:
        """Calculate sustainability score based on ingredients' seasons and origins.

        A higher sustainability score is achieved if the recipe contains
        ingredients that are in season and originate regionally. Ingredients
        that are off-season and come from further afield result in lower
        scores.

        Args:
            document (Document): Recipe for which score is calculated.

        Returns:
            float: Sustainability score between `0.0` and `1.0`.
        """
        score = 0.0

        ingredient_ids = map(lambda ingredient: ingredient["id"], document["ingredients"])
        ingredients = self._database.ingredient.get_documents(ingredient_ids)
        seasonal_ingredients = list(filter(self._has_season_info, ingredients))

        if not seasonal_ingredients:
            return score

        current_month = datetime.date.today().month
        season_score = lambda x, y, z: math.exp(x * y * (1 - z) / 11) - 1 + x

        for ingredient in seasonal_ingredients:
            has_season = self._is_month_between(current_month, *ingredient["season"])
            is_storing = self._is_month_between(current_month, *ingredient["storage"])
            length = self._calc_season_length(*ingredient["season"]) + self._calc_season_length(*ingredient["storage"])

            if has_season:
                score += season_score(SEASON_COEFFICIENT, RARITY_COEFFICIENT, length)
            elif is_storing:
                score += season_score(STORAGE_COEFFICIENT, RARITY_COEFFICIENT, length)

            score += ORIGIN_COEFFICIENT / ingredient["origin"] if ingredient["origin"] else 0.0

        return score / len(seasonal_ingredients)

    @staticmethod
    def _has_season_info(ingredient: Document) -> bool:
        """Check if ingredient has information about season or storage.

        Args:
            ingredient (Document): Ingredient to be checked.

        Returns:
            bool: `True` if season information is available, `False` otherwise.
        """
        return ingredient["season"][0] > 0 or ingredient["storage"][0] > 0

    @staticmethod
    def _is_month_between(month: int, start: int, end: int) -> bool:
        """Check if month lies within time period.

        Args:
            month (int): Month to be checked.
            start (int): First month of time period.
            end (int): Last month of time period.

        Returns:
            bool: `True` if month is within time period, `False` otherwise.
        """
        return (month - start) % 12 <= (end - start) % 12

    @staticmethod
    def _calc_season_length(start: int, end: int) -> int:
        """Calculate range between two months.

        Args:
            start (int): First month of season.
            end (int): Last month of season.

        Returns:
            int: Length of season.
        """
        return (end - start) % 12 + 1 if start and end else 0

    def fill_portion_field(self) -> None:
        """Set number of portions from recipe data."""
        if (list_entry := self._recipe_list.selected_entry) is not None:
            recipe = self._database.recipe.get_documents([list_entry.data])[0]
            self._portion_field.fill(str(recipe["portions"]))
        else:
            self._portion_field.fill("")

    def search_database_for_recipes(self) -> None:
        """Search database for recipes, filtered by name or ingredients."""
        conditions = []

        if recipe_name := self._recipe_name_field.content:
            conditions.append(f"name.contains('{recipe_name}')")
        if self._ingredient_combo_box.selected_index >= 0:
            ingredient_id = self._ingredient_combo_box.selected_entry.data
            conditions.append(f"ingredients.id == {ingredient_id}")

        conditions = (f"({condition})" for condition in conditions) if len(conditions) > 1 else conditions
        documents = self._database.recipe.search(
            " & ".join(conditions),
            sort_by={self.calc_sustainability_score: "desc", "name": "asc"},
        )
        self._recipe_list.entries = {document["name"]: document.id for document in documents}

    def add_recipe_to_database(self) -> None:
        """Add new recipe to database.

        Open the recipe window to create a new recipe. The newly created recipe
        is then added to the recipe list. If the creation process is cancelled,
        nothing is added.
        """
        recipe_name = self._recipe_name_field.content
        self._recipe_window.fill(Recipe(name=recipe_name))
        self._recipe_window.run()

    def update_recipe_in_database(self) -> None:
        """Update selected recipe in database.

        Open the recipe window to update the recipe behind the selected entry
        from the recipe list. If the update process is cancelled, the database
        remains untouched.
        """
        if self._recipe_list.selected_index >= 0:
            recipe_id = self._recipe_list.selected_entry.data
            self._recipe_window.fill(recipe_id)
            if self._recipe_window.run() == Result.CONFIRMED:
                index = self._recipe_list.entries.data.index(recipe_id)
                self._recipe_list.select(index)

    def delete_recipe_from_database(self) -> None:
        """Delete selected recipe from database.

        Ask whether the recipe behind the selected entry should be deleted from
        database. If the deletion is confirmed, the entry is also removed from
        recipe list. Otherwise, no changes are applied.
        """
        if (index := self._recipe_list.selected_index) >= 0:
            recipe_id = self._recipe_list.selected_entry.data
            if self._delete_recipe_dialog.run() == Result.CONFIRMED:
                self._database.recipe.remove_documents([recipe_id])
                self._recipe_list.remove(index)

    def export_database_to_json(self) -> None:
        """Export ingredients and recipes from database to JSON files.

        If the database is empty, nothing will be exported.
        """
        if self._export_already_exists() and self._existing_file_dialog.run() == Result.CANCELLED:
            return

        has_exported = False

        if not self._database.ingredient.is_empty():
            self._export_table_to_json(self._database.ingredient, "ingredients.json")
            has_exported = True
        if not self._database.recipe.is_empty():
            self._export_table_to_json(self._database.recipe, "recipes.json")
            has_exported = True

        if has_exported:
            self._export_done_message_box.run()

    @staticmethod
    def _export_already_exists() -> bool:
        """Check if files to be exported already exist.

        Returns:
            bool: `True` if database export already exists, `False` otherwise.
        """
        return os.path.exists("ingredients.json") or os.path.exists("recipes.json")

    @staticmethod
    def _export_table_to_json(table: Table, filename: str) -> None:
        """Write documents of table to JSON file.

        Args:
            table (Table): Table to be exported.
            filename (str): Name of JSON file.
        """
        with open(filename, "w") as file:
            documents = table.get_documents()
            json.dump(documents, file, indent=2)

    def update_recipe_list(self, recipe: str) -> None:
        """Update recipe list entries and selection.

        Args:
            recipe (str): New or edited recipe name from input mask.
        """
        documents = self._database.recipe.search(sort_by={self.calc_sustainability_score: "desc", "name": "asc"})
        recipes = {document["name"]: document.id for document in documents}
        self._recipe_list.entries = recipes
        index = self._recipe_list.entries.labels.index(recipe)
        self._recipe_list.select(index)

    def add_recipe_to_view(self) -> None:
        """Update recipe view according to selected recipe.

        The quantity of the ingredients is adjusted according to the content of
        the portions field. The number of portions must be at least one.
        """
        if self._recipe_list.selected_index < 0:
            self._recipe_view.fill("")

        elif self._portion_field.content:
            recipe_id = self._recipe_list.selected_entry.data
            recipe = self._database.recipe.get_documents([recipe_id])[0]
            recipe_text = "Ingredients:\n\n"

            for ingredient in recipe["ingredients"]:
                ingredient = ingredient.copy()
                ingredient["quantity"] *= int(self._portion_field.content) / recipe["portions"]
                ingredient_label = self._recipe_window.create_ingredient_list_entry(ingredient).label
                recipe_text += f"{ingredient_label}\n"

            recipe_text += f"\n\nPreparation:\n\n{recipe['preparation']}"

            self._recipe_view.fill(recipe_text)
