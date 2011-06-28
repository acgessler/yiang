#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [score.py]
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
from player import Player,Entity


class ScoreTile(AnimTile):
    """The player receives a certain extra score upon
    entering this tile"""

    def __init__(self,text,height,frames,speed,points,randomize=False):
        AnimTile.__init__(self,text,height,frames,speed,halo_img="halo_score.png",randomize=randomize)
        self.points = points
        
    def Interact(self,other):
        if isinstance(other,Player):
            
            if not hasattr(self,"score_taken"):
            
                points = self.game.Award(self.points)
                
                self.game.RemoveEntity(self) 
                self.game.AddEntity(ScoreTileAnimStub(_("{0:4.4} ct").format(points),self.pos,1.0))
                self.score_taken = True
                
                #if self.game.GetGameMode() != Game.BACKGROUND:
                #    from posteffect import FlashOverlay
                #    Renderer.AddDrawable(FlashOverlay(self.color,0.02,0.5))
            
        return Entity.ENTER


class LifeTile(AnimTile):
    """The player receives an extra life upon
    entering a LifeTile"""

    def __init__(self,text,height,frames,speed,lives=1,randomize=False):
        AnimTile.__init__(self,text,height,frames,speed,halo_img="halo_score.png",randomize=randomize)
        self.lives = lives
        
    def Interact(self,other):
        if isinstance(other,Player):
            self.game.AddLife(self.lives)
            
            self.game.RemoveEntity(self) 
            self.game.AddEntity(ScoreTileAnimStub(_("+ 1 Life"),self.pos,1.0))
            
        return Entity.ENTER


class ScoreTileAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the player triggers a score item."""

    def __init__(self,text,pos,speed):
        Tile.__init__(self,text,draworder=11001,permute=False)
        
        self.SetPosition( pos )
        self.speed = speed

    def GetBoundingBox(self):
        return None
    
    def GetBoundingBoxAbs(self):
        return None

    def Update(self,time_elapsed,time_delta):
        self.SetPosition((self.pos[0],self.pos[1]-time_delta*self.speed))

        if self.pos[1] < -1:
            self.game.RemoveEntity(self) 
            
    def _GetHaloImage(self):
        return None


    

# vim: ai ts=4 sts=4 et sw=4