FROM python:3.11-alpine

# Install FFmpeg (no cache to keep image small)
RUN apk add --no-cache ffmpeg

# Setup App
WORKDIR /app

# Install Flask (no cache to keep image small)
RUN pip install --no-cache-dir flask

# Copy Application
COPY app.py .

# Run
CMD ["python", "app.py"]