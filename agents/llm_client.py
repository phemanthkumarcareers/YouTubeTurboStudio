"""
Unified LLM Client for YouTube Turbo Studio
Supports Google Gemini (with multi-model fallback chain) and OpenAI-compatible endpoints (DeepSeek, Groq, Ollama, etc.)
"""
import json
import time
import requests
from config import load_config
from core.logger import log_info, log_warn, log_error

# Gemini fallback model chain — ordered: best quality → fastest (verified working 2026-10-03)
# gemini-2.5-flash / gemini-2.5-flash-lite return 404 with this API key
# gemini-pro-latest has free-tier quota exhausted
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest"
]


def test_gemini_connection(api_key: str, model_name: str = "gemini-2.5-flash") -> tuple[bool, str]:
    """Test a Google Gemini API Key."""
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key.strip())
        
        quota_hit = False
        # Test models in chain if the preferred one has quota issues
        test_models = [model_name] + [m for m in GEMINI_MODELS if m != model_name]
        for m in test_models:
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents="Reply with: OK",
                    config=types.GenerateContentConfig(max_output_tokens=10)
                )
                if resp and resp.text:
                    return True, f"Connected successfully! (Model: {m})"
            except Exception as sub_e:
                if any(x in str(sub_e) for x in ["404", "not found", "NOT_FOUND", "503", "UNAVAILABLE", "high demand"]):
                    continue
                if any(x in str(sub_e) for x in ["429", "quota", "RESOURCE_EXHAUSTED"]):
                    quota_hit = True
                    continue
                raise sub_e

        if quota_hit:
            return True, "Key is authentic & valid! (Note: Current free quota is temporarily exhausted. It will reset or you can enable billing at aistudio.google.com)"
        return False, "Could not reach tested Gemini models. Please verify API key."
    except Exception as e:
        return False, f"Gemini Error: {str(e)}"


def test_openai_connection(api_key: str, base_url: str = "https://api.openai.com/v1", model_name: str = "gpt-4o-mini") -> tuple[bool, str]:
    """Test an OpenAI-compatible API endpoint."""
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip(), base_url=base_url.strip() if base_url else None)
        resp = client.chat.completions.create(
            model=model_name or "gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with: OK"}],
            max_tokens=10
        )
        content = resp.choices[0].message.content
        return True, f"Connected successfully! Response: {content.strip()}"
    except Exception as e:
        return False, f"OpenAI Error: {str(e)}"


def _generate_gemini(prompt: str, config: dict, json_mode: bool = False) -> str:
    from google import genai
    from google.genai import types

    key = config.get("gemini_api_key", "").strip()
    if not key:
        raise ValueError("Google Gemini API Key is missing. Configure it in the Settings tab.")

    client = genai.Client(api_key=key)
    pref_model = config.get("gemini_model", "gemini-2.5-flash")
    chain = [pref_model] + [m for m in GEMINI_MODELS if m != pref_model]

    last_error = None
    for model in chain:
        for attempt in range(2):
            try:
                gen_config = types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json" if json_mode else "text/plain"
                )
                log_info(f"Generating content with Gemini model: {model}...")
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=gen_config
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                # Check if quota/rate-limited or not found -> fallback
                if any(k in err_str for k in ["429", "quota", "RESOURCE_EXHAUSTED", "404", "not found", "503", "UNAVAILABLE"]):
                    log_warn(f"Model {model} hit issue: {err_str[:80]}... Trying next model in chain.")
                    break
                else:
                    log_error(f"Gemini API error: {err_str}")
                    raise e
    raise RuntimeError(f"All Gemini models in fallback chain failed. Last error: {last_error}")


def _generate_groq(prompt: str, config: dict, json_mode: bool = False) -> str:
    """Generate using Groq REST API directly via requests (no openai package required)."""
    key = config.get("groq_api_key", "").strip()
    if not key:
        raise ValueError("Groq API Key is missing. Get a free key at console.groq.com and configure it in API Keys tab.")
    model = config.get("groq_model", "openai/gpt-oss-120b").strip() or "openai/gpt-oss-120b"
    log_info(f"Generating content with Groq ({model})...")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(url, headers=headers, json=payload, timeout=45)
    if resp.status_code != 200:
        err_msg = resp.text
        try:
            err_json = resp.json()
            err_msg = err_json.get("error", {}).get("message", resp.text)
        except Exception:
            pass
        raise RuntimeError(f"Groq API Error ({resp.status_code}): {err_msg}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def test_groq_connection(api_key: str, model: str = "openai/gpt-oss-120b") -> tuple[bool, str]:
    """Test a Groq API key using direct HTTP request."""
    if not api_key or not api_key.strip():
        return False, "Groq API key cannot be empty"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Reply with: OK"}],
            "max_tokens": 10
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return True, f"Groq connected successfully! Model: {model} (Response: {reply})"
        else:
            err_text = resp.text
            try:
                err_text = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            return False, f"Groq Error ({resp.status_code}): {err_text}"
    except Exception as e:
        return False, f"Groq connection failed: {str(e)}"


def _generate_openai(prompt: str, config: dict, json_mode: bool = False) -> str:
    """Generate content via OpenAI or OpenAI-compatible endpoint."""
    from openai import OpenAI
    key = config.get("openai_api_key", "").strip()
    if not key:
        raise ValueError("OpenAI API Key is missing. Configure it in the Settings tab.")
    base_url = config.get("openai_base_url", "https://api.openai.com/v1").strip() or "https://api.openai.com/v1"
    model = config.get("openai_model", "gpt-4o-mini").strip() or "gpt-4o-mini"
    client = OpenAI(api_key=key, base_url=base_url)
    log_info(f"Generating content with OpenAI ({model})...")
    kwargs = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.8}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content.strip()


def generate(prompt: str, json_mode: bool = False) -> str:
    """Unified text generation routing with cross-provider fallback across Gemini, Groq, and OpenAI."""
    cfg = load_config()
    provider = cfg.get("llm_provider", "gemini").lower()

    if provider == "groq":
        try:
            return _generate_groq(prompt, cfg, json_mode=json_mode)
        except Exception as e:
            if cfg.get("gemini_api_key"):
                log_warn(f"Groq failed ({e}). Auto-falling back to Google Gemini...")
                return _generate_gemini(prompt, cfg, json_mode=json_mode)
            raise e
    elif provider == "openai":
        try:
            return _generate_openai(prompt, cfg, json_mode=json_mode)
        except Exception as e:
            if cfg.get("gemini_api_key"):
                log_warn(f"OpenAI failed ({e}). Auto-falling back to Google Gemini...")
                return _generate_gemini(prompt, cfg, json_mode=json_mode)
            raise e
    else:
        # Default to Gemini with automatic cross-provider fallback to Groq or OpenAI
        try:
            return _generate_gemini(prompt, cfg, json_mode=json_mode)
        except Exception as e:
            if cfg.get("groq_api_key"):
                log_warn(f"Gemini quota/error ({e}). Auto-falling back to Groq LLaMA 3.3...")
                return _generate_groq(prompt, cfg, json_mode=json_mode)
            elif cfg.get("openai_api_key"):
                log_warn(f"Gemini quota/error ({e}). Auto-falling back to OpenAI...")
                return _generate_openai(prompt, cfg, json_mode=json_mode)
            raise e
