import RPi.GPIO as GPIO
import ephem
import time

from datetime import datetime,tzinfo,timedelta
from threading import Timer

class Relay:

        def __init__(self, port, rest_state = 1):
                self.Off = rest_state
                self.On = not self.Off
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(port, GPIO.OUT)
                self.port = port
                self.turnOff

        def set(self, state):
                GPIO.output(self.port, state)
                self.state = state

        def turnOn(self):
                self.set(self.On)

        def turnOff(self):
                self.set(self.Off)

        def toggle(self):
                self.set(not self.state)
