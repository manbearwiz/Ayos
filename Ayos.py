import RPi.GPIO as GPIO
import ephem
import time
import geocoding

from simpledaemon import Daemon
from RelayController import Relay
from datetime import datetime,tzinfo,timedelta
from threading import Timer

class AyosDaemon(Daemon):
    default_conf = '/etc/ayosdaemon.conf'
    section = 'ayos'
    
    self.location = ephem.Observer()
    Sun = ephem.Sun()

    def run(self):
        relay = Relay(args.port)
        self.location.lat=args.latitude
        self.location.lon=args.longitude

        if nightTime()
            relay.turnOff()
            
            sleepUntil(self.location.next_rising(Sun).datetime())

        while True:
            relay.turnOn()

            sleepUntil(self.location.next_setting(Sun).datetime())
            
            relay.turnOff()

            sleepUntil(self.location.next_rising(Sun).datetime())
            
    def add_arguments(self):
        super(AyosDaemon, self).add_arguments()
        
        
        location_group = self.start_parser.add_mutually_exclusive_group()
        location_group.add_argument('--address', action='store')
        latlong_group = location_group.add_argument_group('latlong', 'lat long description')
        latlong_group.add_argument(
            '--latitude', action='store', required='True',
            help='Latitude of location', type=float
        )
        latlong_group.add_argument(
            '--longitude', action='store' required='True',
            help='Longitude of location', type=float
        )
        self.start_parser.add_argument('--port', dest='port', required='True'
                            action='store', help='GPIO port to control', type=int)                    
        self.parser.description = 'Run Ayos light controller for a specified location'
        
    def nightTime(self):
        return self.location.next_rising(Sun).datetime() < self.location.next_setting(Sun).datetime()
        
    def sleepUntil(self, date):
        time.sleep(date - datetime.utcnow())

if __name__ == '__main__':
    AyosDaemon().main()
