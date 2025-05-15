import grpc
from rpc.auth.declaration.auth_pb2_grpc import AuthServiceStub
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

STORED_CLIENT = None

AUTH_HOST = os.getenv("AUTH_HOST", "auth_service")
AUTH_PORT = os.getenv("AUTH_PORT", "50001")

async def generate_client():
    global STORED_CLIENT

    if STORED_CLIENT:
        return STORED_CLIENT

    channel = grpc.aio.insecure_channel(f"{AUTH_HOST}:{AUTH_PORT}")
    client = AuthServiceStub(channel)

    STORED_CLIENT = client
    return client