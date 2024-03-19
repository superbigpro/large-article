from fastapi import Header
from rpc import auth
from fastapi.exceptions import HTTPException
from grpc.aio._call import AioRpcError


async def RequireAuth(authorization: str = Header(...)):
    try:
        token_type = authorization.split(" ")[0]
        token = authorization.split(" ")[1]

        if token_type != "Bearer":
            raise

        userid = await auth.authorize(token)
        if not userid:
            raise
        return userid
    except AioRpcError:
        raise HTTPException(status_code=500, detail="INTERNAL_COMMUNICATION_ERROR")
    except:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")