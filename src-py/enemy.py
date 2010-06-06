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

# Python Core
import random

# PySFML
import sf

# My own stuff
import defaults
from game import Entity,TileLoader,Game,Tile,AnimTile

class SmallTraverser(AnimTile):
    """The simplest class of entities, it moves in a certain
    range and kills the player immediately"""

    def __init__(self,text,height,frames,speed=1.0,move_speed=3,randomdir=True):
        AnimTile.__init__(self,text,height,frames,speed,2)

        if randomdir is True:
            self.vel = move_speed*random.choice((-1,1))

    def Interact(self,other,game):
        return Entity.KILL

    def Update(self,time_elapsed,time,game):

        rect = self.GetBoundingBox()
        res = 0
        for collider in game._EnumEntities():
            if collider is self:
                continue
            
            mycorner = collider.GetBoundingBox()
            if mycorner is None:
                continue
            
            tj = self._BBCollide(rect, mycorner)
            if tj>0:
                game.AddToActiveBBs(collider)
                assert False
                res |= tj

        if self.vel < 0 and res & Entity.ALL == (Entity.UPPER_LEFT|Entity.LOWER_LEFT) or\
           res & Entity.ALL == (Entity.UPPER_RIGHT|Entity.LOWER_RIGHT):
               
            self.vel *= -1
            
        self.pos = (self.pos[0]+self.vel*time,self.pos[1])
        AnimTile.Update(self,time_elapsed,time,game)

        self.SetState(1 if self.vel >0 else 0 )
            
        
