"""
Penyiapan data tampilan demo: `Answer` generator -> `ResultView` siap render.

Modul ini TIDAK mengimpor Streamlit dan TIDAK memanggil API, sehingga bisa diuji
tanpa antarmuka (`tests/test_presentation.py`). Seluruh salinan antarmuka dan
pemetaan status -> warna/ikon ada di sini, di satu tempat.

Warna di sini adalah NAMA warna tema Streamlit ("red", "orange", ...), bukan kode
heks. Nilai heksnya ditetapkan sekali di `.streamlit/config.toml`
(`redColor`, `orangeColor`, `yellowColor`, `grayColor`).

Tidak ada logika retrieval atau penyusunan jawaban: status tetap dari metadata
artikel, rujukan tetap dari `references` (Aturan Wajib #1 dan #3), dan
`claim_sources` tidak pernah disentuh.
"""

import re
from dataclasses import dataclass, field
from enum import Enum

from generator import MAX_FORMAT_RETRIES, Answer

# --------------------------------------------------------------------------
# Salinan antarmuka (Bahasa Indonesia, tanpa istilah teknis di bagian utama)
# --------------------------------------------------------------------------

PAGE_TITLE = "Cek Klaim"
PAGE_SUBTITLE = (
    "Tempel pesan yang Anda terima untuk dicocokkan dengan artikel cek fakta "
    "TurnBackHoax.id."
)
LIMITATION_NOTE = (
    "Basis data ini hanya memuat hoaks yang sudah diperiksa TurnBackHoax.id, "
    "sehingga pesan yang baru beredar mungkin belum ada di dalamnya. "
    "Hasil “belum ditemukan” tidak berarti klaimnya benar."
)
INPUT_LABEL = "Pesan atau klaim yang ingin dicek"
INPUT_PLACEHOLDER = "Tempel pesan atau tulis klaimnya di sini"
SUBMIT_LABEL = "Periksa"
EMPTY_INPUT_MESSAGE = "Tulis atau tempel pesan yang ingin dicek terlebih dahulu."

# Batas masukan 1.500 karakter: wilayah yang TERUKUR bekerja pada ablasi retrieval
# (testset/retrieval_ablation_report.txt, eksperimen 4: Recall@3 19/20 pada ~1.500 karakter,
# runtuh ke 2/20 pada ~5.000 karakter karena klaim terdorong keluar dari 512 token embedding).
# Batas 5.000 sebelumnya ditetapkan tanpa pengukuran. Teks yang melebihi batas TIDAK dipotong:
# pengguna diberi tahu dan tidak ada pemeriksaan yang dijalankan. (Widget sengaja tanpa
# `max_chars`, karena widget memotong teks tempelan tanpa pemberitahuan.)
MAX_INPUT_CHARS = 1500
TOO_LONG_MESSAGE = (
    "Pesan Anda {length} karakter, melebihi batas {limit} karakter, jadi belum "
    "diperiksa dan tidak ada bagian yang dipotong. Salin bagian yang memuat klaim "
    "utamanya saja, lalu periksa lagi."
)

# Peringatan pesan panjang, ditampilkan SEBELUM pemeriksaan. Ambang dalam token model embedding
# (satuan yang sebenarnya dibatasi, 512 token). 220 token ~ 1.000 karakter: rasio terukur pada
# teks pesan berantai sintetis eksperimen 4 ~4,5 karakter/token (335 token pada 1.500 karakter).
# Ambang ini pilihan konservatif pemilik proyek, BUKAN titik runtuh terukur (1.500 karakter
# masih 19/20). Bila tokenizer tidak tersedia, dipakai ambang karakter.
LONG_CLAIM_WARN_TOKENS = 220
LONG_CLAIM_WARN_CHARS = 1000
LONG_CLAIM_WARNING = (
    "Pesan Anda cukup panjang. Pesan yang terlalu panjang menurunkan ketepatan pencarian, "
    "karena bagian di luar klaim ikut terbaca dan klaimnya bisa terlewat. Hasil paling "
    "tepat bila Anda menyalin bagian inti klaimnya saja."
)
LONG_CLAIM_CONFIRM = "Tekan {button} sekali lagi untuk tetap memeriksa pesan ini apa adanya."

