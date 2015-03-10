#!/usr/bin/python

import socket
import re
import sqlite3
import time

server = "aprs.glidernet.org"
port = 14580

username = "Zapol"
password = "-1"
_filter = "r/45.55/5.98/1000"
# _filter = ""
sw_ver = "gliderview 0.01"

def db_create(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS DATAPOINTS
                (id integer,
                flight integer,
                flarm_id text,
                time integer,
                lat real,
                lon real,
                heading real,
                speed real,
                altitude real,
                vario real)''')

    c.execute('''CREATE TABLE IF NOT EXISTS FLIGHTS
                (id integer,
                flarm_id text,
                towplane_id text,
                t_takeoff integer,
                t_landing integer)''')

    c.execute('''CREATE TABLE IF NOT EXISTS CALLSIGNS
                (flarm_id integer,
                callsign text,
                towplane boolean)''')

def db_end_flights(conn):
    c = conn.cursor()
    c.execute("SELECT id FROM FLIGHTS WHERE t_landing = '0'");
    (flights) = c.fetchall()
    for f in flights:
        c.execute("SELECT time FROM DATAPOINTS WHERE flight = '%d' ORDER BY time DESC LIMIT 1" % f)
        (t) = c.fetchone()
        c.execute("UPDATE FLIGHTS SET t_landing = '%d' WHERE id = '%d'" % (t,f) )

def db_append(conn,flight,flarm_id,timestamp,lat,lon,heading,speed,altitude,vario):
    c = conn.cursor()
    c.execute("INSERT INTO DATAPOINTS (flight,flarm_id,time,lat,lon,heading,speed,altitude,vario) VALUES ('%d','%s','%d','%s','%s','%f','%f','%f','%f')" % (flight,flarm_id,timestamp,lat,lon,heading,speed,altitude,vario))

def zulutime_to_timestamp(zulutime):
    print time.strptime(zulutime,"%H%M%S")
    print int(time.time())
    timestamp = int(zulutime)
    return timestamp


sock = socket.socket()

print "Connecting"
sock.connect((server,port))

msg = ""
while len(msg)==0:
    msg = sock.recv(256)
print "Connected:"+msg

msg = "user %s pass %s vers %s filter %s" % (username, password, sw_ver, _filter)
print "sending: " + msg
sock.send(msg+"\n")

conn = sqlite3.connect('gliders.db')
db_create(conn)
db_end_flights(conn)

#Good:
#FLRDD940D>APRS,qAS,MotServlx:/131220h4534.15N/00559.35E'152/075/A=002637 id0ADD940D +396fpm +0.2rot 14.5dB 0e +0.4kHz gps3x3 hearA361 hearA39C
#[('FLRDD940D', 'qAS', 'MotServlx', '131220', '4534.15N', '00559.35E', '152', '075', '002637', 'id0ADD940D', '+396', '+0.2', '14.5', '0', '+0.4')]

#Bad:
#FLRDDA371>APRS,qAS,LFLE:/131220h4533.43N/00558.73E'/A=000964 id06DDA371 +020fpm +0.0rot 39.5dB 0e -3.3kHz gps3x7 hear940D hearA361 hearA39C

while True:
    msg = sock.recv(1024)
    if msg:
        m = re.findall("(.*)>APRS,(.*),(.*):/([0-9]*)h(.*)/(.*)'([0-9]*)/([0-9]*)/A=([0-9]*) (.*) (.*)fpm (.*)rot (.*)dB ([0-9]*)e (.*)kHz", msg)
        if m:
            flarm_id = m[0][0]
            zulutime = m[0][3]
            lat = m[0][4]
            lon = m[0][5]
            heading = float(m[0][6])
            speed = float(m[0][7])*1.852
            altitude = float(m[0][8])*0.3048
            vario = float(m[0][10])*0.00508
            print "ID: %s, time: %s, AirSPD: %3d, alt: %4d, vario: %5.1f" % (flarm_id, zulutime, speed, altitude, vario)
            timestamp = zulutime_to_timestamp(zulutime)
            flight = 0
            db_append(conn,flight,flarm_id,timestamp,lat,lon,heading,speed,altitude,vario);

            
        # print msg