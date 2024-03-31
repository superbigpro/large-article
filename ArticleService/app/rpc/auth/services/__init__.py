from .authorize import authorize
from .getuser import get_user

from rpc.auth.declaration import auth_pb2_grpc
from .authorize import AuthorizeInterface
from .getuser import GetUserInterface

class AuthorizeServicer(auth_pb2_grpc.AuthServiceServicer):
    async def Authorize(self, request, context):
        return await AuthorizeInterface(self, request, context)

    async def GetUser(self, request, context):
        return await GetUserInterface(self, request, context)