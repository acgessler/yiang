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
from game import Entity,Game
from tile import AnimTile
from player import Player
from notification import MessageBox
from keys import KeyMapping
from fonts import FontCache

class OrganTransplantMachine(AnimTile):
    """The OrganTransplantMachine allows the player to trade
    money for lives."""

    def __init__(self,text,height,frames,speed,use_counter=1):
        AnimTile.__init__(self,text,height,frames,speed)
        self.use_counter = use_counter
        self.text_formatted = """Welcome to the Instant Organ Transplantation Machine (IOTM)!

Do you want to buy new organs and have them transplanted immediately 
to heal your wounds? This gives you an extra life for not more than 
$ 1! 
This is a truly incredible offer! This is the time to get rid of your
ill organs and get a fresh body! Note: No orphans were harmed for 
building this machine. 


Press {0} to accept the deal (-$1.0, +L) and {1} to leave.
""".format(KeyMapping.GetString("accept"),KeyMapping.GetString("escape"))

    def Interact(self,other):
        if isinstance(other,Player) and not hasattr(self, "running") and self.use_counter > 0:
            self._RunMachine()
        
        return Entity.ENTER
    
    def _RunMachine(self):
    
        print("Show OrganTransplantMachine '{0}', use counter: {1}".format(id(self), self.use_counter))
        accepted = (KeyMapping.Get("escape"), KeyMapping.Get("accept"))
            
        # closure to be called when the player has made his decision
        def on_close(key):
            delattr(self, "running")
            if key == accepted[1]:
                self.game.lives += 1
                self.game.score -= 1.0
            
                self.use_counter -= 1
                if self.use_counter == 0:
                    self.SetColor(sf.Color(60,60,60))
                    print("Disable OrganTransplantMachine '{0}'".format(id(self)))
            
        self.running  = True
        self.game._FadeOutAndShowStatusNotice( sf.String(self.text_formatted,
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_machines, face=defaults.font_machines
        )),defaults.game_over_fade_time, (640,210) , 0.0, accepted, sf.Color.Red, on_close)

    def GetVerboseName(self):
        return "the Instant Organ Transplant Machine (OTM)"
    
    
    