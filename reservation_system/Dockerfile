FROM python:3.11-slim as stage0

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update ; \
    apt-get install -y --no-install-recommends \
        vim

COPY requirements.txt /python_requirements/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /python_requirements/requirements.txt

ENV ROOT_DIR /app

WORKDIR $ROOT_DIR

COPY reservation_system $ROOT_DIR/reservation_system
COPY alembic.ini $ROOT_DIR/reservation_system/

# ------------ test -----------------------
FROM stage0 as test

COPY reservation_system_tests $ROOT_DIR/reservation_system_tests

RUN pytest $ROOT_DIR/reservation_system_tests

# ------------ final -----------------------

FROM stage0 as final

CMD ["python3", "-m", "reservation_system.main"]