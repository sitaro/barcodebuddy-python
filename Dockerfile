FROM python:3.11-alpine

# Home Assistant Labels
LABEL \
    io.hass.version="2.0.0" \
    io.hass.type="addon" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386"

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    libevdev-dev

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ /app/
COPY run.sh /app/

RUN chmod +x /app/run.sh

# Expose port
EXPOSE 5000

CMD ["/app/run.sh"]
