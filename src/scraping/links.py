"""
Kebijakan penyaringan tautan: normalisasi URL dan daftar domain yang diblokir.

Berubah bila ditemukan kebocoran tautan hoaks pada artikel lain (Aturan Wajib #1).
"""

from urllib.parse import urldefrag, urlparse


# Penyaringan `references`. Pencocokan domain mencakup subdomain
# (vt.tiktok.com, web.archive.org). Tambahkan domain baru di sini bila
# ditemukan kebocoran pada artikel lain.

# Domain yang disaring dari `references`, apa pun path-nya (postingan maupun
# beranda akun). Empat kelompok: media sosial (tempat hoaks beredar; akun resmi
# instansi tidak bisa dibedakan dari akun penyebar hoaks tanpa penilaian
# kredibilitas, ditunda ke Versi 2), arsip (salinan unggahan hoaks), hosting
# gambar (tangkapan layar yang tidak bisa diverifikasi pengguna), dan pemendek
# URL (tujuannya tidak bisa diverifikasi pengguna sebelum diklik, bahkan bila
# rujukannya sah; ditambahkan 2026-10-03 setelah tautan pendek sumber hoaks
# ditemukan tampil sebagai rujukan pada 7 artikel).
ALWAYS_BLOCKED_DOMAINS: tuple[str, ...] = (
    # media sosial
    "tiktok.com",
    "facebook.com",
    "fb.watch",  # pemendek resmi Facebook
    "fb.me",  # pemendek resmi Facebook (ditemukan di data)
    "instagram.com",
    "x.com",
    "twitter.com",
    "threads.com",
    "youtube.com",
    "youtu.be",  # pemendek resmi YouTube
    # arsip
    "archive.li",
    "archive.ph",
    "archive.org",
    "web.archive.org",
    "archive.today",
    "archive.is",
    "archive.vn",
    "archive.md",
    "webarchive.io",
    "ghostarchive.org",
    "archive.fo",  # alias archive.today
    "arsip.cekfakta.com",  # arsip unggahan hoaks milik jaringan cek fakta (mis. lowongan palsu, 35161)
    "megalodon.jp",
    "perma.cc",
    "archive.cob.web.id",
    # hosting gambar
    "ibb.co.com",
    "ibb.co",  # domain asli imgbb; ibb.co.com adalah cerminannya
    # pemendek URL: enam pertama ditetapkan pemilik proyek; sisanya ditemukan di data
    "tinyurl.com",
    "shorturl.at",
    "short-url.org",
    "bit.ly",
    "s.id",
    "cutt.ly",
    "surl.li",
    "g.co",  # pemendek resmi Google; tetap tidak bisa diverifikasi sebelum diklik
)


# Alasan penyaringan untuk URL yang tidak dapat diurai `urllib` (mis. "http://kemenag.go.id]" di
# seksi Referensi artikel 29437: kurung siku nyasar di sumber). URL seperti itu TIDAK diperbaiki
# (itu menebak isi sumber): ia tetap apa adanya di `references_raw`, disaring dari `references`,
# dan tercatat di `references_filtered` dengan alasan ini.
INVALID_URL_REASON = "URL tidak sah"


def normalize_url(url: str) -> str:
    """
    Bersihkan URL: buang spasi di ujung dan fragmen (bagian setelah #).

    URL yang tidak dapat diurai dikembalikan apa adanya (hanya spasi di ujung dibuang), tidak
    diperbaiki; `blocked_reason` yang kemudian menandainya tidak sah.
    """
    stripped = url.strip()
    try:
        return urldefrag(stripped)[0]
    except ValueError:
        return stripped


def unique_urls(urls: list[str]) -> list[str]:
    """Normalkan tiap URL lalu buang duplikat dengan urutan tetap."""
    seen: set[str] = set()
    result: list[str] = []
    for u in urls:
        n = normalize_url(u)
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


