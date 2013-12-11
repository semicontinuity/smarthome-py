"""
On request (SIGINT), posts the current temperature information from Cube
to the web server.
If upload fails (e.g. internet connection is down),
retains the data until the next upload request.
"""

################################################################################
# Collecting information from Cube
################################################################################

from elvmax import cube, house, messages
from time import sleep

the_house = house.House()

print 'Searching Cube'
cubes = cube.Search.list_cubes()
if len(cubes) != 1:
    raise ValueError('Expected to find 1 Cube in the network')

found_cube = cubes[0]
print 'Found cube ' + found_cube[0]

connection = cube.Connection()
connection.host = found_cube[1]
connection.port = found_cube[2]
connection.on_message = the_house.on_message
connection.start()


################################################################################
# Custom JSON encoder: strings are b16-encoded (hex)
################################################################################

import json
import base64


class Base16Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, str):
            return base64.b16encode(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

################################################################################
# Uploading
################################################################################

import httplib
import signal


def encode_temperature(t):
    """
    convert to 2-byte fixed-point I.F string
    input: temperature, half-degree precision
    """
    rounded = float(int((t) * 2)) / 2
    integer = int(rounded)
    return str(chr(integer & 0xFF)) + str(chr(int((rounded - integer) * 256.0) & 0xFF))

def upload():
    print 'Upload!'

    for key in the_house.rf_address_to_device:
        the_device = the_house.rf_address_to_device[key]
        print the_device.mode(), the_device.temperature(), the_device.target_temperature()

        # headers = {"Content-type": "text/plain"}
    # conn = httplib.HTTPConnection("localhost:8080")
    # conn.request("POST", "/temperature_statistics", "test", headers)
    # response = conn.getresponse()
    # print response.status, response.reason
    # data = response.read()
    # print data
    # conn.close()


signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGINT, lambda signum, frame: upload())

################################################################################
# Wait for shutdown signal
################################################################################

import threading
shutdown_event = threading.Event()


def shutdown():
    shutdown_event.set()

signal.signal(signal.SIGTERM, lambda signum, frame: shutdown())

while 1:
  try:
    shutdown_event.wait(0.1)
    if shutdown_event.is_set():
        break
  except:
    pass
