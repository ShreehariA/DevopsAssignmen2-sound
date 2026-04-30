FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY aceest_fitness_web aceest_fitness_web
COPY wsgi.py .

ENV APP_VERSION="0.1.0" \
    DATABASE_PATH="/data/aceest_fitness.db"

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app"]
