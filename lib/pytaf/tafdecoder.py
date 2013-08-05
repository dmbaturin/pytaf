from taf import TAF

class DecodeError:
    def __init__(msg):
        self.msg = msg

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
                result += "    Clouds: %s \n" % self._decode_clouds(group["clouds"])

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

        # Type
        if header["type"] == "AMD":
            result += "TAF amended for"
        elif header["type"] == "COR":
            result += "TAF corrected for"
        elif header["type"] == "RTD":
           result += "TAF related for"
        else:
            result += "TAF for"

        result += """ %(icao_code)s issued %(origin_date)s %(origin_hours)s:%(origin_minutes)s UTC, valid from %(valid_from_date)s %(valid_from_hours)s:00 UTC to %(valid_till_date)s %(valid_till_hours)s:00 UTC """

        result = result % header

        return(result)

    def _decode_group_header(self, header):
        result = ""

        if header.has_key("type"):
            if header["type"] == "FM":
                result += "From %s %s:%s: " % (header["from_date"], header["from_hours"], header["from_minutes"])
            elif header["type"] == "PROB":
                result += "Probability %s%% of the following between %s %s:00 and %s %s:00: " % (header["probability"], header["from_date"], header["from_hours"], header["till_date"], header["till_hours"])
            elif header["type"] == "TEMPO":
                result += "Temporarily between %s %s:00 and %s %s:00: " % (header["from_date"], header["from_hours"], header["till_date"], header["till_hours"])
            elif header["type"] == "BECMG":
                result += "Gradual change to between %s %s:00 and %s %s:00" % (header["from_date"], header["from_hours"], header["till_date"], header["till_hours"])

        return(result)

    def _decode_wind(self, wind):
        result = ""

        if wind["direction"] == "000":
            result += "calm"
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
                i_result += "scattered "
            elif layer["layer"] == "BKN":
                i_result += "broken "
            elif layer["layer"] == "FEW":
                i_result += "few "
            elif layer["layer"] == "OVC":
                i_result += "overcast "

            if layer["type"] == "CB":
                i_result += "cumulonimbus "
            elif layer["type"] == "CU":
                i_result += "cumulus "
            elif layer["type"] == "TC":
                i_result += "towering cumulus "
            elif layer["type"] == "CI":
                i_result += "cirrus "

            i_result += "at %d feet" % (int(layer["ceiling"])*100)
            list.append(i_result)
            i_result = ""

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
        return(result)

    def _decode_windshear(self, windshear):
        result = "at %s, wind %s at %s %s" % ((int(windshear["altitude"])*100), windshear["direction"], windshear["speed"], windshear["unit"])
        return(result)

    def _decode_maintenance(self, maintenance):
        if maintenance:
            return "Station is under maintenance check\n"

        
