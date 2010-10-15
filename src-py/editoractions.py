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

# Our stuff
import defaults
from minigui import Component, Button, ToggleButton

class ContextHandler:
    """Base class for all context menu handlers"""

    def __init__(self,editor):
        self.elements = []
        self.entities = []
        self.editor = editor
        
    def _Dispatch(self,callable,*args,**kwargs):
        with self.editor.BeginTransaction() as transaction:
            for n in range(len(self.entities)):
                r = callable(self.entities[n],*args,**kwargs)
                if not r is None:
                    self.entities[n] = r
                
    def _SetupSimpleAlternatives(self,values):
        def UpdateTextColor(entity, gui,code):
            gui.fgcolor= sf.Color.Yellow if code==entity.editor_tcode else None
        
        for k,v in values.items():
            self.elements.append(Button(text="-> {0}".format(k)) + 
                ("release", (lambda src,v=v: self._Dispatch( self._ChangeTo,v)))+
                ("update",  (lambda src,v=v: UpdateTextColor((lambda: self.entities[0])(),src,v)))
            )
            
    def _SelectEntitySameColor(self,entity,code):
        # Don't bother with color codes, simply take the old
        # color and let Save() do the work for us.
        elem = self.editor._LoadTileFromTag("_"+code)
        elem.color = entity.color
        self.editor._SelectEntity(elem,entity.pos)
        
        return None # important!
                    
    def _ChangeTo(self,entity, codename):
        elem = self.editor._PlaceEntity(codename if len(codename)==3 else "_"+codename,entity.pos)
        elem.color = entity.color
        
        # Update the current selection accordingly
        if hasattr(self.editor,"template"):
            try:
                del self.editor.template[entity]
                self.editor.template[elem] = None
            except KeyError:
                pass
        
        return elem
    

from player import Player
class ContextHandler_Player(ContextHandler):
    """Context menu handler for Player objects"""
    
    @staticmethod
    def GetClasses():
        return (Player,)
    
    def __call__(self, entities):
        self.entities = entities
        self.elements.append(Button(text=_("Award 1ct (temporary)")) + 
            ("release", (lambda src: self._Dispatch(self.Award,1.0)))
        )
        
        self.elements.append(Button(text=_("Award 1$  (temporary)")) + 
            ("release", (lambda src: self._Dispatch(self.Award,100.0)))
        )
        
        
from score import ScoreTile
class ContextHandler_ScoreTile(ContextHandler):
    """Context menu handler for ScoreTile objects"""
    
    @staticmethod
    def GetClasses():
        return (ScoreTile,)
    
    def __call__(self, entities):
        self.entities = entities
        values = {
            0.1    :"S0",
            0.05   :"S1",
            0.2    :"S2",
            0.5    :"S3",
            1.00   :"S4"
        }
        
        def UpdateTextColor(entity,gui,code):
            gui.fgcolor= sf.Color.Yellow if code==entity.editor_tcode else None
        
        for k,v in values.items():
            # if k==self2.entity.points:
            #     continue
            
            self.elements.append(Button(text="-> {0} ct".format(k)) + 
                ("release", (lambda src,v=v: self._Dispatch(self._ChangeTo,v)))+
                ("update",  (lambda src,v=v: UpdateTextColor((lambda: self.entities[0])(),src,v)))
            )
        
        
from enemy import SmallTraverser
class ContextHandler_SmallTraverser(ContextHandler):
    """Context menu handler for SmallTraverser objects"""
    
    @staticmethod
    def GetClasses():
        return (SmallTraverser,)
    
    def __call__(self, entities):
        self.entities = entities
        
        values = {
            _("Horizontal moves")           : "E0",
            _("Vertical moves")             : "E2",
            _("Horizontal moves, quick")    : "E1"
        }
        
        self._SetupSimpleAlternatives(values)
            
            
from danger import DangerousBarrel, FakeDangerousBarrel
class ContextHandler_DangerBarrel(ContextHandler):
    """Context menu handler for all kinds of DANGER barrels"""
    
    @staticmethod
    def GetClasses():
        return (DangerousBarrel, FakeDangerousBarrel)
    
    def __call__(self, entities):
        self.entities = entities
        
        values = {
                _("'Normal' barrel")    : "DA",
                _("Rounded barrel")     : "DS",
                _("Fake barrel")        : "TR"
        }
        
        self._SetupSimpleAlternatives(values)
        
        
from weapon import Weapon
class ContextHandler_Weapon(ContextHandler):
    """Context menu handler for all kinds of weapons"""
    
    @staticmethod
    def GetClasses():
        return (Weapon,)
    
    def __call__(self, entities):
        self.entities = [ e for e in entities if e.GetAmmoCode()==entities[0].GetAmmoCode() ]
        
        self.elements.append(Button(text="Select ammo") + 
            ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,entities[0].GetAmmoCode())))
        )
        
        
