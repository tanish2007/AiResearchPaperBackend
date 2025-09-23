# pdf_utils.py
from supabase import create_client, Client
import os
import re
import logging
import threading
import hashlib
SUPABASE_URL = "https://mzvtmqvtvsknbzughdnq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16dnRtcXZ0dnNrbmJ6dWdoZG5xIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODY2NzU2MSwiZXhwIjoyMDc0MjQzNTYxfQ.MmH_6WMZK7Cd2sULNM_brPv4cUCsEkU1D6SbGAuWOVw"
BUCKET_NAME = "pdfs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def make_safe_name(url: str) -> str:
    # Generate a short hash from the URL
    h = hashlib.sha1(url.encode()).hexdigest()[:12]
    return f"{h}.pdf"

current_pdf_url = None
current_pdf_path = None
model_loading = False

# def download_pdf(url: str) -> str:
#     os.makedirs("pdfs", exist_ok=True)
#     safe_name = make_safe_name(url)
#     local_path = os.path.join("pdfs", safe_name)

#     # Try download from Supabase
#     try:
#         data = supabase.storage.from_(BUCKET_NAME).download(safe_name)
#         if data:
#             content = data.read() if hasattr(data, "read") else data
#             with open(local_path, "wb") as f:
#                 f.write(content)
#             logging.info(f"Downloaded PDF from Supabase: {safe_name}")
#             return local_path
#     except Exception as e:
#         logging.info(f"PDF not found in bucket: {safe_name}, will download from URL. {e}")

#     # Download from original URL
#     import requests
#     logging.info(f"Downloading PDF from {url}")
#     resp = requests.get(url, timeout=15)
#     resp.raise_for_status()
#     with open(local_path, "wb") as f:
#         f.write(resp.content)

#     # Upload to Supabase
#     with open(local_path, "rb") as f:
#         supabase.storage.from_(BUCKET_NAME).upload(safe_name, f.read(), {"cacheControl": "3600"})
#     logging.info(f"Uploaded PDF to Supabase bucket: {safe_name}")
#     return local_path

def download_pdf(url: str) -> str:
    os.makedirs("pdfs", exist_ok=True)
    safe_name = make_safe_name(url)
    local_path = os.path.join("pdfs", safe_name)

    # Delete any existing PDF in the bucket
    try:
        existing_files = supabase.storage.from_(BUCKET_NAME).list()
        for file in existing_files:
            supabase.storage.from_(BUCKET_NAME).remove(file['name'])
            logging.info(f"Deleted old PDF from Supabase: {file['name']}")
    except Exception as e:
        logging.warning(f"Could not list/delete old PDFs: {e}")

    # Download from original URL
    import requests
    logging.info(f"Downloading PDF from {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)

    # Upload new PDF
    with open(local_path, "rb") as f:
        supabase.storage.from_(BUCKET_NAME).upload(safe_name, f.read(), {"cacheControl": "3600"})
    logging.info(f"Uploaded PDF to Supabase bucket: {safe_name}")

    return local_path


def _download_and_reload(pdf_url: str):
    """Download the PDF and reload the RAG model in background."""
    global current_pdf_path, model_loading
    try:
        path = download_pdf(pdf_url)
        current_pdf_path = path
        # reload_rag_model(path)
        logging.info("Background download & RAG reload complete")
    except Exception:
        logging.exception("Background download/reload failed")
    finally:
        model_loading = False

def ensure_pdf_loaded(pdf_url: str):
    """
    If this is a new PDF URL, kick off a background thread
    to download & reload the model, and immediately return.
    """
    global current_pdf_url, model_loading
    if pdf_url != current_pdf_url:
        current_pdf_url = pdf_url
        model_loading   = True
        thread = threading.Thread(
            target=_download_and_reload, args=(pdf_url,), daemon=True
        )
        thread.start()
        logging.info(f"Started background download & reload for {pdf_url}")