# Indikator proses: satu baris per langkah, agar pemuatan model pertama (~67 detik
# terukur) tidak tampak seperti aplikasi berhenti.
PROGRESS_RUNNING = "Memeriksa pesan…"
PROGRESS_DONE = "Pemeriksaan selesai"
PROGRESS_FAILED = "Pemeriksaan tidak selesai"
STEP_OPEN_INDEX = "Membuka basis data artikel cek fakta…"
STEP_LOAD_MODEL = (
    "Menyiapkan model bahasa… Pada pemeriksaan pertama sejak aplikasi dinyalakan, "
    "langkah ini bisa memakan sekitar satu menit."
)
STEP_SEARCH = "Mencari artikel cek fakta yang mirip…"
STEP_COMPARE = "Membandingkan pesan Anda dengan artikel yang ditemukan…"

ARTICLE_LINK_PREFIX = "Artikel cek fakta:"
CLARIFICATION_HEADING = "Faktanya"
REFERENCES_HEADING = "Rujukan"
ADVICE_HEADING = "Saran umum"
DIAGNOSTICS_LABEL = "Detail untuk penguji"

# Mode penguji: panel diagnostik hanya tampil bila diaktifkan. Bawaan MATI.
# Diatur lewat variabel lingkungan (diutamakan) atau `.streamlit/secrets.toml`.
TESTER_MODE_ENV = "DEMO_TESTER_MODE"
TESTER_MODE_SECRET = "demo_tester_mode"
_TRUE_VALUES = {"1", "true", "ya", "yes", "on"}

# "Belum ditemukan": artikel bertopik dekat ditampilkan sebagai rujukan baca, TANPA
# mengubah vonis (Aturan Wajib #4). Hanya kandidat dengan skor >= ambang.
# Dasar ambang 0,57 (hasil evaluasi set uji v1, retrieval identik di 3 run; dicek
# silang pada 10 kueri set pengembangan):
#   - skor kandidat TERTINGGI pada 10 negatif mudah (topik tak terkait) = 0,5680,
#     jadi pada ambang 0,57 tidak satu pun negatif mudah memunculkan daftar ini;
#   - artikel tetangga topik yang dipasangkan dengan negatif sulit (16 yang ada di
#     top-3) berskor 0,5419-0,8256; 13 dari 16 lolos ambang;
#   - set pengembangan: 36729 (0,5739, "malaysia marah soal asap") dan 36214 (0,6671,
#     "vaksin flu") tampil; negatif jauh (gas melon, megathrust, daun sirsak, bumi
#     datar; tertinggi 0,5353) tidak tampil. Ambang 0,58 akan membuang 36729.
# Marginnya tipis (0,002 di atas negatif mudah tertinggi) dan sampelnya kecil.
RELATED_SCORE_THRESHOLD = 0.57
RELATED_HEADING = "Mungkin terkait, tapi klaimnya berbeda"
RELATED_NOTE = (
    "Artikel berikut membahas topik yang mirip, tetapi klaim yang diperiksa di "
    "dalamnya tidak sama dengan pesan Anda. Hasil pemeriksaannya tidak berlaku "
    "untuk pesan Anda."
)

# Saran statis untuk SEMUA kasus penipuan: kalimatnya selalu sama, tidak merujuk
# isi klaim tertentu, dan dirender terpisah dari klarifikasi (bukan hasil cek fakta).
SCAM_ADVICE = (
    "Jangan klik tautan, jangan mengisi formulir, dan jangan mengirim data pribadi, "
    "kode OTP, atau uang kepada pengirim pesan. Saran ini berlaku umum untuk semua "
    "pesan penipuan dan bukan bagian dari hasil pemeriksaan fakta."
)

# Keterbacaan klarifikasi (hanya penyajian; teksnya dari generator yang terkunci):
# kolom ~60-65 karakter pada ukuran huruf isi dan jarak baris lebih lega.
READING_WIDTH_PX = 560
CLARIFICATION_LINE_HEIGHT = 1.75


@dataclass(frozen=True)
class StatusStyle:
    """Tampilan satu status: label, nama warna tema, ikon Material, kalimat ringkas."""

    label: str
    color: str
    icon: str
    summary: str


# Intensitas menurun: PENIPUAN (merugikan langsung) > SALAH > PARODI.
STATUS_STYLES: dict[str, StatusStyle] = {
    "PENIPUAN": StatusStyle(
        label="Penipuan",
        color="red",
        icon=":material/gpp_bad:",
        summary="Pesan ini termasuk modus penipuan yang sudah diperiksa TurnBackHoax.id.",
    ),
    "SALAH": StatusStyle(
        label="Salah",
        color="orange",
        icon=":material/report:",
        summary="Klaim ini sudah diperiksa TurnBackHoax.id dan dinyatakan salah.",
    ),
    "PARODI": StatusStyle(
        label="Parodi",
        color="yellow",
        icon=":material/theater_comedy:",
        summary=(
            "Konten ini sudah diperiksa TurnBackHoax.id dan merupakan parodi atau "
            "satire, bukan berita sungguhan."
        ),
    ),
}

