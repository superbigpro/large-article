from ..client import generate_client
from rpc.auth.declaration.auth.auth_pb2 import AuthorizeRequest

async def authorize(token: str) -> int:
    client = await generate_client()

    response = await client.Authorize(AuthorizeRequest(token=token))
    # response = await check_auth(token)
    return response.userid if response.userid else None