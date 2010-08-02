
import defaults
from player import Player


def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            
            assert type == "vec2"
            if hasattr(self,"game") is False or not self.game.GetLevel():
                return
            
            candidates = (entity for entity in self.game.GetLevel().EnumActiveEntities() if isinstance(entity,Player))
            
            try:
                player = sorted(candidates,key=lambda x:x.pos[0],reverse=True)[0]
            except IndexError:
                return
            
            origin = self.game.GetLevel().GetOrigin()
            x,y = ((player.pos[0] + player.pwidth // 2 - origin[0]) / defaults.tiles[0],
                1.0 - (player.pos[1] + player.pheight // 2 - origin[1]) / defaults.tiles[1])
                
            # fix for editor mode: if the player is outside the valid range,
            # why not simply make the postfx belief he's at the center?
            # Usually, this will make sure that this part of the screen
            # appears visible and undistorted.
            if  x < -0.1 or x > 1.1 or y < -0.1 or y > 1.1 or (self.game.GetGameMode()==3 and not self.game.IsGameRunning()):
                x = y = 0.5
                
            pfx.SetParameter(name,x,y)
            
        def SetOuterParam(self,name,value):
            if name == "game":
                self.game = value
                
    return Updater()
        