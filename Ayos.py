import RPi.GPIO as GPIO
import ephem
import time
import simpledaemon

from RelayController import Relay
from datetime import datetime,tzinfo,timedelta
from threading import Timer

class AyosDaemon(simpledaemon.Daemon):
    default_conf = '/etc/ayosdaemon.conf'
    section = 'ayos'
    
    relay = Relay(4)

    Platteville = ephem.Observer()
    Sun = ephem.Sun()

    Platteville.lat='42.7371'
    Platteville.lon='-90.4775'
    
    def run(self):
            
        next_sunrise_date = Platteville.next_rising(Sun).datetime()
        next_sunset_date = Platteville.next_setting(Sun).datetime()
        
        if next_sunrise_date < next_sunset_date: #It is night time
            relay.turnOff()
            time.sleep(next_sunrise_date - datetime.utcnow())

        while True:
            relay.turnOn()
            
            next_sunset_date = Platteville.next_setting(Sun).datetime()

            time.sleep(next_sunset_date - datetime.utcnow())
            
            relay.turnOff()
            
            next_sunrise_date = Platteville.next_rising(Sun).datetime()

            time.sleep(next_sunrise_date - datetime.utcnow())

if __name__ == '__main__':
    AyosDaemon().main()
