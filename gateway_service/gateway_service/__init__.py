import logging
from asyncio import CancelledError, Task, sleep
from functools import wraps
from typing import Callable, Coroutine

logger = logging.getLogger(__name__)


def run_forever(repeat_delay: int = 0, failure_delay: int = None):
    """
    Декоратор, позволяющий сделать функцию для asyncio.Task повторяемой, с заданным интервалом времени.
    :param repeat_delay: Задержка между вызовами, секунд.
    :param failure_delay: Задержка между вызовами в случае ошибки выполнения, секунд.
    """
    if failure_delay is None:
        failure_delay = repeat_delay

    def decorator(func: Callable[..., Coroutine]):
        @wraps(func)
        async def task_wrapper(*args, **kwargs):
            while True:
                try:
                    await func(*args, **kwargs)

                except CancelledError:
                    raise

                except Exception:
                    await sleep(failure_delay)

                else:
                    await sleep(repeat_delay)

        return task_wrapper

    return decorator


async def cancel_and_stop_task(task: Task):
    """
    Отменяет задачу и ожидает ее завершения.
    """
    if task.cancelled():
        logger.debug('The task has already been canceled')
        return

    task.cancel()

    try:
        await task

    except CancelledError:
        logger.debug('Task canceled by us')
        # WARN: Здесь НЕЛЬЗЯ делать `raise' потому что тогда данная функция никогда не закончится.

    except Exception:
        logger.exception(f'The task was completed with an error:')

    else:
        logger.debug('Task completed successfully')
