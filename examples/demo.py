#!/usr/bin/env python

import pytaf

taf_str = """
TAF AMD KDEN 291134Z 2912/3018 32006KT 1/4SM FG OVC001
     TEMPO 2914/2915 1SM -BR CLR
     FM291500 04006KT P6SM SKC
     TEMPO 2915/2917 2SM BR OVC008
     FM291900 05007KT P6SM SCT050 BKN090 WS010/13040KT
     PROB30 2921/3001 VRB20G30KT -TSRA BKN050CB
     FM300100 31007KT P6SM SCT070 BKN120 +FC
     FM300500 23006KT P6SM SCT120 $
"""

# Create a parsed TAF object from string
t = pytaf.TAF(taf_str)

# Create a decoder object from the TAF object
d = pytaf.Decoder(t)

# Print the raw string for the reference
print(taf_str)

# Decode and print the decoded string
dec = d.decode_taf()
print(dec)

