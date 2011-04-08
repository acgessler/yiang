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

import sf

import defaults
from player import Player
from game import Game

def GetUpdater():
    class Updater:
        def __call__(self,pfx, type, name):
            
            assert type == "vec2"
            if hasattr(self,"game") is False:
                if hasattr(self,"player"):
                    self.game = self.player.game
                else:
                    return
            
            if not self.game.GetLevel():
                return
            
            if not hasattr(self,"player") or not hasattr(self,"clock") or self.clock.GetElapsedTime() > 1.0:
                self.clock = sf.Clock()
                candidates = (entity for entity in self.game.GetLevel().EnumActiveEntities() \
                    if isinstance(entity,Player))
                
                try:
                    self.player = sorted(candidates,
                        key=lambda x:x.pos[0],reverse=True
                    )[0]
                except IndexError:
                    self.player = None
            
            player = self.player
            if not player:
                return
            
            origin = self.game.GetLevel().GetOrigin()
            x,y = ((player.pos[0] + player.pwidth // 2 - origin[0]) / defaults.tiles[0],
                1.0 - (player.pos[1] + player.pheight // 2 - origin[1]) / defaults.tiles[1])
            
                
            # fix for editor mode: if the player is outside the valid range,
            # why not simply make the postfx belief he's at the center?
            # Usually, this will make sure that this part of the screen
            # appears visible and undistorted.
            if  x < -1.1 or x > 1.1 or y < -1.1 or y > 1.1 \
                or (self.game.GetGameMode()==Game.EDITOR and not self.game.IsGameRunning()) \
                or self.game.GetGameMode()==Game.BACKGROUND:
                x = y = 0.5
                
            
            pfx.SetParameter(name,x,y)
            
        def SetOuterParam(self,name,value):
            if name == "game":
                self.game = value
            elif name == "player":
                self.player = value
                
    return Updater()
        