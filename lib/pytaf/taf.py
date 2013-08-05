import re

class MalformedTAF(Exception):
    def __init__(self, msg):
        self.strerror = msg

class TAF:
    """ TAF "envelope" parser """

    def __init__(self, string):
        # Instance variables
        self._raw_taf = None
        self._taf_header = None
        self._raw_weather_groups = []
        self._weather_groups = []
        self._maintenance = None

        if isinstance(string, str) and string != "":
            self._raw_taf = string
        else:
            raise MalformedTAF("TAF string expected")

        # Patterns use ^ and $, so we don't want
        # leading/trailing spaces
        self._raw_taf = self._raw_taf.strip()

        # Initialize header part
        self._taf_header = self._init_header(self._raw_taf)

        # Get weather groups
        self._raw_weather_groups = self._init_groups(self._raw_taf)

        for group in self._raw_weather_groups:
            parsed_group = self._parse_group(group)
            self._weather_groups.append(parsed_group)

        self._maintenance = self._parse_maintenance(self._raw_taf)

    def _init_header(self, string):
        """ Extract header part from TAF string and populate header dict """

        taf_header_pattern = """
            ^
            TAF*    # TAF header (at times missing or duplicate)
            \s+
            (?P<type> (COR|AMD|RTD)){0,1} # Corrected/Amended/Related
             
            \s* # There may or may not be space as COR/AMD/RTD is optional
            (?P<icao_code> [A-Z]{4}) # Station ICAO code
            
            \s+
            (?P<origin_date> \d{2})
            (?P<origin_hours> \d{2})
            (?P<origin_minutes> \d{2})
            Z # Zulu time (UTC, that is)
            
            \s+
            (?P<valid_from_date> \d{2})
            (?P<valid_from_hours> \d{2})
            /
            (?P<valid_till_date> \d{2})
            (?P<valid_till_hours> \d{2})
        """

        header = re.match(taf_header_pattern, string, re.VERBOSE)

        if header:
             return header.groupdict()
        else:
            raise MalformedTAF("No valid TAF header found")

    def _init_groups(self, string):
        """ Extract weather groups """

        taf_group_pattern = """
            (?:Z\s+\d{4}/\d{4}|FM|PROB|TEMPO|BECMG)[A-Z0-9\+\-/\s$]+?(?=FM|PROB|TEMPO|BECMG|$)
        """

        group_list = []

        groups = re.findall(taf_group_pattern, string, re.VERBOSE)
        if not groups:
            raise MalformedTAF("No valid groups found")

        for group in groups:
            group_list.append(group)

        return(group_list)

    def _parse_group(self, string):
        group = {}

        group["header"] = self._parse_group_header(string)
        group["wind"] = self._parse_wind(string)
        group["visibility"] = self._parse_visibility(string)
        group["clouds"] = self._parse_clouds(string)
        group["vertical_visibility"] = self._parse_vertical_visibility(string)
        group["weather"] = self._parse_weather_phenomena(string)
        group["windshear"] = self._parse_wind_shear(string)

        return(group)
         
    def _parse_group_header(self, string):
        # From header pattern
        fm_pattern = """
            (?P<type> FM) (?P<from_date>\d{2}) (?P<from_hours>\d{2})(?P<from_minutes> \d{2})
        """

        # PROB|TEMPO|BECMG header pattern, they have almost the same format
        ptb_pattern = """
            (?P<type> PROB|TEMPO|BECMG)
            (?P<probability>\d{1,2}){0,1} # For PROB, this is probability
            \s+
            (?P<from_date> \d{2})
            (?P<from_hours> \d{2})
            /
            (?P<till_date> \d{2})
            (?P<till_hours> \d{2})
        """

        header = {}

        # Get type and associated fields
        fm = re.search(fm_pattern, string, re.VERBOSE)
        if fm:
            header = fm.groupdict()

        ptb = re.search(ptb_pattern, string, re.VERBOSE)
        if ptb:
            header = ptb.groupdict()

        return(header)

    def _parse_wind(self, string):
        wind_pattern = """
            (?<= \s )
            (?P<direction> (\d{3}|VRB)) # Three digits or VRB
            (?P<speed> \d{2,3})         # Next two digits are speed in knots
            (G(?P<gust> \d{2,3})){0,1}  # Optional gust data (Gxx)
            (?P<unit> KT|MPS)           # Knots or meters per second
            (?= \s|$ )
        """

        wind = re.search(wind_pattern, string, re.VERBOSE)

        if wind:
            return(wind.groupdict())
        else:
            return(None)

    def _parse_visibility(self, string):
        # Visibility in statute miles
        visibility_pattern = """
            (?<= \s )
            (?P<more> P){0,1} # "P" prefix indicates visibility more than
            (?P<range> \d | \d/\d | \d\s\d/\d)    # More than 6 is always just P6SM
            (?P<unit> SM)                # Statute miles
            (?= \s|$ )
        """

        # Visibility in meters
        # XXX: In case "TEMPO 1012" style reports still exist,
        # it will not work as is and I haven't came up with a fix yet
        visibility_meters_pattern = """
            (?<= \s )
            (?P<range> \d{4})
            (?= \s|$ )
        """

        visibility = {}

        # US-style
        visibility_sm = re.search(visibility_pattern, string, re.VERBOSE)
        if visibility_sm:
            visibility = visibility_sm.groupdict()
         
        # Metric style
        visibility_meters = re.search(visibility_meters_pattern, string, re.VERBOSE)
        if visibility_meters:
            visibility["range"] = visibility_meters.group("range")
            # 9999 in fact means "more than 10 km"
            if visibility_meters.group("range") == "9999":
                visibility["more"] = True
                visibility["range"] = "10 000"
            visibility["unit"] = "M"

        return(visibility)

    def _parse_clouds(self, string):
        clouds_pattern = """
            (?<= \s )
            (?P<layer> BKN|SCT|FEW|OVC)
            (?P<ceiling> \d{3})
            (?P<type> CU|CB|TC|CI){0,1}
            (?= \s|$ )
        """

        sky_clear_pattern = """ (SKC|CLR) """

        clouds = []

        clear = re.search(sky_clear_pattern, string, re.VERBOSE)
        if clear:
            clouds.append({"layer": clear.group(0)})
            return(clouds)

        cloud_layers = re.finditer(clouds_pattern, string, re.VERBOSE)
        for layer in cloud_layers:
            # SKC or CLR mean "sky clear", nothing to do
