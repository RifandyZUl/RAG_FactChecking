"""
Kebijakan penyaringan tautan: normalisasi URL dan daftar domain yang diblokir.

Berubah bila ditemukan kebocoran tautan hoaks pada artikel lain (Aturan Wajib #1).
"""

from urllib.parse import urldefrag, urlparse


# Penyaringan `references`. Pencocokan domain mencakup subdomain
# (vt.tiktok.com, web.archive.org). Tambahkan domain baru di sini bila
# ditemukan kebocoran pada artikel lain.

# Domain yang disaring dari `references`, apa pun path-nya (postingan maupun
# beranda akun). Tiga kelompok: media sosial (tempat hoaks beredar; akun resmi
# instansi tidak bisa dibedakan dari akun penyebar hoaks tanpa penilaian
# kredibilitas, ditunda ke Versi 2), arsip (salinan unggahan hoaks), dan
# hosting gambar (tangkapan layar yang tidak bisa diverifikasi pengguna).
ALWAYS_BLOCKED_DOMAINS: tuple[str, ...] = (
    # media sosial
    "tiktok.com",
    "facebook.com",
    "fb.watch",  # pemendek resmi Facebook
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
    # hosting gambar
    "ibb.co.com",
    "ibb.co",  # domain asli imgbb; ibb.co.com adalah cerminannya
)


def normalize_url(url: str) -> str:
    """Bersihkan URL: buang spasi di ujung dan fragmen (bagian setelah #)."""
    return urldefrag(url.strip())[0]


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


def blocked_reason(url: str) -> str | None:
    """
    Kembalikan alasan URL harus disaring berdasarkan domainnya, atau None.

    Pencocokan mencakup subdomain (vt.tiktok.com, web.archive.org) dan tidak
    memperhatikan path: postingan maupun beranda akun sama-sama disaring.
    """
    host = (urlparse(url).hostname or "").lower()
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
          atau hosting gambar), apa pun path-nya.

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
