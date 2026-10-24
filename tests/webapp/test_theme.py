"""Uji tema demo: slot warna status ada, kontras teks lolos WCAG AA, dan palet tanpa hijau."""

import re
import tomllib
from pathlib import Path

import pytest

from webapp.presentation import (
    FAILURE_COLOR,
    FALLBACK_STATUS_COLOR,
    NOT_FOUND_COLOR,
    STATUS_STYLES,
)

ROOT = Path(__file__).resolve().parents[2]
THEME = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
CSS = (ROOT / "src" / "webapp" / "ui" / "style.css").read_text(encoding="utf-8")
CSS_VARS = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", CSS))
STATUS_COLORS = sorted({s.color for s in STATUS_STYLES.values()} | {NOT_FOUND_COLOR, FALLBACK_STATUS_COLOR, FAILURE_COLOR})
AA_NORMAL_TEXT = 4.5
WHITE = "#FFFFFF"


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
    """Setiap nama warna status punya slot di config.toml (satu-satunya tempat warna status)."""
    text = THEME[f"{color}TextColor"]
    assert THEME[f"{color}Color"] == text, "warna dan warna teks status sama"
    for name, background in (("halaman", THEME["backgroundColor"]), ("sekunder", THEME["secondaryBackgroundColor"]),
                             ("kartu", CSS_VARS["surface"]), ("latar sendiri", THEME[f"{color}BackgroundColor"])):
        assert contrast(text, background) >= AA_NORMAL_TEXT, f"{color} pada latar {name}: {contrast(text, background):.2f}"


@pytest.mark.parametrize("color", sorted({s.color for s in STATUS_STYLES.values()} | {FALLBACK_STATUS_COLOR}))
def test_white_pill_text_on_every_status_color_passes_aa(color: str) -> None:
    assert contrast(WHITE, THEME[f"{color}Color"]) >= AA_NORMAL_TEXT


@pytest.mark.parametrize(("fg", "bg"), [
    ("text-secondary", "surface"), ("text-body", "surface"), ("text-body", "line"), ("warn-text", "warn-bg"),
    ("warn-text-body", "warn-bg"), ("text-secondary", "muted-bg"),
])
def test_supporting_text_colors_pass_aa(fg: str, bg: str) -> None:
    assert contrast(CSS_VARS[fg], CSS_VARS[bg]) >= AA_NORMAL_TEXT


def test_body_and_accent_text_pass_aa_on_page_and_cards() -> None:
    for fg in (THEME["textColor"], THEME["primaryColor"], CSS_VARS["text-secondary"]):
        for bg in (THEME["backgroundColor"], CSS_VARS["surface"]):
            assert contrast(fg, bg) >= AA_NORMAL_TEXT


def test_status_colors_are_distinct_hex_values_and_violet_is_not_the_accent() -> None:
    values = [THEME[f"{c}Color"].upper() for c in STATUS_COLORS]
    assert len(set(values)) == len(values)
    assert THEME["violetColor"].upper() not in {THEME["primaryColor"].upper(), THEME["linkColor"].upper()}


def _is_greenish(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return g > r + 20 and g > b + 20


def test_no_green_anywhere_in_the_palette() -> None:
    """Hijau terkesan "benar" (keputusan pemilik proyek); berkas acuan Tentang memakainya, demo tidak."""
    css_hex = re.findall(r"#[0-9A-Fa-f]{6}\b", CSS)
    theme_hex = [v for v in THEME.values() if isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v)]
    assert not [h for h in css_hex + theme_hex if _is_greenish(h)]


def test_status_hex_values_live_only_in_config_toml() -> None:
    """Warna status tidak disalin ke CSS: CSS memakai var(--status-*) yang diisi dari config.toml."""
    status_hex = {THEME[f"{c}Color"].upper() for c in STATUS_COLORS}
    assert not status_hex & {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", CSS)}
