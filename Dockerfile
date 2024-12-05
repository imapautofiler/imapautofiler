FROM python:3-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --root-user-action ignore imapautofiler

WORKDIR /app
COPY . imapautofiler/

CMD ["bash", "/app/imapautofiler/starting.sh"]

