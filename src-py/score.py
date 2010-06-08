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
from tile import AnimTile,Tile
from player import Player,Entity

class ScoreTile(AnimTile):
    """The player receives a certain extra score upon
    entering this tile"""

    def __init__(self,text,height,frames,speed,points,randomize=False):
        AnimTile.__init__(self,text,height,frames,speed)
        self.points = points

        if randomize is True:
            self.GotoRandom()
        
    def Interact(self,other,game):
        if isinstance(other,Player):
            points = game.Award(self.points)
            
            game.RemoveEntity(self) 
            game.AddEntity(ScoreTileAnimStub("{0:4.4} ct".format(points),self.pos,1.0))
            
        return Entity.ENTER


class ScoreTileAnimStub(Tile):
    """Implements the text string that is spawned whenever
    the aplyer triggers a score item."""

    def __init__(self,text,pos,speed):
        Tile.__init__(self,text)
        
        self.SetPosition( pos )
        self.speed = speed

    def GetBoundingBox(self):
        return None

    def Update(self,time_elapsed,time_delta,game):
        self.SetPosition((self.pos[0],self.pos[1]-time_delta*self.speed))

        if self.pos[1] < 0:
            game.RemoveEntity(self) 


    
