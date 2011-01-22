#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [loadscreen.py]
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

# Our stuff
import defaults

from renderer import Drawable,Renderer
from level import Level
from tile import Tile
from game import Entity,Game
from keys import KeyMapping

import time

# range of levels usable as background for the loadscreen
SPECIAL_LEVEL_LOADING_START = 50000
SPECIAL_LEVEL_LOADING_END = -1

class CountingTile(Tile):
    
    def __init__(self,text, *args,**kwargs):
        self.orig_text = text
        Tile.__init__(self, text, *args,**kwargs)
        
        
class EntitySpawner(Entity):
    
    def __init__(self, *args, dt=1.0, **kwargs):
        Entity.__init__( self,*args,**kwargs)
        self.clock  = sf.Clock()
        self.dt = dt
        
    def Update(self,time,dtime):
        import random
        
        inp = Renderer.app.GetInput()
        if inp.IsKeyDown(sf.Key.E):
            if self.clock.GetElapsedTime() > self.dt:
                self.clock  = sf.Clock()
                
                e = self.level.AddTileFromCode("{0}E2".format(random.choice("rgby_pG~")),*self.pos)
                from enemy import SmallTraverser
                
                assert isinstance(e, SmallTraverser)
                e.vel = random.random()*15 + 1.0
                
            
from level import Level
class LoadScreenLevel(Level):
        
    def __init__(self, level, game, raw, *args, name="GenericLoadScreenLevel",distortion_params=False,color=(30,30,30),scroll=0,autoscroll_speed=(0.0,0.0),vis_ofs=0,audio_section="current",**kwargs):
        Level.__init__(self, level, game, raw, *args,
            distortion_params=distortion_params,
            color=color,
            scroll=scroll,
            autoscroll_speed=autoscroll_speed,
            vis_ofs=vis_ofs,
            audio_section=audio_section,
            **kwargs
        )
        
    def Draw(self, _time, dtime):
        frate = self.game.GetFrameRateUnsmoothed()
        if frate > 20.0:
            time.sleep(0.025) # try to slow down this thread to favour the loading thread
        Level.Draw(self,_time,dtime)
        
        
class LoadScreen:
    """Displays the 'be patient or kill a chicken' loading screen"""
    
    loadlevel = None
    progress_tile = None
    running = False
    
    @staticmethod
    def LoadLoadLevel():
        import random
        
        LoadScreen.progress_tile = None
        
        global SPECIAL_LEVEL_LOADING_END
        if SPECIAL_LEVEL_LOADING_END < SPECIAL_LEVEL_LOADING_START:
            from level import LevelLoader
            
            m = SPECIAL_LEVEL_LOADING_START-1
            for n,readonly in sorted(LevelLoader.EnumLevelIndices()):
                if n < SPECIAL_LEVEL_LOADING_START:
                    continue
                if n-m != 1:
                    break
                m = n
                
            SPECIAL_LEVEL_LOADING_END = m+1
            print("Number of loading levels: {0}".format(SPECIAL_LEVEL_LOADING_END-SPECIAL_LEVEL_LOADING_START))
        
        g = Game(mode=Game.BACKGROUND,undecorated=True)
        if not g.LoadLevel(random.randint(SPECIAL_LEVEL_LOADING_START,SPECIAL_LEVEL_LOADING_END-1),
            no_loadscreen=True):
            return
        
        e = [ e for e in g.GetLevel().EnumAllEntities() if isinstance(e, CountingTile) ]
        if len(e)!=1:
            return
            
        LoadScreen.progress_tile, = e
        LoadScreen.loadlevel = g
        
    @staticmethod
    def UpdateProgressBar(progress):
        e = LoadScreen.progress_tile
        if not e:
            return
        
        l = 36
        e.text = e.orig_text.format("[" + ("#"*int(progress*l) + "."*int((1.0-progress)*l))+"]")
        e._Recache()
        
    @staticmethod
    def IsRunning():
        return LoadScreen.running
        
    @staticmethod
    def EndProgressBar():
        import random
        ret = not not [e for e in Renderer.GetEvents() if e.Type == sf.Event.KeyPressed]
        e = LoadScreen.progress_tile
        if not e:
            return ret
        
        e.text = _("""
Finally, everything is ready. 
This makes me SO happy {0} 
... Press any key to continue ... """).format(random.choice(
        (":-)",";-0",";-)",";-*","8)",":)",";)")
        ))
        e._Recache()
        LoadScreen.progress_tile = None
        return ret
        
    @staticmethod
    def Load(loadProc,*args,**kwargs):
        if defaults.no_threading:
            return loadProc(*args,**kwargs)
        
        from threading import Thread
        LoadScreen.LoadLoadLevel()
        
        import time 
        a = time.time()
        
        LoadScreen.running = True
        
        try:
        
            ret = [None]
            def DoLoading():    
                
                ret[0] = loadProc(*args,**kwargs)
                if not ret[0]:
                    return
                
                while True:
                    b = time.time()
                    if inp.IsKeyDown(sf.Key.S) or b-a > defaults.loading_time:
                        break
                        
                    time.sleep( min(1.0, max(0, defaults.loading_time - (b-a))))
                
            if LoadScreen.loadlevel:
                Renderer.AddDrawable(LoadScreen.loadlevel)
            
            LoadScreen.stop = False
            t = Thread(target=DoLoading)
            t.daemon = True
            t.start()
            
            inp = Renderer.app.GetInput()    
            try:
                while Renderer.IsMainloopRunning():
                    if [e for e in Renderer.SwallowEvents() if e.Type == sf.Event.KeyPressed 
                        and e.Key.Code == KeyMapping.Get("escape")]:
                       break
                            
                    Renderer._DoSingleFrame()
                    
                    if t.is_alive():
                        c = time.time()
                        LoadScreen.UpdateProgressBar((c-a)/defaults.loading_time)
                    else:    
                        if not ret[0] or LoadScreen.EndProgressBar():
                            break
            
            finally:
                if LoadScreen.loadlevel:
                    Renderer.RemoveDrawable(LoadScreen.loadlevel)
        except:
            raise
        finally:
            LoadScreen.running = False
        return ret[0]
        

 
        
        
        

# vim: ai ts=4 sts=4 et sw=4