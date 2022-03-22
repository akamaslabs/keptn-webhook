FROM python:3.8-slim

EXPOSE 6000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY build/requirements.txt .
RUN python -m pip install -r requirements.txt

# Install curl
USER root
RUN apt-get update && apt-get install -y curl jq
RUN curl -o akamas_cli -O https://s3.us-east-2.amazonaws.com/akamas/cli/$(curl https://s3.us-east-2.amazonaws.com/akamas/cli/stable.txt)/linux_64/akamas
RUN mv akamas_cli /usr/local/bin/akamas
RUN chmod 755 /usr/local/bin/akamas

WORKDIR /app
COPY webhook.py  /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
