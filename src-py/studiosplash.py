#!/usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [studiosplash.py]
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

import time,random,os
from stubs import *

class Splash(Drawable):
    """This class is responsible for displaying the studio's logo"""

    def __init__(self,on_close):
        Drawable.__init__(self)
        
        print("Entering studiosplash")
        
        self.on_close = on_close
        self.trigger_close = False
        self.splashimg = TextureCache.Get(os.path.join(defaults.data_dir,"textures","splash.png"))
        Renderer.SetClearColor(sf.Color.Black)
        
    def Draw(self):
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            
        time = self.clock.GetElapsedTime()
        
        s = sf.Sprite(self.splashimg)
        
        w,h = self.splashimg.GetWidth(),self.splashimg.GetHeight()
        s.Move((defaults.resolution[0]-w)/2,(defaults.resolution[1]-h)/2)
    
        Renderer.app.Draw(s)
            
        if time > 1.2 or any(e for e in Renderer.SwallowEvents() if e.Type == sf.Event.KeyPressed): 
            if self.trigger_close:
                return
            
            self.trigger_close = True
            
            def next(old):
                Renderer.RemoveDrawable(self)
                Renderer.RemoveDrawable(old)
                self.on_close()
            
            from posteffect import FadeOutOverlay
            Renderer.AddDrawable(FadeOutOverlay(fade_time=0.3,fade_end=0.0,on_close=next))
            
            
            
            