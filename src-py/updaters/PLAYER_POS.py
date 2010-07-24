
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
            pfx.SetParameter(name, (player.pos[0] + player.pwidth // 2 - origin[0]) / defaults.tiles[0],
                1.0 - (player.pos[1] + player.pheight // 2 - origin[1]) / defaults.tiles[1])
            
        def SetOuterParam(self,name,value):
            if name == "game":
                self.game = value
                
    return Updater()
        