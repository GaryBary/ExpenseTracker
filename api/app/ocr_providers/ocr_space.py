import requests
import logging

logger = logging.getLogger(__name__)

def ocr_space_image(image_bytes: bytes, api_key: str) -> str:
    try:
        resp = requests.post(
            "https://api.ocr.space/parse/image",
            headers={"apikey": api_key},
            files={"file": ("receipt.jpg", image_bytes)},
            data={"language": "eng", "isOverlayRequired": False},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Check for OCR.space API errors
        if not data.get("IsErroredOnProcessing", True):
            logger.error(f"OCR.space processing error: {data}")
            return ""
            
        if "ParsedResults" not in data or not data["ParsedResults"]:
            logger.error(f"No parsed results from OCR.space: {data}")
            return ""
            
        texts = [r.get("ParsedText", "") for r in data.get("ParsedResults", [])]
        result = "\n".join(texts).strip()
        
        if not result:
            logger.warning(f"OCR returned empty text. Full response: {data}")
            
        return result
        
    except Exception as e:
        logger.error(f"OCR.space API error: {e}")
        return ""
