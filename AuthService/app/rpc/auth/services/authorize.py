from tools import check_auth
from rpc.auth.declaration.auth_pb2 import (
    AuthorizeResult,
)

async def AuthorizeInterface(self, request, context):
    result = await check_auth(request.token)
    if result:
        return AuthorizeResult(success=True, userid=result)
    else:
        return AuthorizeResult(success=False)