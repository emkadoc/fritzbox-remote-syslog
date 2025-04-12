FROM --platform=$BUILDPLATFORM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fritzbox_remote_syslog.py .

ENV REPEAT_EVERY_MINUTES=default
ENV FRITZ_IP=default
ENV FRITZ_USER=default
ENV FRITZ_PASS=default
ENV FRITZ_NAME=default
ENV FRITZ_SERVICE_NAME=default
ENV SYSLOG_SERVER=default
ENV SYSLOG_PORT=default

CMD ["cron", "-f"]