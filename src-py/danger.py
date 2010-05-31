# PySFML
import sf

# My own stuff
import defaults
from game import Entity,TileLoader,Game,Tile,AnimTile

class DangerousBarrel(AnimTile):
    """This entity is an animated barrel which kills
    the player immediately when he touches it"""

    def __init__(self,text,height,frames,speed,randomize):
        AnimTile.__init__(self,text,height,frames,speed)

        if randomize is True:
            self.GotoRandom()

    def Interact(self,other,game):
        return Entity.KILL


    
