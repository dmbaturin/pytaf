pytaf
=====

Python TAF parser and decoder

TAF 
---

TAF stands for "Terminal Aerodrome Forecast". It's the weather 
forecast reporting format used in aviation.

Unlike "normal" weather forecast, TAF is issued for no more than
next 24-30 hours, and includes highly detailed information about
current and expected meteorological conditions, like exact
clouds type and ceiling, as it's important for flight safety.

This is what a TAF report may look like:

    TAF 
      AMD KMKE 172034Z 1721/1824 14013G19KT P6SM SCT028 BKN035 BKN250 
     FM180100 17008KT P6SM SCT035 BKN120 
     FM181000 17007KT P6SM VCSH BKN040 OVC080 
      TEMPO 1811/1815 6SM -TSRA BR BKN030CB 
     FM181500 18009KT P6SM VCSH BKN050 
     FM182100 16012KT P6SM SCT050 BKN150

It reads as:

    "TAF AMD KMKE": TAF amended for General Mitchell International Airport,

    "172034Z": Issued at 20:34 Zulu time (UTC) on [September the] 17th

    "1721/1824": Valid from 21:00 UTC on 17th to 24:00 UTC on 18th

    "14013G19KT": Wind from 140 degrees at 13 knots, gusting to 19 knots

    "P6SM": Visibility more than 6 statute miles

    "SCT028 BKN035 BKN250": Clouds scattered at 2800 (28*100) feet, broken at 3500 feet, broken at 25000 feet

    "FM180100 ...": From 01:00 UTC on 18th [wind, visibility, clouds]

    "FM181000 17007KT P6SM VCSH BKN040 OVC080": From 10:00 UTC on 18th [wind, visibility], 
          showers in the vicinity, clouds broken at 4000, overcast at 8000

    "TEMPO 1811/1815 6SM -TSRA BR BKN030CB": Temporarily between 11:00 UTC and 15:00 UTC on 18th
           visibility 6 statute miles, light thunderstorms and rain, mist, broken cumulonimbus clouds at 3000 

     ...

**Note:** despite the terse format, TAF reports are
written by humans, and are supposed to be interpreted by humans too.

This means the format is (from computer point of view) loosely
standardized and is not guaranteed to be machine readable.

Moreover, TAF format is not exactly the same in all countries.
Not different enough for people to have problems understanding it,
but different enough to make implementatng a universal parser
very hard, if not impossible.

United States civil airports produce the most machine friendly reports,
and this library primarily deals with those. TAFs from other countries
are very likely not to be parsed and interpeted correctly.

Information about US TAF format can be found at NOAA website:
http://aviationweather.gov/static/help/taf-decode.php

You can get raw and interpreted reports from there too:
http://www.aviationweather.gov/adds/tafs/


API
---

pytaf contains two base classes: pytaf.TAF and pytaf.Decoder

TAF is initialized with a raw TAF report string and parses it.

Decoder accepts a TAF object as argument, interprets it and produces human readable
output.

    import pytaf

    taf = pytaf.TAF("<my TAF string>")
    decoder = pytaf.Decoder(taf)
    print decoder.decode_taf()


Hacking
-------

If you want to change the decoder output format (e.g. output to HTML),
inherit from pytaf.Decoder and overload _decode_taf() method.
That methods contains nothing but calls to other methods and output
string formatting.

If you want to redefine the interpretation, e.g. use numeric values
for display in a widget, you may want to use TAF object directly.
All its methods return dicts with pretty straightforward key names.
