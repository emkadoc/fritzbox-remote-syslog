FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fritzbox_remote_syslog.py .

ENV TZ="Europe/Berlin"
ENV DEBUG=default
ENV MINUTES=default
ENV IP=default
ENV USER=default
ENV PW=default
ENV NAME=default
ENV SERVICE=default
ENV SYSLOG_SERVER=default
ENV SYSLOG_PORT=default

CMD ["python", "fritzbox_remote_syslog.py"]