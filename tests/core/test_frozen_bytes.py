"""Hash byte bukti untuk data beku testset/ (lihat testset/README.md dan .gitattributes).

`87e2ad83...` (eksternal_butir.json) dan `ecef6636...` (v1.jsonl) dicatat dari byte salinan kerja CRLF di
Windows. `.gitattributes` (`testset/** eol=crlf`) membuat salinan kerja itu sama di Windows dan Linux, jadi
hash tercatat bisa diverifikasi di mana pun. Hash LF adalah isi yang tersimpan di git (verifikasi kedua).
"""

import hashlib
from pathlib import Path

import pytest

TESTSET = Path(__file__).resolve().parents[2] / "testset"
RECORDED = {
    # berkas: (sha256 byte salinan kerja CRLF yang tercatat, sha256 isi git LF sebagai pembanding)
    "eksternal_butir.json": ("87e2ad836da60687f5e0b9ba51344f0de4797ea815357d15e34c94edf566be2b",
                             "667a67a09dca88e88c6480c7166960866f238a2eca163fa7d5a176a13c90b62b"),
    "v1.jsonl": ("ecef6636f71f1e9c00786427f973ab3790f598e6c308fb0e561b39d8cbe80dd0",
                 "d948addcf4487467d9c67c18d7587dc8a03f4979ccb86281b8a20c6b19ff18ec"),
}


@pytest.mark.parametrize("name", sorted(RECORDED))
def test_recorded_crlf_byte_hash_and_lf_content_hash(name: str) -> None:
    data = (TESTSET / name).read_bytes()
    crlf_hash, lf_hash = RECORDED[name]
    assert hashlib.sha256(data).hexdigest() == crlf_hash, (
        f"{name}: byte salinan kerja tidak sama dengan hash bukti tercatat (cek .gitattributes, testset/** eol=crlf)")
    assert hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest() == lf_hash
