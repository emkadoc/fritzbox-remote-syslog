from fritzconnection import FritzConnection
from fritzconnection.core.utils import get_xml_root
from dotenv import load_dotenv
import socket
import os
import datetime
import time
import dataclasses

load_dotenv()

REPEAT_EVERY_MINUTES = os.getenv('REPEAT_EVERY_MINUTES')
FRITZ_IP = os.getenv('FRITZ_IP')
FRITZ_USER = os.getenv('FRITZ_USER')
FRITZ_PASS = os.getenv('FRITZ_PASS')
FRITZ_NAME = os.getenv('FRITZ_NAME')
FRITZ_SERVICE_NAME = os.getenv('FRITZ_SERVICE_NAME')
SYSLOG_SERVER = os.getenv('SYSLOG_SERVER')
SYSLOG_PORT = os.getenv('SYSLOG_PORT')


@dataclasses.dataclass(order=True, frozen=True)
class Event:
    timestamp: str
    id: str
    group: str
    msg: str

    def syslog(self):
        hostname = FRITZ_NAME
        service = FRITZ_SERVICE_NAME
        dt = datetime.datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
        formatted_timestamp = dt.strftime("%b %d %H:%M:%S")
        return f'<38>{formatted_timestamp} {hostname} {service}[123]: {self.timestamp}-{self.msg}'

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
    fc = FritzConnection(address=FRITZ_IP, user=FRITZ_USER, password=FRITZ_PASS)
    result = fc.call_action('DeviceInfo:1', 'X_AVM-DE_GetDeviceLogPath')
    url = f'{fc.address}:{fc.port}{result["NewDeviceLogPath"]}'
    logsxml = get_xml_root(url, session=fc.session)
    logs = set(parse_event(event) for event in logsxml)
    return logs

def send_to_syslog(message, syslog_server, syslog_port=514):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode('utf-8'), (syslog_server, syslog_port))

logs = get_fritzbox_logs()

t = int(REPEAT_EVERY_MINUTES) * 60

while True:
    now = datetime.datetime.now()
    recent_events = [event for event in logs if (now - datetime.datetime.fromisoformat(event.timestamp)).total_seconds() <= t]
    recent_events.sort(key=lambda event: event.timestamp)

    for event in recent_events:
        syslog_message = event.syslog()
        print(syslog_message)
        send_to_syslog(syslog_message, SYSLOG_SERVER, int(SYSLOG_PORT))

    time.sleep(t)