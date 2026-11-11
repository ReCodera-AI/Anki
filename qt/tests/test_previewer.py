# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import MagicMock

import pytest

import aqt.editor
from aqt.browser.browser import Browser
from aqt.browser.previewer import BrowserPreviewer, MultiCardPreviewer
from aqt.qt import QPoint, QWidget


class BrowserStub(QWidget):
    _show_preview_menu = Browser._show_preview_menu
    _close_preview_menu = Browser._close_preview_menu
    onTogglePreview = Browser.onTogglePreview

    def __init__(self) -> None:
        super().__init__()
        self._preview_menu = None
        self._previewer = None
        self._open_preview = MagicMock()
        self.card = MagicMock()
        self.card.id = 123
        self.card.template.return_value = {"afmt": "{{Back}}"}
        self.editor = MagicMock(spec=aqt.editor.Editor)
        self.editor.note = object()
        self.editor.web = MagicMock()
        self.editor.web.zoomFactor.return_value = 1
        self.editor.web.mapToGlobal.return_value = QPoint(10, 20)
        self.editor.web.evalWithCallback.side_effect = lambda js, cb: cb(
            {"x": 10, "y": 20}
        )


@pytest.fixture
def browser(qapp, monkeypatch):
    from aqt.browser import browser as browser_module

    monkeypatch.setattr(
        browser_module.tr, "card_templates_preview_front_page", lambda: "Front Page"
    )
    monkeypatch.setattr(
        browser_module.tr, "card_templates_preview_back_page", lambda: "Back Page"
    )
    widget = BrowserStub()
    yield widget
    widget._close_preview_menu()
    widget.close()


@pytest.mark.parametrize("index, side", [(0, "question"), (1, "answer")])
def test_preview_menu_opens_the_selected_side(browser, index, side) -> None:
    browser.onTogglePreview()
    menu = browser._preview_menu
    assert menu is not None
    assert [action.text() for action in menu.actions()] == ["Front Page", "Back Page"]
    browser._open_preview.assert_not_called()
    menu.actions()[index].trigger()
    browser._open_preview.assert_called_once_with(side)


def test_dismissing_preview_menu_does_not_open_preview(browser) -> None:
    browser.onTogglePreview()
    menu = browser._preview_menu
    assert menu is not None
    menu.close()
    assert browser._preview_menu is None
    browser._open_preview.assert_not_called()


def test_pressing_preview_again_closes_the_menu(browser) -> None:
    browser.onTogglePreview()
    assert browser._preview_menu is not None
    browser.onTogglePreview()
    assert browser._preview_menu is None
    browser._open_preview.assert_not_called()


def test_second_press_cancels_a_pending_menu(browser) -> None:
    callbacks = []
    browser.editor.web.evalWithCallback.side_effect = lambda js, cb: callbacks.append(
        cb
    )
    browser.onTogglePreview()
    assert browser._preview_menu is not None
    browser.onTogglePreview()
    callbacks[0]({"x": 10, "y": 20})
    assert browser._preview_menu is None
    browser._open_preview.assert_not_called()


def test_selection_change_cancels_a_pending_menu(browser) -> None:
    callbacks = []
    browser.editor.web.evalWithCallback.side_effect = lambda js, cb: callbacks.append(
        cb
    )
    browser.onTogglePreview()
    browser.card.id = 456
    callbacks[0]({"x": 10, "y": 20})
    assert browser._preview_menu is None
    browser._open_preview.assert_not_called()


def test_one_sided_card_opens_preview_without_menu(browser) -> None:
    browser.card.template.return_value = {"afmt": "  "}
    browser.onTogglePreview()
    assert browser._preview_menu is None
    browser._open_preview.assert_called_once_with()


def test_no_selected_card_does_not_offer_side_choices(browser) -> None:
    browser.card = None
    browser.onTogglePreview()
    assert browser._preview_menu is None
    browser._open_preview.assert_called_once_with()


@pytest.mark.parametrize("side", [None, "question", "answer"])
def test_previewer_initializes_the_requested_side(qapp, monkeypatch, side) -> None:
    monkeypatch.setattr(MultiCardPreviewer, "open", lambda self: None)
    previewer = BrowserPreviewer(None, MagicMock(), lambda: None)
    previewer.open(side)
    assert previewer._initial_state == (side or "question")
    assert previewer._explicit_side_selection is (side is not None)
