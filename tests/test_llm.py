import httpx
import pytest
import config
import llm


@pytest.fixture(autouse=True)
def cfg(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "k")
    monkeypatch.setattr(config, "LLM_MODEL", "m")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def run(monkeypatch, handler, capture=None):
    real = httpx.Client

    def wrapped(handler=handler, **kw):
        def h(req):
            if capture is not None:
                capture.append(req)
            return handler(req)
        return real(transport=httpx.MockTransport(h), **kw)
    monkeypatch.setattr(httpx, "Client", wrapped)
    return llm.LLMClient().generate([{"role": "user", "content": "hi"}])


def ok(text):
    return lambda r: httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def test_success(monkeypatch):
    assert run(monkeypatch, ok(" hello ")) == "hello"


def test_retry_once_on_503(monkeypatch):
    n = {"c": 0}

    def h(r):
        n["c"] += 1
        return httpx.Response(503) if n["c"] == 1 else ok("fine")(r)
    assert run(monkeypatch, h) == "fine" and n["c"] == 2


def test_retry_once_on_timeout_then_error(monkeypatch):
    n = {"c": 0}

    def h(r):
        n["c"] += 1
        raise httpx.ReadTimeout("t")
    with pytest.raises(llm.LLMError):
        run(monkeypatch, h)
    assert n["c"] == 2


def test_no_retry_on_401(monkeypatch):
    n = {"c": 0}

    def h(r):
        n["c"] += 1
        return httpx.Response(401)
    with pytest.raises(llm.LLMError):
        run(monkeypatch, h)
    assert n["c"] == 1


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_answer_is_llm_error(monkeypatch, content):
    with pytest.raises(llm.LLMError):
        run(monkeypatch, ok(content))


def test_bad_json_is_llm_error(monkeypatch):
    with pytest.raises(llm.LLMError):
        run(monkeypatch, lambda r: httpx.Response(200, text="<html>"))


def test_token_param_is_configurable(monkeypatch):
    import json
    seen = []
    monkeypatch.setattr(config, "LLM_TOKEN_PARAM", "max_completion_tokens")
    run(monkeypatch, ok("x"), capture=seen)
    body = json.loads(seen[0].content)
    assert "max_completion_tokens" in body and "max_tokens" not in body


def test_missing_config_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    with pytest.raises(llm.LLMError):
        llm.LLMClient()
