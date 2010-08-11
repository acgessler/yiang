
import defaults

def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            assert type == "vec2"
            
            if hasattr(self,"game") is False or not self.game.level:
                return

            pfx.SetParameter(name,self.game.GetUpperStatusBarHeight()/defaults.tiles[1],
                (self.game.GetLowerStatusBarHeight()+0.1)/defaults.tiles[1])
            
        def SetOuterParam(self,name,value):
            if name == "game":
                self.game = value
    
    return Updater()

