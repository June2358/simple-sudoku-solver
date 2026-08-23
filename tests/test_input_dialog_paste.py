import json

import pygame
import pytest
from sample_puzzles import UNIQUE_GRID

import sudoku.input_dialog as input_dialog_module
from sudoku.board import Puzzle, validate_grid
from sudoku.input_dialog import SudokuInputDialog


@pytest.fixture
def dialog() -> SudokuInputDialog:
    pygame.init()
    instance = SudokuInputDialog()
    yield instance
    pygame.quit()


def test_ctrl_v_then_start_returns_the_pasted_puzzle(
    dialog: SudokuInputDialog, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        input_dialog_module, "paste_text", lambda: json.dumps(UNIQUE_GRID)
    )
    event = pygame.event.Event(
        pygame.KEYDOWN,
        key=pygame.K_v,
        mod=pygame.KMOD_CTRL,
    )

    assert dialog._handle_keydown(event) is None
    result = dialog._handle_start()

    assert isinstance(result, Puzzle)
    assert result.grid == tuple(tuple(row) for row in UNIQUE_GRID)


def test_invalid_paste_preserves_the_existing_board(
    dialog: SudokuInputDialog, monkeypatch: pytest.MonkeyPatch
) -> None:
    dialog._replace_board(UNIQUE_GRID)
    before = validate_grid(dialog.board)
    monkeypatch.setattr(input_dialog_module, "paste_text", lambda: "not JSON")

    dialog._paste_matrix()

    assert validate_grid(dialog.board) == before
    assert dialog.validation_error


def test_conflicting_matrix_can_be_edited_but_not_started(
    dialog: SudokuInputDialog, monkeypatch: pytest.MonkeyPatch
) -> None:
    conflicting = [row[:] for row in UNIQUE_GRID]
    conflicting[0][1] = 5
    monkeypatch.setattr(
        input_dialog_module, "paste_text", lambda: json.dumps(conflicting)
    )

    dialog._paste_matrix()

    assert validate_grid(dialog.board)[0][:2] == (5, 5)
    assert dialog._handle_start() is None
    assert dialog.validation_error


def test_run_draws_once_then_waits_for_a_quit_event(
    dialog: SudokuInputDialog,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draw_calls: list[None] = []
    wait_calls: list[tuple[object, ...]] = []

    monkeypatch.setattr(dialog, "draw", lambda: draw_calls.append(None))

    def wait_for_quit(*args: object) -> pygame.event.Event:
        wait_calls.append(args)
        return pygame.event.Event(pygame.QUIT)

    monkeypatch.setattr(pygame.event, "wait", wait_for_quit)
    monkeypatch.setattr(pygame.event, "get", lambda: [])

    assert dialog.run() is None
    assert draw_calls == [None]
    assert wait_calls == [()]
