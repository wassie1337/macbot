from agent.router import Router


class DummySettings:
    ollama_model_fast = "fast-model"
    ollama_model_chat = "chat-model"
    ollama_model_code = "code-model"
    ollama_model_default = "default-model"
    num_ctx = 2048
    num_predict = 220
    temperature = 0.6
    api_key = ""
    enable_stt = False


class DummyProvider:
    def __init__(self):
        self.last_options = None

    def chat(self, messages, options):
        self.last_options = options
        return "ok"


class DummyApiProvider(DummyProvider):
    pass


def test_resolve_model_for_mode():
    r = Router(DummySettings(), DummyProvider(), DummyApiProvider(), [])
    assert r.resolve_model_for_mode("fast") == "fast-model"
    assert r.resolve_model_for_mode("chat") == "chat-model"
    assert r.resolve_model_for_mode("code") == "code-model"


def test_generate_reply_uses_state_model():
    p = DummyProvider()
    r = Router(DummySettings(), p, DummyApiProvider(), [])
    state = {"mode": "fast", "model": "override-model"}
    out = r.generate_reply("hello", state)
    assert out == "ok"
    assert p.last_options["model"] == "override-model"
