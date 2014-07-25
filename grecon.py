import argparse
import socket
import re
import pygeoip
import sqlite3
import Queue
import threading
from sqlite3 import IntegrityError
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='filewall log to parse')
args = parser.parse_args()

### Declarations
geoDB = '/home/alex/Downloads/GeoLiteCity.dat'

if args.file:
    logfile = args.file
else:
    logfile = '/var/log/suspect-ips.log'

gi = pygeoip.GeoIP(geoDB)
unique = set()
queue = Queue.Queue()

### Functions
def get_hostname(address):
    try:
        hostname, foo, ip = socket.gethostbyaddr(address)
    except socket.herror:
        return None, None
    else:
        return ip[0], hostname


def get_geo(ip):
    results = gi.record_by_addr(ip)

    try:
        latitude = results['latitude']
        longitude = results['longitude']
        country = results['country_name']
    except (UnicodeEncodeError, TypeError):
        return None, None, None
    else:
        return latitude, longitude, country


def add_record(ip, hostname, latitude, longitude, country):
    db = sqlite3.connect('suspect_ips.db')
    cursor = db.cursor()

    today = datetime.now().date()

    sql_query = ('INSERT INTO suspect_ips '
                '(ip, hostname, latitude, longitude, country, date) '
                'VALUES (?,?,?,?,?,?)')

    data_values = (ip, hostname, latitude, longitude, country, today)

    try:
        cursor.execute(sql_query, data_values)
    except IntegrityError:
        print "%s\t already exists in database" % ip
        cursor.close()
        db.close()
        return False
    else:
        db.commit()
        cursor.close()
        db.close()
        return True

### Classes
class ThreadUrl(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            address = self.queue.get()
            ip, hostname = get_hostname(address)
            if ip is None:
                print "%s\t hostname not found" % address
            else:
                latitude, longitude, country = get_geo(ip)
                if latitude is None:
                    print "%s\t geodata not found" % ip
                else:
                    if add_record(ip, hostname, latitude, longitude, country):
                        print ip + "\t " + hostname

            # Complete
            self.queue.task_done()


### Main
# Find ip's and load them into unique
with open(logfile) as f:
    for line in f:
        match = re.search('SRC=\S+', line)
        if match:
            ip = match.group()[4:]
            unique.add(ip)

# Spawn pool of threads, and pass them queue instances
for i in range(4):
    t = ThreadUrl(queue)
    t.setDaemon(True)
    t.start()

# Load queue and execute threads
for ip_address in unique:
    queue.put(ip_address)

# Sit on queue and wait for threads to finish
queue.join()

print "Done"
