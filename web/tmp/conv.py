

import os
import re

s = re.compile(r"\VALUES \(\'(\w\w)\',\'[a-zA-Z ]*\',\'([a-zA-Z ]*)\'")
with open("out.json","wt") as out:
    out.write("{\n")
    with open("iso_country_list.sql","rt") as a:
        t = "\n".join([',"{0}" : "{1}"'.format(k,v) for k,v in re.findall(s, a.read() )])
    out.write(t[1:])
    out.write("}\n")
        
    
    
