import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.chat import ChatResponse, ChatSourceResponse, ChatTimingResponse

CHAT_URL = "/api/v1/repositories/{repository_id}/chat"


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    response = await client.post(
        CHAT_URL.format(repository_id=uuid4()),
        json={"message": "Explain auth"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_empty_message(authenticated_client):
    repo_id = uuid4()
    with patch(
        "app.api.v1.endpoints.repositories._build_chat_service",
    ) as mock_build:
        mock_service = AsyncMock()
        from app.services.exceptions import ValidationError

        mock_service.answer = AsyncMock(side_effect=ValidationError("Message cannot be empty"))
        mock_build.return_value = mock_service
        response = await authenticated_client.post(
            CHAT_URL.format(repository_id=repo_id),
            json={"message": "   "},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_success_json(authenticated_client):
    repo_id = uuid4()
    mock_response = ChatResponse(
        answer="Authentication uses JWT.",
        sources=[
            ChatSourceResponse(
                chunk_id=uuid4(),
                file_path="auth.py",
                symbol_name="validate",
                chunk_type="function",
            )
        ],
        execution_time_ms=95.5,
        timing=ChatTimingResponse(
            retrieval_ms=10,
            prompt_build_ms=1,
            llm_ms=80,
            total_ms=95.5,
        ),
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_chat_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.answer = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.post(
            CHAT_URL.format(repository_id=repo_id),
            json={"message": "How does authentication work?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Authentication uses JWT."
    assert len(data["sources"]) == 1


@pytest.mark.asyncio
async def test_chat_stream_sse(authenticated_client):
    repo_id = uuid4()

    async def fake_stream(**kwargs):
        yield {"type": "token", "content": "Hello"}
        yield {
            "type": "done",
            "sources": [],
            "execution_time_ms": 50.0,
            "timing": {
                "retrieval_ms": 1,
                "prompt_build_ms": 1,
                "llm_ms": 40,
                "total_ms": 50,
            },
            "token_usage": None,
        }

    with patch(
        "app.api.v1.endpoints.repositories._build_chat_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.stream_answer = fake_stream
        mock_build.return_value = mock_service
        response = await authenticated_client.post(
            CHAT_URL.format(repository_id=repo_id),
            json={"message": "Hello", "stream": True},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    body = response.text
    assert "data:" in body
    assert "token" in body
    assert "done" in body
    assert json.loads(body.split("data: ")[1].split("\n\n")[0])["type"] == "token"
