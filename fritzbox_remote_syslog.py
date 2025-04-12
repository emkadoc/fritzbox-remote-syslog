from fritzconnection import FritzConnection
from fritzconnection.core.utils import get_xml_root
from dotenv import load_dotenv
import socket
import os
import datetime
import time
import dataclasses

load_dotenv()

DEBUG = os.getenv('DEBUG')
MINUTES = os.getenv('MINUTES')
IP = os.getenv('IP')
USER = os.getenv('USER')
PW = os.getenv('PW')
NAME = os.getenv('NAME')
SERVICE = os.getenv('SERVICE')
SYSLOG_SERVER = os.getenv('SYSLOG_SERVER')
SYSLOG_PORT = os.getenv('SYSLOG_PORT')

@dataclasses.dataclass(order=True, frozen=True)
class Event:
    timestamp: str
    id: str
    group: str
    msg: str

    def syslog(self):
        hostname = NAME
        service = SERVICE
        dt = datetime.datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
        formatted_timestamp = dt.strftime("%b %d %H:%M:%S")
        return f'<38>{formatted_timestamp} {hostname} {service}[123]: {self.timestamp} - {self.msg}'

    @classmethod
    def from_csv(cls, csv):
        timestamp, id, group, msg = csv.split(' | ')
        return cls(timestamp=timestamp, id=id, group=group, msg=msg)

def parse_event(ev):
    event = {}
    for item in ev:
        tag, value = item.tag, item.text.strip()
        match tag:
            case 'id':
                value = value.zfill(5)
            case 'date':
                day, month, year = value[:2], value[3:5], value[6:8]
                value = datetime.date.fromisoformat(f'20{year}-{month}-{day}')
            case 'time':
                value = datetime.time.fromisoformat(value)
        event[tag] = value
    # combine date+time
    event['timestamp'] = str(datetime.datetime.combine(event['date'], event['time']))
    del event['date']
    del event['time']
    for tag in event.keys():
        if tag not in Event.__dataclass_fields__.keys():
            raise ValueError(f'Unknown tag {tag}!')
    return Event(**event)

def get_fritzbox_logs():
    fc = FritzConnection(address=IP, user=USER, password=PW)
    result = fc.call_action('DeviceInfo:1', 'X_AVM-DE_GetDeviceLogPath')
    url = f'{fc.address}:{fc.port}{result["NewDeviceLogPath"]}'
    logsxml = get_xml_root(url, session=fc.session)
    logs = set(parse_event(event) for event in logsxml)
    return logs

def send_to_syslog(message, syslog_server, syslog_port=514):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode('utf-8'), (syslog_server, syslog_port))

t = int(MINUTES) * 60

while True:
    now = datetime.datetime.now()
    if (DEBUG): print(str(now) + " - woke up...")
    logs = get_fritzbox_logs()

    recent_events = [event for event in logs if (now - datetime.datetime.fromisoformat(event.timestamp)).total_seconds() <= t]
    recent_events.sort(key=lambda event: event.timestamp)

    for event in recent_events:
        if (DEBUG): print((now - datetime.datetime.fromisoformat(event.timestamp)).total_seconds())
        syslog_message = event.syslog()
        if (DEBUG): print(syslog_message)
        send_to_syslog(syslog_message, SYSLOG_SERVER, int(SYSLOG_PORT))

    if (DEBUG): print("fallen asleep...")
    time.sleep(t)