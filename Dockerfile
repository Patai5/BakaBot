FROM mcr.microsoft.com/playwright/python:v1.32.0-jammy

WORKDIR /app

COPY .env pyproject.toml ./
COPY src /app/src

RUN pip install -e .

CMD ["python3", "-m", "src.main"]