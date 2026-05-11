FROM python:3.12-slim

WORKDIR /app

# Copy and install dependencies first.
# Docker caches each step as a "layer". By copying requirements.txt before the source
# code, this layer is only rebuilt when dependencies change — not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ ./src/

EXPOSE 8000

# `python -m uvicorn` runs uvicorn through Python's module system, which guarantees
# it uses the same Python/pip environment as this image.
# --host 0.0.0.0 binds to all network interfaces — required so Docker can route
# external traffic into the container (127.0.0.1 would only be reachable inside it).
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
