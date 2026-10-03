@echo off
rem Peluncur pembaruan berkala (SCRAPING SAJA; ingest tetap manual). Dipanggil Task Scheduler atau manual.
rem Kode keluar = kode keluar proses Python (lihat src\scraping\scheduled.py).
cd /d "%~dp0.."
set "PYTHONPATH=src"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"
".venv\Scripts\python.exe" -m scraping.scheduled %*
exit /b %ERRORLEVEL%
