import re
from datetime import date
from typing import Optional, Dict, Tuple

DATE_PATTERNS = [
    r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b",      # dd/mm/yyyy or dd-mm-yyyy
    r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b",      # yyyy-mm-dd
]

AMOUNT_PATTERNS = [
    r"\btotal\s*[:\-]?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\b",
    r"\bamount\s*[:\-]?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\b",
    r"\b([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))\b",
]

CATEGORY_RULES: Dict[str, str] = {
    "uber": "Travel",
    "taxi": "Travel",
    "fuel": "Travel",
    "petrol": "Travel",
    "flight": "Travel",
    "cafe": "Meals & Entertainment",
    "restaurant": "Meals & Entertainment",
    "coffee": "Meals & Entertainment",
    "officeworks": "Office Supplies",
    "staples": "Office Supplies",
    "paper": "Office Supplies",
    "electricity": "Utilities",
    "internet": "Utilities",
    "phone": "Utilities",
}

def _parse_amount_cents(text: str) -> Optional[int]:
    t = text.lower().replace("aud", "").replace(" ", "")
    found = []
    for pat in AMOUNT_PATTERNS:
        for m in re.finditer(pat, t, flags=re.IGNORECASE):
            num = m.group(1).replace(",", "")
            try:
                found.append(round(float(num) * 100))
            except ValueError:
                pass
    return max(found) if found else None

def _parse_date(text: str) -> Optional[date]:
    for pat in DATE_PATTERNS:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            continue
        try:
            if len(m.groups()) == 3 and len(m.group(1)) == 2:
                dd, mm, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                yyyy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return date(yyyy, mm, dd)
        except Exception:
            continue
    return None

def _parse_vendor(text: str) -> Optional[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ignore = {"tax invoice", "invoice", "receipt", "abn", "gst", "total"}
    for i in range(min(6, len(lines))):
        l = re.sub(r"[^a-zA-Z0-9 &@'\-\.]", " ", lines[i]).strip()
        low = l.lower()
        if not l or any(k in low for k in ignore):
            continue
        if len(l) >= 3:
            return " ".join(l.split())
    return None

def _infer_category(vendor: Optional[str], desc: Optional[str]) -> Optional[str]:
    base = " ".join([vendor or "", desc or ""]).lower()
    for k, cat in CATEGORY_RULES.items():
        if k in base:
            return cat
    return None

def parse_receipt(text: str) -> Tuple[Optional[date], Optional[int], Optional[str], Optional[str], Optional[str]]:
    if not text:
        return None, None, None, None, None
    d = _parse_date(text)
    amt = _parse_amount_cents(text)
    vendor = _parse_vendor(text)
    desc = None
    cat = _infer_category(vendor, desc)
    return d, amt, vendor, desc, cat
