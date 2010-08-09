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
from game import Entity, Game
from renderer import NewFrame
from tile import Tile
from player import Player

class LevelUp(Tile):
    """The player enters the next level upon touching this tile"""

    def __init__(self,text,width,height):
        Tile.__init__(self,text,width,height)
        
    def Interact(self,other):
        if isinstance(other,Player) and not hasattr(self,"working_now"):
            print("Level completed: {0}!".format(self.level.GetName() or ""))
            self.game.Award(defaults.levelup_score_base*self.game.GetLevelStats()[-1])
                      
            # in campaign mode, make sure the level is correctly marked done
            # so the player won't be able to enter it again, even if he
            # wants to because there's so much score in it.
            self.game.MarkLevelDone(self.level.GetLevelIndex())
            
    
            self.working_now = True
            if self.game.GetGameMode() == Game.CAMPAIGN:
                self.game.BackToWorldMap()
            
            elif self.game.GetGameMode() == Game.SINGLE:
                self.game.GameOverQuitToMenu()
            elif self.game.GetGameMode() == Game.EDITOR or self.game.GetGameMode() == Game.EDITOR_HIDDEN:
                pass
            else:
                self.game.NextLevel()

            raise NewFrame()
            
        return Entity.ENTER


    
