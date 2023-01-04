from __future__ import annotations

import re
import math

import bot.commands


class conversion_set():
    keys = []
    rexp = {}
    ideal_key = ''
    convert_to = {}
    convert_from = {}
    
    regexp_set = ''
    
    def __init__(self, keys_in, convert_to_in, convert_from_in, rexp_in="", ideal_key="", second_key=""):
        self.keys = keys_in
        if rexp_in == "":
            self.rexp = {i:i for i in keys_in}
        else:
            self.rexp = rexp_in
        self.convert_to = convert_to_in
        self.convert_from = convert_from_in
        
        if ideal_key == "":
            self.ideal_key = keys_in[0]
            self.second_key = keys_in[1]
        else:
            self.ideal_key = ideal_key
            if second_key == "":
                if self.ideal_key == keys_in[1]:
                    self.second_key = keys_in[0]
                else:
                    self.second_key = keys_in[1]
            else:
                self.second_key = second_key
        
        self.form_regexp()
        
    def form_regexp(self):
        self.regexp_set = "|".join([str(i_rexp) for i_rexp in self.rexp.values()])
        self.matcher = re.compile("(" + self.regexp_set + ")")
        
    def get_regexp_set(self) -> str:
        return self.regexp_set
    def get_re(self) -> re.Pattern:
        return self.matcher
    def get_keys(self):
        return self.keys
    
    def get_preferred(self) -> str:
        return self.ideal_key
    def get_secondary(self) -> str:
        return self.second_key
    
    def convert(self, key_in, num_in, key_out):
        val_1 = self.convert_from[key_in](num_in)
        val_2 = self.convert_to[key_out](val_1)
        return val_2
        
    def convert_all(self, key_in, num_in):
        # Change to index 1
        # (Uses Convert_from)
        val_1 = self.convert_from[key_in](num_in)
        
        out = [self.convert_to[i_key](val_1) for i_key in self.convert_to.keys()]
        return out
    
    def determine_key(self, unit):
        # Basically go from the regexp to the key.
        for i_key in self.get_keys():
            this_matcher = re.compile("(" + self.rexp[i_key] + ")")
            if bool(this_matcher.search(unit)):
                return i_key
            
        return ''
    
    def determine_target_keys(self, unit):
        # Determine key
        this_key = self.determine_key(unit)
        
        # Process
        target_keys = []
        if not (self.get_preferred() == this_key):
            target_keys.append(self.get_preferred())
        if not (self.get_secondary() == this_key):
            target_keys.append(self.get_secondary())
        return(target_keys)
    
class conversion_set_number(conversion_set):
    def __init__(self, keys_in, numbers_in, rexp_in="", ideal_key=""):
        convert_to_in = {}
        convert_from_in = {}
        for i_key in keys_in:
            # Normalise numbers_in based off #1
            i_num = numbers_in[i_key]
            i_num_normalised = i_num/numbers_in[keys_in[0]]
            
            convert_to_in[i_key] = lambda t, b=i_num_normalised: t*b
            convert_from_in[i_key] = lambda t, b=i_num_normalised: t/b
        
        super().__init__(keys_in, convert_to_in, convert_from_in, rexp_in, ideal_key)

conversion_sets = [
    conversion_set(['°C','°F','°K','°R'],
                   {'°C': lambda x: x,
                    '°F': lambda t: (t*9/5)+32,
                    '°K': lambda t: t+273.15,
                    '°R': lambda t: (t*9/5)+32+459.67},
                   {'°C': lambda x: x,
                    '°F': lambda t: (t-32)*(5/9),
                    '°K': lambda t: t-273.15,
                    '°R': lambda t: (t-32-459.67)*(5/9)},
                   rexp_in = {'°C':'[°]?C','°F':'[°]?F','°K':'[°]?K','°R':'[°]?R'},
                   ideal_key = '°C',
                   second_key = '°F')
    ]

MATCHER = re.compile("(?P<value>-?\\d+(\\.\\d+)?)°? *(?P<unit>%s)(\\s|$|[,;.])"
                     % "|".join(a.get_regexp_set() for a in conversion_sets))


class TemperatureCommand(bot.commands.Command):
    def __init__(self) -> None:
        pass

    def matches(self, message: str) -> bool:
        return bool(MATCHER.search(message))

    async def process(self, context: bot.commands.MessageContext, message: str) -> bool:
        output = []

        for match in MATCHER.finditer(message):
            try:
                temp = float(match.group("value"))
                unit = match.group("unit").upper()
            except ValueError:
                return False

            conversion = self.convert(temp, unit)
            if conversion:
                output.append(conversion)

        if output:
            await context.reply_all("**Conversions!**: " + "; ".join(output))

        return True

    @staticmethod
    def convert(value: float, unit: str) -> str:
        # Find which conversion set this is part of
        i_set_use = -1
        for i_set in range(len(conversion_sets)):
            if bool(conversion_sets[i_set].get_re().search(unit)):
                i_set_use = i_set
                break;
        if i_set_use == -1:
            return ''
        
        # Target vals
        target_keys = conversion_sets[i_set].determine_target_keys(unit)
        
        init_unit = conversion_sets[i_set].determine_key(unit)
        output = f"{value:.1f}{init_unit} is"
        for i_target_key in target_keys:
            new_value = conversion_sets[i_set].convert(init_unit,value,i_target_key)
            order_of_mag = math.log10(abs(new_value))
            if (-1 < order_of_mag) or (order_of_mag < 5):
                out_text = f" {new_value:.1f}"
            else:
                out_text = f" {new_value:.3e}"
            out_text += i_target_key
            output += out_text
        output += '.'
        
        return output