FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Sistema: dependencias nativas para WeasyPrint (pango/cairo) y locales.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      libpango-1.0-0 \
      libpangoft2-1.0-0 \
      libharfbuzz0b \
      libcairo2 \
      libffi8 \
      shared-mime-info \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install build deps first (cache layer), then install from pyproject.toml.
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install \
      "alembic>=1.16.0" \
      "fastapi>=0.116.0" \
      "fpdf2>=2.8.5" \
      "jinja2>=3.1.0" \
      "openai>=1.55.0" \
      "python-docx>=1.2.0" \
      "python-multipart>=0.0.20" \
      "pypdf>=6.0.0" \
      "psycopg[binary]>=3.2.0" \
      "pydantic-settings>=2.10.1" \
      "sqlalchemy>=2.0.41" \
      "uvicorn[standard]>=0.35.0" \
      "weasyprint>=63.0"

COPY . /app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
