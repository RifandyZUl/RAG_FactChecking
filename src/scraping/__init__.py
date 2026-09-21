"""
Scraper artikel TurnBackHoax.id

Mengambil artikel cek fakta dan memecahnya berdasarkan seksi (Narasi,
Penjelasan, Kesimpulan) sesuai struktur baku artikel TurnBackHoax.

Catatan: halaman daftar artikel sudah terverifikasi server-side rendered
dengan paginasi ?page=N. Kendala utamanya adalah latensi server yang
tinggi, sehingga semua permintaan memakai timeout, retry, dan cache HTML.

Modul (dipisah menurut alasan berubah):
  links      kebijakan penyaringan tautan (domain diblokir)
  client     sesi HTTP, timeout/retry, cache HTML
  discovery  pengumpulan URL artikel dari halaman daftar
  parser     parsing HTML artikel menjadi dict terstruktur
  pipeline   orkestrasi dan CLI (`python -m scraping`)
"""
