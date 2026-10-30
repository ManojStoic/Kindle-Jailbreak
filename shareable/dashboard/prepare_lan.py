"""Generate a single-server TLS identity and bearer token for the local LAN."""
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
import json
import secrets
import socket

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from dashboard.lan import LAN_DIR


def local_address():
    # Connect on a UDP socket selects a route without transmitting a packet.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("1.1.1.1", 80))
        addr = sock.getsockname()[0]
    if not ip_address(addr).is_private or ip_address(addr).is_loopback:
        raise ValueError("No suitable private local IPv4 address")
    return addr


def main():
    if LAN_DIR.exists() and any(LAN_DIR.iterdir()):
        raise SystemExit("LAN identity already exists; not replacing it")
    LAN_DIR.mkdir(parents=True, exist_ok=True)
    addr = local_address()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "KindleLab Local Dashboard")])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=730))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(key, hashes.SHA256()))
    (LAN_DIR / "server-key.pem").write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    (LAN_DIR / "server-cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (LAN_DIR / "token.txt").write_text(secrets.token_urlsafe(32), encoding="ascii")
    (LAN_DIR / "config.json").write_text(json.dumps({"host": addr, "port": 8766}), encoding="utf-8")
    print("Private LAN identity and token created; values withheld.")


if __name__ == "__main__":
    main()
