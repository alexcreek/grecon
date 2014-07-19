import socket
import re
import pygeoip
import mysql.connector
from mysql.connector import IntegrityError
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
    cnx = mysql.connector.connect(user='', password='',
                                  host='127.0.0.1',
                                  database='suspect_ips')
    cursor = cnx.cursor()

    today = datetime.now().date()

    add_data = ('INSERT INTO suspect_ips '
                '(ip, hostname, latitude, longitude, country, date) '
                'VALUES (%s,%s,%s,%s,%s,%s)')

    data_ip = (ip, hostname, latitude, longitude, country, today)

    try:
        cursor.execute(add_data, data_ip)
        cnx.commit()
    except IntegrityError:
        print "%s\t already exists in database" % ip
        cursor.close()
        cnx.close()
        return False
    else:
        cursor.close()
        cnx.close()
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
