FROM python:3.11

WORKDIR /app

COPY .env setup.cfg pyproject.toml ./
COPY src /app/src

RUN python3 -m venv env
RUN env/bin/pip3 install -e .

CMD ["env/bin/python3", "src/bakabot/main.py"]