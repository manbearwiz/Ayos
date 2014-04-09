import RPi.GPIO as GPIO
import ephem
import time

from RelayController import Relay
from datetime import datetime,tzinfo,timedelta
from threading import Timer

def Schedule():
        Platteville.date = datetime.now()

        print("Scheduling Relay Cycles for next day")
        next_sunrise = Platteville.next_rising(Sun)
        next_sunset = Platteville.next_setting(Sun)

        utcnow = datetime.utcnow()

        next_sunrise_date = next_sunrise.datetime()
        next_sunset_date = next_sunset.datetime()
        print(next_sunrise_date)
        print(next_sunset_date)
        if next_sunrise_date < next_sunset_date:
                print("It is night time")
                relay.turnOff()
        else:
                print("It is day time")
                relay.turnOn()

        sunrise_delay = next_sunrise_date - utcnow
        sunset_delay = next_sunset_date - utcnow
        reschedule_delay = sunrise_delay + timedelta(minutes=30)

        print("Turning on in {0}".format(sunrise_delay))
        Timer(sunrise_delay.seconds, relay.turnOn).start()
        print("Turning off in {0}".format(sunset_delay)) 
        Timer(sunset_delay.seconds, relay.turnOff).start()
        print("Rescheduling in {0}".format(reschedule_delay))
        Timer(reschedule_delay.seconds, Schedule).start()

relay = Relay(4)


Platteville = ephem.Observer()
Sun = ephem.Sun()

Platteville.lat='42.7371'
Platteville.lon='-90.4775'
Platteville.elevation = 302
Platteville.date = datetime.now() 

Schedule()
