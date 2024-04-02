from grpc import aio
from rpc.auth.declaration.auth import auth_pb2_grpc
from rpc.auth.services import AuthorizeServicer


class gRPCServer:
    @staticmethod
    async def run():
        server = aio.server()

        auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthorizeServicer(), server)

        server.add_insecure_port("[::]:50051")
        await server.start()
        print("[GRPC] Server is running on port", 50051)
        await server.wait_for_termination()