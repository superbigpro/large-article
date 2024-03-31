from rpc import gRPCServer
import asyncio


async def main():
    await gRPCServer.run()


if __name__ == "__main__":
    asyncio.run(main())