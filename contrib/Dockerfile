FROM python:3-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y --no-install-recommends git && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir setuptools wheel twine build 

WORKDIR /app
COPY . imapautofiler/

RUN pip install --no-cache-dir ./imapautofiler && \
    rm -rf ./imapautofiler/.git ./imapautofiler/.github ./imapautofiler/doc

CMD ["bash", "/app/imapautofiler/contrib/starting.sh"]
