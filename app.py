from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import FileResponse, PlainTextResponse
import os, re, shutil, tempfile, subprocess

API_KEY = os.getenv("API_KEY")  # optional: Header x-api-key muss passen

app = FastAPI()

def extract_shortcode(url: str) -> str:
    m = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)/?', url)
    if not m:
        raise ValueError("No shortcode in URL")
    return m.group(1)

@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"

@app.get("/download")
def download(url: str = Query(...), x_api_key: str | None = Header(default=None)):
    if os.getenv("API_KEY") and x_api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Unauthorized")

    tmpdir = tempfile.mkdtemp(prefix="ig_")
    try:
        shortcode = extract_shortcode(url)
        cmd = [
            "instaloader",
            "--no-compress-json", "--no-captions", "--no-profile-pic",
            f"--dirname-pattern={tmpdir}",
            f"--filename-pattern={shortcode}",
            "--", url
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise HTTPException(400, f"Instaloader error: {proc.stderr.strip()}")

        mp4 = os.path.join(tmpdir, f"{shortcode}.mp4")
        if not os.path.exists(mp4):
            raise HTTPException(404, "Video not found (is it public?)")

        return FileResponse(mp4, media_type="video/mp4", filename=f"{shortcode}.mp4")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
