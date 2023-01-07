import asyncio
import logging
import os
from asyncio import Task

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from gateway_service import cancel_and_stop_task
from gateway_service.exceptions import ServiceNotAvailableError
from gateway_service.queue_processor import QUEUE, queue_processor
from gateway_service.routers import router

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router, prefix='/api/v1', tags=['Gateway API'])

queue_task: Task


@app.get('/manage/health', status_code=status.HTTP_200_OK)
async def check_health():
    return None


@app.on_event('startup')
async def startup_event() -> None:
    global queue_task
    queue_task = asyncio.create_task(queue_processor(QUEUE))
    logger.info('Queue processor is started')


@app.on_event('shutdown')
async def shutdown_event() -> None:
    await cancel_and_stop_task(queue_task)
    logger.info('Queue processor is stopped')


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
