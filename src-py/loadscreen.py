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

from renderer import Drawable,Renderer
from level import Level
from tile import Tile
from game import Entity,Game

# range of levels usable as background for the loadscreen
SPECIAL_LEVEL_LOADING_START = 50000
SPECIAL_LEVEL_LOADING_END = 50001

class CountingTile(Tile):
    
    def __init__(self,text, *args,**kwargs):
        self.orig_text = text
        Tile.__init__(self, text, *args,**kwargs)
        
        
class EntitySpawner(Entity):
    
    def __init__(self,*args,**kwargs):
        Entity.__init__( self,*args,**kwargs)
        self.locked = False
        
    def Update(self,time,dtime):
        import random
        
        inp = Renderer.app.GetInput()
        if inp.IsKeyDown(sf.Key.E):
            if not self.locked:
                self.locked= True
                
                e = self.level.AddTileFromCode("{0}E2".format(random.choice("rgby_pG~")),*self.pos)
                from enemy import SmallTraverser
                
                assert isinstance(e, SmallTraverser)
                e.vel = 10.0
        else:
            self.locked= False
            
        
class LoadScreen:
    """Displays the 'be patient or kill a chicken' loading screen"""
    
    instance = None
    loadlevel = None
    progress_tile = None
    
    @staticmethod
    def LoadLoadLevel():
        import random
        
        LoadScreen.progress_tile = None
        
        LoadScreen.loadlevel = g = LoadScreen.instance = Game(mode=Game.BACKGROUND,undecorated=True)
        if not g.LoadLevel(random.randint(SPECIAL_LEVEL_LOADING_START,SPECIAL_LEVEL_LOADING_END-1),
            no_loadscreen=True):
            return
        
        e = [ e for e in g.GetLevel().EnumAllEntities() if isinstance(e, CountingTile) ]
        if len(e)!=1:
            return
            
        LoadScreen.progress_tile, = e

        
    @staticmethod
    def UpdateProgressBar(progress):
        e = LoadScreen.progress_tile
        if not e:
            return
        e.text = e.orig_text.format("."*int((progress*10)))
        e._Recache()
        
    @staticmethod
    def Load(loadProc,*args,**kwargs):
        from threading import Thread
        
        LoadScreen.LoadLoadLevel()
        
        import time 
        a = time.time()
        
        ret = [None]
        def DoLoading():    
            
            ret[0] = loadProc(*args,**kwargs)
            b = time.time()

            time.sleep(max(0, defaults.loading_time - (b-a)))
            Renderer.RemoveDrawable(LoadScreen.loadlevel)
            
        Renderer.AddDrawable(LoadScreen.loadlevel)
        
        LoadScreen.stop = False
        t = Thread(target=DoLoading)
        t.daemon = True
        t.start()
        
        while t.is_alive() and Renderer.IsMainloopRunning():
            
            Renderer._DoSingleFrame()
            
            c = time.time()
            LoadScreen.UpdateProgressBar((c-a)/defaults.loading_time)
            
        return ret[0]
        

 
        
        
        