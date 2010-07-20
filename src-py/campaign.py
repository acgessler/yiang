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
from tile import Tile
from player import Player
from keys import KeyMapping

class LevelEntrance(Tile):
    """Only found on the campaign world map, marks the entrance
    to a particular level"""
    
    def __init__(self,width=Tile.AUTO,height=Tile.AUTO,next_level=5,draworder=15000):
        Tile.__init__(self,width,height,draworder=draworder)
        self.next_level = next_level
        
    def Interact(self,other):
        if isinstance(other,Player) and Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
            self._RunLevel()
        
        return Entity.ENTER
        
    def _RunLevel(self):
        self.game.PushLevel(self.next_level)
        #self.game.Set
        raise NewFrame()
        

        