# Baris "Sumber:" di seksi Hasil Periksa Fakta memuat sumber klaim yang diperiksa (unggahan hoaks,
# arsipnya, tautan penipuan) dan kadang juga situs pembanding yang sah. Aturan (pemilik proyek,
# 2026-10-03): BAWAAN = SARING. Setiap URL di baris itu diperlakukan sebagai sumber klaim, KECUALI
# domainnya situs pemerintah (*.go.id) atau media/cek fakta pada daftar eksplisit di bawah. Daftar
# ini sengaja pendek dan hanya memuat media arus utama serta pemeriksa fakta yang memang muncul
# sebagai rujukan di data; domain di luar daftar tersaring sampai ditambahkan dengan sengaja.
TRUSTED_SOURCE_SUFFIXES: tuple[str, ...] = ("go.id",)
TRUSTED_SOURCE_DOMAINS: tuple[str, ...] = (
    # media arus utama
    "kompas.com", "kompas.tv", "kompas.id", "tempo.co", "detik.com", "antaranews.com",
    "cnbcindonesia.com", "cnnindonesia.com", "liputan6.com", "tirto.id", "metrotvnews.com",
    "kumparan.com", "bisnis.com", "idntimes.com", "suara.com", "tribunnews.com", "republika.co.id",
    "merdeka.com", "inews.id", "tvonenews.com", "beritasatu.com", "mediaindonesia.com", "medcom.id",
    "viva.co.id", "sindonews.com", "rri.co.id", "katadata.co.id", "jawapos.com", "batampos.co.id",
    "bbc.com", "reuters.com", "aljazeera.com",
    # cek fakta
    "afp.com", "snopes.com", "cekfakta.com",
)


def _matches_domain(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def is_trusted_source(url: str) -> bool:
    """
    Apakah URL dari baris "Sumber:" boleh TETAP menjadi rujukan (pemerintah, media, cek fakta).

    URL yang tidak dapat diurai atau berdomain daftar-blokir tidak pernah tepercaya (mis.
    arsip.cekfakta.com tersaring walau cekfakta.com ada di daftar).
    """
    if blocked_reason(url) is not None:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(_matches_domain(host, d) for d in TRUSTED_SOURCE_SUFFIXES + TRUSTED_SOURCE_DOMAINS)


def blocked_reason(url: str) -> str | None:
    """
    Kembalikan alasan URL harus disaring berdasarkan domainnya, atau None.

    Pencocokan mencakup subdomain (vt.tiktok.com, web.archive.org) dan tidak
    memperhatikan path: postingan maupun beranda akun sama-sama disaring.
    URL yang tidak dapat diurai disaring dengan alasan INVALID_URL_REASON.
    """
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return INVALID_URL_REASON
    for domain in ALWAYS_BLOCKED_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return f"domain daftar-blokir: {domain}"
    return None


def filter_references(
    references_raw: list[str], claim_sources: list[str]
) -> tuple[list[str], list[dict]]:
    """
    Pisahkan referensi mentah menjadi yang aman ditampilkan dan yang dibuang.

    Dua kriteria berlaku sekaligus (sebuah URL bisa memenuhi keduanya):
      (a) URL juga ada di claim_sources, dan
      (b) domainnya masuk ALWAYS_BLOCKED_DOMAINS (media sosial, arsip,
          atau hosting gambar), apa pun path-nya; URL yang tidak dapat
          diurai ikut dibuang (INVALID_URL_REASON).

    Mengembalikan (references, references_filtered); tiap elemen yang
    dibuang berbentuk {"url": ..., "reasons": [...]} agar bisa diaudit.
    """
    claim_set = set(claim_sources)
    kept: list[str] = []
    filtered: list[dict] = []

    for url in references_raw:
        reasons: list[str] = []
        if url in claim_set:
            reasons.append("cocok dengan claim_sources")
        reason = blocked_reason(url)
        if reason:
            reasons.append(reason)

        if reasons:
            filtered.append({"url": url, "reasons": reasons})
        else:
            kept.append(url)

    return kept, filtered
