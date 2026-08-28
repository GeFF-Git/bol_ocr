import json, os, PIL.Image
from json_repair import repair_json
from extractors.base import BaseExtractor
from prompts.extraction_prompt import EXTRACTION_PROMPT

class GeminiExtractor(BaseExtractor):
    def __init__(self):
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY", "")
        if not key: raise EnvironmentError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    def extract(self, image_path: str) -> dict:
        import google.generativeai as genai
        img = PIL.Image.open(image_path)
        res = self.model.generate_content(
            [EXTRACTION_PROMPT, img],
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        raw = res.text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        return json.loads(repair_json(raw))
