*pytaf is python module for parsing and decoding aviation weather forecasts*

TAF
---

TAF stands for "Terminal Aerodrome Forecast". It's the weather
forecast reporting format used in aviation.

Unlike "normal" weather forecasts for everyday use, TAF is issued for no more than
next 24-30 hours, and includes information critical for flight safety, such as
exact clouds type and ceiling.


This is what a TAF report from the United States may look like:

::

    TAF
      AMD KMKE 172034Z 1721/1824 14013G19KT P6SM SCT028 BKN035 BKN250
     FM180100 17008KT P6SM SCT035 BKN120
     FM181000 17007KT P6SM VCSH BKN040 OVC080
      TEMPO 1811/1815 6SM -TSRA BR BKN030CB
     FM181500 18009KT P6SM VCSH BKN050
     FM182100 16012KT P6SM SCT050 BKN150

What it means:

::

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

This means the format (from computer point of view) is loosely
standardized and is not guaranteed to be machine readable.

Moreover, TAF format is not exactly the same in all countries.
Not different enough for people to have problems understanding it,
but different enough to make implementing a universal parser
very hard, if not impossible.

United Stated civil airports produce the most machine friendly and
standardized reports and those are the most likely to be interpreted correctly.
Effort was made to interpret European Union civil airport reports
properly, but they exhibit more regional variations, so the interpretation
may be incomplete.
Remember that the interpretation is provided for information purposes only
and should not be used for flight planning (at least not without inspecting
the original undecoded report).

Information about the US TAF format can be found at NOAA website:
http://aviationweather.gov/static/help/taf-decode.php

You can get raw and interpreted reports from there too:
http://www.aviationweather.gov/adds/tafs/


API
---

pytaf contains two base classes: pytaf.TAF and pytaf.Decoder

The constructor of the TAF class takes a string, takes it apart, and stores raw values in a TAF object.

The Decoder is initialized with a TAF object and provides decode() method that returns a string that contains
a human-readable interpretation.

::

    import pytaf

    taf = pytaf.TAF("<my TAF string>")
    decoder = pytaf.Decoder(taf)
    print(decoder.decode_taf())

This is what a decoded string may look like:

::

    TAF for KSFO issued 05:46 UTC on the 20th, valid from 06:00 UTC on the 20th to 12:00 UTC on the 21st
    Wind: variable at 04 knots 
    Visibility: more than 6 statute miles 
    Sky conditions: few clouds at 1000 feet, scattered clouds at 1500 feet, broken clouds at 20000 feet 


Hacking
-------

If you want to change the decoder output format (e.g. output to HTML),
inherit from pytaf.Decoder and overload the _decode_taf() method.
That method contains nothing but calls to other methods and output
string formatting.

The Decoder class provides methods for decoding every type of weather information independently,
so you can easily combine them to wrap that information in any desirable format.

If you want to redefine the interpretation, e.g. produce numeric values
for display in a widget rather than plain english descriptions, you may want to use the TAF object directly.
All its methods return dicts with pretty straightforward key names.
