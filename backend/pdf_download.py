# pdf_utils.py
import os
import re
import logging
import threading
import requests

# from rag import reload_rag_model   # wherever your reload logic lives

# global state
current_pdf_url = None
current_pdf_path = None
model_loading   = False

def download_pdf(url: str, timeout: int = 15) -> str:
    os.makedirs("pdfs", exist_ok=True)
    safe_name = re.sub(r'\W+', '_', url)[:50] + ".pdf"
    local_path = os.path.join("pdfs", safe_name)
    if os.path.exists(local_path):
        return local_path
    logging.info(f"Downloading PDF from {url}")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)
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
