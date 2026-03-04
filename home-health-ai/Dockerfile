FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/
COPY config/ /app/config/
COPY static/ /app/static/

EXPOSE 8300

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8300"]
