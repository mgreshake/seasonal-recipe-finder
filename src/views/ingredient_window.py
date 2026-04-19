import warnings
from collections.abc import Sequence
from typing import Any, NamedTuple, overload

from database import Database
from layouts import FormLayout, HorizontalBoxLayout, VerticalBoxLayout
from utils.collections import Enum
from widgets import Button, DropdownList, Label, TextField
from windows import MessageBox, Window


MONTHS: Enum = Enum([
    "",
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
])

LOCATIONS: Enum = Enum(["", "regional", "kontinental", "global"])


class Ingredient(NamedTuple):
    name: str = ""
    season: Sequence[int] = [0, 0]
    storage: Sequence[int] = [0, 0]
    origin: int = 0


class IngredientWindow(Window):
    """Input mask for adding or updating ingredients."""

    def __init__(self, parent: Window, *args: Any, **kwargs: Any) -> None:
        """Create input mask and assign button triggers.

        Args:
            parent (Window): Recipe window instance.
            *args (Any): Argument list for base window.
            **kwargs (Any): Keyword arguments for base window.
        """
        layout = VerticalBoxLayout(margins=(25, 25, 25, 25))
        super().__init__(parent, "Ingredient", 350, 250, layout, *args, **kwargs)

        self._database: Database = Database("database.json")
        self._document_id: int | None = None

        self._name_field: TextField = TextField()
        self._season_from_dropdown: DropdownList = DropdownList(
            MONTHS,
            callback=self.synchronize_season_to_dropdown,
            width=100,
        )
        self._season_to_dropdown: DropdownList = DropdownList(
            MONTHS,
            callback=self.synchronize_season_from_dropdown,
            width=100,
        )
        self._storage_from_dropdown: DropdownList = DropdownList(
            MONTHS,
            callback=self.synchronize_storage_to_dropdown,
            width=100,
        )
        self._storage_to_dropdown: DropdownList = DropdownList(
            MONTHS,
            callback=self.synchronize_storage_from_dropdown,
            width=100,
        )
        self._origin_dropdown: DropdownList = DropdownList(LOCATIONS, width=100)

        self._confirm_button: Button = Button("Okay", callback=self.apply_input_and_confirm, width=100)
        self._cancel_button: Button = Button("Cancel", callback=self.cancel, width=100)

        self._missing_name_message_box: MessageBox = MessageBox(
            self,
            "Name field is empty. Please give your ingredient a name.",
            type="warning",
        )
        self._existing_name_message_box: MessageBox = MessageBox(
            self,
            "Ingredient with this name already exists. Please choose another name.",
            type="warning",
        )

        season_selection = HorizontalBoxLayout(spacing=13)
        season_selection.add_item(self._season_from_dropdown)
        season_selection.add_item(Label("to", alignment="center"))
        season_selection.add_item(self._season_to_dropdown)

        storage_selection = HorizontalBoxLayout(spacing=13)
        storage_selection.add_item(self._storage_from_dropdown)
        storage_selection.add_item(Label("to", alignment="center"))
        storage_selection.add_item(self._storage_to_dropdown)

        form = FormLayout(horizontal_spacing=15, vertical_spacing=15)
        form.add_item(Label("Name:"), self._name_field)
        form.add_item(Label("Season:"), season_selection)
        form.add_item(Label("Storage:"), storage_selection)
        form.add_item(Label("Origin:"), self._origin_dropdown)

        buttons = HorizontalBoxLayout("center", spacing=40)
        buttons.add_item(self._confirm_button)
        buttons.add_item(self._cancel_button)

        self.layout.add_item(form)
        self.layout.add_item(buttons)

    def synchronize_season_to_dropdown(self) -> None:
        """If second season dropdown is unset, set it to entry of first one as soon as it is set, and vice versa."""
        if hasattr(self, "_season_to_dropdown"):
            if (self._season_from_dropdown.selected_index <= 0 < self._season_to_dropdown.selected_index
                    or self._season_to_dropdown.selected_index <= 0 < self._season_from_dropdown.selected_index):
                self._season_to_dropdown.select(self._season_from_dropdown.selected_index)

    def synchronize_season_from_dropdown(self) -> None:
        """If first season dropdown is unset, set it to entry of second one as soon as it is set, and vice versa."""
        if hasattr(self, "_season_from_dropdown"):
            if (self._season_to_dropdown.selected_index <= 0 < self._season_from_dropdown.selected_index
                    or self._season_from_dropdown.selected_index <= 0 < self._season_to_dropdown.selected_index):
                self._season_from_dropdown.select(self._season_to_dropdown.selected_index)

    def synchronize_storage_to_dropdown(self) -> None:
        """If second storage dropdown is unset, set it to entry of first one as soon as it is set, and vice versa."""
        if hasattr(self, "_storage_to_dropdown"):
            if (self._storage_from_dropdown.selected_index <= 0 < self._storage_to_dropdown.selected_index
                    or self._storage_to_dropdown.selected_index <= 0 < self._storage_from_dropdown.selected_index):
                self._storage_to_dropdown.select(self._storage_from_dropdown.selected_index)

    def synchronize_storage_from_dropdown(self) -> None:
        """If first storage dropdown is unset, set it to entry of second one as soon as it is set, and vice versa."""
        if hasattr(self, "_storage_from_dropdown"):
            if (self._storage_to_dropdown.selected_index <= 0 < self._storage_from_dropdown.selected_index
                    or self._storage_from_dropdown.selected_index <= 0 < self._storage_to_dropdown.selected_index):
                self._storage_from_dropdown.select(self._storage_to_dropdown.selected_index)

    def apply_input_and_confirm(self) -> None:
        """Read inputs from mask and write ingredient to database, then closes window.

        If the ingredient's name is missing or already present in the database,
        a pop-up warning appears. However, if an existing ingredient has been
        loaded from the database, its fields will be updated instead.
        """
        if not self._name_field.content:
            self._missing_name_message_box.run()
            return

        document = {
            "name": self._name_field.content,
            "season": [self._season_from_dropdown.selected_entry.data, self._season_to_dropdown.selected_entry.data],
            "storage": [self._storage_from_dropdown.selected_entry.data, self._storage_to_dropdown.selected_entry.data],
            "origin": self._origin_dropdown.selected_entry.data,
        }

        if self._ingredient_already_exists(document["name"]):
            self._existing_name_message_box.run()
            return

        if self._document_id is None:
            self._database.ingredient.insert_document(document)
        else:
            self._database.ingredient.update_documents([self._document_id], document)

        self.confirm(document["name"])

    def _ingredient_already_exists(self, name: str) -> bool:
        """Check if ingredient with same name already exists in database.

        Args:
            name (str): Ingredient name.

        Returns:
            bool: `True` if name already exists, `False` otherwise.
        """
        if results := self._database.ingredient.search(f"name == '{name}'"):
            return results[0].id != self._document_id
        return False

    @overload
    def fill(self, ingredient: Ingredient) -> None:
        ...

    @overload
    def fill(self, ingredient_id: int) -> None:
        ...

    def fill(self, ingredient: Ingredient | int) -> None:
        """Fill input mask either with predefined values or with document retrieved from database.

        Args:
            ingredient (Ingredient | int): Values to be applied. If `int`, argument is interpreted as document ID and
                values are fetched from database.
        """
        self.clear()

        if isinstance(ingredient, int):
            self._document_id = ingredient
            ingredient = self._get_ingredient_from_database()

        self._name_field.fill(ingredient.name)
        self._season_from_dropdown.select(ingredient.season[0])
        self._season_to_dropdown.select(ingredient.season[1])
        self._storage_from_dropdown.select(ingredient.storage[0])
        self._storage_to_dropdown.select(ingredient.storage[1])
        self._origin_dropdown.select(ingredient.origin)

    def _get_ingredient_from_database(self) -> Ingredient:
        """Return ingredient with specified ID from database if available.

        If no document with the specified ID is found, raise a warning and return default values.

        Returns:
            Ingredient: Document including ingredient name, season, storage and origin.
        """
        try:
            document = self._database.ingredient.get_documents([self._document_id])[0]
            return Ingredient(**document.fields)
        except IndexError:
            if self._document_id is not None:
                warnings.warn(f"No document with ID {self._document_id} found. New ingredient will be created.")
                self._document_id = None
            return Ingredient()

    def clear(self) -> None:
        """Reset input mask."""
        self._document_id = None
        self._name_field.fill("")
        self._season_from_dropdown.select(0)
        self._season_to_dropdown.select(0)
        self._storage_from_dropdown.select(0)
        self._storage_to_dropdown.select(0)
        self._origin_dropdown.select(0)

    def on_started(self) -> None:
        """Hide recipe window."""
        self.parent.hide()
        super().on_started()

    def on_closed(self) -> None:
        """Shows recipe window again."""
        self.clear()
        self.parent.show()
        super().on_closed()
