FROM python:3.12.9-slim-bookworm

# UV를 컨테이너 내에 설치
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/

RUN apt-get update -q \
    && apt-get install --no-install-recommends -qy python3-dev g++ gcc

ENV PATH="/root/.local/bin/:$PATH"

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked


EXPOSE 8000
# Presuming there is a `my_app` command provided by the project
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0" ,"--port", "8000"]