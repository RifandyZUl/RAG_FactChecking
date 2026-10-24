# syntax=docker/dockerfile:1
# Image demo (Tahap 2). Python 3.13 di container; venv lokal pemilik proyek tetap 3.11 (tempat evaluasi
# dijalankan). Isi image hanya kode + konfigurasi tampilan + dua berkas angka publik untuk halaman "Tentang".
# Indeks, articles.json, buku besar kuota, .env, cache model, dan log TIDAK pernah masuk image: semuanya
# dipasang sebagai volume oleh docker-compose.yml (.dockerignore berupa daftar-putih).

# Base dipatok ke digest (indeks multi-arsitektur) python:3.13.16-slim-trixie, diambil 2026-10-24.
ARG PYTHON_IMAGE=python:3.13.16-slim-trixie@sha256:cf50a4f6ac4f026458b08d5222023d700ac806410dff5e9ca8728fa44f2b850f

# --- Tahap 1: dependensi di venv /opt/venv ------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS deps
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
# torch build CPU dari indeks PyTorch (tanpa pustaka CUDA); versinya dibaca dari requirements.txt, jadi
# tetap satu sumber versi. Paket lain persis dari requirements.txt (torch sudah terpenuhi, tidak diganti).
RUN --mount=type=cache,target=/root/.cache/pip \
    /opt/venv/bin/pip install "torch==$(sed -n 's/^torch==//p' /tmp/requirements.txt)" \
        --index-url https://download.pytorch.org/whl/cpu \
 && /opt/venv/bin/pip install -r /tmp/requirements.txt \
 && /opt/venv/bin/pip check

# --- Tahap 2: runtime -----------------------------------------------------------------------------------
FROM ${PYTHON_IMAGE}
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
COPY --from=deps /opt/venv /opt/venv

WORKDIR /app
COPY LICENSE ./
COPY src ./src
COPY .streamlit/config.toml ./.streamlit/config.toml
COPY assets/brand ./assets/brand
COPY testset/eksternal_hasil_per_butir.json testset/eksternal_butir.json ./testset/
# Setara `pip install -e .` (berkas .pth yang menunjuk ke src/), tanpa mengunduh setuptools saat build.
RUN echo /app/src > "$(/opt/venv/bin/python -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/rag_factchecking.pth" \
 && mkdir -p /app/data && chown app:app /app/data

# HF_HUB_OFFLINE=1: model dan tokenizer hanya dari cache yang dipasang (juga disetel hf_env.prepare_hf_env);
# revisi bge-m3 dipatok di ingest.MODEL_REVISION. RAG_READY_FILE: ditulis webapp.serve setelah pemanasan.
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/home/app/.cache/huggingface \
    HF_HUB_OFFLINE=1 \
    DISABLE_SAFETENSORS_CONVERSION=1 \
    RAG_READY_FILE=/tmp/rag_pemanasan_siap

USER app
EXPOSE 8501

# Sehat = server Streamlit membalas DAN pemanasan (tokenizer, indeks, model, penyedia LLM) selesai tanpa
# galat. Image slim tidak punya curl, jadi pemeriksaan memakai Python. start-period diukur, lihat README.
HEALTHCHECK --interval=15s --timeout=10s --start-period=240s --retries=3 \
    CMD python -c "import os, sys, urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5); sys.exit(0 if os.path.exists(os.environ['RAG_READY_FILE']) else 1)"

CMD ["python", "-m", "webapp.serve", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
