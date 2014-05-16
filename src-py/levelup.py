#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [levelup.py]
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

import math
from stubs import *
from player import Player
from sfutil import ColorLerp

class LevelUp(AnimTile):
    """The player enters the next level upon touching this tile"""

    def __init__(self,text,height,frames,speed):
        AnimTile.__init__(self, text, height, frames, speed, dropshadow=True, draworder=30)
        self.first_time = True

        # but oscilate the drop shadow between gray and white
        self.dropshadow_color = self.dropshadow_blend_color = sf.Color(255, 0, 0, 128);

    def Update(self,time,dtime):     
        AnimTile.Update(self, time, dtime)
        # Force the color to be a medium gray
        # cannot do this in the constructor as it would get overridden
        if self.first_time:
            self.SetColor(sf.Color.White)
            self.first_time = False

        self.dropshadow_color = ColorLerp(self.dropshadow_blend_color,self.color,(math.sin(time)+1.0)/2)
        
    def Interact(self,other):
        if isinstance(other,Player) and not hasattr(other,"has_levelup"):
            # we can no longer be sure that only one LevelUp will be triggered
            
            print("Level completed: {0}!".format(self.level.GetName() or ""))
            
            # In campaign mode, make sure the level is correctly marked done
            # so the player won't be able to enter it again, even if he
            # wants to because there's so much score in it.
            self.game.MarkLevelDone(self.level.GetLevelIndex())
    
            other.has_levelup = True
            if self.game.GetGameMode() == Game.CAMPAIGN:
                self.game.BackToWorldMap(int(self.level.metadata.get('reward_lives',1)))
            else:
                # score aways only outside campaign mode
                self.game.Award(defaults.levelup_score_base*self.game.GetLevelStats()[-1])
                if self.game.GetGameMode() == Game.SINGLE:
                    self.game.GameOverQuitToMenu()
                elif self.game.GetGameMode() == Game.EDITOR or self.game.GetGameMode() == Game.EDITOR_HIDDEN:
                    pass
                else:
                    self.game.NextLevel()

            #raise NewFrame()
            
        return Entity.ENTER

# vim: ai ts=4 sts=4 et sw=4
