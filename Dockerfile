FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# results.db is pre-generated locally via `python pipeline/run.py`
# and included via COPY. No live database connection is needed at runtime.
# To refresh: run the pipeline locally, then redeploy.

EXPOSE 8050

CMD ["gunicorn", "app.app:server", \
     "-b", "0.0.0.0:8050", \
     "-w", "1", \
     "--worker-class", "gthread", \
     "--threads", "4", \
     "--timeout", "120"]