#            if layer.group("layer") == "SKC" or layer.group("layer") == "CLR":
#                clouds = []
#                break
 #           else:
            clouds.append(layer.groupdict())
          
        return(clouds)

    def _parse_vertical_visibility(self, string):

        vertical_visibility_pattern = """
            (?<= \s )
            VV
            (?P<vertical_visibility> \d{3} )
            (?= \s|$ )
        """

        vertical_visibility = None

        vv = re.search(vertical_visibility_pattern, string, re.VERBOSE)
        if vv:
            vertical_visibility = vv.group("vertical_visibility")

        return(vertical_visibility)

    def _parse_weather_phenomena(self, string):


        # XXX: The problem here is that from the intensity (+|-|VC), modifier (MI|BC|...)
        # and phenomenon (RA|SN|...) either one, two, or three can be present
        # which makes the detailed regex not specific enough and prone to catching
        # weird stuff.
        # So we first search for words that look like weather descriptors,
        # then analyze them in detail.
        # If there is a better way, it should be used here instead of this hack.

        weather_word_pattern = """
          (?<= \s )
          ( (?: \+|\-|VC|MI|BC|DR|BL|SH|TS|FZ|PR|DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|DU|SA|HZ|PY|VA|PO|SQ|FC|SS|DS)+ )
          (?= \s|$)
        """

        weather_pattern = """
            (?P<intensity> \+|\-|VC ){0,1}
            (?P<modifier> MI|BC|DR|BL|SH|TS|FZ|PR ){0,1}
            (?P<phenomenon> DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|DU|SA|HZ|PY|VA|PO|SQ|FC|SS|DS ){0,1}
        """
        
        weather = []

        weather_words = re.findall(weather_word_pattern, string, re.VERBOSE)
        for word in weather_words:
            parsed_word = re.search(weather_pattern, word, re.VERBOSE)
            weather.append(parsed_word.groupdict())

        return(weather)

    def _parse_wind_shear(self, string):
        wind_shear_pattern = """
            \s+
            WS (?P<altitude> \d{3})
            /
            (?P<direction> \d{3})
            (?P<speed> \d{2})
            (?P<unit> KT|MPS)
        """

        windshear = re.search(wind_shear_pattern, string, re.VERBOSE)

        if windshear:
            return(windshear.groupdict())
        else:
            return(None)

    def _parse_maintenance(self, string):
        maintenance_pattern = """ ( \$ ) """

        maintenance = re.search(maintenance_pattern, string, re.VERBOSE)

        if maintenance:
            return(maintenance.group(0))
        else:
            return(None)

    def get_taf(self):
        """ Return raw TAF string the object was initialized with """
        return self.__raw_taf

    def get_header(self):
        """ Return header dict """
        return(self._taf_header)

    def get_groups(self):
        """ Return weather groups (initial and FM's) """
        return(self._weather_groups)

    def get_maintenance(self):
        """ Return station maintenance indicator """
        return(self._maintenance)
