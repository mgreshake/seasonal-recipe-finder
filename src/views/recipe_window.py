import warnings
from collections.abc import Sequence
from typing import Any, NamedTuple, TypedDict, overload

from database import Database
from layouts import FormLayout, HorizontalBoxLayout, VerticalBoxLayout
from utils.collections import Enum, ListEntry
from utils.numerics import Number
from views.ingredient_window import Ingredient, IngredientWindow
from widgets import Button, ComboBox, DropdownList, Icon, Label, ListBox, TextBox, TextField
from windows import Dialog, MessageBox, Result, Window


DECIMAL_SEPARATOR: str = ","

QUANTITY_UNITS: Enum = Enum([
    "",
    "g",
    "kg",
    "mg",
    "l",
    "ml",
    "cl",
    "TL",
    "EL",
    "Prise",
    "Msp.",
    "Pck.",
    "Bund",
    "Handvoll",
    "Tropfen",
    "Scheiben",
    "Stangen",
    "Stiele",
    "Zweige",
    "Blätter",
    "Beet",
])

INGREDIENT_PLACEHOLDER: str = "Unknown"

MIN_NUM_INGREDIENTS: int = 2


class Recipe(NamedTuple):
    name: str = ""
    portions: int = 1
    ingredients: Sequence = []
    preparation: str = ""


class IngredientData(TypedDict):
    quantity: float
    unit: int
    id: int


