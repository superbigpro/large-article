from grpc import aio
from rpc.auth.declaration import auth_pb2_grpc
from rpc.auth.services import AuthorizeServicer
import os


class gRPCServer:
    @staticmethod
    async def run():
        server = aio.server()

        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthorizeServicer(), server)

        article_port = os.getenv("ARTICLE_PORT", "50002")
        server.add_insecure_port(f"[::]:{article_port}")
        await server.start()
        print("[GRPC] Server is running on port", article_port)
        await server.wait_for_termination()