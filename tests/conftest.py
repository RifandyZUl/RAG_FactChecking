"""Konfigurasi bersama pytest."""

import sys

import pytest


@pytest.fixture(autouse=True)
def _stop_chroma_systems_opened_by_test():
    """
    Hentikan backend ChromaDB yang dibuka sebuah uji begitu uji itu selesai.

    chromadb menyimpan satu `System` per direktori indeks di kamus tingkat kelas
    (`SharedSystemClient._identifier_to_system`) dan tidak pernah menghentikannya kecuali `close()`
    dipanggil; kode proyek tidak memanggilnya (umur proses = umur indeks). Tanpa fixture ini setiap uji
    yang membuka indeks meninggalkan backend Rust hidup (thread, koneksi sqlite, berkas HNSW terbuka di
    direktori sementara) sampai proses pytest berakhir, sehingga uji indeks berikutnya berjalan
    berdampingan dengan sisa uji sebelumnya. Memakai atribut privat chromadb 1.5.9: bila berubah,
    fixture ini gagal keras (tidak diam-diam berhenti mengisolasi).
    """
    module = sys.modules.get("chromadb.api.shared_system_client")
    before = set(module.SharedSystemClient._identifier_to_system) if module else set()
    yield
    module = sys.modules.get("chromadb.api.shared_system_client")
    if module is None:
        return
    shared = module.SharedSystemClient
    for identifier in set(shared._identifier_to_system) - before:
        shared._identifier_to_refcount.pop(identifier, None)
        shared._identifier_to_system.pop(identifier).stop()
