"""
Penyiapan data tampilan demo: hasil layanan (`service.CheckOutcome`) -> `ResultView` siap render.

Modul ini TIDAK mengimpor Streamlit dan TIDAK memanggil API, sehingga bisa diuji tanpa antarmuka
(`tests/test_presentation.py`). Seluruh salinan antarmuka dan pemetaan status -> warna ada di sini.

Warna di sini adalah NAMA warna tema ("red", "orange", ...), bukan kode heks; nilainya ditetapkan sekali
di `.streamlit/config.toml` dan diteruskan ke CSS oleh `ui/components.py`.

Tidak ada logika retrieval atau keputusan: status dari LABEL metadata artikel, Kesimpulan dari indeks apa
adanya, rujukan dari metadata `references` yang disaring ulang (Aturan Wajib #1 dan #3); `claim_sources`
dan `references_filtered` tidak pernah sampai ke sini (tidak ada di metadata indeks).
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from urllib.parse import urlparse

import settings
from generator import MAX_FORMAT_RETRIES, Answer
from resources import parse_metadata_date
from scraping.links import blocked_reason
from service import CheckError, CheckOutcome

logger = logging.getLogger("presentation")

# --------------------------------------------------------------------------
# Salinan antarmuka (dari berkas acuan docs/desain_tampilan/; teks baru ditandai "BARU")
# --------------------------------------------------------------------------

APP_NAME = "Cek Pesan Hoaks"
HOME_TITLE = "Dapat pesan mencurigakan? Cek dulu sebelum dibagikan."
HOME_SUBTITLE = "Tempel pesannya. Kami carikan apakah klaim yang sama pernah diperiksa oleh TurnBackHoax.id."
INPUT_LABEL = "Pesan yang Anda terima"
INPUT_PLACEHOLDER = "Tempel teks pesan WhatsApp, unggahan media sosial, atau judul berita di sini"
INPUT_PRIVACY_HINT = "Tanpa nomor telepon atau data pribadi"
SUBMIT_LABEL = "Periksa pesan"
EXAMPLES_HEADING = "Belum punya pesan? Coba contoh:"
HOW_IT_WORKS_HEADING = "Cara kerjanya"
HOW_IT_WORKS_STEPS = ("Tempel pesan", "Dicari di arsip cek fakta", "Baca hasil dan cocokkan sendiri")
ABOUT_LINK_LABEL = "Tentang sistem ini dan seberapa akurat hasilnya"
CHECK_ANOTHER_LABEL = "Periksa pesan lain"
BACK_LABEL = "Kembali"

# Contoh klaim siap klik: USULAN, menunggu persetujuan pemilik proyek (laporan Tahap 1). Diambil dari
# judul artikel publik di articles.json, bukan artikel sasaran set eksternal/set uji v1, tanpa nomor
# telepon atau nama orang biasa.
EXAMPLE_CLAIMS: tuple[str, ...] = (
    "Link pemutihan pajak motor dan mobil gratis seluruh Indonesia",  # dari 31781 (PENIPUAN)
    "Sabah dan Sarawak lepas dari Malaysia, resmi jadi bagian Indonesia",  # dari 35133 (SALAH)
    "Tautan pendaftaran bantuan bibit ikan lele",  # dari 36119 dengan objek pembeda diganti -> belum ditemukan
)

# Masukan
EMPTY_INPUT_MESSAGE = "Tulis atau tempel pesan yang ingin dicek terlebih dahulu."
TOO_LONG_MESSAGE = (
    "Pesan Anda {length} karakter, melebihi batas {limit} karakter, jadi belum diperiksa dan tidak ada "
    "bagian yang dipotong. Salin bagian yang memuat klaim utamanya saja, lalu periksa lagi."
)
LONG_CLAIM_WARNING = (
    "Pesan Anda cukup panjang. Pesan yang terlalu panjang menurunkan ketepatan pencarian, karena bagian di "
    "luar klaim ikut terbaca dan klaimnya bisa terlewat. Hasil paling tepat bila Anda menyalin bagian inti "
    "klaimnya saja."
)
LONG_CLAIM_CONFIRM = "Tekan “{button}” sekali lagi untuk tetap memeriksa pesan ini apa adanya."

# Proses (BARU: berkas acuan tidak memuat keadaan ini)
PROGRESS_CHECKING = "Memeriksa pesan Anda… Biasanya selesai dalam setengah menit, kadang lebih lama saat layanan AI sedang sibuk."
PROGRESS_PREPARING = "Menyiapkan sistem untuk pemeriksaan pertama… Ini bisa memakan sekitar satu menit."
PROGRESS_QUEUED = "Ada pemeriksaan lain yang sedang berjalan. Pesan Anda menunggu giliran…"
WARMUP_NOTE = "Sistem sedang disiapkan. Pemeriksaan pertama bisa sedikit lebih lama."

# Hasil ditemukan
SOURCE_SUFFIX = "menurut TurnBackHoax.id"
SHOW_ALL_LABEL = "Tampilkan semua"
SHOW_LESS_LABEL = "Tampilkan lebih sedikit"
MATCH_CHECK_HEADING = "Pastikan klaimnya benar-benar sama"
MATCH_CHECK_INTRO = "Hasil ini berlaku untuk pesan Anda hanya jika isinya sama. Bandingkan dulu:"
MATCH_CHECK_YOURS = "PESAN ANDA"
MATCH_CHECK_CHECKED = "YANG DIPERIKSA"
MATCH_CHECK_QUESTIONS = (
    "Lembaga atau tokoh yang disebut sama?",
    "Nama program, tawaran, atau nominalnya sama?",
    "Tautan atau nomor kontaknya mirip?",
)
MATCH_CHECK_CLOSING = "Jika salah satu berbeda, bisa jadi ini pesan lain dengan pola serupa. Anggap belum terverifikasi."
ARTICLE_HEADING = "ARTIKEL CEK FAKTA"
ARTICLE_SOURCE = "TurnBackHoax.id"
READ_ARTICLE_LABEL = "Baca artikel lengkap"
EXPLANATION_LABEL = "Penjelasan lengkap"
REFERENCES_LABEL = "Rujukan resmi ({n})"
PROVENANCE_NOTE = (
    "Label, kesimpulan, dan tautan diambil langsung dari artikel cek fakta, bukan dikarang AI. "
    "AI hanya membantu mencocokkan pesan Anda dengan artikel."
)
PROVENANCE_LINK_LABEL = "Seberapa akurat?"

# Hasil belum ditemukan
NOT_FOUND_PILL = "BELUM DITEMUKAN"
NOT_FOUND_TITLE = "Pesan ini belum ada di arsip cek fakta kami."
NOT_FOUND_CALLOUT = "Ini bukan berarti pesannya benar."
NOT_FOUND_BODY = (
    "Bisa jadi pesannya baru beredar dan belum sempat diperiksa, atau diperiksa situs lain. Arsip kami hanya "
    "berisi artikel TurnBackHoax.id dan tidak mencakup semua hoaks."
)
NEXT_STEPS_HEADING = "Yang bisa Anda lakukan sekarang"
NEXT_STEPS = (
    "Jangan klik tautannya dan jangan kirim data pribadi, kode OTP, atau uang.",
    "Cek langsung ke situs atau akun resmi lembaga yang disebut dalam pesan.",
    "Cari kata kuncinya di situs cek fakta:",
)
FACT_CHECK_SITES = (("TurnBackHoax.id", settings.TURNBACKHOAX_URL),
                    ("Cek Fakta Liputan6", settings.LIPUTAN6_CEK_FAKTA_URL))
SCAM_SIGNS_HEADING = "Tanda umum pesan penipuan"
SCAM_SIGNS = (
    "Meminta data pribadi atau kode OTP",
    "Tautan bukan dari situs resmi lembaga",
    "Mendesak: “kuota terbatas”, “hari ini saja”",
    "Hadiah atau bantuan yang terlalu mudah",
)

# Tentang
ABOUT_TITLE = "Tentang sistem ini"
ABOUT_DOES_HEADING = "YANG DILAKUKAN"
ABOUT_DOES = "Mencari artikel cek fakta yang pernah memeriksa klaim yang sama dengan pesan Anda."
ABOUT_DOES_NOT_HEADING = "YANG TIDAK DILAKUKAN"
ABOUT_DOES_NOT = "Menilai sendiri benar-salahnya klaim yang belum pernah diperiksa."
ABOUT_STEPS = (
    "Pesan Anda dibandingkan dengan {articles} artikel TurnBackHoax.id untuk mencari tiga yang paling mirip.",
    "Model AI membaca ketiganya dan memutuskan apakah ada yang memeriksa klaim yang sama.",
    "Label, kesimpulan, dan tautan ditampilkan apa adanya dari artikel. AI tidak menulis putusan atau tautan sendiri.",
)
RELIABILITY_HEADING = "Seberapa bisa diandalkan?"
RELIABILITY_INTRO = "Diuji dengan {total} klaim hoaks nyata dari Cek Fakta Liputan6. Batas lulus ditetapkan sebelum pengujian."
RELIABILITY_FOUND = "klaim yang ada di arsip ditemukan dengan benar ({pct})."
RELIABILITY_FALSE = (
    "klaim yang tidak ada di arsip keliru dicocokkan dengan artikel lain ({pct}), terutama penipuan berpola "
    "sama."
)
RELIABILITY_ADVICE = "Karena itu, selalu cocokkan sendiri lembaga, program, dan tautan di hasil dengan pesan Anda."
RELIABILITY_FOOTNOTE = (
    "Angka berlaku untuk arsip {articles} artikel. Rincian, interval kepercayaan, dan keterbatasan ada di "
    "README proyek."
)
LIMITS_HEADING = "Batasan yang perlu Anda tahu"
LIMITS = (
    "Hanya mencari di artikel TurnBackHoax.id, jadi tidak semua hoaks tercakup.",
    "Hoaks yang baru beredar beberapa hari mungkin belum ada di arsip.",
    "Hanya membaca teks. Gambar, video, dan suara tidak bisa diperiksa.",
    "Belum diuji pada berita yang benar. Untuk pengumuman resmi, tetap cek ke sumber resminya.",
    # BARU (privasi; CLAUDE.md "Privasi data"): konten tier gratis dipakai Google untuk perbaikan produk.
    ("Pesan yang Anda periksa dikirim ke layanan AI Google (Gemini, tier gratis), yang dapat memakainya "
     "untuk meningkatkan produknya. Jangan menempel data pribadi."),
)
DATA_SOURCE_HEADING = "Sumber data"
DATA_SOURCE_BODY = (
    "Artikel cek fakta TurnBackHoax.id (Mafindo), diperbarui berkala. Artikel terbaru: {date}. Ini proyek "
    "portofolio pribadi, bukan layanan resmi Mafindo."
)
SOURCE_CODE_LABEL = "Kode dan laporan evaluasi di GitHub"
FOOTER_ARCHIVE = "Arsip: {articles} artikel TurnBackHoax.id · artikel terbaru: {date}"
UNKNOWN_VALUE = "(tidak terbaca)"

DIAGNOSTICS_LABEL = "Detail untuk penguji"

def about_steps(current_articles: int | None) -> tuple[str, ...]:
    """Langkah "Cara kerjanya" di halaman Tentang: jumlah artikel = indeks yang SEDANG dipakai (dinamis)."""
    count = UNKNOWN_VALUE if current_articles is None else format_count(current_articles)
    return (ABOUT_STEPS[0].format(articles=count), *ABOUT_STEPS[1:])


def reliability_footnote(evaluated_articles: int) -> str:
    """Catatan angka evaluasi: ukuran indeks SAAT EVALUASI (tetap, dari sumber evaluasi), bukan indeks kini."""
    return RELIABILITY_FOOTNOTE.format(articles=format_count(evaluated_articles))


def footer_archive(current_articles: int | None, latest: date | None) -> str:
    """Kaki beranda: jumlah artikel dan tanggal artikel TERBARU di indeks yang sedang dipakai."""
    count = UNKNOWN_VALUE if current_articles is None else format_count(current_articles)
    return FOOTER_ARCHIVE.format(articles=count, date=format_date(latest))


_MONTHS = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September",
           "Oktober", "November", "Desember")


def format_count(value: int) -> str:
    """Bilangan bulat dengan pemisah ribuan titik (gaya Indonesia)."""
    return f"{value:,}".replace(",", ".")


def format_date(value: date | None) -> str:
    """Tanggal gaya Indonesia ("12 Maret 2026")."""
    return UNKNOWN_VALUE if value is None else f"{value.day} {_MONTHS[value.month - 1]} {value.year}"


def format_metadata_date(value: str) -> str:
    """Tanggal metadata artikel (dd/mm/yyyy) -> "12 Maret 2026"; teks asli bila formatnya lain."""
    parsed = parse_metadata_date(value)
    return value.strip() if parsed is None else format_date(parsed)


def format_percent(rate: float) -> str:
    return f"{round(rate * 100)}%"


def format_wait(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} detik"
    return f"{-(-seconds // 60)} menit"


# --------------------------------------------------------------------------
# Status per label: judul satu kalimat + saran tetap (ditulis manual, bukan oleh LLM)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StatusStyle:
    """Tampilan satu status: nama warna tema, judul satu kalimat, dan satu kalimat saran tetap."""

    color: str
    headline: str
    advice: str


# Intensitas warna menurun: PENIPUAN (merugikan langsung) > SALAH > PARODI. BELUM TERBUKTI di luar skala itu.
STATUS_STYLES: dict[str, StatusStyle] = {
    "PENIPUAN": StatusStyle(
        color="red",
        headline="Klaim serupa pernah diperiksa dan dinyatakan penipuan.",
        advice="Jangan klik tautannya, jangan isi formulirnya, dan jangan teruskan pesannya.",
    ),
    "SALAH": StatusStyle(
        color="orange",
        headline="Klaim serupa pernah diperiksa dan dinyatakan salah.",
        advice="Jangan teruskan pesan ini sebagai kabar yang benar.",
    ),
    "PARODI": StatusStyle(
        color="yellow",
        headline="Klaim serupa pernah diperiksa dan dinyatakan konten humor.",
        advice="Ini parodi, satire, atau komedi, bukan berita sungguhan, jadi jangan teruskan sebagai kabar yang benar.",
    ),
    # Kalimat saran = kalimat persis yang ditetapkan pemilik proyek 2026-10-03 (tanpa saran medis atau
    # kalimat lain); ungu berada di luar skala bahaya dan berbeda dari abu-abu "belum ditemukan".
    "BELUM TERBUKTI": StatusStyle(
        color="violet",
        headline="Klaim serupa pernah diperiksa dan belum terbukti.",
        advice=(
            "Klaim ini sudah diperiksa TurnBackHoax.id dan belum ada bukti yang mendukungnya, "
            "sehingga belum dapat dianggap benar."
        ),
    ),
}

# Alias TAMPILAN saja (label tersimpan tidak diubah): SATIRE, SATIR (2026-09-28), KOMEDI (2026-10-02)
# = satu kategori dengan PARODI. Pil tetap menampilkan label aslinya.
STATUS_ALIASES: dict[str, str] = {"SATIRE": "PARODI", "SATIR": "PARODI", "KOMEDI": "PARODI"}

# Label di luar yang dikenal: NETRAL (keputusan 2026-10-02). Artinya tidak ditafsirkan; label asli
# dikutip apa adanya, dan setiap kemunculan dicatat ke log agar ditinjau manusia (Aturan Wajib #7).
FALLBACK_STATUS_COLOR = "gray"
FALLBACK_HEADLINE = "Klaim serupa pernah diperiksa dan diberi label “{label}”."
FALLBACK_ADVICE = "Aplikasi ini belum mengenali label tersebut. Baca artikelnya untuk mengetahui hasil pemeriksaannya."
# Label kosong atau penanda parser "TIDAK DIKETAHUI" bukan label dari TurnBackHoax: tidak dikutip.
UNREADABLE_LABELS = frozenset({"", "TIDAK DIKETAHUI"})
UNREADABLE_PILL = "SUDAH DIPERIKSA"
UNREADABLE_HEADLINE = "Klaim serupa pernah diperiksa dan labelnya tidak terbaca."
UNREADABLE_ADVICE = "Baca artikelnya untuk mengetahui hasil pemeriksaannya."

NOT_FOUND_COLOR = "gray"  # pil "belum ditemukan" memakai gaya netral berkas acuan (lihat style.css)
FAILURE_COLOR = "gray"


def status_style_key(label: str) -> str:
    """Kunci STATUS_STYLES untuk label metadata (huruf besar, alias tampilan diterapkan)."""
    key = label.strip().upper()
    return STATUS_ALIASES.get(key, key)


def status_for_label(label: str, article_id: str = "") -> tuple[str, StatusStyle]:
    """(teks pil, gaya) untuk label metadata; label tak dikenal -> netral dan dicatat ke log."""
    clean = label.strip()
    style = STATUS_STYLES.get(status_style_key(clean))
    if style is not None:
        return clean.upper(), style
    logger.warning("label status tidak dikenal %r pada artikel %s: ditampilkan netral, perlu ditinjau",
                   clean, article_id)
    if clean.upper() in UNREADABLE_LABELS:
        return UNREADABLE_PILL, StatusStyle(FALLBACK_STATUS_COLOR, UNREADABLE_HEADLINE, UNREADABLE_ADVICE)
    return clean.upper(), StatusStyle(FALLBACK_STATUS_COLOR, FALLBACK_HEADLINE.format(label=clean), FALLBACK_ADVICE)


# --------------------------------------------------------------------------
# Kegagalan: jenis yang dibedakan untuk pengguna (bahasa awam, tanpa jejak teknis)
# --------------------------------------------------------------------------


class FailureKind(Enum):
    QUOTA = "kuota_habis"
    TIMEOUT = "timeout"
    UNAVAILABLE = "layanan_tidak_tersedia"
    PARSE = "format_tidak_dikenali"
    CONFIG = "konfigurasi"
    NO_INDEX = "basis_data_tidak_ada"
    RATE_LIMITED = "batas_laju"
    BUSY = "antrean_penuh"
    OTHER = "lainnya"


# Setiap pesan: apa yang terjadi + apa yang bisa dilakukan pengguna. "{wait}" diisi waktu tunggu.
FAILURE_MESSAGES: dict[FailureKind, tuple[str, str]] = {
    FailureKind.QUOTA: (
        "Batas pemakaian harian tercapai",
        ("Layanan pemeriksa sudah mencapai batas pemakaian untuk hari ini, jadi pesan Anda belum diperiksa. "
         "Batas ini dipulihkan sekali sehari; silakan coba lagi beberapa jam lagi."),
    ),
    FailureKind.RATE_LIMITED: (
        "Tunggu sebentar sebelum memeriksa lagi",
        ("Pemeriksaan dibatasi agar layanan bisa dipakai banyak orang. Pesan Anda belum diperiksa. Silakan "
         "coba lagi dalam {wait}."),
    ),
    FailureKind.BUSY: (
        "Sedang banyak yang memeriksa",
        ("Pesan Anda sudah menunggu cukup lama tetapi belum mendapat giliran, jadi belum diperiksa. Silakan "
         "coba lagi dalam satu atau dua menit."),
    ),
    FailureKind.TIMEOUT: (
        "Pemeriksaan memakan waktu terlalu lama",
        ("Layanan pemeriksa tidak menjawab dalam batas waktu, jadi pesan Anda belum diperiksa. Silakan coba "
         "lagi dalam beberapa menit."),
    ),
    FailureKind.UNAVAILABLE: (
        "Layanan pemeriksa sedang tidak tersedia",
        ("Layanan sedang sibuk atau tidak dapat dihubungi, jadi pesan Anda belum diperiksa. Periksa koneksi "
         "internet Anda, lalu coba lagi dalam beberapa menit."),
    ),
    FailureKind.PARSE: (
        "Hasil pemeriksaan tidak dapat dibaca",
        ("Sistem menerima jawaban dalam bentuk yang tidak dikenali, sehingga hasilnya tidak ditampilkan agar "
         "tidak menyesatkan. Silakan coba sekali lagi; bila terulang, coba tulis klaimnya dengan kalimat lain."),
    ),
    FailureKind.CONFIG: (
        "Aplikasi belum siap dipakai",
        ("Kunci akses layanan pemeriksa belum diatur. Pengelola aplikasi perlu mengisi berkas .env sesuai "
         "contoh di .env.example, lalu memuat ulang halaman ini."),
    ),
    FailureKind.NO_INDEX: (
        "Basis data artikel belum tersedia",
        ("Basis data artikel cek fakta belum disiapkan di komputer ini. Pengelola aplikasi perlu "
         "membangunnya lebih dulu (lihat README), lalu memuat ulang halaman ini."),
    ),
    FailureKind.OTHER: (
        "Terjadi kesalahan",
        ("Pemeriksaan tidak dapat diselesaikan karena kesalahan yang tidak terduga. Silakan coba lagi "
         "beberapa saat lagi; bila terus terjadi, beri tahu pengelola aplikasi."),
    ),
}

_SERVICE_FAILURES: dict[CheckError, FailureKind] = {
    CheckError.SESSION_INTERVAL: FailureKind.RATE_LIMITED,
    CheckError.SESSION_HOURLY: FailureKind.RATE_LIMITED,
    CheckError.GLOBAL_HOURLY: FailureKind.RATE_LIMITED,
    CheckError.DAILY_STOP: FailureKind.QUOTA,
    CheckError.BUSY: FailureKind.BUSY,
    CheckError.NO_INDEX: FailureKind.NO_INDEX,
    CheckError.CONFIG: FailureKind.CONFIG,
    CheckError.UNEXPECTED: FailureKind.OTHER,
}

# Format `CallRecord.error` dari GeminiProvider: "<NamaGalat> status=<kode>[ ...]" (src/llm/gemini.py).
# Bila formatnya berubah, galat jatuh ke FailureKind.OTHER: pesan umum, bukan pesan yang keliru.
_CALL_ERROR_PATTERN = re.compile(r"^(?P<name>\w+) status=(?P<status>\S+)")
_UNAVAILABLE_STATUS = {"429", "500", "502", "503", "504"}
_CONNECTION_NAMES = ("Connect", "Network", "RemoteProtocol", "ReadError")


def classify_call_error(error: str) -> FailureKind | None:
    """Petakan `CallRecord.error` ke jenis kegagalan; None bila tidak dikenali."""
    match = _CALL_ERROR_PATTERN.match(error)
    if match is None:
        return None
    name, status = match["name"], match["status"]
    if "Timeout" in name:
        return FailureKind.TIMEOUT
    if status in _UNAVAILABLE_STATUS or any(n in name for n in _CONNECTION_NAMES):
        return FailureKind.UNAVAILABLE
    return None


def classify_failure(ans: Answer) -> FailureKind | None:
    """
    Jenis kegagalan jawaban generator; None bila bukan kegagalan. Urutan: kuota (flag eksplisit) ->
    galat panggilan terakhir yang gagal -> galat parsing (semua percobaan format gagal) -> lainnya.
    """
    if ans.verdict != "gagal":
        return None
    if ans.quota_exhausted:
        return FailureKind.QUOTA
    failed_calls = [c for c in ans.calls if not c.ok]
    if failed_calls:
        return classify_call_error(failed_calls[-1].error) or FailureKind.OTHER
    if ans.parse_failures >= 1 + MAX_FORMAT_RETRIES:
        return FailureKind.PARSE
    return FailureKind.OTHER


def input_problem_message(error: CheckError, text: str) -> str | None:
    """Pesan sebaris untuk masukan yang tidak bisa diperiksa (ditampilkan di beranda); None bila bukan."""
    if error is CheckError.EMPTY:
        return EMPTY_INPUT_MESSAGE
    if error is CheckError.TOO_LONG:
        return TOO_LONG_MESSAGE.format(length=format_count(len(text)), limit=format_count(settings.MAX_INPUT_CHARS))
    return None


# --------------------------------------------------------------------------
# Model tampilan
# --------------------------------------------------------------------------


@dataclass
class CandidateRow:
    article_id: str
    title: str
    label: str
    score: float


@dataclass
class Diagnostics:
    """Untuk penguji saja (panel tersembunyi); boleh berisi istilah teknis."""

    model: str = ""
    timings: dict[str, float] = field(default_factory=dict)
    llm_calls: int = 0
    attempts: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    candidates: list[CandidateRow] = field(default_factory=list)
    llm_reason: str = ""
    llm_paraphrase: str = ""  # parafrase Kesimpulan oleh LLM: TIDAK ditampilkan ke pengguna umum
    error_detail: str = ""  # sudah disamarkan
    failure_kind: str = ""
    parse_failures: int = 0
    invalid_id: bool = False
    llm_urls_removed: int = 0
    query_tokens: int | None = None
    query_token_limit: int | None = None


@dataclass
class ResultView:
    """Semua yang dibutuhkan fungsi render; tidak ada panggilan API di baliknya."""

    kind: str  # "found" | "not_found" | "failed"
    status_color: str = ""
    pill_text: str = ""
    headline: str = ""
    kesimpulan: str = ""  # Kesimpulan TurnBackHoax APA ADANYA (dari indeks)
    advice: str = ""
    message_excerpt: str = ""
    article_title: str = ""
    article_url: str = ""
    article_date: str = ""
    penjelasan: str = ""
    references: list[str] = field(default_factory=list)
    failure_title: str = ""
    failure_body: str = ""
    diagnostics: Diagnostics = field(default_factory=Diagnostics)


def is_safe_url(url: str) -> bool:
    """Hanya http/https dengan host: skema lain (javascript:, data:, file:) tidak pernah ditautkan."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def display_references(references: list[str], article_id: str = "") -> list[str]:
    """
    Saring ULANG rujukan metadata tepat sebelum ditampilkan (Aturan Wajib #1, lapisan kedua).

    Metadata indeks bisa BASI (ingest inkremental hanya membandingkan teks chunk), jadi kebijakan terkini
    `scraping.links.blocked_reason` diterapkan lagi, dan hanya URL http/https yang lolos. Yang terbuang
    dicatat ke log (alasan + id artikel, bukan tautannya), tidak ditampilkan, dan tidak diganti.
    """
    kept: list[str] = []
    for url in references:
        reason = blocked_reason(url) or (None if is_safe_url(url) else "skema URL tidak diizinkan")
        if reason is None:
            kept.append(url)
        else:
            logger.warning("rujukan dari metadata indeks disaring saat tampil (artikel %s): %s",
                           article_id or "?", reason)
    return kept


