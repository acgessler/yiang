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
from game import Entity, NewFrame
from player import Player
from keys import KeyMapping
from fonts import FontCache

class SimpleNotification(Entity):
    """The SimpleNotification class displays a popup box when the players
    enters its area. This is used extensively for story telling."""

    def __init__(self, text, text_color = sf.Color.Red, only_once=True, width=1, height=1, line_length = 50):
        self.text = text
        self.use_counter = 1 if only_once is True else 1000000000 
        self.dim = (width,height)
        
        self.text_formatted = ""
        self.line_length = line_length
        self.text_color = text_color
        
        # format the text nicely
        # XXX monospace is not everything, really
        for paragraph in self.text.split("\n"):
            cnt = 0
            for word in paragraph.split(" "):
                if cnt+len(word)>line_length:
                    self.text_formatted += "\n"
                    cnt = 0
                self.text_formatted += word + " "
                cnt+=len(word)
            
            self.text_formatted += "\n\n"
        
        self.box_dim = (line_length*11, self.text_formatted.count("\n")*16)
        
    def Interact(self, other, game):
        if isinstance(other, Player) and self.use_counter > 0:
            
            print("Show notification")
            
            accepted = (KeyMapping.Get("escape"), KeyMapping.Get("accept"))
            key = game._FadeOutAndShowStatusNotice(defaults.game_over_fade_time,
            	sf.String(self.text_formatted,
                Size=defaults.letter_height_game_over,
                Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
            )), self.box_dim , 0.0, accepted, self.text_color) 
            
            self.use_counter -= 1
            if self.use_counter == 0:
                game.RemoveEntity(self)
            
        return Entity.ENTER
    
    def GetBoundingBox(self):
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])


    
