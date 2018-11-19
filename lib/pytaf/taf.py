import re

class MalformedTAF(Exception):
    def __init__(self, msg):
        self.strerror = msg

class TAF(object):
    """ TAF "envelope" parser """

    def __init__(self, string):
        """
        Initializes the object with TAF/METAR report text.

        Args:
            string: TAF/METAR report string

        Raises:
            MalformedTAF: An error parsing the TAF/METAR report
        """

        # Instance variables
        self._raw_taf = None
        self._taf_header = None
        self._raw_weather_groups = []
        self._weather_groups = []
        self._maintenance = None

        if isinstance(string, str) and string != "":
            self._raw_taf = string
        else:
            raise MalformedTAF("TAF/METAR string expected")

        # Patterns use ^ and $, so we don't want
        # leading/trailing spaces
        self._raw_taf = self._raw_taf.strip()

        # Initialize header part
        self._taf_header = self._init_header(self._raw_taf)

        if self._taf_header['form'] == 'metar':
            self._weather_groups.append(self._parse_group(self._raw_taf))
        else:
            # Get all TAF weather groups
            self._raw_weather_groups = self._init_groups(self._raw_taf)

            for group in self._raw_weather_groups:
                parsed_group = self._parse_group(group)
                self._weather_groups.append(parsed_group)

        self._maintenance = self._parse_maintenance(self._raw_taf)

    def _init_header(self, string):
        """ Extracts header part from TAF/METAR string and populates header dict

        Args:
            TAF/METAR report string

        Raises:
            MalformedTAF: An error parsing the report

        Returns:
            Header dictionary
        """

        taf_header_pattern = """
            ^
            (TAF)?    # TAF header (at times missing or duplicate)
            \s*
            (?P<type> (COR|AMD|AMD\sCOR|COR\sAMD|RTD)){0,1}

            \s* # There may or may not be space as COR/AMD/RTD is optional
            (?P<icao_code> [A-Z]{4}) # Station ICAO code

            \s* # at some aerodromes does not appear
            (?P<origin_date> \d{0,2}) # at some aerodromes does not appear
            (?P<origin_hours> \d{0,2}) # at some aerodromes does not appear
            (?P<origin_minutes> \d{0,2}) # at some aerodromes does not appear
            Z? # Zulu time (UTC, that is) # at some aerodromes does not appear

            \s*
            (?P<valid_from_date> \d{0,2})
            (?P<valid_from_hours> \d{0,2})
            /
            (?P<valid_till_date> \d{0,2})
            (?P<valid_till_hours> \d{0,2})
        """

        metar_header_pattern = """
            ^
            (METAR)?    # METAR header (at times missing or duplicate)
            \s*
            (?P<icao_code> [A-Z]{4}) # Station ICAO code

            \s* # at some aerodromes does not appear
            (?P<origin_date> \d{0,2}) # at some aerodromes does not appear
            (?P<origin_hours> \d{0,2}) # at some aerodromes does not appear
            (?P<origin_minutes> \d{0,2}) # at some aerodromes does not appear
            Z? # Zulu time (UTC, that is) # at some aerodromes does not appear
            \s+
            (?P<type> (COR){0,1}) # Corrected # TODO: Any other values possible?
        """

        header_taf = re.match(taf_header_pattern, string, re.VERBOSE)
        header_metar = re.match(metar_header_pattern, string, re.VERBOSE)

        # The difference between a METAR and TAF header isn't that big
        # so it's likely to get both regex to match. TAF is a bit more specific so if
        # both regex match then we're most likely dealing with a TAF string.
        if header_taf:
            header_dict = header_taf.groupdict()
            header_dict['form'] = 'taf'
        elif header_metar:
            header_dict = header_metar.groupdict()
            header_dict['form'] = 'metar'
        else:
            raise MalformedTAF("No valid TAF/METAR header found")

        return header_dict


    def _init_groups(self, string):
        """ Extracts weather groups (FM, PROB etc.) and populates group list

        Args:
            TAF report string

        Raises:
            MalformedTAF: Group decoding error

        """

        taf_group_pattern = """
            (?:FM|(?:PROB(?:\d{1,2})\s*(?:TEMPO)?)|TEMPO|BECMG|[\S\s])[A-Z0-9\+\-/\s$]+?(?=FM|PROB|TEMPO|BECMG|$)
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

        if self._taf_header['form'] == "taf":
            group["header"] = self._parse_group_header(string)

        if self._taf_header['form'] == "metar":
            group["temperature"] = self._parse_temperature(string)
            group["pressure"] = self._parse_pressure(string)

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
            (?P<type> (?:PROB(?P<probability>\d{1,2})\s*(?:TEMPO)?)|TEMPO|BECMG)
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
            (?P<type> CU|CB|TCU|CI){0,1}
            (?= \s|$ )
        """

        special_case_pattern = """ (SKC|CLR|NSC|CAVOK|CAVU) """
        special_case_vv = """VV///"""
        
        clouds = []

        clear = re.search(special_case_pattern, string, re.VERBOSE)
        if clear:
            clouds.append({"layer": clear.group(0)})
            return(clouds)
        
        vv = re.search(special_case_vv, string, re.VERBOSE)
        if vv:
            clouds.append({"layer": vv.group(0)})
            return(clouds)
        

        cloud_layers = re.finditer(clouds_pattern, string, re.VERBOSE)
        for layer in cloud_layers:
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

        weather_word_pattern = """
          (?<= \s )
          ( (?: \+|\-|VC|RE|MI|BC|DR|BL|SH|TS|FZ|PR|DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|DU|SA|HZ|PY|VA|PO|SQ|FC|SS|DS)+ )
          (?= \s|$)
        """

        weather = []

        # At first, find all weather strings in the TAF weather group or METAR string.
        weather_words = re.findall(weather_word_pattern, string, re.VERBOSE)
        for word in weather_words:
            intensities = []
            modifiers = []
            phenomenons = []

            # Find all intensity descriptors...
            while re.match('(\+|\-|VC|RE)', word):
                parsed_intensity = re.match('(\+|\-|VC|RE)', word)
                intensities.append(parsed_intensity.group(0))
                chars_len = len(intensities[-1])
                word = word[chars_len:]

            # Find all modifiers...
            while re.match('(MI|BC|DR|BL|SH|TS|FZ|PR)', word):
                parsed_modifier = re.match('(MI|BC|DR|BL|SH|TS|FZ|PR)', word)
                modifiers.append(parsed_modifier.group(0))
                chars_len = len(modifiers[-1])
                word = word[chars_len:]

            # Find all phenomenon descriptors...
            while re.match('(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|DU|SA|HZ|PY|VA|PO|SQ|FC|SS|DS)', word):
                parsed_phenomenon = re.match('(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|DU|SA|HZ|PY|VA|PO|SQ|FC|SS|DS)', word)
                phenomenons.append(parsed_phenomenon.group(0))
                chars_len = len(phenomenons[-1])
                word = word[chars_len:]

            # ...and put all three lists in a dictionary.
            # There's a dictionary for each weather string found in a TAF weather group or METAR string.
            group_dict = {'intensity' : intensities, 'modifier' : modifiers, 'phenomenon' : phenomenons}
            weather.append(group_dict)

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

    # METAR specific functions
    # TODO: Condition of runway(s)
    # TODO: Parse North American METAR codes (RMK)
    def _parse_temperature(self, string):
        temperature_pattern = """
            (?<= \s )
            (?P<air_prefix> M?)
            (?P<air> \d{2})
            /
            (?P<dewpoint_prefix> M?)
            (?P<dewpoint> \d{2})
            (?= \s|$)
        """

        temperature = re.search(temperature_pattern, string, re.VERBOSE)

        if temperature:
            return(temperature.groupdict())
        else:
            return(None)

    def _parse_pressure(self, string):
        # FIXME: Any other possible values than 'Q' as altimeter setting?
        pressure_pattern = """
            (?<= \s )
            (?P<altimeter_setting> Q)
            (?P<athm_pressure> \d{4})
            (?= \s|$)
        """

        pressure = re.search(pressure_pattern, string, re.VERBOSE)

        if pressure:
            return(pressure.groupdict())
        else:
            return(None)

    # TODO: Calculate relative/absolute humidity
    # Nice-to-have - Not present in a METAR/TAF string, but it can be calculated by air temperature and dewpoint

    # Getters
    def get_taf(self):
        """ Return raw TAF string the object was initialized with """
        return self._raw_taf

    def get_header(self):
        """ Return header dict """
        return(self._taf_header)

    def get_groups(self):
        """ Return weather groups (initial and FM's) """
        return(self._weather_groups)

    def get_maintenance(self):
        """ Return station maintenance indicator """
        return(self._maintenance)
