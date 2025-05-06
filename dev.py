import subprocess
from pathlib import Path

def ensure_cert(cert_file: Path, key_file: Path):
    if not cert_file.exists() or not key_file.exists():
        from main import generate_ssl_cert
        generate_ssl_cert(cert_file, key_file)

if __name__ == "__main__":
    cert_file = Path.home() / "TKDiscRipper" / "config" / "server.crt"
    key_file = Path.home() / "TKDiscRipper" / "config" / "server.key"

    ensure_cert(cert_file, key_file)

    subprocess.run([
        "uvicorn", "main:app",
        "--reload",
        "--host", "::",
        "--port", "8000",
        "--ssl-certfile", str(cert_file),
        "--ssl-keyfile", str(key_file)
    ])