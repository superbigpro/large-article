#!/bin/bash

rm -rf ./declaration/*.py

python3 -m grpc_tools.protoc -I ./declaration --python_out=./declaration --grpc_python_out=./declaration ./declaration/auth.proto