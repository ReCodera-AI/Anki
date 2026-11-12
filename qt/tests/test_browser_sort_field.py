from anki.models import NotetypeId
from aqt.browser.table.state import (
    CardState,
    NoteState,
    browser_group_sort_locale,
)
from tests.shared import getEmptyCol


def test_browser_group_locale_uses_only_unambiguous_manual_setting():
    assert browser_group_sort_locale("fr", ["en", "sv"]) == "fr"
    assert browser_group_sort_locale("", ["sv", "SV"]) == "sv"
    assert browser_group_sort_locale("", ["en", "sv"]) == ""
    assert browser_group_sort_locale("", ["en", ""]) == ""
    assert browser_group_sort_locale("", []) == ""


def test_browser_global_override_is_explicit_and_deck_setting_wins():
    col = getEmptyCol()
    deck_id = col.decks.add_normal_deck_with_name("Sort Field Scope").id
    col.set_config(f"_deck_{deck_id}_sortField", {"mode": "automatic", "locale": ""})
    col.set_config("_browser_sortFieldMode", "browser")
    state = NoteState(col)
    sort_field = col.get_browser_column("noteFld")
    other_column = col.get_browser_column("noteCrt")
    assert sort_field is not None
    assert other_column is not None

    assert state._find_browser_sorted_items("", other_column, False) is None
    assert state._find_browser_sorted_items("", sort_field, False) == []
    assert (
        state._find_browser_sorted_items('deck:"Sort Field Scope"', sort_field, False)
        is None
    )
    col.close()


def test_browser_global_search_groups_across_decks_and_resolves_locales():
    col = getEmptyCol()
    first_deck = col.decks.add_normal_deck_with_name("Sort Field First").id
    second_deck = col.decks.add_normal_deck_with_name("Sort Field Second").id
    col.set_config(f"_deck_{first_deck}_sortField", {"mode": "manual", "locale": "sv"})
    col.set_config(f"_deck_{second_deck}_sortField", {"mode": "manual", "locale": "en"})
    col.set_config("_browser_sortFieldMode", "browser")

    notetype = col.models.copy(col.models.by_name("Basic"))
    notetype["name"] = "Turkish Sort Field"
    col.models.update_dict(notetype)
    values = [
        "Istanbul güzel bir şehir",
        "İzmir güzel bir şehir",
        "istanbul güzel bir şehir",
        "ışık güzel bir şehir",
    ]
    for index, value in enumerate(values):
        deck_id = first_deck if index % 2 == 0 else second_deck
        note = col.new_note(notetype)
        note["Front"] = value
        note["Back"] = "back"
        col.add_note(note, deck_id)

    state = NoteState(col)
    sort_field = col.get_browser_column("noteFld")
    assert sort_field is not None
    search = 'deck:"Sort Field First" or deck:"Sort Field Second"'
    notetype_id = notetype["id"]

    # Note Type locale wins over conflicting Manual Deck locales.
    col.set_aux_notetype_config(NotetypeId(notetype_id), "sortFieldLocale", "tr")
    localized = state.find_items(search, sort_field, False)
    expected_localized = state._find_items_with_locale(
        search, sort_field, False, "en", "tr", notetype_id
    )
    assert list(localized) == list(expected_localized)

    # Without a Note Type locale, conflicting Deck locales fall back to detection.
    col.set_aux_notetype_config(NotetypeId(notetype_id), "sortFieldLocale", "")
    detected = state.find_items(search, sort_field, False)
    expected_detected = state._find_items_with_locale(
        search, sort_field, False, "en", "", notetype_id
    )
    assert list(detected) == list(expected_detected)

    # A Manual locale from only one contributing Deck is not a group-wide policy.
    col.set_config(
        f"_deck_{second_deck}_sortField", {"mode": "automatic", "locale": "en"}
    )
    partly_manual = state.find_items(search, sort_field, False)
    assert list(partly_manual) == list(expected_detected)
    assert list(state.find_items(search, sort_field, True)) == list(
        reversed(partly_manual)
    )
    col.close()


def test_browser_mode_groups_by_notetype_and_reverses_complete_result():
    col = getEmptyCol()
    deck_id = col.decks.add_normal_deck_with_name("Sort Field Test").id
    col.decks.select(deck_id)
    col.set_config(f"_deck_{deck_id}_sortField", {"mode": "browser", "locale": ""})

    alpha = col.models.copy(col.models.by_name("Basic"))
    alpha["name"] = "Alpha"
    col.models.update_dict(alpha)
    beta = col.models.copy(col.models.by_name("Basic"))
    beta["name"] = "Beta"
    col.models.update_dict(beta)
    omega = col.models.copy(col.models.by_name("Basic"))
    omega["name"] = "Omega"
    col.models.update_dict(omega)
    zulu = col.models.copy(col.models.by_name("Basic"))
    zulu["name"] = "Zulu"
    col.models.update_dict(zulu)

    for notetype, values, locale in (
        (alpha, ["z", "ä"], "en"),
        (beta, ["ت", "ا", "ب"], "ar"),
        (
            omega,
            [
                f"{letter} это обычное русское слово"
                for letter in ["я", "ё", "ж", "е", "а"]
            ],
            "",
        ),
        (zulu, ["я", "ё", "ж", "е", "а"], "ru"),
    ):
        if locale:
            col.set_aux_notetype_config(
                NotetypeId(notetype["id"]), "sortFieldLocale", locale
            )
        for value in values:
            note = col.new_note(notetype)
            note["Front"] = value
            col.add_note(note, deck_id)

    order = col.get_browser_column("noteFld")
    assert order is not None
    state = NoteState(col)
    search = 'deck:"Sort Field Test"'
    ids = state.find_items(search, order, False)
    values = [col.get_note(nid)["Front"] for nid in ids]
    expected = [
        "ä",
        "z",
        "ا",
        "ب",
        "ت",
        "а это обычное русское слово",
        "е это обычное русское слово",
        "ё это обычное русское слово",
        "ж это обычное русское слово",
        "я это обычное русское слово",
        "а",
        "е",
        "ё",
        "ж",
        "я",
    ]
    assert values == expected
    assert state._find_browser_sorted_items("", order, False) is None
    col.set_config("_browser_sortFieldMode", "browser")
    global_ids = state.find_items("", order, False)
    assert [col.get_note(nid)["Front"] for nid in global_ids] == expected
    global_reverse_ids = state.find_items("", order, True)
    assert [col.get_note(nid)["Front"] for nid in global_reverse_ids] == list(
        reversed(expected)
    )
    reverse_ids = state.find_items(search, order, True)
    assert [col.get_note(nid)["Front"] for nid in reverse_ids] == list(
        reversed(expected)
    )
    card_state = CardState(col)
    card_ids = card_state.find_items(search, order, False)
    assert [col.get_card(cid).note()["Front"] for cid in card_ids] == expected
    reverse_card_ids = card_state.find_items(search, order, True)
    assert [col.get_card(cid).note()["Front"] for cid in reverse_card_ids] == list(
        reversed(expected)
    )
    col.close()
