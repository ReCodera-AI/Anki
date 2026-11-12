# Copyright: Anki Software, LLC and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from __future__ import annotations

import re
from abc import ABC, abstractmethod, abstractproperty
from collections.abc import Sequence
from typing import cast

import anki.lang
from anki.browser import BrowserConfig
from anki.cards import Card, CardId
from anki.collection import Collection
from anki.errors import NotFoundError
from anki.models import NotetypeId
from anki.notes import Note, NoteId
from anki.utils import ids2str
from aqt.browser.table import Column, ItemId, ItemList


def browser_group_sort_locale(
    notetype_locale: str, manual_locales: Sequence[str]
) -> str:
    """Prefer a Note Type locale, then a shared Manual locale for every Deck."""
    if notetype_locale:
        return notetype_locale
    if not manual_locales or any(not locale for locale in manual_locales):
        return ""
    locales: dict[str, str] = {}
    for locale in manual_locales:
        normalized = locale.replace("_", "-")
        locales.setdefault(normalized.casefold(), normalized)
    return next(iter(locales.values())) if len(locales) == 1 else ""


class ItemState(ABC):
    GEOMETRY_KEY_PREFIX: str
    SORT_COLUMN_KEY: str
    SORT_BACKWARDS_KEY: str
    _active_columns: list[str]
    BROWSER_SORT_FIELD_MODE_KEY = "_browser_sortFieldMode"

    def __init__(self, col: Collection) -> None:
        self.col = col
        self._sort_column = self.col.get_config(self.SORT_COLUMN_KEY)
        self._sort_backwards = self.col.get_config(self.SORT_BACKWARDS_KEY, False)

    def is_notes_mode(self) -> bool:
        """Return True if the state is a NoteState."""
        return isinstance(self, NoteState)

    def _sort_field_settings(self, search: str, order: bool | str | Column):
        if not isinstance(order, Column) or order.key != "noteFld":
            return None
        deck_match = re.match(
            r'^\s*deck:(?:"((?:\\.|[^"])*)"|([^\s]+))(?:\s|$)', search
        )
        if not deck_match or re.search(
            r"\bor\b|(?:^|\s)-?deck:", search[deck_match.end() :]
        ):
            return None
        deck_name = deck_match.group(1)
        if deck_name is not None:
            deck_name = deck_name.replace('\\"', '"').replace("\\\\", "\\")
        else:
            deck_name = deck_match.group(2)
        deck_id = (
            self.col.decks.get_current_id()
            if deck_name == "current"
            else self.col.decks.id_for_name(deck_name)
        )
        if deck_id is None:
            return None
        options = self.col.get_config(f"_deck_{deck_id}_sortField", {})
        if not isinstance(options, dict):
            return None
        mode = options.get("mode", "automatic")
        locale = options.get("locale", "")
        if mode not in ("automatic", "manual", "browser") or not isinstance(
            locale, str
        ):
            return None
        return mode, locale

    def _find_items_with_locale(
        self,
        search: str,
        order: bool | str | Column,
        reverse: bool,
        fallback_locale: str,
        manual_locale: str,
        notetype_id: int = 0,
    ) -> Sequence[ItemId]:
        if self.is_notes_mode():
            return self.col.find_notes(
                search,
                order,
                reverse,
                fallback_locale,
                manual_sort_locale=manual_locale,
                sort_notetype_id=notetype_id,
            )
        return self.col.find_cards(
            search,
            order,
            reverse,
            fallback_locale,
            manual_sort_locale=manual_locale,
            sort_notetype_id=notetype_id,
        )

    def _find_browser_sorted_items(
        self, search: str, order: bool | str | Column, reverse: bool
    ) -> Sequence[ItemId] | None:
        settings = self._sort_field_settings(search, order)
        if settings is None:
            if (
                not isinstance(order, Column)
                or order.key != "noteFld"
                or self.col.get_config(self.BROWSER_SORT_FIELD_MODE_KEY) != "browser"
            ):
                return None
            mode, manual_locale = "browser", ""
        else:
            mode, manual_locale = settings
        fallback_locale = anki.lang.current_lang
        if mode == "manual" and manual_locale:
            return self._find_items_with_locale(
                search, order, reverse, fallback_locale, manual_locale
            )
        if mode != "browser":
            return None

        unordered = self._find_items_with_locale(
            search, False, False, fallback_locale, ""
        )
        if not unordered:
            return []
        assert self.col.db is not None
        matching_cards = (
            self.col.find_cards(search, False, False, fallback_locale)
            if self.is_notes_mode()
            else unordered
        )
        if not matching_cards:
            return []
        rows = self.col.db.all(
            f"select distinct n.mid, c.did from cards c join notes n on n.id=c.nid "
            f"where c.id in {ids2str(matching_cards)}"
        )
        group_decks: dict[int, set[int]] = {}
        for notetype_id, deck_id in rows:
            group_decks.setdefault(notetype_id, set()).add(deck_id)
        names = {entry.id: entry.name for entry in self.col.models.all_names_and_ids()}
        ordered_ids: list[ItemId] = []
        for notetype_id in sorted(
            group_decks, key=lambda ntid: (names.get(ntid, "").casefold(), ntid)
        ):
            notetype_locale = self.col.get_aux_notetype_config(
                NotetypeId(notetype_id), "sortFieldLocale", ""
            )
            if not isinstance(notetype_locale, str):
                notetype_locale = ""
            manual_locales = []
            for did in group_decks[notetype_id]:
                deck_options = self.col.get_config(f"_deck_{did}_sortField", {})
                if (
                    isinstance(deck_options, dict)
                    and deck_options.get("mode") == "manual"
                    and isinstance(deck_options.get("locale"), str)
                    and deck_options["locale"]
                ):
                    manual_locales.append(deck_options["locale"])
                else:
                    manual_locales.append("")
            locale = browser_group_sort_locale(notetype_locale, manual_locales)
            ordered_ids.extend(
                self._find_items_with_locale(
                    search,
                    order,
                    False,
                    fallback_locale,
                    locale,
                    notetype_id,
                )
            )
        if reverse:
            ordered_ids.reverse()
        return ordered_ids

    # Stateless Helpers

    def note_ids_from_card_ids(self, items: Sequence[ItemId]) -> Sequence[NoteId]:
        assert self.col.db is not None
        return self.col.db.list(
            f"select distinct nid from cards where id in {ids2str(items)}"
        )

    def card_ids_from_note_ids(self, items: Sequence[ItemId]) -> Sequence[CardId]:
        assert self.col.db is not None
        return self.col.db.list(f"select id from cards where nid in {ids2str(items)}")

    def column_key_at(self, index: int) -> str:
        return self._active_columns[index]

    def column_label(self, column: Column) -> str:
        return (
            column.notes_mode_label if self.is_notes_mode() else column.cards_mode_label
        )

    def column_tooltip(self, column: Column) -> str:
        if self.is_notes_mode():
            return column.notes_mode_tooltip
        return column.cards_mode_tooltip

    # Columns and sorting

    # abstractproperty is deprecated but used due to mypy limitations
    # (https://github.com/python/mypy/issues/1362)
    @abstractproperty
    def active_columns(self) -> list[str]:
        """Return the saved or default columns for the state."""

    @abstractmethod
    def toggle_active_column(self, column: str) -> None:
        """Add or remove an active column."""

    @property
    def sort_column(self) -> str:
        return self._sort_column

    @sort_column.setter
    def sort_column(self, column: str) -> None:
        self.col.set_config(self.SORT_COLUMN_KEY, column)
        self._sort_column = column

    @property
    def sort_backwards(self) -> bool:
        "If true, descending order."
        return self._sort_backwards

    @sort_backwards.setter
    def sort_backwards(self, order: bool) -> None:
        self.col.set_config(self.SORT_BACKWARDS_KEY, order)
        self._sort_backwards = order

    # Get objects

    @abstractmethod
    def get_card(self, item: ItemId) -> Card:
        """Return the item if it's a card or its first card if it's a note."""

    @abstractmethod
    def get_note(self, item: ItemId) -> Note:
        """Return the item if it's a note or its note if it's a card."""

    # Get ids

    @abstractmethod
    def find_items(
        self, search: str, order: bool | str | Column, reverse: bool
    ) -> Sequence[ItemId]:
        """Return the item ids fitting the given search and order."""

    @abstractmethod
    def get_item_from_card_id(self, card: CardId) -> ItemId:
        """Return the appropriate item id for a card id."""

    @abstractmethod
    def get_card_ids(self, items: Sequence[ItemId]) -> Sequence[CardId]:
        """Return the card ids for the given item ids."""

    @abstractmethod
    def get_note_ids(self, items: Sequence[ItemId]) -> Sequence[NoteId]:
        """Return the note ids for the given item ids."""

    # Toggle

    @abstractmethod
    def toggle_state(self) -> ItemState:
        """Return an instance of the other state."""

    @abstractmethod
    def get_new_items(self, old_items: Sequence[ItemId]) -> ItemList:
        """Given a list of ids from the other state, return the corresponding ids for this state."""


