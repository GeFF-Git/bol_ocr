import base64, json, logging, os, time, httpx
from json_repair import repair_json
from extractors.base import BaseExtractor
from prompts.extraction_prompt import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class OllamaExtractor(BaseExtractor):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "minicpm-v")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "600"))

    def extract(self, image_path: str, prompt: str = None) -> dict:
        used_prompt = prompt or EXTRACTION_PROMPT
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        payload = {
            "model": self.model,
            "prompt": used_prompt,
            "images": [b64],
            "stream": False,
            "format": "json"
        }

        # Attempt extraction with retry for transient runner initialization / wake-up states
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                res = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if res.status_code != 200:
                    error_msg = res.text
                    try:
                        err_json = res.json()
                        if "error" in err_json:
                            error_msg = err_json["error"]
                    except Exception:
                        pass
                    
                    if attempt < max_attempts and res.status_code in (400, 500, 503):
                        logger.warning(f"Ollama returned {res.status_code} ({error_msg}). Retrying in 3s (attempt {attempt}/{max_attempts})...")
                        time.sleep(3)
                        continue

                    raise RuntimeError(f"Ollama error ({res.status_code}): {error_msg}")

                raw = res.json().get("response", "")
                if not raw:
                    raise ValueError("Ollama returned an empty response.")
                if raw.startswith("```"):
                    raw = "\n".join(raw.split("\n")[1:-1])
                return json.loads(repair_json(raw))

            except httpx.ConnectError:
                raise RuntimeError(f"Could not connect to Ollama at {self.base_url}. Please ensure the Ollama service is running (`ollama serve`).")
            except httpx.TimeoutException:
                raise TimeoutError(f"Ollama inference timed out after {self.timeout}s.")

