FROM mcr.microsoft.com/playwright/python:v1.32.0-jammy

WORKDIR /app

COPY .env setup.cfg pyproject.toml ./
COPY src /app/src

RUN pip install -e .

CMD ["python3", "src/bakabot/main.py"]