# Label di luar tiga yang dikenal: gaya SALAH, label asli dari metadata.
FALLBACK_STATUS_COLOR = "orange"
FALLBACK_STATUS_ICON = ":material/report:"
FALLBACK_STATUS_SUMMARY = "Klaim ini sudah diperiksa TurnBackHoax.id dengan hasil: {label}."

# Netral: bukan kegagalan dan bukan pernyataan bahwa klaimnya benar.
NOT_FOUND_STYLE = StatusStyle(
    label="Belum ditemukan",
    color="gray",
    icon=":material/search_off:",
    summary=(
        "Klaim ini belum ditemukan di antara artikel cek fakta TurnBackHoax.id. "
        "Ini tidak berarti klaimnya benar; hanya belum ada artikel yang memeriksa "
        "klaim yang sama."
    ),
)

FAILURE_COLOR = "gray"
FAILURE_ICON = ":material/info:"


class FailureKind(Enum):
    """Jenis kegagalan yang dibedakan untuk pengguna."""

    QUOTA = "kuota_habis"
    TIMEOUT = "timeout"
    UNAVAILABLE = "layanan_tidak_tersedia"
    PARSE = "format_tidak_dikenali"
    CONFIG = "konfigurasi"
    NO_INDEX = "basis_data_tidak_ada"
    OTHER = "lainnya"


# Setiap pesan: apa yang terjadi + apa yang bisa dilakukan pengguna.
FAILURE_MESSAGES: dict[FailureKind, tuple[str, str]] = {
    FailureKind.QUOTA: (
        "Batas pemakaian harian tercapai",
        (
            "Layanan pemeriksa sudah mencapai batas pemakaian untuk hari ini, jadi pesan "
            "Anda belum diperiksa. Batas ini dipulihkan sekali sehari; silakan coba lagi "
            "beberapa jam lagi."
        ),
    ),
    FailureKind.TIMEOUT: (
        "Pemeriksaan memakan waktu terlalu lama",
        (
            "Layanan pemeriksa tidak menjawab dalam batas waktu, jadi pesan Anda belum "
            "diperiksa. Silakan coba lagi dalam beberapa menit."
        ),
    ),
    FailureKind.UNAVAILABLE: (
        "Layanan pemeriksa sedang tidak tersedia",
        (
            "Layanan sedang sibuk atau tidak dapat dihubungi, jadi pesan Anda belum "
            "diperiksa. Periksa koneksi internet Anda, lalu coba lagi dalam beberapa menit."
        ),
    ),
    FailureKind.PARSE: (
        "Hasil pemeriksaan tidak dapat dibaca",
        (
            "Sistem menerima jawaban dalam bentuk yang tidak dikenali, sehingga hasilnya "
            "tidak ditampilkan agar tidak menyesatkan. Silakan coba sekali lagi; bila "
            "terulang, coba tulis klaimnya dengan kalimat lain."
        ),
    ),
    FailureKind.CONFIG: (
        "Aplikasi belum siap dipakai",
        (
            "Kunci akses layanan pemeriksa belum diatur. Pengelola aplikasi perlu mengisi "
            "berkas .env sesuai contoh di .env.example, lalu memuat ulang halaman ini."
        ),
    ),
    FailureKind.NO_INDEX: (
        "Basis data artikel belum tersedia",
        (
            "Basis data artikel cek fakta belum disiapkan di komputer ini. Pengelola "
            "aplikasi perlu membangunnya lebih dulu (lihat bagian “Membangun basis "
            "pengetahuan” di README), lalu memuat ulang halaman ini."
        ),
    ),
    FailureKind.OTHER: (
        "Terjadi kesalahan",
        (
            "Pemeriksaan tidak dapat diselesaikan karena kesalahan yang tidak terduga. "
            "Silakan coba lagi beberapa saat lagi; bila terus terjadi, beri tahu "
            "pengelola aplikasi."
        ),
    ),
}

# --------------------------------------------------------------------------
# Klasifikasi galat
# --------------------------------------------------------------------------

# Format `CallRecord.error` dari GeminiProvider: "<NamaGalat> status=<kode>[ ...]"
# (src/llm/gemini.py). Bila formatnya berubah, galat jatuh ke FailureKind.OTHER:
# pesan umum, bukan pesan yang keliru.
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
    Tentukan jenis kegagalan sebuah jawaban; None bila jawabannya bukan kegagalan.

    Urutan: kuota (flag eksplisit dari generator) -> galat panggilan terakhir yang
    gagal (timeout/layanan) -> galat parsing (semua percobaan format gagal tanpa
    galat panggilan) -> lainnya.
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


