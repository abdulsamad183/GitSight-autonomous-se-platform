import pytest

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"
LOGOUT_URL = "/api/v1/auth/logout"


@pytest.mark.asyncio
async def test_register_success(db_client, register_payload):
    response = await db_client.post(REGISTER_URL, json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == register_payload["username"]
    assert data["email"] == register_payload["email"]
    assert "id" in data
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(db_client, register_payload):
    await db_client.post(REGISTER_URL, json=register_payload)
    duplicate = {**register_payload, "username": "otheruser"}
    response = await db_client.post(REGISTER_URL, json=duplicate)
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(db_client, register_payload):
    await db_client.post(REGISTER_URL, json=register_payload)
    duplicate = {**register_payload, "email": "other@example.com"}
    response = await db_client.post(REGISTER_URL, json=duplicate)
    assert response.status_code == 409
    assert "username" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(db_client, register_payload):
    await db_client.post(REGISTER_URL, json=register_payload)
    response = await db_client.post(
        LOGIN_URL,
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert response.status_code == 200
    assert response.json()["email"] == register_payload["email"]
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_credentials(db_client, register_payload):
    await db_client.post(REGISTER_URL, json=register_payload)
    response = await db_client.post(
        LOGIN_URL,
        json={"email": register_payload["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(db_client, register_payload):
    register_response = await db_client.post(REGISTER_URL, json=register_payload)
    cookies = register_response.cookies
    response = await db_client.get(ME_URL, cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == register_payload["username"]
    assert data["email"] == register_payload["email"]


@pytest.mark.asyncio
async def test_me_unauthenticated(db_client):
    response = await db_client.get(ME_URL)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(db_client, register_payload):
    register_response = await db_client.post(REGISTER_URL, json=register_payload)
    cookies = register_response.cookies
    logout_response = await db_client.post(LOGOUT_URL, cookies=cookies)
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out"

    me_response = await db_client.get(ME_URL, cookies=logout_response.cookies)
    assert me_response.status_code == 401