_TITLE_LABEL_PREFIX = re.compile(r"^\s*\[[^\]]*\]\s*")


def display_title(title: str) -> str:
    """Buang label dalam kurung siku di awal judul ("[SALAH] ..."): status sudah tampil di pil."""
    return _TITLE_LABEL_PREFIX.sub("", title).strip() or title.strip()


def excerpt(text: str, limit: int) -> str:
    """Potongan awal teks pada batas kata, dengan elipsis bila dipotong; spasi dirapikan."""
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    cut = flat[:limit].rsplit(" ", 1)[0] or flat[:limit]
    return cut.rstrip(",.;:") + "…"


def kesimpulan_preview(text: str, limit: int = settings.KESIMPULAN_PREVIEW_CHARS) -> tuple[str, bool]:
    """(pratinjau, dipotong?): dipotong pada akhir kalimat terakhir yang muat, atau batas kata."""
    clean = text.strip()
    if len(clean) <= limit:
        return clean, False
    head = clean[:limit]
    sentence_end = max(head.rfind(". "), head.rfind("? "), head.rfind("! "))
    if sentence_end >= limit // 2:
        return head[: sentence_end + 1], True
    return excerpt(clean, limit), True


def _sum_tokens(values: list[int | None]) -> int | None:
    known = [v for v in values if v is not None]
    return sum(known) if known else None