# --------------------------------------------------------------------------
# Model tampilan
# --------------------------------------------------------------------------


@dataclass
class CandidateRow:
    """Satu kandidat artikel hasil pencarian (untuk panel diagnostik)."""

    article_id: str
    title: str
    label: str
    score: float


@dataclass
class Diagnostics:
    """Informasi untuk penguji; ditampilkan di panel tertutup, boleh berisi istilah teknis."""

    model: str = ""
    latency_s: float = 0.0
    llm_calls: int = 0
    attempts: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    candidates: list[CandidateRow] = field(default_factory=list)
    llm_reason: str = ""
    error_detail: str = ""  # sudah disamarkan oleh penyedia atau oleh pemanggil
    failure_kind: str = ""
    parse_failures: int = 0
    invalid_id: bool = False
    llm_urls_removed: int = 0
    clarification_fallback: bool = False
    # Panjang klaim dalam token model embedding; bagian di atas batas tidak ikut dicari
    # (retriever memotong ke MAX_SEQ_LENGTH), walau LLM tetap membaca klaim utuh.
    query_tokens: int | None = None
    query_token_limit: int | None = None
    related_threshold: float = RELATED_SCORE_THRESHOLD


@dataclass
class RelatedArticle:
    """Artikel bertopik dekat untuk hasil "belum ditemukan" (judul + tautan saja)."""

    title: str
    url: str


@dataclass
class ResultView:
    """Semua yang dibutuhkan fungsi render; tidak ada panggilan API di baliknya."""

    kind: str  # "found" | "not_found" | "failed"
    status_label: str
    status_color: str
    status_icon: str
    summary: str
    article_title: str = ""
    article_url: str = ""
    clarification: str = ""
    advice: str = ""  # saran umum statis; hanya untuk PENIPUAN
    references: list[str] = field(default_factory=list)
    related: list[RelatedArticle] = field(default_factory=list)  # hanya "not_found"
    diagnostics: Diagnostics = field(default_factory=Diagnostics)


_TITLE_LABEL_PREFIX = re.compile(r"^\s*\[[^\]]*\]\s*")


def display_title(title: str) -> str:
    """Buang label dalam kurung siku di awal judul ("[SALAH] ..."): status sudah tampil."""
    return _TITLE_LABEL_PREFIX.sub("", title).strip() or title.strip()


def _sum_tokens(values: list[int | None]) -> int | None:
    """Jumlahkan token yang tercatat; None bila tidak satu pun tercatat."""
    known = [v for v in values if v is not None]
    return sum(known) if known else None


def build_diagnostics(ans: Answer, model: str, failure: FailureKind | None) -> Diagnostics:
    """Susun data panel diagnostik dari jawaban generator."""
    return Diagnostics(
        model=model,
        latency_s=sum(c.latency_s for c in ans.calls),
        llm_calls=len(ans.calls),
        attempts=sum(c.attempts for c in ans.calls),
        input_tokens=_sum_tokens([c.input_tokens for c in ans.calls]),
        output_tokens=_sum_tokens([c.output_tokens for c in ans.calls]),
        candidates=[
            CandidateRow(
                article_id=str(c["article_id"]),
                title=str(c["title"]),
                label=str(c["label"]),
                score=float(c["score"]),
            )
            for c in ans.candidates
        ],
        llm_reason=ans.alasan,
        error_detail=ans.error,
        failure_kind=failure.value if failure else "",
        parse_failures=ans.parse_failures,
        invalid_id=ans.invalid_id,
        llm_urls_removed=len(ans.llm_urls_found),
        clarification_fallback=ans.klarifikasi_fallback,
    )


def failure_view(kind: FailureKind, diagnostics: Diagnostics | None = None) -> ResultView:
    """Tampilan kegagalan; juga dipakai untuk galat sebelum generator dipanggil."""
    title, body = FAILURE_MESSAGES[kind]
    diag = diagnostics or Diagnostics()
    diag.failure_kind = kind.value
    return ResultView(
        kind="failed",
        status_label=title,
        status_color=FAILURE_COLOR,
        status_icon=FAILURE_ICON,
        summary=body,
        diagnostics=diag,
    )


