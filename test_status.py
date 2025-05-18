try:
    from fastapi import status as fastapi_status
    print("FastAPI status import successful")
    print(f"HTTP_502_BAD_GATEWAY: {fastapi_status.HTTP_502_BAD_GATEWAY}")
except Exception as e:
    print(f"FastAPI status import failed: {e}")

try:
    from starlette import status as starlette_status
    print("Starlette status import successful")
    print(f"HTTP_502_BAD_GATEWAY: {starlette_status.HTTP_502_BAD_GATEWAY}")
except Exception as e:
    print(f"Starlette status import failed: {e}") 