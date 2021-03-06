#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [background.py]
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

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import Tile
from player import Player

class Sun(Tile):
    """The sun is a nice sun, for it always sticks to the player position"""

    def __init__(self, text, width, height, posy=-0.3):
        Tile.__init__(self, text, width, height, halo_img="halo_sun.png")

        self.posy = posy

    def Interact(self, other):
        return Entity.ENTER
    
    def GetDrawOrder(self):
        return -1000

    def Update(self, time_elapsed, time):
        Tile.Update(self,time_elapsed,time)
        if self.game.GetGameMode() in (Game.EDITOR,Game.EDITOR_HIDDEN):
            return
        
        if not getattr(self,"player",None):
            for entity in self.game._EnumEntities():
                if isinstance(entity, Player):
                    self.player = entity
                    break
            else:
                return
        
        pos = [self.player.pos[0], self.posy]
        self.SetPosition(pos)
            
        

# vim: ai ts=4 sts=4 et sw=4