def related_articles(
    candidates: list[dict], article_urls: dict[str, str], threshold: float = RELATED_SCORE_THRESHOLD
) -> list[RelatedArticle]:
    """
    Kandidat retrieval dengan skor >= ambang, urut skor, sebagai judul + tautan artikel.

    Tautan hanya URL artikel TurnBackHoax dari metadata hasil retrieval (`article_urls`);
    kandidat tanpa URL dilewati, tidak ditebak. Skor tidak ikut ditampilkan.
    """
    ranked = sorted(candidates, key=lambda c: float(c["score"]), reverse=True)
    return [
        RelatedArticle(title=display_title(str(c["title"])), url=article_urls[str(c["article_id"])])
        for c in ranked
        if float(c["score"]) >= threshold and article_urls.get(str(c["article_id"]))
    ]


def build_view(
    ans: Answer,
    model: str = "",
    article_urls: dict[str, str] | None = None,
    query_tokens: int | None = None,
    query_token_limit: int | None = None,
) -> ResultView:
    """
    Ubah `Answer` generator menjadi `ResultView`. Fungsi murni: tanpa UI dan tanpa API.

    `article_urls` (article_id -> URL artikel, dari hasil retrieval) hanya dipakai untuk
    daftar "mungkin terkait" pada hasil "belum ditemukan"; vonisnya tidak berubah.
    """
    failure = classify_failure(ans)
    diag = build_diagnostics(ans, model, failure)
    diag.query_tokens = query_tokens
    diag.query_token_limit = query_token_limit

    if failure is not None:
        return failure_view(failure, diag)

    if ans.verdict == "ditemukan":
        label = (ans.status_label or "").strip()
        style = STATUS_STYLES.get(label.upper())
        if style is None:
            style = StatusStyle(
                label=label.capitalize() or "Sudah diperiksa",
                color=FALLBACK_STATUS_COLOR,
                icon=FALLBACK_STATUS_ICON,
                summary=FALLBACK_STATUS_SUMMARY.format(label=label or "tidak diketahui"),
            )
        return ResultView(
            kind="found",
            status_label=style.label,
            status_color=style.color,
            status_icon=style.icon,
            summary=style.summary,
            article_title=display_title(ans.title),
            article_url=ans.article_url,
            clarification=ans.klarifikasi,
            advice=SCAM_ADVICE if label.upper() == "PENIPUAN" else "",
            references=list(ans.references),  # dari metadata, bukan dari LLM
            diagnostics=diag,
        )

    # "tidak_ditemukan": alasan LLM hanya di panel diagnostik, bukan di bagian utama.
    return ResultView(
        kind="not_found",
        status_label=NOT_FOUND_STYLE.label,
        status_color=NOT_FOUND_STYLE.color,
        status_icon=NOT_FOUND_STYLE.icon,
        summary=NOT_FOUND_STYLE.summary,
        related=related_articles(ans.candidates, article_urls or {}),
        diagnostics=diag,
    )


# --------------------------------------------------------------------------
# Masukan dan setelan
# --------------------------------------------------------------------------


def _format_count(value: int) -> str:
    """Bilangan bulat dengan pemisah ribuan titik (gaya Indonesia)."""
    return f"{value:,}".replace(",", ".")


def validate_claim(text: str, limit: int = MAX_INPUT_CHARS) -> str | None:
    """Pesan untuk pengguna bila masukan tidak bisa diperiksa; None bila layak diperiksa."""
    stripped = text.strip()
    if not stripped:
        return EMPTY_INPUT_MESSAGE
    if len(stripped) > limit:
        return TOO_LONG_MESSAGE.format(length=_format_count(len(stripped)), limit=_format_count(limit))
    return None


def is_long_claim(text: str, token_count: int | None) -> bool:
    """
    Apakah masukan cukup panjang untuk diberi peringatan (sebelum pemeriksaan).

    Memakai hitungan token model embedding bila tersedia; bila tidak (None), ambang karakter.
    """
    if token_count is not None:
        return token_count > LONG_CLAIM_WARN_TOKENS
    return len(text.strip()) > LONG_CLAIM_WARN_CHARS


def parse_flag(value: object) -> bool:
    """Tafsirkan nilai setelan sebagai boolean; hanya nilai "hidup" yang eksplisit yang benar."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in _TRUE_VALUES


# --------------------------------------------------------------------------
# Pengamanan teks untuk Markdown
# --------------------------------------------------------------------------

# Tanda baca yang bermakna di Markdown Streamlit, termasuk "$" (LaTeX) dan ":"
# (direktif warna/ikon seperti ":red[...]" atau ":material/...:").
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|$~<>:])")


def escape_markdown(text: str) -> str:
    """Loloskan karakter Markdown agar teks dari data/LLM tampil apa adanya."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)


def markdown_link(text: str, url: str) -> str:
    """Tautan Markdown aman: teks diloloskan, tanda kurung dan spasi di URL dikodekan."""
    safe_url = url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    return f"[{escape_markdown(text)}]({safe_url})"
