import grpc
from .declaration.auth_pb2_grpc import AuthServiceStub
from env import MicroEnv

STORED_CLIENT = None


async def generate_client():
    global STORED_CLIENT

    if STORED_CLIENT:
        return STORED_CLIENT

    channel = grpc.aio.insecure_channel(f"{MicroEnv.AUTH_HOST}:{MicroEnv.AUTH_PORT}")
    client = AuthServiceStub(channel)

    STORED_CLIENT = client
    return client