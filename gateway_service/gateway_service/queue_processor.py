import logging
from asyncio import Queue
from typing import Callable, Tuple

from pydantic import BaseModel

from gateway_service import run_forever
from gateway_service.exceptions import ServiceNotAvailableError, ServiceTemporaryNotAvailableError

logger = logging.getLogger(__name__)

QUEUE = Queue()


class Func(BaseModel):
    name: Callable
    args: Tuple


async def get_queue() -> Queue:
    return QUEUE


@run_forever()
async def queue_processor(queue: Queue) -> None:
    func: Func = await queue.get()

    logger.info(f'Gotten func={func}')

    try:
        await func.name(*func.args)
    except (ServiceNotAvailableError, ServiceTemporaryNotAvailableError) as exc:
        logger.debug(f'Gotten exception again: {exc}')
        await queue.put(func)

    queue.task_done()
