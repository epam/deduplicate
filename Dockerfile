# Prepare the builder by installing the bneeded software
FROM debian:12-slim as builder
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade --no-cache-dir pip

# Build python venv based on requirements.txt file
FROM builder AS build-venv
COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --no-cache-dir -r /requirements.txt && \
    find /venv \( -type d -a \( -name test -o -name tests -o -name test_data -o -name test-data \) \) -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) -exec rm -rf '{}' +

# Copy the app and build final image based on google distroless base container
FROM gcr.io/distroless/python3-debian12
COPY --from=build-venv /venv /venv
COPY . /app
WORKDIR /app
EXPOSE 8899
ENTRYPOINT ["/venv/bin/python3", "deduplicate.py"]
