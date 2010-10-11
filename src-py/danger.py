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

    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,hideontouch=False,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,**kwargs)

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
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,radius=3,hideontouch=False,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=None,**kwargs)
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
        return self.Distance(other) < (self.radius**2) 

    

class Heat(AnimTile):
    """Player gets 'hot' and dies around this brick"""
    
    HOT_COLOR = sf.Color.Red
    POSTFX_NAME = "heat.sfx"
    FADE_IN_SPEED = 1
    
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,radius=2,DeathTimerEnd=0.5,hideontouch=False,halo_img=None,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=halo_img,**kwargs)
        self.heat_activated = False
        self.DeathTimerEnd = DeathTimerEnd
        self.hideontouch = hideontouch
        self.radius = radius
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        if self.heat_activated:
            return Entity.ENTER
        else:
            if self.DistanceInnerRadius(other):
                self.DeathTimer = sf.Clock()
                self.__other = other
                self.heat_activated = True
                if not hasattr(self.__other,"oldcolor"):
                    self.__other.oldcolor = other.color
                    self.__other.heat_counter = 1
                    
                    if not Heat.POSTFX_NAME in [ n for n,p,e in self.level.postfx_rt ]:
                        self.__other.postfx_heat_shader = self.level.AddPostFX(Heat.POSTFX_NAME, ())
                        self.__other.postfx_heat_shader_intensity = 0.0
                        
                else:
                    self.__other.heat_counter += 1
                other.SetColor(Heat.HOT_COLOR)
            return Entity.ENTER
        
        
    def Update(self,time_elapsed,time_delta):
        AnimTile.Update(self,time_elapsed,time_delta)
        if self.heat_activated == True:
            
            now, end = self.DeathTimer.GetElapsedTime(), self.DeathTimerEnd
            
            self.__other.postfx_heat_shader_intensity += now*time_delta*Heat.FADE_IN_SPEED/end
            self.__other.postfx_heat_shader.SetParameter("redintensity",min(1,self.__other.postfx_heat_shader_intensity))
            
            if now >= end:
                if self.DistanceInnerRadius(self.__other):
                    if not defaults.debug_godmode:
                        self.game.Kill(self.GetVerboseName(),self.__other)
                        
                if hasattr(self.__other,"oldcolor"):
                    self.__other.heat_counter -= 1
                    if self.__other.heat_counter == 0:
                        self.__other.SetColor(self.__other.oldcolor)
                        delattr(self.__other,"oldcolor")
                        
                        self.level.RemovePostFX(Heat.POSTFX_NAME)
                    
                    
                self.heat_activated = False
    
    def GetVerboseName(self):
        return "a terribly hot stone"
    
    def DistanceInnerRadius(self,other):
        return self.Distance(other) < (self.radius**2) 
    
  
  
class FakeDangerousBarrel(AnimTile):
    """This entity looks like a DangerousBarrel, but
    actually it doesn't kill the player - it just
    erases itself and can thus be used for secret
    doors ... stuff like that. """

    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.75,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,**kwargs)

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


    
