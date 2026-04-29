#!/usr/bin/env python3
"""
wrapper.py - Integracion takeovflow + Telegram
Uso: python3 wrapper.py -d example.com [--min-sev HIGH]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TAKEOVFLOW_PATH = os.environ.get("TAKEOVFLOW_PATH", "./takeovflow.py")
OUTPUT_DIR = os.environ.get("TAKEOVFLOW_OUTPUT", "/tmp/takeovflow_reports")

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEV_LABEL = {
    "CRITICAL": "[CRITICAL]",
    "HIGH": "[HIGH]",
    "MEDIUM": "[MEDIUM]",
    "LOW": "[LOW]",
    "INFO": "[INFO]",
}

def send_telegram(text: str, document_path: str = None) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no definidos.", file=sys.stderr)
        return

    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    url_doc = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"

    requests.post(
        url_msg,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=15,
    )

    if document_path and Path(document_path).exists():
        with open(document_path, "rb") as f:
            requests.post(
                url_doc,
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"document": f},
                timeout=30,
            )

def run_takeovflow(domain: str) -> Path:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        TAKEOVFLOW_PATH,
        "-d",
        domain,
        "--quiet",
        "--json-output",
        "--output-dir",
        OUTPUT_DIR,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    match = re.search(r"JSON\s+:\s+(\S+)", result.stdout)
    if match:
        return Path(match.group(1))

    reports = sorted(
        Path(OUTPUT_DIR).glob("takeovflow_report_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if reports:
        return reports[0]

    raise FileNotFoundError("No se encontro el reporte JSON.")

def build_message(domain: str, data: dict, min_sev: str) -> str:
    threshold = SEV_ORDER.get(min_sev, 1)
    takeovers = data.get("potential_takeovers", [])
    filtered = [
        f for f in takeovers
        if SEV_ORDER.get(f.get("severity", "INFO"), 4) <= threshold
    ]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"<b>takeovflow scan — {domain}</b>",
        f"<i>{now}</i>",
        "",
        f"Subdominios descubiertos: <b>{len(data.get('subdomains', []))}</b>",
        f"Resueltos DNS: <b>{len(data.get('resolved', []))}</b>",
        f"Servicios HTTP: <b>{len(data.get('httpx', []))}</b>",
        f"Posibles takeovers: <b>{len(takeovers)}</b>",
    ]

    if filtered:
        lines += ["", "<b>Hallazgos relevantes:</b>", ""]
        for f in sorted(filtered, key=lambda x: SEV_ORDER.get(x.get("severity"), 4)):
            sev = f.get("severity", "INFO")
            src = f.get("source", "?")
            sub = f.get("subdomain") or f.get("raw", "")[:80]
            cname = f.get("cname", "")
            svc = f.get("service", "")
            label = SEV_LABEL.get(sev, "[INFO]")
            detail = f"{sub} -> {cname} ({svc})" if cname else sub
            lines.append(f"{label} <code>{detail}</code> via {src}")
    else:
        lines += ["", "Sin takeovers detectados en este rango de severidad."]

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", required=True)
    parser.add_argument(
        "--min-sev",
        default="HIGH",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
    )
    parser.add_argument(
        "--send-report",
        action="store_true",
        help="Adjuntar el .md como fichero en Telegram",
    )
    args = parser.parse_args()

    print(f"[*] Lanzando takeovflow para {args.domain}...")
    json_path = run_takeovflow(args.domain)

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    domain_data = summary.get("domains", {}).get(args.domain, {})

    msg = build_message(args.domain, domain_data, args.min_sev)

    md_path = str(json_path).replace(".json", ".md") if args.send_report else None
    send_telegram(msg, document_path=md_path)

    print("[OK] Mensaje enviado a Telegram.")

if __name__ == "__main__":
    main()
