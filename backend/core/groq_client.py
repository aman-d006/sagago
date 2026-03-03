import httpx
import json
from types import SimpleNamespace
from .config import settings


class GroqLLM:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        base = settings.GROQ_BASE_URL.rstrip("/")
        
        if base.endswith("/v1") or base.endswith("/openai/v1"):
            self.base_url = f"{base}/chat/completions"
        else:
            self.base_url = f"{base}/chat/completions"

    def invoke(self, prompt_text: str):
        try:
            if not isinstance(prompt_text, str):
                if hasattr(prompt_text, "to_string"):
                    prompt_text = prompt_text.to_string()
                elif hasattr(prompt_text, "to_messages"):
                    msgs = prompt_text.to_messages()
                    parts = []
                    for m in msgs:
                        if hasattr(m, "content"):
                            parts.append(m.content)
                        else:
                            parts.append(str(m))
                    prompt_text = "\n".join(parts)
                elif hasattr(prompt_text, "content"):
                    prompt_text = prompt_text.content
                else:
                    prompt_text = str(prompt_text)
        except Exception:
            prompt_text = str(prompt_text)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }

        with httpx.Client(timeout=60, trust_env=True) as client:
            try:
                resp = client.post(self.base_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                content = None
                if isinstance(data, dict):
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            content = choice["message"]["content"]
                        elif "text" in choice:
                            content = choice["text"]
                    elif "output" in data and isinstance(data["output"], list) and data["output"]:
                        content = data["output"][0]
                    elif "generations" in data and isinstance(data["generations"], list) and data["generations"]:
                        first = data["generations"][0]
                        content = first.get("text") or first.get("content")
                
                if content is None:
                    content = resp.text
                    
                return SimpleNamespace(content=content)
                
            except httpx.ConnectError as e:
                raise RuntimeError(
                    "Network error contacting Groq API (connect error). "
                    "Check internet, DNS, VPN/proxy, or host reachability. "
                    f"Details: {e}"
                ) from e
            except httpx.ReadTimeout as e:
                raise RuntimeError(f"Timeout contacting Groq API: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Groq API returned HTTP error: {e.response.status_code} - {e.response.text}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error contacting Groq API: {e}") from e


class MockLLM:
    def invoke(self, prompt_text: str):
        story = {
            "title": "Fallback Story",
            "rootNode": {
                "content": "A short fallback story generated locally because the LLM was unreachable.",
                "isEnding": True,
                "isWinningEnding": False,
                "options": None
            }
        }
        return SimpleNamespace(content=json.dumps(story))