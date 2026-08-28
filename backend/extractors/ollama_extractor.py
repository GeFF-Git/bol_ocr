import base64, json, os, httpx
from json_repair import repair_json
from extractors.base import BaseExtractor
from prompts.extraction_prompt import EXTRACTION_PROMPT

class OllamaExtractor(BaseExtractor):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "minicpm-v")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "360"))

    def extract(self, image_path: str) -> dict:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "model": self.model,
            "prompt": EXTRACTION_PROMPT,
            "images": [b64],
            "stream": False,
            "format": "json"
        }
        res = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        res.raise_for_status()
        raw = res.json().get("response", "")
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        return json.loads(repair_json(raw))
