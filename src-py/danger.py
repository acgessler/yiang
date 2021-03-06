#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [danger.py]
# (c) 2008-2011 Yiang Development Team
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


from stubs import *
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
        if isinstance(other, Player):
            return Entity.KILL
        return Entity.BLOCK

    def GetVerboseName(self):
        return _("a deathly barrel (it's hilarious!)")


class Mine(AnimTile):
    """This entity is an animated mine which kills
    the player after the animation of the explosion ended"""
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,radius=4,hideontouch=False,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=None,**kwargs)
        self.mine_activated = False
        self.radius = radius
        self.hideontouch = hideontouch
        self.__other = None
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        if self.mine_activated:
            return Entity.ENTER
        else:
            self.Set(0)
            self.SetState(1)
            
            from posteffect import FlashOverlay
            Renderer.AddDrawable(FlashOverlay(sf.Color(255,120,0),0.09,4,3))

            from posteffect import BlurInOverlay
            Renderer.AddDrawable(BlurInOverlay())
                
            self.DeathTimer = sf.Clock()
            self.DeathTimerEnd = (self.GetNumFrames()-1)*self.speed
            self.__other = other
            self.mine_activated = True
            return Entity.ENTER

    def Draw(self,*args):
        # Draw a semi-transparent circle to visualize the mine radius
        # This is slow, but mines are rare.
        cpos = self.level.ToCameraDeviceCoordinates(self.GetCenter())

        border_color = sf.Color(90,90,90,80)
        if self.__other and self.DistanceInnerRadius(self.__other):
            border_color = sf.Color(120,120,120,150)

        self.game.DrawSingle(sf.Shape.Circle(cpos[0],cpos[1],
            self.radius*defaults.tiles_size_px[0], sf.Color(50,50,50,60), 1, border_color
        ))
        AnimTile.Draw(self,*args)
        
    def Update(self,time_elapsed,time_delta):
        AnimTile.Update(self,time_elapsed,time_delta)
        if self.GetState() == 1:
            if self.DeathTimer.GetElapsedTime() >= self.DeathTimerEnd:
                self.Set(self.GetNumFrames())
                
                if not defaults.debug_godmode and not self.game.mode == Game.BACKGROUND:
                    self.KillNeighbors()                   
                self.SetState(0)
                self.level.RemoveEntity(self)
    
    def GetVerboseName(self):
        return _("an explosive mine (BOOooOOM!)")
    
    def DistanceInnerRadius(self,other):
        return self.Distance(other) < (self.radius**2)

    def KillNeighbors(self):
        # Get all enemies, and the player, from within the mines
        # radius of influence and kill them.
        cpos = self.GetCenter()
        radius = self.radius
        bb = [cpos[0] - radius, cpos[1] - radius, cpos[0] + radius, cpos[1] + radius]
        for e in self.game.GetLevel().EnumPossibleColliders(bb):
            if not isinstance(e, Player) and not isinstance(e, Enemy):
                continue
            if self.DistanceInnerRadius(e):
                if isinstance(e, Player):
                    self.game.Kill(self.GetVerboseName(),e)
                elif isinstance(e, Enemy):
                    e.Kill()

    

class Heat(AnimTile):
    """Player gets 'hot' and dies around this brick"""
    
    # HOT_COLOR = sf.Color.Red
    POSTFX_NAME = "heat.sfx"
    FADE_IN_SPEED = 2
    
    def __init__(self,text,height,frames,speed,randomize,bbadjust=0.55,radius=2,DeathTimerEnd=1.5,hideontouch=False,halo_img=None,**kwargs):
        AnimTile.__init__(self,text,height,frames,speed,2,halo_img=halo_img,**kwargs)
        self.heat_activated = False
        self.DeathTimerEnd = DeathTimerEnd
        self.hideontouch = hideontouch
        self.radius = radius
        if randomize is True:
            self.GotoRandom()

        self._ShrinkBB(bbadjust)

    def Interact(self,other):
        if not isinstance(other,Player):
            return Entity.BLOCK
        
        if self.heat_activated and self.myplayer.heat_counter > 0:
            return Entity.ENTER
        else:
            if self.DistanceInnerRadius(other) and other.dead is False:
                self.DeathTimer = sf.Clock()
                self.myplayer = other
                self.heat_activated = True
                if not hasattr(self.myplayer,"oldcolor"):
                    self.myplayer.oldcolor = other.color
                    self.myplayer.heat_counter = 1
                    
                    if not Heat.POSTFX_NAME in [ n for n,p,e in self.level.postfx_rt ]:
                        self.myplayer.postfx_heat_shader = self.level.AddPostFX(Heat.POSTFX_NAME, ())
                    self.myplayer.postfx_heat_shader_intensity = 0.0
                        
                else:
                    self.myplayer.heat_counter += 1
                other.SetColor(self.color)
            return Entity.ENTER
        
        
    def Update(self,time_elapsed,time_delta):
        AnimTile.Update(self,time_elapsed,time_delta)
        if self.heat_activated and self.myplayer.heat_counter > 0:
            
            # fix to avoid different behaviour in higher rounds
            now, end = self.DeathTimer.GetElapsedTime(), self.DeathTimerEnd  / self.game.speed_scale 
            
            self.myplayer.postfx_heat_shader_intensity += time_delta*Heat.FADE_IN_SPEED
            
            s = min(1,self.myplayer.postfx_heat_shader_intensity)*0.1
            self.myplayer.postfx_heat_shader.SetParameter("col_scale", s)
            self.myplayer.postfx_heat_shader.SetParameter("col_target", self.color.r*s, self.color.g*s, self.color.b*s)
            
            if now >= end:
                if self.DistanceInnerRadius(self.myplayer):
                    if not defaults.debug_godmode and not self.game.mode == Game.BACKGROUND and self.myplayer.MeCanDie():
                        
                        def garbagify_ppfx():
                            self.level.RemovePostFX(Heat.POSTFX_NAME)
                        
                        # manually reset everything to keep other Heat tiles from kicking in
                        delattr(self.myplayer,"oldcolor")
                        self.myplayer.heat_counter = 0
                        self.heat_activated = False
                        
                        self.myplayer.postfx_heat_shader.SetParameter("redintensity",1.0)
                        self.game.Kill(self.GetVerboseName(),self.myplayer,on_close_mb_extra=garbagify_ppfx)
                        return
                    
            if now >= end or not self.DistanceInnerRadius(self.myplayer):    
                self.myplayer.heat_counter -= 1
                self.heat_activated = False
                if self.myplayer.heat_counter == 0:
                    self.myplayer.SetColor(self.myplayer.oldcolor)
                    delattr(self.myplayer,"oldcolor")
                    
                    self.level.RemovePostFX(Heat.POSTFX_NAME)                   
    
    def GetVerboseName(self):
        return _("a terribly hot stone")
    
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
        if isinstance(other,Player) and not hasattr(self, "done"):
            print("Huh, you've found an special door which doesn't kill you!")
            self.game.RemoveEntity(self)

            from score import ScoreTileAnimStub
            import random
            # Randomly pick a small score that is awarded to the player
            score = max(0.01, random.random()**3)
            self.game.Award(score)
            self.game.AddEntity(ScoreTileAnimStub(_("{0:4.4} ct").format(score),self.pos,2.0,False))
            self.done = True

        if isinstance(other,Enemy):
            return Entity.BLOCK if other.color != self.color else Entity.ENTER
            
        return Entity.ENTER


    

# vim: ai ts=4 sts=4 et sw=4
