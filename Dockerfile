FROM python:3.11-slim-buster

WORKDIR /app

COPY pyproject.toml .
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY docker-entrypoint.sh .

# Copy the application code to the container
COPY app/ /app/app

RUN pip install -e .

# Expose the default port used by Uvicorn
EXPOSE 8000

# Start the application with Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["./docker-entrypoint.sh"]
