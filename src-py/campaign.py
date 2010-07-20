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
from game import Entity
from renderer import NewFrame, Renderer
from tile import AnimTile
from player import Player
from keys import KeyMapping

class LevelEntrance(AnimTile):
    """Only found on the campaign world map, marks the entrance
    to a particular level"""
    
    def __init__(self,text,height,frames,speed,states,next_level=5,draworder=15000):
        AnimTile.__init__(self,text,height,frames,speed,states,draworder=draworder)
        self.next_level = next_level
        self.done = False
        
    def Interact(self,other):
        if isinstance(other,Player) and Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
            self._RunLevel()
        
        return Entity.ENTER
    
    def Update(self,time_elapsed,time):
        AnimTile.Update(self,time_elapsed,time)
        done = (self.next_level in self.game.GetDoneLevels())
        if done != self.done:
            self.done = done
            self.SetState(1)
        
    def _RunLevel(self):
        if self.done is True:
            return
        
        accepted = (KeyMapping.Get("accept"),KeyMapping.Get("escape"))
        def on_close(key):
            if key == accepted[0]:
                self.game.PushLevel(self.next_level)
                raise NewFrame()
            
        self.game.FadeOutAndShowStatusNotice("""Enter {1}? You might die here, so be careful. 
Press {0} to risk it and {2} to leave.""".format(
                KeyMapping.GetString("accept"),
                "Level {0}".format(self.next_level),
                KeyMapping.GetString("escape")),
            defaults.game_over_fade_time,(550,60),0.0,accepted,sf.Color.White,on_close)
        
        

        