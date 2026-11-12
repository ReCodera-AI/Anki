from tests.shared import getEmptyCol

from anki.models import NotetypeId
from aqt.browser.table.state import CardState, NoteState


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
