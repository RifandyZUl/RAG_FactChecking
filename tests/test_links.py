"""Uji kebijakan penyaringan tautan (scraping.links).
"""

from scraping.links import (
    INVALID_URL_REASON,
    blocked_reason,
    filter_references,
    is_trusted_source,
    normalize_url,
    unique_urls,
)


def test_normalize_and_domain() -> None:
    assert normalize_url("  https://a.com/x?p=1#frag  ") == "https://a.com/x?p=1"
    assert normalize_url("https://a.com/x") == "https://a.com/x"

    # Arsip dan hosting gambar: selalu disaring, apa pun path-nya
    for u in [
        "https://archive.li/n2Rxw", "https://archive.ph/6Yd1j",
        "https://web.archive.org/web/2020/x", "http://archive.today/TwOTs",
        "https://archive.is/abc", "https://archive.vn/abc", "https://archive.md/HzI4C",
        "https://webarchive.io/archive/chaa/x", "https://ghostarchive.org/archive/F59Ye",
        "https://ibb.co.com/cKj7vmkf", "https://ibb.co/cKj7vmkf",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Media sosial: disaring, baik postingan maupun beranda akun
    for u in [
        "https://vt.tiktok.com/ZSq9c6ky7/",
        "https://www.tiktok.com/@sindonews/video/7516875885891374343",
        "https://x.com/a/status/1", "https://twitter.com/a/status/1",
        "https://www.instagram.com/p/DdApnwrzvas/",
        "https://www.instagram.com/reel/DCQov8YyCgw/",
        "https://www.instagram.com/kemensosri/p/DXjyJ9gkZf_/",
        "https://web.facebook.com/photo/?fbid=1&set=a.2",
        "https://www.facebook.com/photo.php?fbid=1&set=pb.1",
        "https://www.facebook.com/share/1EDkBDGFdE",
        "https://web.facebook.com/khanza.khulfi/posts/pfbid02cKx",
        "https://www.youtube.com/watch?v=T7UMijc_ddI",
        "https://www.youtube.com/shorts/a3B204GdwtI", "https://youtu.be/abc",
        "https://www.threads.com/@bacotwakanda.id/post/DcgGDHyEkiA",
        # beranda akun: sengaja ikut disaring (penilaian akun resmi vs
        # penyebar hoaks ditunda ke Versi 2, lihat CLAUDE.md)
        "https://www.instagram.com/kemensetneg.ri/",
        "https://www.instagram.com/bank_brksyariah?igshid=YzAw",
        "https://x.com/brksyariahid",
        "https://web.facebook.com/bankriaukeprisyariah.id?mibextid=LQQJ4d&_rdc=1&_rdr",
        "https://www.tiktok.com/@binmas_penjaringan",
        "https://www.youtube.com/@kemenkes",
        "https://www.threads.com/@lowongankerja209",
    ]:
        assert blocked_reason(u), f"seharusnya disaring: {u}"

    # Tidak boleh salah cocok pada domain yang hanya berakhiran mirip
    assert blocked_reason("https://www.netflix.com/id") is None
    assert blocked_reason("https://www.cnnindonesia.com/a") is None
    assert blocked_reason("https://box.com/status/1") is None


# URL cacat di sumber (bentuk kasus 29437: kurung siku nyasar di akhir host). Domain contoh.
BAD_URLS = ["http://contoh.go.id]", "http://contoh.go.id]#bagian", "http://[contoh.go.id/x", "https://a.id]/x?p=1"]


def test_unparseable_url_is_filtered_as_invalid_not_repaired() -> None:
    for bad in BAD_URLS:
        assert blocked_reason(bad) == INVALID_URL_REASON == "URL tidak sah", bad
        assert normalize_url(f"  {bad}  ") == bad, "tidak diperbaiki; hanya spasi di ujung dibuang"
    assert unique_urls(["http://contoh.go.id]", " http://contoh.go.id] ", "https://a.id/x#f"]) == [
        "http://contoh.go.id]", "https://a.id/x"]

    raw = ["https://www.contoh.go.id/rilis", "http://contoh.go.id]", "https://x.com/a/status/1", "http://b.id]#f"]
    kept, filtered = filter_references(raw, claim_sources=["http://b.id]#f"])
    assert kept == ["https://www.contoh.go.id/rilis"], "URL cacat tidak tampil sebagai rujukan"
    assert filtered == [
        {"url": "http://contoh.go.id]", "reasons": ["URL tidak sah"]},
        {"url": "https://x.com/a/status/1", "reasons": ["domain daftar-blokir: x.com"]},
        {"url": "http://b.id]#f", "reasons": ["cocok dengan claim_sources", "URL tidak sah"]},
    ]


def test_valid_urls_are_unaffected_by_invalid_url_handling() -> None:
    assert blocked_reason("https://www.contoh.go.id/a?b=[1]#c") is None  # kurung di query/fragmen sah
    assert blocked_reason("http://[2001:db8::1]/x") is None  # IPv6 sah
    assert normalize_url("https://www.contoh.go.id/a?b=[1]#c") == "https://www.contoh.go.id/a?b=[1]"


def test_url_shorteners_are_always_filtered() -> None:
    """Tautan pendek tidak bisa diverifikasi pengguna sebelum diklik (ditetapkan 2026-10-03)."""
    for url in [
        "https://tinyurl.com/contoh1", "https://shorturl.at/AbCdE", "https://short-url.org/1abCd",
        "https://bit.ly/contoh", "http://bit.ly/contoh", "https://s.id/contoh", "https://cutt.ly/contoh",
        "https://surl.li/contoh", "https://g.co/contoh", "https://fb.me/contoh", "https://www.tinyurl.com/x",
    ]:
        assert blocked_reason(url), f"seharusnya disaring: {url}"
    # domain yang hanya berakhiran mirip tidak ikut tersaring
    for url in [
        "https://news.id/a", "https://bisnis.id/a", "https://www.contoh.go.id/a", "https://rabbit.ly/a",
        "https://blog.co/a", "https://www.bing.co/a", "https://mytinyurl.com.example.org/a", "https://kompas.id/a",
        "https://tirto.id/a", "https://www.ojk.go.id/a",
    ]:
        assert blocked_reason(url) is None, f"tidak boleh disaring: {url}"


def test_all_archive_domains_are_filtered() -> None:
    """Kebijakan sejak awal: seluruh domain arsip disaring (lima domain ditambahkan 2026-10-03)."""
    for url in [
        "https://arsip.cekfakta.com/archive/123.456/index.html", "https://archive.fo/AbCdE",
        "https://megalodon.jp/2026-0101-0000-00/contoh.example/a", "https://perma.cc/ABCD-1234",
        "https://archive.cob.web.id/contoh",
    ]:
        assert blocked_reason(url), f"seharusnya disaring: {url}"
    assert blocked_reason("https://cekfakta.com/a") is None, "hanya subdomain arsipnya yang disaring"
    assert blocked_reason("https://cekfakta.tempo.co/a") is None


def test_trusted_source_is_government_or_listed_media_only() -> None:
    """Baris "Sumber:": bawaan saring; hanya *.go.id dan media/cek fakta pada daftar yang dikecualikan."""
    for url in [
        "https://www.contoh.go.id/", "http://cek.layanan.contoh.go.id", "https://mediaindonesia.com/a/1",
        "https://news.batampos.co.id/a", "https://nasional.kompas.com/read/1", "https://cekfakta.tempo.co/a",
        "https://periksafakta.afp.com/a",
    ]:
        assert is_trusted_source(url), f"seharusnya tepercaya: {url}"
    for url in [
        "https://klaim-hadiah.contoh.top/?x=1", "https://docs.google.com/document/d/x", "https://drive.google.com/file/d/x",
        "https://contoh-go.id/a", "https://go.id.contoh.top/a", "https://kompas.com.contoh.top/a",
        "https://lowongan.vercel.app/a", "https://tinyurl.com/contoh1", "https://web.facebook.com/reel/1",
        "https://arsip.cekfakta.com/archive/1/index.html",  # arsip: tersaring walau cekfakta.com tepercaya
        "http://contoh.go.id]",  # tidak dapat diurai: tidak pernah tepercaya
    ]:
        assert not is_trusted_source(url), f"tidak boleh tepercaya: {url}"


def test_trusted_source_matches_on_domain_boundary_not_substring() -> None:
    """
    Situs penipuan sering meniru nama media. Pencocokan daftar tepercaya harus pada BATAS DOMAIN
    (host persis atau subdomain sejati), bukan pencocokan teks.
    """
    for url in [
        "https://kompas.com/a", "https://berita.kompas.com/a", "https://www.nasional.kompas.com/a",
        "HTTPS://Berita.KOMPAS.com/a", "https://tempo.co/a", "https://cekfakta.tempo.co/a",
        "https://kompas.com:443/a", "https://layanan.contoh.go.id/a",
    ]:
        assert is_trusted_source(url), f"seharusnya tepercaya: {url}"
    for url in [
        "https://kompas.com.situspalsu.xyz/a",  # nama media sebagai subdomain situs lain
        "https://palsukompas.com/a",  # nama media sebagai akhiran teks, bukan batas domain
        "https://tempo.co.id-palsu.net/a",
        "https://tempo.co.id/a",  # domain lain yang hanya diawali nama media
        "https://kompascom.xyz/a", "https://kompas.com-berita.top/a", "https://kompas-com.web.id/a",
        "https://situspalsu.xyz/kompas.com/a",  # nama media di jalur
        "https://situspalsu.xyz/?u=https://kompas.com/a",  # nama media di query
        "https://kompas.com@situspalsu.xyz/a",  # nama media di bagian kredensial URL
        "https://kompas.com.situspalsu.xyz:443/a",
        "https://xn--kmpas-jua.com/a",  # punycode mirip
        "https://go.id.situspalsu.xyz/a", "https://palsu-go.id/a", "https://contohgo.id/a", "https://go.id-palsu.top/a",
    ]:
        assert not is_trusted_source(url), f"tiruan tidak boleh tepercaya: {url}"