class CardState(ItemState):
    GEOMETRY_KEY_PREFIX = "editor"
    SORT_COLUMN_KEY = BrowserConfig.CARDS_SORT_COLUMN_KEY
    SORT_BACKWARDS_KEY = BrowserConfig.CARDS_SORT_BACKWARDS_KEY

    def __init__(self, col: Collection) -> None:
        super().__init__(col)
        self._active_columns = self.col.load_browser_card_columns()

    @property
    def active_columns(self) -> list[str]:
        return self._active_columns

    def toggle_active_column(self, column: str) -> None:
        if column in self._active_columns:
            self._active_columns.remove(column)
        else:
            self._active_columns.append(column)
        self.col.set_browser_card_columns(self._active_columns)

    def get_card(self, item: ItemId) -> Card:
        return self.col.get_card(CardId(item))

    def get_note(self, item: ItemId) -> Note:
        return self.get_card(item).note()

    def find_items(
        self, search: str, order: bool | str | Column, reverse: bool
    ) -> Sequence[ItemId]:
        sorted_items = self._find_browser_sorted_items(search, order, reverse)
        if sorted_items is not None:
            return sorted_items
        return self._find_items_with_locale(
            search, order, reverse, anki.lang.current_lang, ""
        )

    def get_item_from_card_id(self, card: CardId) -> ItemId:
        return card

    def get_card_ids(self, items: Sequence[ItemId]) -> Sequence[CardId]:
        return cast(Sequence[CardId], items)

    def get_note_ids(self, items: Sequence[ItemId]) -> Sequence[NoteId]:
        return super().note_ids_from_card_ids(items)

    def toggle_state(self) -> NoteState:
        return NoteState(self.col)

    def get_new_items(self, old_items: Sequence[ItemId]) -> Sequence[CardId]:
        return super().card_ids_from_note_ids(old_items)


