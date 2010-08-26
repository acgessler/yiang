

import os
import re

s = re.compile(r"\VALUES \(\'(\w\w)\',\'[a-zA-Z ]*\',\'([a-zA-Z ]*)\'")
out = open("out.json","wt")
out.write("{\n")
with open("iso_country_list.sql","rt") as a:
    s = re.findall(s,a.read())
    out.write("\n".join(['"{0}" : "{1}",'.format(k,v) for k,v in s]))
out.write("}\n")
        
    
    
