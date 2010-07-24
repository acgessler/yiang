
import defaults

def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            assert type == "float"
            
            if hasattr(self,"game") is False or not self.game.GetLevel():
                return

            pfx.SetParameter(name,self.game.GetLevel().dither_strength)
            
        def SetOuterParam(self,name,value):
            if name == "game":
                self.game = value
    
    return Updater()

