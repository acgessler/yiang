
import random

def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            if type == "vec2":
                pfx.SetParameter(name, random.random(), random.random())
            elif type == "vec3":
                pfx.SetParameter(name, random.random(), random.random(), random.random())
            elif type == "vec4":
                pfx.SetParameter(name, random.random(), random.random(), random.random(), random.random())
            elif type == "float":
                pfx.SetParameter(name, random.random())
            else:
                assert False

    
    return Updater()


        
    