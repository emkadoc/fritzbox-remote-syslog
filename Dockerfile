FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fritzbox_remote_syslog.py .

ENV TZ="Europe/Berlin"
ENV REPEAT_EVERY_MINUTES=default
ENV FRITZ_IP=default
ENV FRITZ_USER=default
ENV FRITZ_PASS=default
ENV FRITZ_NAME=default
ENV FRITZ_SERVICE_NAME=default
ENV SYSLOG_SERVER=default
ENV SYSLOG_PORT=default

CMD ["python", "fritzbox_remote_syslog.py"]