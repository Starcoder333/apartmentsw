#!/usr/bin/env python3
"""
Secure BBPS adapter for live HESCOM electricity bill lookup.

Configure your authorized BBPS/Bill Aggregator details in environment variables:
  BBPS_API_URL=https://provider.example/api/bill-fetch
  BBPS_API_TOKEN=your-secret-token
  BBPS_BILLER_ID=optional-HESCOM-biller-id

The UI calls: GET /api/hescom/bill?consumer=ACCOUNT_ID
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent

PENDING_KEYS = (
    "billAmount", "billAmountInMinorUnit", "amountDue", "amountPayable",
    "netAmount", "netPayable", "outstandingAmount", "dueAmount", "totalDue",
    "pendingAmount", "amount",
)
PAID_KEYS = ("paid", "paymentStatus", "billStatus", "status")


def decimal_amount(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        amount = float(value)
        return amount if amount >= 0 else None
    text = str(value).replace("₹", "").replace("INR", "").replace("Rs.", "")
    text = re.sub(r"[^0-9.\-]", "", text)
    if not text:
        return None
    try:
        amount = float(text)
        return amount if amount >= 0 else None
    except ValueError:
        return None


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            name = str(key)
            full = f"{prefix}.{name}" if prefix else name
            if isinstance(value, (dict, list)):
                out.update(flatten(value, full))
            else:
                out[name.lower()] = value
                out[full.lower()] = value
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, (dict, list)):
                out.update(flatten(value, f"{prefix}[{index}]"))
    return out


def find_value(data, keys):
    flat = flatten(data)
    for key in keys:
        wanted = key.lower()
        for name, value in flat.items():
            leaf = name.rsplit(".", 1)[-1].rsplit("]", 1)[-1]
            if leaf == wanted or leaf.replace("_", "") == wanted.replace("_", ""):
                return value
    return None


def normalize_bbps_response(payload):
    status_value = find_value(payload, PAID_KEYS)
    status_text = str(status_value or "").upper()
    paid = status_text in ("PAID", "SUCCESS", "SETTLED", "CLOSED")

    raw_amount = find_value(payload, PENDING_KEYS)
    amount = decimal_amount(raw_amount)
    amount = 0.0 if paid else (amount or 0.0)

    consumer = find_value(payload, ("consumerNumber", "accountId", "rrNumber", "accountNumber"))
    units = decimal_amount(find_value(payload, ("units", "unitConsumed", "consumption", "kwh")))
    due_date = find_value(payload, ("dueDate", "billDueDate", "paymentDueDate"))

    if due_date:
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", str(due_date))
        if match:
            due_date = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        else:
            match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", str(due_date))
            if match:
                due_date = f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"

    return {
        "consumerNo": str(consumer or "").strip(),
        "name": "HESCOM Electricity Meter",
        "provider": "HESCOM",
        "amount": amount,
        "units": units,
        "dueDate": str(due_date or ""),
        "status": "PAID" if paid else "PENDING",
        "source": "BBPS live bill fetch",
    }


def fetch_bbps(consumer):
    api_url = os.getenv("BBPS_API_URL", "").strip()
    if not api_url:
        raise RuntimeError("BBPS_API_URL is not configured")

    token = os.getenv("BBPS_API_TOKEN", "").strip()
    biller_id = os.getenv("BBPS_BILLER_ID", "HESCOM").strip()
    body = json.dumps({
        "billerId": biller_id,
        "billerName": "HESCOM",
        "consumerNumber": consumer,
        "accountId": consumer,
    }).encode("utf-8")

    request = urllib.request.Request(api_url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"BBPS provider returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"BBPS provider connection failed: {exc.reason}") from exc


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json(200, {"ok": True, "bbpsConfigured": bool(os.getenv("BBPS_API_URL"))})
            return

        if parsed.path == "/api/hescom/test":
            consumer = parse_qs(parsed.query).get("consumer", ["4509281734"])[0]
            bill = normalize_bbps_response({
                "consumerNumber": consumer,
                "billAmount": 674,
                "units": 412,
                "dueDate": "2026-11-24",
                "status": "PENDING",
            })
            self._json(200, {"ok": True, "bill": bill})
            return

        if parsed.path == "/api/hescom/bill":
            consumer = parse_qs(parsed.query).get("consumer", [""])[0].strip()
            if not re.fullmatch(r"[A-Za-z0-9-]{6,30}", consumer):
                self._json(400, {"ok": False, "error": "Invalid consumer/account number"})
                return
            try:
                if os.getenv("BBPS_TEST_MODE") == "1" and not os.getenv("BBPS_API_URL"):
                    payload = {
                        "consumerNumber": consumer,
                        "billAmount": 674,
                        "units": 412,
                        "dueDate": "2026-11-24",
                        "status": "PENDING",
                    }
                else:
                    payload = fetch_bbps(consumer)
                bill = normalize_bbps_response(payload)
                bill["consumerNo"] = consumer
                self._json(200, {"ok": True, "bill": bill})
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
            return

        self._json(404, {"ok": False, "error": "Not found"})

    def _json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def main():
    port = int(os.getenv("BBPS_LOCAL_PORT", "4180"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"HESCOM BBPS API layer listening on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
