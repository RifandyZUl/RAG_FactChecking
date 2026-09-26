"""
Penyamaran fixture HTML uji (tests/fixtures/) -- alat, BUKAN uji (pytest hanya mengumpulkan test_*.py).

Fixture berasal dari HTML nyata TurnBackHoax dan Liputan6. Agar repositori publik tidak
mendistribusikan ulang isi artikel, tautan sumber hoaks, maupun kontak, fixture disamarkan dengan
aturan GENERIK (tidak ada tabel nilai asli di berkas ini):

  1. Teks isi artikel (seksi artikel TurnBackHoax, badan artikel Liputan6, cuplikan kartu halaman
     daftar, dan atribut alt/title gambar di dalamnya) diganti kata demi kata dengan kata semu
     SEPANJANG kata asli (deterministik per halaman, tetapi BUKAN pemetaan kata-ke-kata tetap). Dipertahankan:
     struktur HTML, tanda baca, tanda kutip, spasi/baris baru, angka, pola huruf besar, dan kata
     penanda yang dipakai kode (label seksi, "Faktanya", "narasi", "[arsip]", "sebagai berikut",
     "lengkapnya", "Hingga", label status). Rasio panjang dan posisi kutipan tetap sama.
  2. Tautan sumber hoaks (domain daftar-blokir scraping.links, mis. media sosial dan arsip) di
     dalam isi artikel diganti jalur fiktif pada domain yang SAMA -- pola domain tetap menguji
     penyaring; akun/postingan asli hilang. Ada/tidaknya query dan fragmen dipertahankan.
  3. Nomor telepon Indonesia (termasuk wa.me dan pemisah en-dash) dan alamat surel di SELURUH
     halaman diganti nilai fiktif (0800-0000-0000 / wa.me/628000000000 / *@contoh.invalid).

Judul, label, tanggal, kategori, navigasi situs, dan tautan rujukan media tidak diubah.

Pemakaian (dari root proyek):
  PYTHONPATH=src python tests/anonymize_fixtures.py <dir_asli> <dir_keluaran>
"""

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString

from scraping.links import blocked_reason