from locked import Door,Bridge
class ContextHandler_Door(ContextHandler):
    """Context menu handler for doors"""
    
    @staticmethod
    def GetClasses():
        return (Door,)
    
    def __call__(self, entities):
        self.entities = entities
        
        def ToggleThisDoor(door):
            door.Lock() if door.unlocked else door.Unlock() 
            
        def UpdateDoorCaption(door,gui):
            gui.text = _("Close Door") if door.unlocked else _("Open Door")
       
        self.elements.append(Button(text="") + 
            ("update",  (lambda src: UpdateDoorCaption((lambda:self.entities[0])(),src))) +
            ("release", (lambda src: self._Dispatch(ToggleThisDoor)))
        )
     
        if len([ e for e in entities if e.color==entities[0].color ]) == len(self.entities):
            if [e for e in entities if isinstance(e,Bridge)]:
                self.elements.append(Button(text=_("Select switch [off]")) + 
                    ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"C9")))
                )
                self.elements.append(Button(text=_("Select switch [on]")) + 
                    ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"CB")))
                )
            else:
                
                self.elements.append(Button(text=_("Select key")) + 
                    ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"KE")))
                )
        
        
from locked import Key
class ContextHandler_Key(ContextHandler):
    """Context menu handler for keys"""
    
    @staticmethod
    def GetClasses():
        return (Key,)
    
    def __call__(self, entities):
        self.entities = entities
        
        if len([ e for e in entities if e.color==entities[0].color ]) == len(self.entities):
            self.elements.append(Button(text=_("Select corr. door")) + 
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"DO")))
            )
            
            
from locked import BridgeControl
class ContextHandler_BridgeControl(ContextHandler):
    """Context menu handler for bridge switches"""
    
    @staticmethod
    def GetClasses():
        return (BridgeControl,)
    
    def __call__(self, entities):
        self.entities = entities
        
        values = {
            _("Default: on")           : "CB",
            _("Default: off")          : "C9"
        }
        
        self._SetupSimpleAlternatives(values)
        
        if len([ e for e in entities if e.color==entities[0].color ]) == len(self.entities):
            self.elements.append(Button(text="Select corr. bridge") + 
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"C8")))
            )
            
            
from teleport import Sender,Receiver
class ContextHandler_Sender(ContextHandler):
    """Context menu handler for TA bricks"""
    
    @staticmethod
    def GetClasses():
        return (Sender,)
    
    def __call__(self, entities):
        self.entities = entities
        
        if len([ e for e in entities if e.color==entities[0].color ]) == len(self.entities):
            self.elements.append(Button(text=_("Select receiver")) +          
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"TB")))
            )
            
            self.elements.append(Button(text=_("Select receiver 90\xb0 cw.")) +         
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"TC")))
            )
            
            self.elements.append(Button(text=_("Select receiver 90\xb0 ccw.")) + 
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"TD")))
            )
            
            
class ContextHandler_Receiver(ContextHandler):
    """Context menu handler for TB,TC,TD,.. bricks"""
    
    @staticmethod
    def GetClasses():
        return (Receiver,) # catches ReceiverRotateRight, etc as well
    
    
    def __call__(self, entities):
        self.entities = entities
        values = {
            _("Normal")                : "TB",
            _("Rotate 90\xb0 cw.")     : "TC",
            _("Rotate 90\xb0 ccw.")    : "TD"
        }
        
        self._SetupSimpleAlternatives(values)
        
        if len([ e for e in entities if e.color==entities[0].color ]) == len(self.entities):
            self.elements.append(Button(text="Select sender") +          
                ("release", (lambda src: self._Dispatch( self._SelectEntitySameColor,"TA")))
            )

from materials import OneSidedWall
#from forcefield import ForceField
class ContextHandler_OneSidedWall(ContextHandler):
    """Context menu handler for D2,.. bricks"""
    
    @staticmethod
    def GetClasses():
        return (OneSidedWall,) 
    
    
    def __call__(self, entities):
        self.entities = entities
        values = {
            _("Block Left")                  : "D3",
            _("Block Right")                 : "D4"
        }
        
        self._SetupSimpleAlternatives(values)

def GetHandlers():
    """Return a list of all known handler classes"""
    return [
        ContextHandler_Player,
        ContextHandler_ScoreTile,
        ContextHandler_SmallTraverser,
        ContextHandler_DangerBarrel,
        ContextHandler_Weapon,
        ContextHandler_Door,
        ContextHandler_Key,
        ContextHandler_Sender,
        ContextHandler_Receiver,
        ContextHandler_BridgeControl,
        ContextHandler_OneSidedWall
    ]


