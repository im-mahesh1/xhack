FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install psycopg2-binary
RUN pip install gunicorn

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

COPY . .
RUN chown -R appuser:appuser /app

EXPOSE 5000 