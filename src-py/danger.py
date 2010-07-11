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
        return Entity.KILL

    def GetVerboseName(self):
        return "a deathly barrel (it's hilarious!)"

class Mine(AnimTile):
    """This entity is an animated mine which kills
    the player after the animation of the explosion ended"""
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,hideontouch=False):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=None)

        self.hideontouch = hideontouch
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        self.Set(self.GetNumFrames())
        self.SetState(1)
        self.DeathTimer = sf.Clock()
        self.DeathTimerEnd = (self.GetNumFrames()+1)*self.speed
        self.__other = other
        return
    
    def Update(self,time_elapsed,time_delta):
        AnimTile.Update(self,time_elapsed,time_delta)
        if self.GetState() == 1:
            if self.DeathTimer.GetElapsedTime() >= self.DeathTimerEnd:
                self.game.Kill("an exploded mine (BOOooOOM!)",self.__other)
                self.SetState(0)
        
            
        

    def GetVerboseName(self):
        return "an exploded mine (BOOooOOM!)"
    
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
            return Entity.BLOCK
            
        return Entity.ENTER


    