SALT = "fixture-samaran-v1"
KEEP_WORDS = {
    "narasi", "penjelasan", "kesimpulan", "hasil", "periksa", "fakta", "referensi", "faktanya",
    "arsip", "sebagai", "berikut", "lengkapnya", "hingga", "salah", "penipuan", "parodi",
}
CONTENT_SELECTORS = (
    "section.article-origin", "section.article-explanation", "section.article-factcheck",
    "section.article-references", "section.article--main > figure",
    "div.article-content-body",
    "p.text-dark-grey",  # cuplikan kartu artikel di halaman daftar
)
CONSONANTS = "bcdfghjklmnprstw"
VOWELS = "aeiou"
# URL berskema, www., ATAU domain polos berakhiran TLD umum (mis. "tirto.id", "x.com/akun"): domain
# polos tidak boleh ikut disamarkan kata demi kata, karena hasilnya bisa menjadi domain nyata lain.
URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s\"'<>]+"
    r"|(?<![\w@.-])(?:[a-z0-9-]+\.)+(?:com|id|net|org|co|io|me|ly|info|site|online)\b(?:/[^\s\"'<>]*)?",
    re.IGNORECASE)
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)  # huruf saja; angka dan tanda baca tetap
DASH = r"[ \-–—]?"  # tanpa titik: angka desimal (mis. 0.8333 di CSS/JS) tidak boleh cocok
PHONE_RE = re.compile(r"(?<![\w./=])(?:\+62|62|0)" + DASH + r"8\d{1,2}(?:" + DASH + r"\d{2,5}){2,4}(?![\w])")
WA_RE = re.compile(r"(wa\.me/|phone=)\+?\d{8,15}", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@(?![\d]x\.)([\w-]+\.)+(?:id|com|org|net|co)\b", re.IGNORECASE)
# Token yang dilindungi dari penyamaran kata: surel (didahulukan) lalu URL/domain.
TOKEN_RE = re.compile(f"(?P<email>{EMAIL_RE.pattern})|(?P<url>{URL_RE.pattern})", re.IGNORECASE)


def pseudo_word(word: str, occurrence: int) -> str:
    """
    Kata semu sepanjang `word`, dengan pola huruf besar yang sama.

    Bergantung pada kata DAN urutan kemunculannya (`occurrence`) di halaman: deterministik untuk
    masukan yang sama, tetapi kata yang sama TIDAK selalu mendapat pengganti yang sama -- pemetaan
    kata-ke-kata yang tetap adalah sandi substitusi yang dapat dipecahkan lewat analisis frekuensi.
    """
    if word.lower() in KEEP_WORDS:
        return word
    digest = hashlib.sha256(f"{SALT}|{occurrence}|{word.lower()}".encode()).digest()
    letters = []
    for i in range(len(word)):
        pool = CONSONANTS if i % 2 == 0 else VOWELS
        letters.append(pool[digest[i % len(digest)] % len(pool)])
    out = "".join(letters)
    if out in KEEP_WORDS:  # jangan sampai kebetulan menjadi kata penanda
        out = out[::-1]
    if word.isupper() and len(word) > 1:
        return out.upper()
    if word[0].isupper():
        return out[0].upper() + out[1:]
    return out


def fake_url(url: str, mapping: dict[str, str]) -> str:
    """Ganti tautan sumber hoaks dengan jalur fiktif pada domain yang sama (konsisten per halaman)."""
    if url not in mapping:
        parts = urlsplit(url)
        n = len(mapping) + 1
        new = f"{parts.scheme or 'https'}://{parts.netloc}/contoh-fiktif-{n}"
        if parts.query:
            new += "?ref=contoh"
        if parts.fragment:
            new += "#contoh"
        mapping[url] = new
    return mapping[url]


def is_hoax_link(url: str) -> bool:
    candidate = url if "://" in url else "https://" + url
    try:
        return blocked_reason(candidate) is not None
    except ValueError:  # bukan URL sah (mis. host berkurung siku); ditangani sebagai teks
        return False


def _next_pseudo(word: str, counter: list[int]) -> str:
    counter[0] += 1
    return pseudo_word(word, counter[0])


def scramble_text(text: str, url_map: dict[str, str], counter: list[int]) -> str:
    """Samarkan kata; URL di dalam teks: sumber hoaks -> fiktif, selain itu dibiarkan."""
    out, last = [], 0
    for m in TOKEN_RE.finditer(text):
        token = m.group(0)
        if m.group("email"):  # surel -> nilai fiktif, dan TIDAK ikut disamarkan kata demi kata
            replacement = "redaksi@contoh.invalid"
        elif "[" in token or "(" in token:  # tautan yang ditulis tersamar ("www[dot]..."): teks biasa
            continue
        else:
            bare_domain = "://" not in token and "/" not in token  # domain polos tanpa jalur
            replacement = fake_url(token, url_map) if is_hoax_link(token) and not bare_domain else token
        out.append(WORD_RE.sub(lambda w: _next_pseudo(w.group(0), counter), text[last:m.start()]))
        out.append(replacement)
        last = m.end()
    out.append(WORD_RE.sub(lambda w: _next_pseudo(w.group(0), counter), text[last:]))
    return "".join(out)


def replace_contacts(html: str) -> str:
    html = WA_RE.sub(lambda m: m.group(1) + "628000000000", html)
    html = PHONE_RE.sub("0800-0000-0000", html)
    return EMAIL_RE.sub("redaksi@contoh.invalid", html)


def anonymize(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    url_map: dict[str, str] = {}
    counter = [0]  # urutan kemunculan kata di halaman
    containers = []
    for sel in CONTENT_SELECTORS:
        for el in soup.select(sel):
            if not any(el in c.descendants for c in containers):
                containers.append(el)
    for container in containers:
        for node in list(container.descendants):
            if isinstance(node, NavigableString) and not isinstance(node, Comment):
                if node.parent is not None and node.parent.name in ("script", "style"):
                    continue
                new = scramble_text(str(node), url_map, counter)
                if new != str(node):
                    node.replace_with(NavigableString(new))
            elif getattr(node, "attrs", None):
                for attr in ("alt", "title"):
                    if node.get(attr):
                        node[attr] = scramble_text(node[attr], url_map, counter)
                for attr in ("href", "src", "data-src"):
                    val = node.get(attr)
                    if val and is_hoax_link(val):
                        node[attr] = fake_url(val, url_map)
    return replace_contacts(str(soup))


def main() -> int:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*.html")):
        (dst / path.name).write_text(anonymize(path.read_text(encoding="utf-8")), encoding="utf-8")
        print("disamarkan:", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
