#!echo "This file is not executable"
# -*- coding: UTF_8 -*-

#/////////////////////////////////////////////////////////////////////////////////
# Yet Another Jump'n'Run Game, unfair this time.
# (c) 2010 Alexander Christoph Gessler
#
# HIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ///////////////////////////////////////////////////////////////////////////////////

# PySFML
import sf

# My own stuff
import defaults
from game import Entity,Game
from tile import Tile,AnimTile
from player import Player
from level import Level
from renderer import NewFrame

# Python stuff
import operator


class Sender(AnimTile):
    """The sender teleport brick transports the player to the
    closest receiver brick with the same color"""

    def __init__(self,text,height=3,frames=5,speed=4.0):
        AnimTile.__init__(self,text,height,frames,speed)

    def Interact(self,other):
        if isinstance(other, Player):
            lv = self.game.GetLevel()
            assert not lv is None
            
            mypos = self.pos
            
            candidates = []
            for entity in lv.EnumAllEntities():
                if isinstance(entity,Receiver) and entity.color == self.color:
                    
                    pos = entity.pos
                    candidates.append(((pos[0]-mypos[0])**2 + (pos[1]-mypos[1])**2,entity))
                    
            if len(candidates)==0:
                print("Failed to find teleport target, my color is {0}".format(self.color))
                
            else:
                target = sorted(candidates,key=operator.itemgetter(0))[0][1]
                print("Teleport to {0} at position {1}".format(target,target.pos))
                other.SetPositionAndMoveView(target.pos)
                raise NewFrame()
        
        return Entity.ENTER

    def GetVerboseName(self):
        return "a sender teleport brick"
    
    
class Receiver(AnimTile):
    """The receiver teleport brick acts as target for teleports"""
    
    def __init__(self,text,height=3,frames=5,speed=4.0):
        AnimTile.__init__(self,text,height,frames,speed)
        
    def Interact(self,other):
        return Entity.ENTER

    def GetVerboseName(self):
        return "a receiver teleport brick"
    
    
    
    