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

# Python core
import os

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
from renderer import Renderer


class Machine(AnimTile):
    """Base class for all kinds of machines, buy stocks, ..."""
    def __init__(self,message_text_file,text,height,frames,speed,use_counter=1):
        AnimTile.__init__(self,text,height,frames,speed,halo_img=None)
        self.use_counter = use_counter
        
        path =os.path.join(defaults.data_dir,"messages",message_text_file)
        try:
            with open(path,"rt") as file:
                tdict = dict(KeyMapping.mapping)
                tdict.update(defaults.__dict__)
                self.messages = [message.format(**tdict) for message in file.read().split("###NEXT###\n")]
        except IOError:
            self.messages = ["Error, see the log file for more details"] * 50
            print("Failure reading {0}".format(path))
            
    def Interact(self,other):
        if isinstance(other,Player) and not hasattr(self, "running") and self.use_counter > 0 and Renderer.app.GetInput().IsKeyDown(KeyMapping.Get("interact")):
            self._RunMachine()
        
        return Entity.ENTER
    
    def DisableMachine(self):
        self.use_counter= 0
        self.SetColor(sf.Color(60,60,60))
        print("Disable Machine '{0}'".format(id(self)))
        
    def _ShowMachineDialog(self,on_close,accepted,text):
        
        def on_close_wrapped(key):
            delattr(self, "running")
            on_close(key)
            
        print("Show Machine '{0}', use counter: {1}".format(id(self), self.use_counter))
        
        self.running  = True
        self.game._FadeOutAndShowStatusNotice( sf.String(self.messages [text],
            Size=defaults.letter_height_machines,
            Font=FontCache.get(defaults.letter_height_machines, face=defaults.font_machines
        )),defaults.game_over_fade_time, (580,180) , 0.0, accepted, sf.Color.Red, on_close_wrapped)
    
    def _RunMachine(self):
        pass
    

class OrganTransplantMachine(Machine):
    """The OrganTransplantMachine allows the player to trade
    money for lives."""
    Message_Normal,Message_NotEnoughMoney = range(2)
    
    def __init__(self,text,height,frames,speed,use_counter=1):
        Machine.__init__(self, "organ_transplant.txt", text, height, frames, speed, use_counter)

    def _RunMachine(self):
        accepted = (KeyMapping.Get("escape"), KeyMapping.Get("accept"))
            
        # closure to be called when the player has made his decision
        def on_close(key):
            if key == accepted[1] and self.game.GetScore() >= defaults.organ_transplant_dollar_in:
                self.game.AddLife()
                self.game.TakeScore(defaults.organ_transplant_dollar_in*100.0)
            
                self.use_counter -= 1
                if self.use_counter == 0:
                    self.DisableMachine()
            
        self._ShowMachineDialog(on_close,accepted, OrganTransplantMachine.Message_Normal 
            if self.game.GetScore() >= defaults.organ_transplant_dollar_in 
            else OrganTransplantMachine.Message_NotEnoughMoney)

    def GetVerboseName(self):
        return "the Instant Organ Transplant Machine (OTM)"
    
    
    
