from grpc import aio
from rpc.auth.declaration import auth_pb2_grpc
from rpc.auth.services import AuthorizeServicer
import dotenv
import os

dotenv.load_dotenv()

GRPC_PORT = os.getenv("GRPC_PORT")

class gRPCServer:
    @staticmethod
    async def run():
        server = aio.server()

        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthorizeServicer(), server)

        server.add_insecure_port(f"[::]:{GRPC_PORT}")
        await server.start()
        print("[GRPC] Server is running on port", GRPC_PORT)
        await server.wait_for_termination()