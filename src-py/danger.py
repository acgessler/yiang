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
from enemy import Enemy

class DangerousBarrel(AnimTile):
    """This entity is an animated barrel which kills
    the player immediately when he touches it"""

    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,hideontouch=False):
        AnimTile.__init__(self,text,height,frames,speed)

        self.hideontouch = hideontouch
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        return Entity.KILL if other.color != self.color else Entity.BLOCK

    def GetVerboseName(self):
        return "a deathly barrel (it's hilarious!)"

class Mine(AnimTile):
    """This entity is an animated mine which kills
    the player after the animation of the explosion ended"""
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,radius=3,hideontouch=False):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=None)
        self.mine_activated = False
        self.radius = radius
        self.hideontouch = hideontouch
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        if self.mine_activated:
            return Entity.ENTER
        else:
            self.Set(0)
            self.SetState(1)
            self.DeathTimer = sf.Clock()
            self.DeathTimerEnd = (self.GetNumFrames()-1)*self.speed
            self.__other = other
            self.mine_activated = True
            return Entity.ENTER
        
    def Update(self,time_elapsed,time_delta):
        AnimTile.Update(self,time_elapsed,time_delta)
        if self.GetState() == 1:
            if self.DeathTimer.GetElapsedTime() >= self.DeathTimerEnd:
                self.Set(self.GetNumFrames())
                if not defaults.debug_godmode:
                    if self.DistanceInnerRadius(self.__other):
                        self.game.Kill(self.GetVerboseName(),self.__other)
                self.SetState(0)
                self.level.RemoveEntity(self)
    
    def GetVerboseName(self):
        return "an exploded mine (BOOooOOM!)"

    def DistanceInnerRadius(self,other):
        midpoint1 = (self.pos[0]+self.dim[0]*0.5,self.pos[1]+self.dim[1]*0.5)
        midpoint2 = (other.pos[0]+other.dim[0]*0.5,other.pos[1]+other.dim[1]*0.5)
        distance = (midpoint1[0]-midpoint2[0])**2+(midpoint1[1]-midpoint2[1])**2
        return False if distance >= (self.radius**2) else True
    
class FakeDangerousBarrel(AnimTile):
    """This entity looks like a DangerousBarrel, but
    actually it doesn't kill the player - it just
    erases itself and can thus be used for secret
    doors ... stuff like that. """

    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.75):
        AnimTile.__init__(self,text,height,frames,speed)

        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        if isinstance(other,Player):
            print("Huh, you've found an special door which doesn't kill you!")
            self.game.RemoveEntity(self)

        if isinstance(other,Enemy):
            return Entity.BLOCK if other.color != self.color else Entity.ENTER
            
        return Entity.ENTER


    
