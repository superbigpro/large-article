from ..client import generate_client
from ..declaration.auth_pb2 import AuthorizeRequest
from tools import check_auth

async def authorize(token: str) -> int:
    client = await generate_client()

    # response = await client.Authorize(AuthorizeRequest(token=token))
    response = await check_auth(token)
    return response.userid if response.userid else None