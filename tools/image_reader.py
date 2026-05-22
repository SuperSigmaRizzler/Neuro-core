from providers.gemini import analyze_image_gemini
from tools.ocr_reader import ocr_image


class ImageReadError(Exception):
    pass


def analyze_image(path: str, prompt: str = "") -> str:
    vision_error = None

    try:
        vision = analyze_image_gemini(
            path,
            prompt or "Analyze this image clearly and answer the user's request."
        )

        if vision.strip():
            return "Vision analysis:\n" + vision.strip()

    except Exception as e:
        vision_error = str(e)

    try:
        text = ocr_image(path)

        return (
            "Image OCR text:\n"
            f"{text}\n\n"
            "Note: Full image understanding failed, so OCR fallback was used.\n"
            f"Vision error: {vision_error}"
        )

    except Exception as e:
        raise ImageReadError(
            f"Image analysis failed. Vision error: {vision_error}. OCR error: {e}"
        )
