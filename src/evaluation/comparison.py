"""
Perbandingan keputusan dua model per kueri.

Hanya informasi kesetaraan keputusan. BUKAN kriteria H3 (yang dinilai terhadap ground truth).
"""


def decision(rec: dict) -> tuple[str, str | None]:
    """Keputusan sebuah kueri: verdict dan artikel yang dipilih (bukan teks bebas)."""
    return rec["verdict"], rec["article_id"]


def compare_models(base: dict[str, dict], cand: dict[str, dict], cases: list[tuple]) -> tuple[str, str]:
    """
    Bandingkan keputusan dua model per kueri; kembalikan (tabel, status kesetaraan).

    Hanya informasi kesetaraan keputusan antarmodel. BUKAN kriteria H3: kesetaraan
    dengan model lain bukan kebenaran (rumusan H3 relatif sebelumnya adalah kesalahan
    desain); H3 dinilai terhadap ground truth. Status: TERDUKUNG bila sama pada semua
    negatif dan berbeda paling banyak pada satu positif; kueri yang belum ada hasilnya
    membuat BELUM KONKLUSIF.
    """
    lines = [f"{'#':>2} {'jenis':<8} {'dasar':<24} {'kandidat':<24} sama  klaim"]
    diff_pos = diff_neg = missing = 0
    for i, (claim, _exp, kind) in enumerate(cases, 1):
        a, b = base.get(claim), cand.get(claim)
        if a is None or b is None:
            missing += 1
            lines.append(f"{i:>2} {kind:<8} {'-' if a is None else str(decision(a)):<24} "
                         f"{'-' if b is None else str(decision(b)):<24} ?     {claim[:50]}")
            continue
        same = decision(a) == decision(b)
        if not same:
            diff_pos += kind == "positif"
            diff_neg += kind == "negatif"
        lines.append(f"{i:>2} {kind:<8} {str(decision(a)):<24} {str(decision(b)):<24} "
                     f"{'ya' if same else 'TIDAK':<5} {claim[:50]}")
    if missing:
        status = f"BELUM KONKLUSIF ({missing} kueri belum ada hasil pada salah satu model)"
    elif diff_neg == 0 and diff_pos <= 1:
        status = (f"TERDUKUNG (beda pada negatif: {diff_neg}, pada positif: {diff_pos}). "
                  "Kesetaraan keputusan, bukan kebenaran: periksa juga akurasi masing-masing.")
    else:
        status = (f"TIDAK TERDUKUNG (beda pada negatif: {diff_neg}, pada positif: {diff_pos}); "
                  "pertahankan 3.8 Flash sebagai generator dan rencanakan evaluasi lintas hari.")
    return "\n".join(lines), status