class RecipeWindow(Window):
    """Input mask for adding or updating recipes."""

    def __init__(self, parent: Window, *args: Any, **kwargs: Any) -> None:
        """Create input mask and assign button triggers.

        Args:
            parent (Window): Main window instance.
            *args (Any): Argument list for base window.
            **kwargs (Any): Keyword arguments for base window.
        """
        layout = VerticalBoxLayout(spacing=25, margins=(25, 25, 25, 25))
        super().__init__(parent, "Recipe", 440, 590, layout, *args, **kwargs)

        self._database: Database = Database("database.json")
        self._document_id: int | None = None

        self._database.create_table("ingredient", suppress_warning=True)

        ingredients = {document["name"]: document.id for document in self._database.ingredient.search(sort_by="name")}

        add_ingredient_icon = Icon("src/resources/plus-solid.svg")
        remove_ingredient_icon = Icon("src/resources/minus-solid.svg")
        edit_ingredient_icon = Icon("src/resources/pen-solid.svg")
        delete_ingredient_icon = Icon("src/resources/trash-can-solid.svg")

        self._name_field: TextField = TextField()
        self._portion_field: TextField = TextField(text="1", alignment="right", policy="count", width=36)

        self._quantity_field: TextField = TextField(alignment="right", policy="number", width=80)
        self._quantity_unit_dropdown: DropdownList = DropdownList(QUANTITY_UNITS, width=80)
        self._ingredient_combo_box: ComboBox = ComboBox(ingredients, width=218)

        self._ingredient_list: ListBox = ListBox(callback=self.update_ingredient_selection, width=356, height=130)
        self._add_ingredient_button: Button = Button(
            add_ingredient_icon,
            callback=self.add_ingredient_to_list,
            height=28,
        )
        self._remove_ingredient_button: Button = Button(
            remove_ingredient_icon,
            callback=self.remove_ingredient_from_list,
            height=28,
        )
        self._edit_ingredient_button: Button = Button(
            edit_ingredient_icon,
            callback=self.update_ingredient_in_database,
            height=28,
        )
        self._delete_ingredient_button: Button = Button(
            delete_ingredient_icon,
            callback=self.delete_ingredient_from_database,
            height=28,
        )

        self._preparation_field: TextBox = TextBox(width=390, height=180)

        self._confirm_button: Button = Button("Okay", callback=self.apply_input_and_confirm, width=100)
        self._cancel_button: Button = Button("Cancel", callback=self.cancel, width=100)

        self._ingredient_window: IngredientWindow = IngredientWindow(
            self,
            confirm_callback=self.update_ingredient_combo_boxes,
        )
        self._delete_ingredient_dialog: Dialog = Dialog(
            self,
            "Are you sure to delete ingredient from database? This operation cannot be reverted.",
        )
        self._missing_name_message_box: MessageBox = MessageBox(
            self,
            "Name field is empty. Please give your recipe a name.",
            type="warning",
        )
        self._missing_ingredients_message_box: MessageBox = MessageBox(
            self,
            f"Recipe must contain at least {MIN_NUM_INGREDIENTS} ingredients. Please add more ingredients.",
            type="warning",
        )
        self._existing_name_message_box: MessageBox = MessageBox(
            self,
            "Recipe with this name already exists. Please choose another name.",
            type="warning",
        )

        form = FormLayout(horizontal_spacing=15)
        form.add_item(Label("Name:"), self._name_field)
        form.add_item(Label("Portions:"), self._portion_field)

        ingredient_selection = HorizontalBoxLayout()
        ingredient_selection.add_item(self._quantity_field)
        ingredient_selection.add_item(self._quantity_unit_dropdown)
        ingredient_selection.add_item(self._ingredient_combo_box)

        ingredient_buttons = VerticalBoxLayout()
        ingredient_buttons.add_item(self._add_ingredient_button)
        ingredient_buttons.add_item(self._remove_ingredient_button)
        ingredient_buttons.add_item(self._edit_ingredient_button)
        ingredient_buttons.add_item(self._delete_ingredient_button)

        ingredient_panel = HorizontalBoxLayout()
        ingredient_panel.add_item(self._ingredient_list)
        ingredient_panel.add_item(ingredient_buttons)

        ingredients = VerticalBoxLayout()
        ingredients.add_item(Label("Ingredients:"))
        ingredients.add_item(ingredient_selection)
        ingredients.add_item(ingredient_panel)

        preparation = VerticalBoxLayout()
        preparation.add_item(Label("Preparation:"))
        preparation.add_item(self._preparation_field)

        buttons = HorizontalBoxLayout("center", spacing=40)
        buttons.add_item(self._confirm_button)
        buttons.add_item(self._cancel_button)

        self.layout.add_item(form)
        self.layout.add_item(ingredients)
        self.layout.add_item(preparation)
        self.layout.add_item(buttons)

    def update_ingredient_selection(self) -> None:
        """Update selection according to selected entry from ingredient list."""
        self._clear_ingredient_selection()

        if self._ingredient_list.selected_index >= 0:
            entry_data = self._ingredient_list.selected_entry.data
            quantity = Number(entry_data["quantity"], DECIMAL_SEPARATOR)
            documents = self._database.get_documents([entry_data["id"]])
            ingredient_name = documents[0]["name"] if documents else ""

            self._quantity_field.fill(str(quantity))
            self._quantity_unit_dropdown.select(entry_data["unit"])
            self._ingredient_combo_box.text_field.fill(ingredient_name)

    def _clear_ingredient_selection(self) -> None:
        """Reset ingredient selection."""
        self._quantity_field.fill("")
        self._quantity_unit_dropdown.select(0)
        self._ingredient_combo_box.text_field.fill("")

    def add_ingredient_to_list(self) -> None:
        """Add ingredient with quantity from selection to ingredient list.

        If the ingredient does not exist, open the ingredient window to create
        a new one. The newly created ingredient is then added to the ingredient
        list. If the creation process is cancelled, nothing is added. Each
        ingredient can only be added once.
        """
        if (ingredient := self._ingredient_combo_box.selected_entry).data is None:
            self._ingredient_window.fill(Ingredient(name=ingredient.label))
            if self._ingredient_window.run() != Result.CONFIRMED:
                return

        entry_data = self.fetch_ingredient_from_selection()
        list_entry = self.create_ingredient_list_entry(entry_data)

        for index, entry in enumerate(self._ingredient_list.entries):
            if entry.data["id"] == list_entry.data["id"]:
                self._ingredient_list.update(index, list_entry)
                return

        if (index := self._ingredient_list.selected_index) < 0:
            self._ingredient_list.append(list_entry)
        else:
            self._ingredient_list.insert(index, list_entry)

    def remove_ingredient_from_list(self) -> None:
        """Remove selected entry from ingredient list."""
        if (index := self._ingredient_list.selected_index) >= 0:
            self._ingredient_list.remove(index)

    def update_ingredient_in_database(self) -> None:
        """Update selected ingredient in database.

        Open the ingredient window to update the ingredient behind the selected
        entry from the ingredient list. If the update process is cancelled, the
        database remains untouched.
        """
        if (index := self._ingredient_list.selected_index) >= 0:
            ingredient = self._ingredient_list.selected_entry
            self._ingredient_window.fill(ingredient.data["id"])
            if self._ingredient_window.run() == Result.CONFIRMED:
                entry_data = self.fetch_ingredient_from_selection()
                list_entry = self.create_ingredient_list_entry(entry_data)
                self._ingredient_list.update(index, list_entry)

    def delete_ingredient_from_database(self) -> None:
        """Delete selected ingredient from database.

        Ask whether the ingredient behind the selected entry should be deleted
        from database. If the deletion is confirmed, the entry is also removed
        from the ingredient list. Otherwise, no changes are applied. If the
        ingredient is still used in a recipe, it cannot be deleted.
        """
        if (index := self._ingredient_list.selected_index) >= 0:
            ingredient_id = self._ingredient_list.selected_entry.data["id"]
            if self._delete_ingredient_dialog.run() == Result.CONFIRMED:
                self._database.ingredient.remove_documents([ingredient_id])
                self.update_ingredient_combo_boxes("")
                self._ingredient_list.remove(index)

    def fetch_ingredient_from_selection(self) -> IngredientData:
        """Fetch ingredient with quantity from selection.

        Returns:
            IngredientData: Quantity, quantity unit and document ID of selected ingredient.
        """
        quantity = Number(self._quantity_field.content, DECIMAL_SEPARATOR)
        quantity_unit = self._quantity_unit_dropdown.selected_entry.data
        ingredient_id = self._ingredient_combo_box.selected_entry.data
        return {"quantity": float(quantity), "unit": quantity_unit, "id": ingredient_id}

    def create_ingredient_list_entry(self, entry_data: IngredientData) -> ListEntry[IngredientData]:
        """Create label and entry data for ingredient list.

        If the ingredient is not found in the database, a placeholder name is used instead.

        Args:
            entry_data (IngredientData): Ingredient data for list entry.

        Returns:
            ListEntry[IngredientData]: List entry including label and ingredient data.
        """
        quantity = Number(entry_data["quantity"], DECIMAL_SEPARATOR)
        quantity_unit = QUANTITY_UNITS(entry_data["unit"]).name
        documents = self._database.ingredient.get_documents([entry_data["id"]])
        ingredient_name = documents[0]["name"] if documents else INGREDIENT_PLACEHOLDER

        label = " ".join(filter(bool, [str(quantity), quantity_unit, ingredient_name]))
        return ListEntry(label, entry_data)

    def update_ingredient_combo_boxes(self, ingredient: str) -> None:
        """Update entries in ingredient combo boxes.

        Args:
            ingredient (str): New or edited ingredient name from input mask.
        """
        ingredients = {document["name"]: document.id for document in self._database.ingredient.search(sort_by="name")}
        self._ingredient_combo_box.entries = ingredients
        self._ingredient_combo_box.text_field.fill(ingredient)
        self.parent._ingredient_combo_box.entries = ingredients
        self.parent._ingredient_combo_box.text_field.fill("")
        self.parent.add_recipe_to_view()

    def apply_input_and_confirm(self) -> None:
        """Read input from mask and write recipe to database, then close window.

        If the recipe's name is missing or the ingredients list features less
        than two ingredients, a pop-up warning appears. However, if an existing
        recipe has been loaded from the database, its fields will be updated
        instead.
        """
        if not self._name_field.content:
            self._missing_name_message_box.run()
            return

        if self._ingredient_list.count < MIN_NUM_INGREDIENTS:
            self._missing_ingredients_message_box.run()
            return

        document = {
            "name": self._name_field.content,
            "portions": int(self._portion_field.content),
            "ingredients": list(self._ingredient_list.entries.data),
            "preparation": self._preparation_field.content,
        }

        if self._recipe_already_exists(document["name"]):
            self._existing_name_message_box.run()
            return

        if self._document_id is None:
            self._database.recipe.insert_document(document)
        else:
            self._database.recipe.update_documents([self._document_id], document)

        self.confirm(document["name"])

    def _recipe_already_exists(self, name: str) -> bool:
        """Check if recipe with same name already exists in database.

        Args:
            name (str): Recipe name.

        Returns:
            bool: `True` if name already exists, `False` otherwise.
        """
        if results := self._database.recipe.search(f"name == '{name}'"):
            return results[0].id != self._document_id
        return False

    @overload
    def fill(self, recipe: Recipe) -> None:
        ...

    @overload
    def fill(self, recipe_id: int) -> None:
        ...

    def fill(self, recipe: Recipe | int) -> None:
        """Fill input mask either with predefined values or with document retrieved from database.

        Args:
            recipe (Recipe | int): Values to be applied. If `int`, argument is interpreted as document ID and values are
                fetched from database.
        """
        self.clear()

        if isinstance(recipe, int):
            self._document_id = recipe
            recipe = self._get_recipe_from_database()

        self._name_field.fill(recipe.name)
        self._portion_field.fill(str(recipe.portions))
        self._preparation_field.fill(recipe.preparation)

        for ingredient in recipe.ingredients:
            list_entry = self.create_ingredient_list_entry(ingredient)
            self._ingredient_list.append(list_entry)

    def _get_recipe_from_database(self) -> Recipe:
        """Return recipe with specified ID from database if available.

        If no document with the specified ID is found, raise a warning and return default values.

        Returns:
            Recipe: Document including recipe name, number of portions, ingredient list and preparation instructions.
        """
        try:
            document = self._database.recipe.get_documents([self._document_id])[0]
            return Recipe(**document.fields)
        except IndexError:
            if self._document_id is not None:
                warnings.warn(f"No document with ID {self._document_id} found. New recipe will be created.")
                self._document_id = None
            return Recipe()

    def clear(self) -> None:
        """Reset input mask."""
        self._document_id = None
        self._name_field.fill("")
        self._portion_field.fill("1")
        self._quantity_field.fill("")
        self._quantity_unit_dropdown.select(0)
        self._ingredient_combo_box.text_field.fill("")
        self._ingredient_list.clear()
        self._preparation_field.fill("")

    def on_started(self) -> None:
        """Hide main window."""
        self.parent.hide()
        super().on_started()

    def on_closed(self) -> None:
        """Shows main window again."""
        self.clear()
        self.parent.show()
        super().on_closed()
