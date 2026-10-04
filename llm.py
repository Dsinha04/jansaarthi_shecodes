"""Provider-independent LLM API client (OpenAI-compatible chat completions).

Set LLM_API_URL, LLM_API_KEY and LLM_MODEL in the environment.
Newer OpenAI models want "max_completion_tokens" instead of "max_tokens":
set LLM_TOKEN_PARAM=max_completion_tokens for those.
"""
import time
import httpx
import config


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self):
        if not config.LLM_API_KEY:
            raise LLMError("LLM_API_KEY is not configured")
        if not config.LLM_MODEL:
            raise LLMError("LLM_MODEL is not configured")

    def generate(self, messages):
        headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.LLM_MODEL,
            "messages": messages,
            "temperature": config.LLM_TEMP,
            config.LLM_TOKEN_PARAM: config.LLM_MAX_TOKENS,
        }
        last = None
        for attempt in range(2):                      # one retry for flaky networks / rate limits
            try:
                with httpx.Client(timeout=config.LLM_TIMEOUT) as client:
                    r = client.post(config.LLM_API_URL, headers=headers, json=payload)
                if r.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(1.5)
                    continue
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise LLMError("LLM returned an empty answer")
                return content.strip()
            except LLMError:
                raise
            except httpx.TransportError as exc:      # timeouts, connection errors
                last = exc
                if attempt == 0:
                    time.sleep(1.5)
                    continue
            except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
                last = exc
                break
        raise LLMError(f"LLM API request failed: {last}")
