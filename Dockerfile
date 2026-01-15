FROM python:3.11-slim
LABEL maintainer="lipschitzappdeveloper.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /requirements.txt
COPY ./api /api
COPY ./Scripts /Scripts

WORKDIR /api
EXPOSE 8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libffi-dev gcc && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip setuptools wheel && \
    /py/bin/pip install -r /requirements.txt && \
    apt-get purge -y --auto-remove build-essential gcc && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --gecos "" app && \
    mkdir -p /home/app/app/staticfiles /home/app/app/mediafiles /vol /vol/web && \
    chown -R app:app /home/app /vol /Scripts /api && \
    chmod -R 755 /vol /Scripts && \
    chmod +x /Scripts/*.sh

ENV PATH="/py/bin:$PATH"

USER app

ENTRYPOINT ["/Scripts/entrypoint.sh"]
