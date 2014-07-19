import socket
import re
import pygeoip
import mysql.connector
from datetime import datetime
import Queue
import threading

### Declarations
logfile = '/var/log/suspect-ips.log'
geoDB = '/home/alex/Downloads/GeoLiteCity.dat'

gi = pygeoip.GeoIP(geoDB)
unique = set()
queue = Queue.Queue()

### Functions
def add_record(ip, hostname, latitude, longitude, country):
    cnx = mysql.connector.connect(user='', password='',
                                  host='127.0.0.1',
                                  database='suspect_ips')
    cursor = cnx.cursor()

    today = datetime.now().date()

    add_data = ('INSERT INTO suspect_ips '
                '(ip, hostname, latitude, longitude, country, date) '
                'VALUES (%s,%s,%s,%s,%s,%s)')

    data_ip = (ip, hostname, latitude, longitude, country, today)

    cursor.execute(add_data, data_ip)
    cnx.commit()

    cursor.close()
    cnx.close()


def get_geo(ip):
    results = gi.record_by_addr(ip)

    try:
        latitude = results['latitude']
        longitude = results['longitude']
        country = results['country_name']
    except (UnicodeEncodeError, TypeError):
        pass
    else:
        return latitude, longitude, country


### Classes
class ThreadUrl(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            address = self.queue.get()

            try:
                hostname, foo, ip = socket.gethostbyaddr(address)
            except socket.herror:
                pass
            else:
                latitude, longitude, country = get_geo(ip[0])
                add_record(ip[0], hostname, latitude, longitude, country)
                print ip[0] + "\t" + hostname

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
    try:
        queue.put(ip_address)
    except:
        pass

# Sit on queue and wait for threads to finish
queue.join()

print "Done"
