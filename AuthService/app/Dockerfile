FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cd /app/rpc/auth/declaration && \
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. auth.proto && \
    sed -i 's/import auth_pb2/from . import auth_pb2/' auth_pb2_grpc.py

EXPOSE 50001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "50001"]
