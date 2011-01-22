#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [machineparts.py]
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

# Python stuff
import os

# PySFML
import sf

# My own stuff
import defaults
from game import Entity, Game
from tile import Tile
from player import Player,InventoryItem
from fonts import FontCache

class Part(InventoryItem, Tile):
    """A part of the mystic machine that the player is requested to complete"""
    
    def __init__(self, text="", width=Tile.AUTO,height = Tile.AUTO,halo_img=None,name=""):
        Tile.__init__(self,text,width,height,halo_img=halo_img)
        InventoryItem.__init__(self,True)
        self.name = name
    
    def GetItemName(self):
        return _("Machine part: ") + self.name
    
    def Interact(self, other):
        if isinstance(other,Player) and not hasattr(self,"fired"):
            
            self.fired = True
            
            def on_close(result):
                self.TakeMe(other)
            
            self.game._FadeOutAndShowStatusNotice(sf.String(_("""You inglourious hero managed to find the item you were
looking for so desperately (I don't say you don't deserve it, just 
I think you could have done better ...). Nevertheless, congrats on
this tremendous success. I am sure it means quite a lot to you.

The item you found is: {0}
            
            
Hit any key to continue""").format(self.name),
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over,face=defaults.font_game_over
                )),defaults.game_over_fade_time,(550,70),0.0,True,sf.Color.Black,on_close) 
            
            
        return Entity.ENTER
    
   
   
   
   

# vim: ai ts=4 sts=4 et sw=4