import requests

def ocr_space_image(image_bytes: bytes, api_key: str) -> str:
    resp = requests.post(
        "https://api.ocr.space/parse/image",
        headers={"apikey": api_key},
        files={"file": ("receipt.jpg", image_bytes)},
        data={"language": "eng", "isOverlayRequired": False},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    texts = [r.get("ParsedText", "") for r in data.get("ParsedResults", [])]
    return "\n".join(texts).strip()
