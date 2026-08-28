from extractors.base import BaseExtractor

def get_extractor(engine: str) -> BaseExtractor:
    eng = engine.strip().lower()
    if eng == "ollama":
        from extractors.ollama_extractor import OllamaExtractor
        return OllamaExtractor()
    if eng == "gemini":
        from extractors.gemini_extractor import GeminiExtractor
        return GeminiExtractor()
    raise ValueError(f"Unknown engine: {engine}")
