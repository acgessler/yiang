

def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            assert type == "texture"

            pfx.SetTexture(name,None)
    
    return Updater()
