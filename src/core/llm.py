from __future__ import annotations
import json, re
import urllib.error
import urllib.request
from src.core.config import (
    LLM_PROVIDER, LLM_MODEL,
    OPENAI_API_KEY, OPENAI_BASE_URL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)

class LLMServiceError(RuntimeError):
    """Raised when the configured LLM provider cannot serve a request."""

def call_llm(prompt: str, system: str = "", temperature: float = 0.2) -> str:
    if LLM_PROVIDER == "openai":
        return _call_openai(prompt, system, temperature)
    elif LLM_PROVIDER == "ollama":
        return _call_ollama(prompt, system, temperature)
    else:
        raise ValueError(f"LLM_PROVIDER không hợp lệ: {LLM_PROVIDER}")

def call_llm_json(prompt: str, system: str = "", temperature: float = 0.1) -> dict:
    raw = call_llm(prompt, system, temperature)
    return _parse_json(raw)

def _call_openai(prompt, system, temperature):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=temperature)
    return resp.choices[0].message.content.strip()

def _call_ollama(prompt, system, temperature):
    payload = json.dumps({
        "model": OLLAMA_MODEL, "prompt": prompt,
        "system": system, "stream": False,
        "options": {"temperature": temperature},
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read()).get("response", "").strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        if exc.code == 404:
            available = _ollama_models()
            suffix = f" Model đã cài: {', '.join(available)}." if available else ""
            raise LLMServiceError(
                f"Không tìm thấy model Ollama '{OLLAMA_MODEL}'. "
                f"Chạy `ollama pull {OLLAMA_MODEL}` hoặc đổi `OLLAMA_MODEL` trong `.env`."
                f"{suffix}"
            ) from exc
        raise LLMServiceError(
            f"Ollama trả về lỗi HTTP {exc.code} tại {OLLAMA_BASE_URL}. "
            f"{detail or exc.reason}"
        ) from exc
    except urllib.error.URLError as exc:
        raise LLMServiceError(
            f"Không thể kết nối tới Ollama tại {OLLAMA_BASE_URL}. "
            "Hãy cài đặt hoặc mở Ollama, chạy `ollama serve` nếu cần, "
            f"và tải model bằng `ollama pull {OLLAMA_MODEL}`."
        ) from exc
    except TimeoutError as exc:
        raise LLMServiceError(
            f"Ollama không phản hồi kịp thời tại {OLLAMA_BASE_URL}. "
            "Kiểm tra dịch vụ và thử lại."
        ) from exc
    except json.JSONDecodeError as exc:
        raise LLMServiceError("Ollama trả về dữ liệu không hợp lệ.") from exc

def _ollama_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=5) as response:
            payload = json.loads(response.read())
        return [model.get("name", "") for model in payload.get("models", []) if model.get("name")]
    except Exception:
        return []

def _parse_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "Không parse được JSON", "raw": text}
