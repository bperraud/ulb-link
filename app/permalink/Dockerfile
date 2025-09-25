FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt /app/

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

#RUN chmod -R u=rX,g=rwx,o= /app/static_root
RUN chmod -R u=rX,g=rwx,o= /var/log

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000

FROM base AS dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prd
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "60", "permalink.wsgi:application"]
