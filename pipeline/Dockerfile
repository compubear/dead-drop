FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg libmagic1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pipeline dependencies
COPY pipeline/requirements.txt ./pipeline/requirements.txt
RUN pip install --no-cache-dir -r pipeline/requirements.txt

# Install video dependencies
COPY video/requirements.txt ./video/requirements.txt
RUN pip install --no-cache-dir -r video/requirements.txt

# Install test dependencies
COPY tests/requirements.txt ./tests/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt

# Copy source code
COPY pipeline/ ./pipeline/
COPY video/ ./video/
COPY config/ ./config/
COPY tests/ ./tests/

CMD ["python", "-m", "pipeline.main"]