class NoteState(ItemState):
    GEOMETRY_KEY_PREFIX = "editorNotesMode"
    SORT_COLUMN_KEY = BrowserConfig.NOTES_SORT_COLUMN_KEY
    SORT_BACKWARDS_KEY = BrowserConfig.NOTES_SORT_BACKWARDS_KEY

    def __init__(self, col: Collection) -> None:
        super().__init__(col)
        self._active_columns = self.col.load_browser_note_columns()

    @property
    def active_columns(self) -> list[str]:
        return self._active_columns

    def toggle_active_column(self, column: str) -> None:
        if column in self._active_columns:
            self._active_columns.remove(column)
        else:
            self._active_columns.append(column)
        self.col.set_browser_note_columns(self._active_columns)

    def get_card(self, item: ItemId) -> Card:
        if cards := self.get_note(item).cards():
            return cards[0]
        raise NotFoundError("card not found", None, None, None)

    def get_note(self, item: ItemId) -> Note:
        return self.col.get_note(NoteId(item))

    def find_items(
        self, search: str, order: bool | str | Column, reverse: bool
    ) -> Sequence[ItemId]:
        sorted_items = self._find_browser_sorted_items(search, order, reverse)
        if sorted_items is not None:
            return sorted_items
        return self._find_items_with_locale(
            search, order, reverse, anki.lang.current_lang, ""
        )

    def get_item_from_card_id(self, card: CardId) -> ItemId:
        return self.col.get_card(card).note().id

    def get_card_ids(self, items: Sequence[ItemId]) -> Sequence[CardId]:
        return super().card_ids_from_note_ids(items)

    def get_note_ids(self, items: Sequence[ItemId]) -> Sequence[NoteId]:
        return cast(Sequence[NoteId], items)

    def toggle_state(self) -> CardState:
        return CardState(self.col)

    def get_new_items(self, old_items: Sequence[ItemId]) -> Sequence[NoteId]:
        return super().note_ids_from_card_ids(old_items)
