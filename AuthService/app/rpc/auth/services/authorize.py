from tools import check_auth
from ..client import generate_client
from rpc.auth.declaration.auth.auth_pb2 import (
    AuthorizeResult,
)

async def AuthorizeInterface(self, request, context):
    result = check_auth(request.token)
    if result:
        return AuthorizeResult(success=True, userid=result)
    else:
        return AuthorizeResult(success=False)