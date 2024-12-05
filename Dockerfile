FROM python:3.10.13-slim-bullseye

# working directory inside container
WORKDIR /home/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# install psycopg dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN find . -type f -name "celerybeat.pid" -exec rm -f {} \;
