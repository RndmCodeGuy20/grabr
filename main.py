import os
import re
import requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from google.cloud import storage

# === GCS Setup ===
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".secrets/bucket_secret.json"
bucket_name = "design_assets"
gcs_client = storage.Client()
bucket = gcs_client.bucket(bucket_name)

# === FastAPI Setup ===
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# === Routes ===

@app.get("/", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/scrape", response_class=HTMLResponse)
def scrape_and_upload(request: Request, url: str = Form(...)):
    try:
        url_name = urlparse(url).netloc
        if not url_name:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": "Invalid URL."
            })
        if not url.startswith(("http://", "https://")):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": "URL must start with http:// or https://."
            })
        if not re.match(r"^(http|https)://[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})", url):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": "Invalid URL format."
            })
        
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        asset_urls = set()

        for tag in soup.find_all(["img", "link", "script"]):
            src = tag.get("src") or tag.get("href")
            if src:
                full_url = urljoin(url, src)
                if re.search(r"\.(png|jpe?g|gif|svg|woff2?|ttf|otf)$", full_url, re.IGNORECASE):
                    asset_urls.add(full_url)

        uploaded_files = []

        parsed_url = urlparse(url)
        domain_folder = parsed_url.netloc  # e.g., "google.com"

        for asset_url in asset_urls:
            try:
                r = requests.get(asset_url, timeout=10)
                if r.status_code == 200:
                    path = urlparse(asset_url).path
                    ext = os.path.splitext(path)[1].lower()

                    if ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
                        subfolder = "images"
                    elif ext in [".woff", ".woff2", ".ttf", ".otf", ".eot"]:
                        subfolder = "fonts"
                    else:
                        subfolder = "misc"

                    filename = os.path.basename(path)
                    gcs_path = f"{domain_folder}/{subfolder}/{filename}"

                    print(f"Uploading {asset_url} to {gcs_path}")

                    blob = bucket.blob(gcs_path)
                    blob.upload_from_string(r.content)
                    uploaded_files.append(gcs_path)
            except Exception as e:
                print(f"Error uploading {asset_url}: {e}")

        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": f"Scraped and uploaded {len(uploaded_files)} assets."
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": f"Error: {str(e)}"
        })
