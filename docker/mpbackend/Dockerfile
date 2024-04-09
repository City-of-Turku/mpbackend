# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:22.04
FROM python:3.10-slim

EXPOSE 8000
WORKDIR /mpbackend

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
ENV STATIC_ROOT=/mpbackend/static
ENV STATIC_URL=/static/
# tzdata installation requires settings frontend
RUN apt-get update && \
    TZ="Europe/Helsinki" DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip gdal-bin
ARG REQUIREMENTS_FILE
COPY . .
# Install pip requirements
RUN python -m pip install -r ${REQUIREMENTS_FILE}
RUN python manage.py collectstatic --no-input


# Creates a non-root user with an explicit UID and adds permission to access the /mpbackend folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /mpbackend
USER appuser

ENTRYPOINT ["./docker-entrypoint.sh"]

