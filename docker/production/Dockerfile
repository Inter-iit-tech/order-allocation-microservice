FROM python:3.10-bullseye AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends liblapack-dev libopenblas-dev gfortran \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir

RUN apt-get update \
    && apt-get purge -y --no-install-recommends liblapack-dev libopenblas-dev gfortran \
    && apt-get install -y --no-install-recommends liblapack3 libopenblas0 \
    && apt-get autopurge -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

FROM builder as runner

RUN python3 manage.py migrate

RUN pip3 install -U uvicorn --no-cache-dir
ENTRYPOINT ["python3"]
CMD ["-m", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "optiserver.asgi:application"]
