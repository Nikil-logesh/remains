import httpx
import pytest

from app.llm import NvidiaGemmaLLM, extract_json


def test_extract_json_is_strict():
    assert extract_json('{"description": null}') == {"description": None}
    with pytest.raises(RuntimeError):
        extract_json("not json")


@pytest.mark.asyncio
async def test_nvidia_sends_bearer_header():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok": true}'}}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await NvidiaGemmaLLM(
            api_key="test-secret", model="google/gemma-4-31b-it", client=client
        ).complete("return JSON")

    assert result == {"ok": True}
    assert seen["authorization"] == "Bearer " + "test-secret"
