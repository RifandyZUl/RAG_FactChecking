"""Uji logika parsing scraper dengan HTML tiruan yang meniru struktur asli."""

from bs4 import BeautifulSoup
from scraper import (parse_title, extract_sections,
                     extract_references, extract_claim_sources)

MOCK_HTML = """
<html><body>
<main>
<h1>[SALAH] Malaysia Laporkan Indonesia ke PBB soal Karhutla</h1>
<a href="https://turnbackhoax.id/articles?category=Politik">Politik</a>
<span>17/09/2026</span>
<span>Mafindo</span>
<p><strong>Narasi</strong></p>
<p>Beredar <a href="https://x.com/gumpanggi/status/209886">gambar</a> dari akun X
pada Minggu (13/9/2026) yang menampilkan klaim jika Malaysia telah melaporkan
Indonesia ke PBB mengenai asap karhutla.</p>
<p><strong>Penjelasan</strong></p>
<p>Tim Pemeriksa Fakta Mafindo memastikan kebenarannya dengan memasukkan kata
kunci ke dalam kolom pencarian Google.</p>
<p>Dari hasil pencarian, tidak ditemukan adanya pemberitaan yang membenarkan
klaim tersebut.</p>
<p><strong>Kesimpulan</strong></p>
<p>Faktanya, Malaysia tidak melaporkan Indonesia ke PBB soal asap karhutla,
melainkan memilih jalur diplomatik ASEAN. Jadi, unggahan tersebut adalah
konten palsu (fabricated content).</p>
<p><strong>Hasil Periksa fakta</strong></p>
<p>Salah</p>
<p><strong>Referensi</strong></p>
<ul>
<li><a href="https://www.cnnindonesia.com/internasional/20260822175014">CNN</a></li>
<li><a href="https://www.kompasiana.com/mnshidqi/5d09fd67">Kompasiana</a></li>
</ul>
</main>
</body></html>
"""


def run():
    soup = BeautifulSoup(MOCK_HTML, "html.parser")
    h1 = soup.find("h1")

    label, title = parse_title(h1.get_text(" ", strip=True))
    print(f"Label     : {label}")
    print(f"Judul     : {title}")

    container = h1.find_parent(["article", "main", "div"]) or soup
    sections = extract_sections(container)

    print(f"\nSeksi terparse: {list(sections.keys())}")
    for k, v in sections.items():
        preview = v[:90].replace("\n", " ")
        print(f"  - {k:22s}: {preview}...")

    refs = extract_references(container)
    print(f"\nReferensi valid ({len(refs)}):")
    for r in refs:
        print(f"  - {r}")

    claim_srcs = extract_claim_sources(container)
    print(f"\nSumber klaim hoaks ({len(claim_srcs)}) - jangan tampilkan sbg rujukan:")
    for r in claim_srcs:
        print(f"  - {r}")

    # Validasi minimum
    assert label == "SALAH", "label gagal diekstrak"
    assert "narasi" in sections, "seksi Narasi tidak terparse"
    assert "kesimpulan" in sections, "seksi Kesimpulan tidak terparse"
    assert sections["kesimpulan"].startswith("Faktanya"), "isi Kesimpulan salah"
    assert any("cnnindonesia" in r for r in refs), "referensi tidak terambil"
    assert not any("x.com" in r for r in refs), \
        "tautan sumber hoaks bocor ke daftar referensi valid"
    assert any("x.com" in r for r in claim_srcs), "sumber klaim tidak terambil"
    print("\nSemua pemeriksaan lolos.")


if __name__ == "__main__":
    run()