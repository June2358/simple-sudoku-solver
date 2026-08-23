import ast
from pathlib import Path

import pygame
import pytest

from sudoku import ui_style


def _glyph_signature(
    font: pygame.font.Font, character: str
) -> tuple[tuple[int, int], bytes]:
    surface = font.render(character, True, "white")
    return surface.get_size(), pygame.image.tobytes(surface, "RGBA")


def _source_characters() -> tuple[str, ...]:
    package = Path(ui_style.__file__).parent
    texts: list[str] = []
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        texts.extend(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )
    return tuple(
        sorted(
            {
                character
                for text in texts
                for character in text
                if not character.isspace() and character != "\ufeff"
            }
        )
    )


def test_bundled_font_renders_every_source_character() -> None:
    pygame.font.init()
    assert ui_style._FONT_PATH.is_file()

    font = pygame.font.Font(str(ui_style._FONT_PATH), 20)
    missing_glyph = _glyph_signature(font, "\U0010ffff")
    missing = [
        character
        for character in _source_characters()
        if _glyph_signature(font, character) == missing_glyph
    ]

    assert missing == []


def test_get_fonts_uses_bundled_korean_glyphs() -> None:
    fonts = ui_style.get_fonts()

    for font in (
        fonts.number,
        fonts.body,
        fonts.candidate,
        fonts.heading,
        fonts.title,
    ):
        assert _glyph_signature(font, "한") != _glyph_signature(font, "\U0010ffff")


def test_get_fonts_survives_a_missing_asset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(ui_style, "_FONT_PATH", tmp_path / "missing.ttf")

    fonts = ui_style.get_fonts()

    assert fonts.body.get_height() > 0
    assert fonts.title.get_bold()
