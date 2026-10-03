"""Uji tema demo (.streamlit/config.toml): slot warna status ada dan kontras teksnya lolos WCAG AA."""

from pathlib import Path

import pytest
import tomllib

from presentation import (
    FAILURE_COLOR,
    FALLBACK_STATUS_COLOR,
    NOT_FOUND_STYLE,
    STATUS_STYLES,
)

THEME = tomllib.loads((Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
STATUS_COLORS = sorted({s.color for s in STATUS_STYLES.values()} | {NOT_FOUND_STYLE.color, FALLBACK_STATUS_COLOR, FAILURE_COLOR})
AA_NORMAL_TEXT = 4.5


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_contrast_formula_matches_known_values() -> None:
    assert contrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)  # tepat di bawah AA


@pytest.mark.parametrize("color", STATUS_COLORS)
def test_every_status_color_has_theme_slots_and_passes_aa(color: str) -> None:
    """Setiap nama warna status di presentation.py punya slot di config.toml (satu-satunya tempat kode heks)."""
    text = THEME[f"{color}TextColor"]
    assert THEME[f"{color}Color"] == text, "warna dan warna teks status sama"
    for name, background in (("halaman", THEME["backgroundColor"]), ("sekunder", THEME["secondaryBackgroundColor"]),
                             ("latar sendiri", THEME[f"{color}BackgroundColor"])):
        assert contrast(text, background) >= AA_NORMAL_TEXT, f"{color} pada latar {name}: {contrast(text, background):.2f}"


def test_status_colors_are_distinct_hex_values_and_violet_is_not_the_accent() -> None:
    values = [THEME[f"{c}Color"].upper() for c in STATUS_COLORS]
    assert len(set(values)) == len(values)
    assert THEME["violetColor"].upper() not in {THEME["primaryColor"].upper(), THEME["linkColor"].upper()}