def build_diagnostics(outcome: CheckOutcome, failure: FailureKind | None) -> Diagnostics:
    """Data panel penguji dari hasil layanan."""
    from chunker import MAX_SEQ_LENGTH

    diag = Diagnostics(model=outcome.model, timings=dict(outcome.timings), error_detail=outcome.error_detail,
                       failure_kind=failure.value if failure else "", query_tokens=outcome.query_tokens,
                       query_token_limit=MAX_SEQ_LENGTH)
    ans = outcome.answer
    if ans is None:
        return diag
    diag.llm_calls = len(ans.calls)
    diag.attempts = sum(c.attempts for c in ans.calls)
    diag.input_tokens = _sum_tokens([c.input_tokens for c in ans.calls])
    diag.output_tokens = _sum_tokens([c.output_tokens for c in ans.calls])
    diag.candidates = [CandidateRow(str(c["article_id"]), str(c["title"]), str(c["label"]), float(c["score"]))
                       for c in ans.candidates]
    diag.llm_reason = ans.alasan
    diag.llm_paraphrase = ans.klarifikasi
    diag.error_detail = diag.error_detail or ans.error
    diag.parse_failures = ans.parse_failures
    diag.invalid_id = ans.invalid_id
    diag.llm_urls_removed = len(ans.llm_urls_found)
    return diag


