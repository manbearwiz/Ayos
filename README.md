Ayos
============

Ayos is a Python3 script to precisely control grow light fixtures according to your current location's sunrise and sunset in order to accurately simulate [photoperiodism](http://en.wikipedia.org/wiki/Photoperiodism#In_plants). This means that your plants will be exposed to light for a marginally different amount of time each day just like they would with natural light. Also this is a justification for me to use a Raspberry Pi to control grow lights rather than a $5 timer.

Dependencies
------------

The following packages should be installed prior to running Ayos.

- [PyEphem](http://rhodesmill.org/pyephem/) - Used to calculate the sun's transition times

- [RPi.GPIO](http://sourceforge.net/p/raspberry-gpio-python/wiki/Home/) - Used to control the GPIO ports for the relay

- [SimpleDaemon](https://bitbucket.org/donspaulding/simpledaemon/overview) - Used to run as daemon. My fork is currently included in this repo.


Hardware
--------
My current setup is a Raspberry Pi hooked up to a 4-channel 5V relay via GPIO. Raspberry Pi GPIO ports only put out 3.3V but in my testing this doesn't seem to cause any issue. I have a [ULN2803A](https://www.sparkfun.com/datasheets/IC/uln2803a.pdf) chip laying around that I may wire up to power the relays on a separate PSU when I get time.


Usage
-----

Thanks to my fork of SimpleDaemon, Ayos can be run like so:

```
./Ayos.py start --lat 42.7371 --lon 90.4775
```

Stopping is similar:

```
./Ayos.py stop
```

For a full list of options, see the help:

```
./Ayos.py --help
```

Future Enhancements
-------------------

###Portabliity

Not to other systems, but rather other locations. As of right now everything is hardcoded to my location, Platteville WI. If anyone wanted to make it customizable via command-line options and [argparse](https://docs.python.org/3.2/library/argparse.html) I would happily merge it in.

###Geocoding

Relating to enhancement above, including geocoding via [The Google Geocoding API](https://developers.google.com/maps/documentation/geocoding/) would be a significant usabiltiy improvement. I attempted to use [pygeocoder](http://code.xster.net/pygeocoder/wiki/Home) and [geopy](https://github.com/geopy/geopy) but unfortunately they both have setup issue on my system when I use pip. Not sure the reason why.

About
--------

###Namesake

Ayos is an alternate pronunciation of Eos, the Greek goddess of the dawn.

###License

The source is released under the [MIT-License](http://opensource.org/licenses/MIT).
