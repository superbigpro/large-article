from rpc import gRPCServer
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grpc-main")

async def main():
    try:
        logger.info("Starting Article gRPC server...")
        await gRPCServer.run()
    except Exception as e:
        logger.error(f"Error starting gRPC server: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())