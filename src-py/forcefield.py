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
from tile import AnimTile,Tile,Entity
from player import Player

class ForceField(AnimTile):
    """Accelerate the player in a specific direction"""
    
    def __init__(self,*args,vel=[0.0,-10.0],halo_img=None, **kwargs):
        AnimTile.__init__(self,*args,halo_img=halo_img,**kwargs)
        self.players = {}
        self.vel = vel
        
    def Update(self,t,dt):
        AnimTile.Update(self,t,dt)
        
        if hasattr(self,"players"):
            for e in self.players:
                # XXX after changing player physics, these values now need to be adjusted
                s = 0.65
                e.SetExtraVelocity((self.vel[0]*dt*s,self.vel[1]*dt*s))
            
            delattr(self,"players")

    def Interact(self, other):
        if isinstance(other,Player):
            
            self.__dict__.setdefault("players",[]).append(other)
        
        return Entity.ENTER
        