def failure_view(kind: FailureKind, diagnostics: Diagnostics | None = None, wait_s: int | None = None) -> ResultView:
    """Tampilan kegagalan dalam bahasa awam; detail teknis hanya di panel penguji."""
    title, body = FAILURE_MESSAGES[kind]
    diag = diagnostics or Diagnostics()
    diag.failure_kind = kind.value
    return ResultView(kind="failed", status_color=FAILURE_COLOR, failure_title=title,
                      failure_body=body.format(wait=format_wait(wait_s or 60)), diagnostics=diag)


def build_view(outcome: CheckOutcome) -> ResultView:
    """
    Ubah hasil layanan menjadi `ResultView`. Fungsi murni: tanpa UI dan tanpa API.

    Galat masukan (kosong/terlalu panjang) BUKAN urusan fungsi ini: tampilan menampilkannya sebaris di
    beranda lewat `input_problem_message`.
    """
    if outcome.error is not None:
        kind = _SERVICE_FAILURES[outcome.error]
        return failure_view(kind, build_diagnostics(outcome, kind), outcome.retry_after_s)
    ans = outcome.answer
    if ans is None:  # tidak seharusnya terjadi: layanan selalu mengisi error atau answer
        logger.error("hasil layanan tanpa jawaban dan tanpa galat")
        return failure_view(FailureKind.OTHER)

    failure = classify_failure(ans)
    diag = build_diagnostics(outcome, failure)
    if failure is not None:
        return failure_view(failure, diag)

    if ans.verdict != "ditemukan":
        return ResultView(kind="not_found", status_color=NOT_FOUND_COLOR, pill_text=NOT_FOUND_PILL,
                          headline=NOT_FOUND_TITLE, diagnostics=diag)

    article_id = str(ans.article_id or "")
    hit = next((h for h in outcome.hits if h.article_id == article_id), None)
    if hit is None:
        logger.error("artikel terpilih %s tidak ada di hasil pencarian", article_id)
    pill, style = status_for_label(ans.status_label or "", article_id)
    return ResultView(
        kind="found",
        status_color=style.color,
        pill_text=pill,
        headline=style.headline,
        kesimpulan=(hit.kesimpulan if hit else "").strip(),  # apa adanya; parafrase LLM hanya di diagnostik
        advice=style.advice,
        message_excerpt=excerpt(outcome.message, settings.MESSAGE_EXCERPT_CHARS),
        article_title=display_title(ans.title),
        article_url=ans.article_url if is_safe_url(ans.article_url) else "",
        article_date=format_metadata_date(hit.date) if hit and hit.date else "",
        penjelasan=outcome.penjelasan.strip(),
        # dari metadata, bukan dari LLM; disaring ulang dengan kebijakan terkini
        references=display_references(list(ans.references), article_id),
        diagnostics=diag,
    )
