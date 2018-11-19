# -*- coding: utf-8 -*-

import re
from .taf import TAF

class DecodeError(Exception):
    def __init__(self, msg):
        self.strerror = msg

class Decoder(object):
    def __init__(self, taf):
        if isinstance(taf, TAF):
            self._taf = taf
        else:
            raise DecodeError("Argument is not a TAF parser object")

    def decode_taf(self):
        form = self._taf.get_header()["form"]
        result = ""

        result += self._decode_header(self._taf.get_header()) + "\n"

        for group in self._taf.get_groups():
            # TAF specific stuff
            if form == "taf":
                if group["header"]:
                    result += self._decode_group_header(group["header"]) + "\n"

            # METAR specific stuff
            if form == "metar":
                if group["temperature"]:
                    result += "    Temperature: %s\n" % self._decode_temperature(group["temperature"])

                if group["pressure"]:
                    result += "    Pressure: %s\n" % self._decode_pressure(group["pressure"])

            # Both TAF and METAR
            if group["wind"]:
                result += "    Wind: %s \n" % self._decode_wind(group["wind"])

            if group["visibility"]:
                result += "    Visibility: %s \n" % self._decode_visibility(group["visibility"])

            if group["clouds"]:
                result += "    Sky conditions: %s \n" % self._decode_clouds(group["clouds"])

            if group["weather"]:
                result += "    Weather: %s \n" % self._decode_weather(group["weather"])

            if group["windshear"]:
                result += "    Windshear: %s\n" % self._decode_windshear(group["windshear"])

            result += " \n"

        if self._taf.get_maintenance():
            result += self._decode_maintenance(self._taf.get_maintenance())

        return(result)

    def _decode_header(self, header):
        result = ""

        # Ensure it's side effect free
        _header = header

        if _header["form"] == 'taf':
            # Decode TAF header
            # Type
            if _header["type"] == "AMD":
                result += "TAF amended for "
            elif _header["type"] == "COR":
                result += "TAF corrected for "
            elif _header["type"] == "RTD":
                result += "TAF delayed for "
            elif _header["type"] == "AMD COR":
                result += "TAF amended and corrected for "
            elif _header["type"] == "COR AMD":
                result += "TAF corrected and amended for "
            else:
                result += "TAF for "

            # Add ordinal suffix
            _header["origin_date"] = _header["origin_date"] + self._get_ordinal_suffix(_header["origin_date"])
            _header["valid_from_date"] = _header["valid_from_date"] + self._get_ordinal_suffix(_header["valid_from_date"])
            _header["valid_till_date" ] = _header["valid_till_date"] + self._get_ordinal_suffix(_header["valid_till_date"])

            result += ("%(icao_code)s issued %(origin_hours)s:%(origin_minutes)s UTC on the %(origin_date)s, " 
                       "valid from %(valid_from_hours)s:00 UTC on the %(valid_from_date)s to %(valid_till_hours)s:00 UTC on the %(valid_till_date)s")
        else:
            # Decode METAR header
            # Type
            if _header["type"] == "COR":
                result += "METAR corrected for "
            else:
                result += "METAR for "

            _header["origin_date"] = _header["origin_date"] + self._get_ordinal_suffix(_header["origin_date"])

            result += ("%(icao_code)s issued %(origin_hours)s:%(origin_minutes)s UTC on the %(origin_date)s")

        result = result % _header

        return(result)

    def _decode_group_header(self, header):
        result = ""
        _header = header

        from_str = "From %(from_hours)s:%(from_minutes)s on the %(from_date)s: "
        prob_str = "Probability %(probability)s%% of the following between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s: "
        tempo_str = "Temporarily between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s: "
        prob_tempo_str = "Probability %(probability)s%% of the following temporarily between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s: "
        becmg_str = "Gradual change to the following between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s: "

        if "type" in _header:
            # Add ordinal suffix
            if "from_date" in _header:
                from_suffix = self._get_ordinal_suffix(_header["from_date"])
                _header["from_date"] = _header["from_date"] + from_suffix
            if "till_date" in _header:
                till_suffix = self._get_ordinal_suffix(_header["till_date"])
                _header["till_date"] = _header["till_date"] + till_suffix

            if _header["type"] == "FM":
                result += from_str % { "from_date":    _header["from_date"],
                                       "from_hours":   _header["from_hours"],
                                       "from_minutes": _header["from_minutes"] }
            elif _header["type"] == "PROB%s" % (_header["probability"]):
                result += prob_str % { "probability": _header["probability"],
                                       "from_date":   _header["from_date"],
                                       "from_hours":  _header["from_hours"],
                                       "till_date":   _header["till_date"],
                                       "till_hours":  _header["till_hours"] }
            elif "PROB" in _header["type"] and "TEMPO" in _header["type"]:
                result += prob_tempo_str % { "probability": _header["probability"],
                                           "from_date":   _header["from_date"],
                                           "from_hours":  _header["from_hours"],
                                           "till_date":   _header["till_date"],
                                           "till_hours":  _header["till_hours"] }
            elif _header["type"] == "TEMPO":
                result += tempo_str % { "from_date":  _header["from_date"],
                                        "from_hours": _header["from_hours"],
                                        "till_date":  _header["till_date"],
                                        "till_hours": _header["till_hours"] }
            elif _header["type"] == "BECMG":
                result += becmg_str % { "from_date":  _header["from_date"],
                                        "from_hours": _header["from_hours"],
                                        "till_date":  _header["till_date"],
                                        "till_hours": _header["till_hours"] }

        return(result)

    def _decode_wind(self, wind):
        unit = ""
        result = ""

        if wind["direction"] == "000":
            return("calm")
        elif wind["direction"] == "VRB":
            result += "variable"
        else:
            result += "from %s degrees" % wind["direction"]

        if wind["unit"] == "KT":
            unit = "knots"
        elif wind["unit"] == "MPS":
            unit = "meters per second"
        else:
            # Unlikely, but who knows
            unit = "(unknown unit)"

        result += " at %s %s" % (wind["speed"], unit)

        if wind["gust"]:
            result += " gusting to %s %s" % (wind["gust"], unit)

        return(result)

    def _decode_visibility(self, visibility):
        result = ""

        if "more" in visibility:
            if visibility["more"]:
                result += "more than "

        result += visibility["range"]

        if visibility["unit"] == "SM":
            result += " statute miles"
        elif visibility["unit"] == "M":
            result += " meters"

        return(result)

    def _decode_clouds(self, clouds):
        result = ""
        i_result = ""
        list = []

        for layer in clouds:
            if layer["layer"] == "SKC" or layer["layer"] == "CLR":
                return "sky clear"

            if layer["layer"] == "NSC":
                return "no significant cloud"

            if layer["layer"] == "CAVOK":
                return "ceiling and visibility are OK"

            if layer["layer"] == "CAVU":
                return "ceiling and visibility unrestricted"

            if layer["layer"] == "VV///":
                return "Sky Obscured"

            if layer["layer"] == "SCT":
                layer_type = "scattered"
            elif layer["layer"] == "BKN":
                layer_type = "broken"
            elif layer["layer"] == "FEW":
                layer_type = "few"
            elif layer["layer"] == "OVC":
                layer_type = "overcast"

            if layer["type"] == "CB":
                type = "cumulonimbus"
            elif layer["type"] == "CU":
                type = "cumulus"
            elif layer["type"] == "TCU":
                type = "towering cumulus"
            elif layer["type"] == "CI":
                type = "cirrus"
            else:
                type = ""

            result = "%s %s clouds at %d feet" % (layer_type, type, int(layer["ceiling"])*100)

            # Remove extra whitespace, if any
            result = re.sub(r'\s+', ' ', result)

            list.append(result)

            layer = ""
            type = ""
            result = ""

        result = ", ".join(list)
        return(result)

    def _decode_weather(self, weather):
        # Dicts for translating the abbreviations
        dict_intensities = {
            "-" : "light",
            "+" : "heavy",
            "VC" : "in the vicinity",
            "RE" : "recent"
        }

        dict_modifiers = {
            "MI" : "shallow",
            "BC" : "patchy",
            "DR" : "low drifting",
            "BL" : "blowing",
            "SH" : "showers",
            "TS" : "thunderstorms",
            "FZ" : "freezing",
            "PR" : "partial"
        }

        dict_phenomenons = {
            "DZ" : "drizzle",
            "RA" : "rain",
            "SN" : "snow",
            "SG" : "snow grains",
            "IC" : "ice",
            "PL" : "ice pellets",
            "GR" : "hail",
            "GS" : "small snow/hail pellets",
            "UP" : "unknown precipitation",
            "BR" : "mist",
            "FG" : "fog",
            "FU" : "smoke",
            "DU" : "dust",
            "SA" : "sand",
            "HZ" : "haze",
            "PY" : "spray",
            "VA" : "volcanic ash",
            "PO" : "dust/sand whirl",
            "SQ" : "squall",
            "FC" : "funnel cloud",
            "SS" : "sand storm",
            "DS" : "dust storm",
        }

        weather_txt_blocks = []

        # Check for special cases first. If a certain combination is found
        # then skip parsing the whole weather string and return a defined string
        # immediately
        for group in weather:
            # +FC = Tornado or Waterspout
            if "+" in group["intensity"] and "FC" in group["phenomenon"]:
                weather_txt_blocks.append("tornado or waterspout")
                continue

            # Sort the elements of the weather string, if no special combi-
            # nation is found.
            intensities_pre = []
            intensities_post = []
            if "RE" in group["intensity"]:
                intensities_pre.append("RE")
                group["intensity"].remove("RE")
            for intensity in group["intensity"]:
                if intensity != "VC":
                    intensities_pre.append(intensity)
                else:
                    intensities_post.append(intensity)

            modifiers_pre = []
            modifiers_post = []
            for modifier in group["modifier"]:
                if modifier != "TS" and modifier != "SH":
                    modifiers_pre.append(modifier)
                else:
                    modifiers_post.append(modifier)

            phenomenons_pre = []
            phenomenons_post = []
            for phenomenon in group["phenomenon"]:
                if phenomenon != "UP":
                    phenomenons_pre.append(phenomenon)
                else:
                    phenomenons_post.append(phenomenon)

            # Build the human readable text from the single weather string
            # and append it to a list containing all the interpreted text
            # blocks from a TAF group
            weather_txt = ""
            for intensity in intensities_pre:
                weather_txt += dict_intensities[intensity] + " "

            for modifier in modifiers_pre:
                weather_txt += dict_modifiers[modifier] + " "

            phenomenons = phenomenons_pre + phenomenons_post
            cnt = len(phenomenons)
            for phenomenon in phenomenons:
                weather_txt += dict_phenomenons[phenomenon]
                if cnt > 2:
                    weather_txt += ", "
                if cnt == 2:
                    weather_txt += " and "
                cnt = cnt-1
            weather_txt += " "

            for modifier in modifiers_post:
                weather_txt += dict_modifiers[modifier] + " "

            for intensity in intensities_post:
                weather_txt += dict_intensities[intensity] + " "

            weather_txt_blocks.append(weather_txt.strip())

        # Put all the human readable stuff together and return the final
        # output as a string.
        weather_txt_full = ""
        for block in weather_txt_blocks[:-1]:
            weather_txt_full += block + " / "
        weather_txt_full += weather_txt_blocks[-1]

        return(weather_txt_full)

    def _decode_temperature(self, temperature, unit='C'):
        if temperature["air_prefix"] == 'M':
            air_c = int(temperature["air"])*-1
        else:
            air_c = int(temperature["air"])

        if temperature["dewpoint_prefix"] == 'M':
            dew_c = int(temperature["dewpoint"])*-1
        else:
            dew_c = int(temperature["dewpoint"])

        if unit == 'C':
            air_txt = air_c
            dew_txt = dew_c

        if unit == 'F':
            air_f = int(round(air_c*1.8+32))
            dew_f = int(round(dew_c*1.8+32))
            air_txt = air_f
            dew_txt = dew_f

        result = "air at %s%s, dewpoint at %s%s" % (air_txt, unit, dew_txt, unit)
        return(result)

    def _decode_pressure(self, pressure):
        result = "%s hPa" % (pressure["athm_pressure"])
        return(result)

    def _decode_windshear(self, windshear):
        result = "at %s, wind %s at %s %s" % ((int(windshear["altitude"])*100), windshear["direction"], windshear["speed"], windshear["unit"])
        return(result)

    def _decode_maintenance(self, maintenance):
        if maintenance:
            return "Station is under maintenance check\n"

    def _get_ordinal_suffix(self, date):
        _date = str(date)

        suffix = ""

        if re.match(".*(1[12]|[04-9])$", _date):
            suffix = "th"
        elif re.match(".*1$", _date):
            suffix = "st"
        elif re.match(".*2$", _date):
            suffix = "nd"
        elif re.match(".*3$", _date):
            suffix = "rd"

        return(suffix)
