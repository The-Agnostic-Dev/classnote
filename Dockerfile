# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_DEBUG=0

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput \
    && useradd --create-home classnote \
    && chown -R classnote /app
USER classnote

EXPOSE 5106
ENTRYPOINT ["./docker-entrypoint.sh"]
# One worker keeps the in-process notice board cache consistent; threads handle concurrency.
CMD ["gunicorn", "classnote.wsgi:application", "--bind", "0.0.0.0:5106", "--workers", "1", "--threads", "4"]
