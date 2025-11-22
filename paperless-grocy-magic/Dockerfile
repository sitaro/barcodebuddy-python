ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies and Python packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    && pip3 install --no-cache-dir --break-system-packages \
        flask \
        requests \
        python-dateutil \
        fuzzywuzzy \
        pdfplumber

# Copy application files
COPY run.sh /
COPY app/ /app/

RUN chmod a+x /run.sh

WORKDIR /app

CMD ["/run.sh"]
