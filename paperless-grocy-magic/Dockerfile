ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies and Python packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    jq \
    gcc \
    musl-dev \
    python3-dev \
    && pip3 install --no-cache-dir \
        requests \
        python-dateutil \
        fuzzywuzzy \
        python-Levenshtein \
    && apk del gcc musl-dev python3-dev

# Copy application files
COPY run.sh /
COPY app/ /app/

RUN chmod a+x /run.sh

WORKDIR /app

CMD ["/run.sh"]
