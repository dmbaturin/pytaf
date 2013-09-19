import re
from taf import TAF

class DecodeError:
    def __init__(self, msg):
        self.strerror = msg

class Decoder:
    def __init__(self, taf):
        if isinstance(taf, TAF):
            self._taf = taf
        else:
            raise DecodeError("Argument is not a TAF parser object")

    def decode_taf(self):
        result = ""

        result += self._decode_header(self._taf.get_header()) + "\n"

        for group in self._taf.get_groups():
            if group["header"]:
                result += self._decode_group_header(group["header"]) + "\n"

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

        # Type
        if _header["type"] == "AMD":
            result += "TAF amended for "
        elif _header["type"] == "COR":
            result += "TAF corrected for "
        elif _header["type"] == "RTD":
           result += "TAF related for "
        else:
            result += "TAF for "

        # Add ordinal suffix
        _header["origin_date"] = _header["origin_date"] + self._get_ordinal_suffix(_header["origin_date"])
        _header["valid_from_date"] = _header["valid_from_date"] + self._get_ordinal_suffix(_header["valid_from_date"]) 
        _header["valid_till_date" ] = _header["valid_till_date"] + self._get_ordinal_suffix(_header["valid_till_date"])

        result += ("%(icao_code)s issued %(origin_hours)s:%(origin_minutes)s UTC on the %(origin_date)s, " 
                   "valid from %(valid_from_hours)s:00 UTC on the %(valid_from_date)s to %(valid_till_hours)s:00 UTC on the %(valid_till_date)s")

        result = result % _header

        return(result)

    def _decode_group_header(self, header):
        result = ""
        _header = header

        from_str = "From %(from_hours)s:%(from_minutes)s on the %(from_date)s: "
        prob_str = "Probability %(probability)s%% of the following between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s: "
        tempo_str = "Temporarily between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(from_date)s: "
        becmg_str = "Gradual change to between %(from_hours)s:00 on the %(from_date)s and %(till_hours)s:00 on the %(till_date)s"

        if _header.has_key("type"):
            # Add ordinal suffix
            if _header.has_key("from_date"):
                from_suffix = self._get_ordinal_suffix(_header["from_date"])
                _header["from_date"] = _header["from_date"] + from_suffix
            if _header.has_key("till_date"):
                till_suffix = self._get_ordinal_suffix(_header["till_date"])
                _header["till_date"] = _header["till_date"] + till_suffix

            if _header["type"] == "FM":
                result += from_str % { "from_date":    _header["from_date"], 
                                       "from_hours":   _header["from_hours"],
                                       "from_minutes": _header["from_minutes"] }
            elif _header["type"] == "PROB":
                result += prob_str % { "probability": _header["probability"],
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
        result = ""

        if wind["direction"] == "000":
            return("calm")
        elif wind["direction"] == "VRB":
            result += "variable"
        else:
            result += "from %s degrees" % wind["direction"]

        result += " at %s knots" % wind["speed"]

        if wind["gust"]:
            result += " gusting to %s knots" % wind["gust"]

        return(result)

    def _decode_visibility(self, visibility):
        result = ""

        if visibility.has_key("more"):
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
            elif layer["type"] == "TC":
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
        result = ""
        i_result = ""
        ii_result = ""
        list = []

        for group in weather:
            # Special cases
            if group["intensity"] == "+" and group["phenomenon"] == "FC":
                i_result += "tornado or watersprout"
                list.append(i_result)
                continue

            if group["modifier"] == "MI":
                ii_result += "shallow "
            elif group["modifier"] == "BC":
                ii_result += "patchy "
            elif group["modifier"] == "DR":
                ii_result += "low drifting "
            elif group["modifier"] == "BL":
                ii_result += "blowing "
            elif group["modifier"] == "SH":
                ii_result += "showers "
            elif group["modifier"] == "TS":
                ii_result += "thunderstorms "
            elif group["modifier"] == "FZ":
                ii_result += "freezing "
            elif group["modifier"] == "PR":
                ii_result = "partial "

            if group["phenomenon"] == "DZ":
                ii_result += "drizzle"
            if group["phenomenon"] == "RA":
                ii_result += "rain"
            if group["phenomenon"] == "SN":
                ii_result += "snow"
            if group["phenomenon"] == "SG":
                ii_result += "snow grains"
            if group["phenomenon"] == "IC":
                ii_result += "ice"
            if group["phenomenon"] == "PL":
                ii_result += "ice pellets"
            if group["phenomenon"] == "GR":
                ii_result += "hail"
            if group["phenomenon"] == "GS":
                ii_result += "small snow/hail pellets"
            if group["phenomenon"] == "UP":
                ii_result += "unknown precipitation"
            if group["phenomenon"] == "BR":
                ii_result += "mist"
            if group["phenomenon"] == "FG":
                ii_result += "fog"
            if group["phenomenon"] == "FU":
                ii_result += "smoke"
            if group["phenomenon"] == "DU":
                ii_result += "dust"
            if group["phenomenon"] == "SA":
                ii_result += "sand"
            if group["phenomenon"] == "HZ":
                ii_result += "haze"
            if group["phenomenon"] == "PY":
                ii_result += "spray"
            if group["phenomenon"] == "VA":
                ii_result += "volcanic ash"
            if group["phenomenon"] == "PO":
                ii_result += "dust/sand whirl"
            if group["phenomenon"] == "SQ":
                ii_result += "squall"
            if group["phenomenon"] == "FC":
                ii_result += "funnel cloud"
            if group["phenomenon"] == "SS":
                ii_result += "sand storm"
            if group["phenomenon"] == "DS":
                ii_result += "dust storm"

            # Fix the most ugly grammar
            if group["modifier"] == "SH" and group["phenomenon"] == "RA":
                ii_result = "showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "SN":
                ii_result = "snow showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "SG":
                ii_result = "snow grain showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "PL":
                ii_result = "ice pellet showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "IC":
                ii_result = "ice showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "GS":
                ii_result = "snow pellet showers"
            if group["modifier"] == "SH" and group["phenomenon"] == "GR":
                ii_result = "hail showers"

            if group["modifier"] == "TS" and group["phenomenon"] == "RA":
                ii_result = "thunderstorms and rain"
            if group["modifier"] == "TS" and group["phenomenon"] == "UP":
                ii_result = "thunderstorms with unknown precipitation"

            if group["intensity"] == "+":
                i_result = "heavy %s" % ii_result
            elif group["intensity"] == "-":
                i_result = "light %s" % ii_result
            elif group["intensity"] == "VC":
                i_result = "%s in the vicinity" % ii_result
            else:
                i_result = ii_result

            list.append(i_result)
            i_result = ""
            ii_result = ""

        result = ", ".join(list)

        # Remove extra whitespace, if any
        result = re.sub(r'\s+', ' ', result)
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
        
