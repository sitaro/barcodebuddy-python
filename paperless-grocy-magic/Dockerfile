ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    && pip3 install --no-cache-dir \
        requests \
        python-dateutil \
        fuzzywuzzy \
        python-Levenshtein

# Copy application files
COPY run.sh /
COPY app/ /app/

RUN chmod a+x /run.sh

WORKDIR /app

CMD ["/run.sh"]
