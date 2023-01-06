import os

import uvicorn
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse

from gateway_service.exceptions import ServiceNotAvailableError
from gateway_service.routers import router

app = FastAPI()
app.include_router(router, prefix='/api/v1', tags=['Gateway API'])


@app.get('/manage/health', status_code=status.HTTP_200_OK)
async def check_health():
    return None


@app.exception_handler(ServiceNotAvailableError)
async def unicorn_exception_handler(request: Request, exc: ServiceNotAvailableError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={'message': 'Bonus Service unavailable'},
    )


if __name__ == "__main__":
    port = os.environ.get('PORT')
    if port is None:
        port = 8080

    uvicorn.run(app, host="0.0.0.0", port=int(port))
