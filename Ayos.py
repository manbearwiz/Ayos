import RPi.GPIO as GPIO
import ephem
import time

from simpledaemon import Daemon
from RelayController import Relay
from datetime import datetime,tzinfo,timedelta
from threading import Timer

class AyosDaemon(Daemon):
    default_conf = '/etc/ayosdaemon.conf'
    section = 'ayos'
    

    def run(self):
        self.location = ephem.Observer()
        Sun = ephem.Sun()

        relay = Relay(args.port)
        self.location.lat=args.latitude
        self.location.lon=args.longitude

        if nightTime():
            relay.turnOff()
            
            sleepUntil(self.location.next_rising(Sun).datetime())

        while True:
            relay.turnOn()

            sleepUntil(self.location.next_setting(Sun).datetime())
            
            relay.turnOff()

            sleepUntil(self.location.next_rising(Sun).datetime())
            
    def add_arguments(self):
        super(AyosDaemon, self).add_arguments()
        self.start_parser.add_argument('--lat', dest='latitude', required='True',
                            action='store', help='Lattitude of location', type=float)
        self.start_parser.add_argument('--lon', dest='longitude', required='True',
                            action='store', help='Longitude of location', type=float)
        self.start_parser.add_argument('--port', dest='port', required='True',
                            action='store', help='GPIO port to control', type=int)                    
        self.parser.description = 'Run Ayos light controller for a specified location'
        
    def nightTime(self):
        return self.location.next_rising(Sun).datetime() < self.location.next_setting(Sun).datetime()
        
    def sleepUntil(self, date):
        time.sleep(date - datetime.utcnow())

if __name__ == '__main__':
    AyosDaemon().main()
