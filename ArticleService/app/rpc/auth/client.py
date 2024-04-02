import grpc
from rpc.auth.declaration.auth.auth_pb2_grpc import AuthServiceV2Stub
from dotenv import load_dotenv
import os

STORED_CLIENT = None

AUTH_HOST = os.getenv("AUTH_HOST")
AUTH_PORT = os.getenv("AUTH_PORT")

async def generate_client():
    global STORED_CLIENT

    if STORED_CLIENT:
        return STORED_CLIENT

    channel = grpc.aio.insecure_channel(f"{AUTH_HOST}:{AUTH_PORT}")
    client = AuthServiceV2Stub(channel)

    STORED_CLIENT = client
    return client