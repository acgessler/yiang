
import random

def Update(pfx, type, name):
    
    if type == "vec2":
        pfx.SetParameter(name,random.random(),random.random())
    elif type == "vec3":
        pfx.SetParameter(name,random.random(),random.random(),random.random())
    elif type == "vec4":
        pfx.SetParameter(name,random.random(),random.random(),random.random(),random.random())
    elif type == "float":
        pfx.SetParameter(name,random.random())
    else:
        assert False
        
    