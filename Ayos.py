import RPi.GPIO as GPIO
import ephem
import time

from RelayController import Relay
from datetime import datetime,tzinfo,timedelta
from threading import Timer

def Schedule():
        utcnow = datetime.utcnow()
        local_time = datetime.now()	

        print("Scheduling Relay Cycles now ({0:%x %X})".format(local_time))
        next_sunrise = Platteville.next_rising(Sun)
        next_sunset = Platteville.next_setting(Sun)

        next_sunrise_date = next_sunrise.datetime()
        next_sunset_date = next_sunset.datetime()

        if next_sunrise_date < next_sunset_date:
                print("It is night time")
                relay.turnOff()
        else:
                print("It is day time")
                relay.turnOn()

        sunrise_delay = next_sunrise_date - utcnow
        sunset_delay = next_sunset_date - utcnow
        reschedule_delay = sunrise_delay + timedelta(minutes=30)

        print("Turning on in {0}, at {1:%x %X}".format(sunrise_delay, sunrise_delay + local_time))
        Timer(sunrise_delay.seconds, relay.turnOn).start()
        print("Turning off in {0}, at {1:%x %X}".format(sunset_delay, sunset_delay + local_time)) 
        Timer(sunset_delay.seconds, relay.turnOff).start()
        print("Rescheduling in {0}, at {1:%x %X}".format(reschedule_delay, reschedule_delay + local_time))
        Timer(reschedule_delay.seconds, Schedule).start()

relay = Relay(4)


Platteville = ephem.Observer()
Sun = ephem.Sun()

Platteville.lat='42.7371'
Platteville.lon='-90.4775'
Platteville.elevation = 302

Schedule()
