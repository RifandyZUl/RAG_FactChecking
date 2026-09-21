"""
Set pengembangan (10 kueri) dengan DUA label terpisah per kueri.

- `expected_retrieval_article`: artikel yang seharusnya TERJANGKAU retrieval (untuk Recall@3). None
  bila tidak ada artikel yang perlu terjangkau (negatif murni).
- `expected_verdict`: keputusan akhir yang seharusnya diberikan generator: "ditemukan" (dengan
  `expected_retrieval_article` sebagai artikelnya) atau "belum_ditemukan".

Keduanya bisa berbeda: klaim yang lebih umum daripada artikel (kueri 3) seharusnya terjangkau retrieval
(36729) tetapi dijawab "belum_ditemukan". Format butir set uji v1 memakai struktur dua label yang sama.

10 kueri ini adalah set PENGEMBANGAN yang sudah terlalu sering dipakai: bukan bukti mutu.
`kekhususan` mengikuti testset/ANNOTATION_GUIDE.md; hanya diisi bila jelas ("tidak_dianotasi" bila belum).
`batas` dilaporkan terpisah dan tidak masuk hitungan utama.
"""

from dataclasses import dataclass

VERDICT_DITEMUKAN = "ditemukan"
VERDICT_BELUM = "belum_ditemukan"
# nilai `verdict` yang dikeluarkan generator -> nilai `expected_verdict`
ANSWER_TO_EXPECTED = {"ditemukan": VERDICT_DITEMUKAN, "tidak_ditemukan": VERDICT_BELUM}


@dataclass(frozen=True)
class DevQuery:
    claim: str
    tipe: str  # positif | negatif_sulit | negatif_sedang | negatif_mudah
    expected_retrieval_article: str | None
    expected_verdict: str  # VERDICT_DITEMUKAN | VERDICT_BELUM
    kekhususan: str = "tidak_dianotasi"
    jenis: str = ""  # keterangan bebas tingkat kesulitan (negatif)
    absence_keywords: tuple[str, ...] = ()  # kata kunci yang harus ABSEN di seluruh artikel (negatif murni)
    catatan: str = ""

    @property
    def batas(self) -> bool:
        return self.kekhususan == "batas"

    @property
    def expected_article_id(self) -> str | None:
        """Artikel yang seharusnya dipilih generator (hanya bila expected_verdict == ditemukan)."""
        return self.expected_retrieval_article if self.expected_verdict == VERDICT_DITEMUKAN else None


DEV_QUERIES: list[DevQuery] = [
    DevQuery("katanya ojol nggak boleh isi pertalite lagi ya?", "positif", "36730", VERDICT_DITEMUKAN),
    DevQuery("ada link pendaftaran bantuan buat orang tua, itu beneran?", "positif", "36737", VERDICT_DITEMUKAN,
             kekhususan="batas",
             catatan="'orang tua' ambigu terhadap 'lansia' (KIA 36737); diputuskan per butir lewat uji Kesimpulan, "
                     "tidak ditetapkan umum (keputusan pemilik proyek)"),
    DevQuery("malaysia marah ke indonesia soal asap", "negatif_sulit", "36729", VERDICT_BELUM, kekhususan="umum",
             catatan="dilabeli ulang dari positif SETELAH melihat keluaran model, berdasarkan pedoman berjangkar KIA; "
                     "hanya untuk set pengembangan"),
    DevQuery("polisi mau razia motor sampai ke rumah-rumah warga?", "positif", "36738", VERDICT_DITEMUKAN),
    DevQuery("daftar cek kesehatan gratis lewat link yang beredar, asli gak sih?", "positif", "36731",
             VERDICT_DITEMUKAN),
    DevQuery("katanya gas melon 3 kg mau dihapus bulan depan, harus beli yang nonsubsidi?", "negatif_sulit", None,
             VERDICT_BELUM, jenis="sulit: ranah kebijakan/subsidi seperti artikel Pertalite dan bansos",
             absence_keywords=("elpiji", "gas melon", "3 kg")),
    DevQuery("vaksin flu bikin laki-laki jadi mandul, benar nggak sih?", "negatif_sulit", None, VERDICT_BELUM,
             jenis="sulit: tetangga dekat 36214 (vaksin HPV bikin impoten)",
             absence_keywords=("vaksin flu", "influenza", "infertil")),
    DevQuery("katanya BMKG bilang bakal ada gempa megathrust besar di Jawa minggu ini", "negatif_sedang", None,
             VERDICT_BELUM, jenis="sedang: ranah gempa ada, tetapi bukan klaim prediksi",
             absence_keywords=("megathrust",)),
    DevQuery("minum rebusan daun sirsak tiap pagi katanya bisa sembuhin diabetes", "negatif_mudah", None,
             VERDICT_BELUM, jenis="mudah: ranah kesehatan tetapi klaimnya tidak ada",
             absence_keywords=("sirsak", "diabetes")),
    DevQuery("NASA ngaku kalau bumi ternyata datar ya?", "negatif_mudah", None, VERDICT_BELUM,
             jenis="mudah: tidak berhubungan dengan isi basis data",
             absence_keywords=("bumi datar", "bumi itu datar")),
]
