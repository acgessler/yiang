#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [posteffect.py]
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
import os
import sys
import threading
import math

# My stuff
import defaults
from cpptools import Preprocessor,CppError
from renderer import Drawable,Renderer

class PostFX:
    """Wrap a single SFML PostFX instance nicely"""
    def __init__(self,name,env):
        self.pfx = sf.PostFX()
        self.name = name 
        self.env = env
        self.vars = set()
        self.updater = []
        
    def __str__(self):
        return "PostFX: {0},{1} [sf.PostFX: {2}]".format(self.name,self.env,id(self.pfx))
    
    def Get(self):
        return self.pfx
    
    def Draw(self):
        for updater in self.updater:
            updater()
            
        # last try to stop postfx to occur if the user disabled it.
        # normally, we shouldn't even get that far.
        if not defaults.no_ppfx:
            Renderer.app.Draw(self.pfx)
    
    def SetParameter(self,name,*args):
        """See sf.PostFX.SetParameter()"""
        # swallow unused parameters to get rid of SFML warnings
        if not name in self.vars:
            return
        
        self.pfx.SetParameter(name,*args)
        
    def SetTexture(self,name,*args):
        """See sf.PostFX.SetTexture()"""
        if not name in self.vars:
            return
        
        self.pfx.SetTexture(name,*args)
        
    def SetUpdaterParam(self,name,value):
        for updater in self.updater:
            if hasattr(updater,"SetOuterParam"):
                updater.SetOuterParam(name,value)
    

class PostFXCache:
    """Tiny utility to cache all postprocessing effect instances"""
    cached = {}
    lock = threading.Lock()
    shared_env = None

    @staticmethod
    def Get(name="",env=(),**kwargs):
        """Obtain a postfx, given either a full path or a file name
        relative to ./data/effects. 'env' is a set of preprocessir
        directives, each is a 2-tuple (name,value) (becomes #define 
        name value). Shaders are cached internally."""
        assert name
        
        with PostFXCache.lock:
        
            if PostFXCache.shared_env is None:
                PostFXCache._SetupSharedEnv()
    
            env = env+PostFXCache.shared_env
            pfx = PostFXCache.cached.get((name,env),None) 
            if not pfx is None:
                return pfx
    
            pfx = PostFX(name,env)
            print("Loading postfx {0} / environment: {1}".format(name,env))
            
            try:
                try:
                    p = open(name,"rt")
                    dir = "."
                except IOError:
                    dir = os.path.join(defaults.data_dir,"effects")
                    p = open(os.path.join(dir,name),"rt")
                
                try:
                    string = Preprocessor.Preprocess( p.readlines(), env, [dir]  )
                except CppError as err:
                    print("Failure preprocessing postfx {0},{1}: {2}".format(name,env,err))
                    return None                
            
                if not pfx.Get().LoadFromMemory("\n".join(string)) is True:
                    print("Failure creating postfx {0},{1}.\nCode after preprocessing: {2})".format(name,env,string))
                    return None
                
                # XXX improve this, myabe query SFML directly
                data_types = ["texture","vec2","vec3","vec4","float","bool","double"]   
                for line in string:
                    words = line.split(None,3)
                    if not words:
                        continue
                    
                    if words[0] == "effect":
                        break
                    
                    if words[0] in data_types:
                        pfx.vars.add(words[1])
                        
                        # handle texture loading manually, SFML doesn't do it.
                        if len(words)>3 and words[2]=="=":
                            words[3] = words[3].strip()
                            if len(words[3]) and words[3][0] == "{" and words[3][-1] == "}":
                                kwd = words[3][1:-1]
                                
                                class closure_maker:
                                    def __init__(self,inner=PostFXCache._GetParameterUpdater(kwd),type=words[0],name=words[1]):
                                        self.inner = inner
                                        self.type = type
                                        self.name = name
                                        
                                    def __getattr__(self,name):
                                        return getattr( self.inner, name )
                                    
                                    def __call__(self):
                                        return self.inner(pfx,self.type,self.name)
                                
                                print("Set auto parameter updater: {0} -> {1}".format(words[1],words[0]))
                                pfx.updater.append(closure_maker())
                            elif words[0]=="texture":
                                # XXX unify this special case, too.
                                
                                tex = words[3].strip()
                                print("Loading implicit texture {0} (shader var: {1})".format(tex, words[1]))
                            
                                from textures import TextureCache
                                img = TextureCache.Get(tex)
                                if img:
                                    pfx.SetTexture(words[1],img)
                                    def tex_updater(pfx=pfx,type=words[0],name=words[1],tex=img):
                                        pfx.SetTexture(name,tex)
                                    
                                    pfx.updater.append(tex_updater)  
                                else:
                                    print(".. failure, ignoring this parameter")  
    
                PostFXCache.cached[(name,env)] = pfx
        
            except IOError:
                print("Cannot access postfx file: {0}".format(name))
                return None
        
        return pfx
    
    @staticmethod
    def _GetParameterUpdater(type):
        """Return a handler to be called once per frame to
        update a specific postfx parameter according to 
        certain rules (i.e. random). The handler function is 
        loaded from within the ./updaters directory, where it
        must be defined in a module with the same name (type),
        providing an Update(postfx,var_type,var_name) member."""
        def default_proc(pfx,type,name):
            pass
        
        modname = "updaters."+type
        
        try:
            __import__(modname,globals())
        except ImportError:
            print("Failure resolving PostFX updater: {0}".format(type))
            return default_proc
        
        mymod= sys.modules[modname]
        
        try:
            return getattr(mymod,"GetUpdater",None)() or getattr(mymod,"Update")
        except AttributeError:
            print("PostFX updater module {0} does not provide Update()".format(type))
        return default_proc
    
    @staticmethod
    def _SetupSharedEnv():
        """Collect some global settings shared by all postfx's"""
        PostFXCache.shared_env = []
        
        if defaults.dither is True:
            PostFXCache.shared_env.append(("ENABLE_DITHER",))
            
        if defaults.no_ppfx is True:
            PostFXCache.shared_env.append(("NO_INTENSE_PPFX",))
            
        PostFXCache.shared_env = tuple(PostFXCache.shared_env)


class PostFXOverlay(Drawable):
    """A drawable to draw a single postprocessing effect"""
    def __init__(self,postfx,draworder=900):
        Drawable.__init__(self)
        self.postfx = postfx
        assert self.postfx
        self.draworder = draworder
        
    def Draw(self):
        self.postfx.Draw()
        
    def GetDrawOrder(self):
        return self.draworder
    
    def Get(self):
        return self.postfx.Get()
    
    
class FadeInOverlay(PostFXOverlay):
    """A special overlay to fade from a specific color to the normal view"""
    def __init__(self,fade_time=1.0,fade_start=defaults.fade_start,on_close=None,draworder=900):
        """
        Construct a FadeOverlay.
        
        Parameters:
            fade_time -- Time to life
            fade_start  -- Fade intensity to start with
            on_close  -- Closure to be called when the end status of the
               animation has been reached. Pass None to let the 
               overlay automatically unregister itself.
            draworder -- Draw order ordinal
                         
        """
        PostFXOverlay.__init__(self,PostFXCache.Get("fade.sfx",()),draworder)
        self.fade_time = fade_time
        self.fade = self.fade_start  = fade_start
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        
    def GetCurrentStrength(self):
        return self.fade
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            print("Begin FadeInOverlay anim")
            
        curtime = self.clock.GetElapsedTime()
        self.fade = min(1.0, self.fade_start + curtime/self.fade_time)
        self.postfx.SetParameter("fade",self.fade)
        
        if self.fade>=1.0 and not self.on_close is None: # sanity check
            print("End FadeInOverlay anim")
            
            self.on_close(self)
            self.on_close = None
        
            
class FadeOutOverlay(PostFXOverlay):
    """A special overlay to fade from the normal view to a specific color"""
    def __init__(self,fade_time=1.0,fade_end=defaults.fade_stop,on_close=None,draworder=900):
        """
        Construct a FadeOverlay.
        
        Parameters:
            fade_time -- Time to life
            fade_end  -- Fade intensity to end at
            on_close  -- Closure to be called when the end status of the
               animation has been reached. Pass None to let the 
               overlay automatically unregister itself.
            draworder -- Draw order ordinal
                         
        """
        PostFXOverlay.__init__(self,PostFXCache.Get("fade.sfx",()),draworder)
        self.fade_time = fade_time
        self.fade_end  = fade_end
        self.fade = 1.0
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        
    def GetCurrentStrength(self):
        return self.fade
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        
        if not hasattr(self,"clock"):
            print("Begin FadeOutOverlay anim")
            self.clock = sf.Clock()
            
        curtime = self.clock.GetElapsedTime()
        self.fade = max(self.fade_end, 1.0 - curtime/self.fade_time)
        self.postfx.SetParameter("fade",self.fade)
        
        if self.fade <= self.fade_end and not self.on_close is None: # sanity check
            print("End FadeOutOverlay anim")
            
            self.on_close(self)
            self.on_close = None
            
            
            
            
class BlurInOverlay(PostFXOverlay):
    """A special overlay to slowly decrease the amount of blur until the normal status is reached"""
    def __init__(self,blur_time=1.0,blur_start=defaults.blur_stop,on_close=None,draworder=910):
        """
        Construct a BlurOverlay.
        
        Parameters:
            blur_time -- Time to life
            blur_start  -- Blur intensity to start with
            on_close  -- Closure to be called when the end status of the
               animation has been reached. Pass None to let the 
               overlay automatically unregister itself.
            draworder -- Draw order ordinal
                         
        """
        PostFXOverlay.__init__(self,PostFXCache.Get("blur_x.sfx",()),draworder)
        self.postfx2 = PostFXCache.Get("blur_y.sfx",())
        assert self.postfx2
        
        self.blur_time = blur_time
        self.blur = self.blur_start  = blur_start
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        
    def GetCurrentStrength(self):
        return self.blur
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        self.postfx2.Draw()
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            print("Begin BlurInOverlay anim")
            
        curtime = self.clock.GetElapsedTime()
        self.blur = min(1.0, self.blur_start + curtime/self.blur_time)
        self.postfx.SetParameter("blurSize",(1-self.blur)*defaults.blur_multiplier / defaults.resolution[0])
        self.postfx2.SetParameter("blurSize",(1-self.blur)*defaults.blur_multiplier / defaults.resolution[1])
        
        if self.blur>=1.0 and not self.on_close is None: # sanity check
            print("End BlurInOverlay anim")
            
            self.on_close(self)
            self.on_close = None
        
            
class BlurOutOverlay(PostFXOverlay):
    """A special overlay to vlur the normal view up to a certain intensity"""
    def __init__(self,blur_time=1.0,blur_end=defaults.blur_stop,on_close=None,draworder=910):
        """
        Construct a BlurOverlay.
        
        Parameters:
            blur_time -- Time to life
            blur_end  -- Blur intensity to end at
            on_close  -- Closure to be called when the end status of the
               animation has been reached. Pass None to let the 
               overlay automatically unregister itself.
            draworder -- Draw order ordinal
                         
        """
        PostFXOverlay.__init__(self,PostFXCache.Get("blur_x.sfx",()),draworder)
        self.postfx2 = PostFXCache.Get("blur_y.sfx",())
        assert self.postfx2
        
        self.blur_time = blur_time
        self.blur_end  = blur_end
        self.blur = 1.0
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        
    def GetCurrentStrength(self):
        return self.blur
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        self.postfx2.Draw()
        
        if not hasattr(self,"clock"):
            print("Begin BlurOutOverlay anim")
            self.clock = sf.Clock()
            
        curtime = self.clock.GetElapsedTime()
        self.blur = max(self.blur_end, 1.0 - curtime/self.blur_time)
        self.postfx.SetParameter("blurSize",(1-self.blur)*defaults.blur_multiplier / defaults.resolution[0])
        self.postfx2.SetParameter("blurSize",(1-self.blur)*defaults.blur_multiplier / defaults.resolution[1])
        
        if self.blur <= self.blur_end and not self.on_close is None: # sanity check
            print("End BlurOutOverlay anim")
            
            self.on_close(self)
            self.on_close = None
            
            
class FlashOverlay(PostFXOverlay):
    """A postprocessing overlay to apply a short color flash"""
    def __init__(self,flash_color=sf.Color.White,flash_intensity=None, flash_length=None,func=0,on_close=None,draworder=900):
        """
        Construct a FadeOverlay.
        
        Parameters:
            fade_time -- Time to life
            fade_start  -- Fade intensity to start with
            on_close  -- Closure to be called when the end status of the
               animation has been reached. Pass None to let the 
               overlay automatically unregister itself.
            draworder -- Draw order ordinal
                         
        """
        PostFXOverlay.__init__(self,PostFXCache.Get("heat.sfx",()),draworder)
        self.flash_length = flash_length or defaults.postfx_flash_length
        self.flash_intensity = flash_intensity or defaults.postfx_flash_intensity
        self.flash_color = flash_color
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        self.func = 0
    
    def EvalIntensity(self,t):
        if self.func == 0:
            # http://www.wolframalpha.com/input/?i=x^2*e^%28-x%29*100+for+x+%3D10
            t *= 10
            return ((t**2)*math.exp(-t)*100)/55
        elif self.func == 1:
            return t
        elif self.func == 2:
            return min(t*5,1) 
        if self.func == 3:
            # same as 0, except it's sharper
            t *= 10
            return (((t*10)**3)*math.exp(-t)*100)/55
        
        assert False
        
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            print("Begin FlashOverlay anim")
            
        curtime = self.clock.GetElapsedTime()
        
        s = self.EvalIntensity(curtime/self.flash_length)*self.flash_intensity
        self.postfx.SetParameter("col_scale",s)
        self.postfx.SetParameter("col_target",self.flash_color.r*s,self.flash_color.g*s,self.flash_color.b*s)
        
        if curtime > self.flash_length and not self.on_close is None: # sanity check
            print("End FlashOverlay anim")
            
            self.on_close(self)
            self.on_close = None   
            
            
class QuickFocus(PostFXOverlay):
    """A postprocessing overlay to limit the view to a circle around the player, 
    which is gradually increased until normal size is reached again"""
    def __init__(self,player,flash_color=sf.Color.White,focus_length=None,on_close=None,draworder=700):
        
        PostFXOverlay.__init__(self,PostFXCache.Get("focusplayer.sfx",()),draworder)
        self.focus_length = focus_length or defaults.postfx_focus_length
        self.on_close  = (lambda x:Renderer.RemoveDrawable(x)) if on_close is None else on_close 
        self.player = player
        
        self.postfx.SetUpdaterParam("player",player)
    
        
    def Draw(self):
        PostFXOverlay.Draw(self)
        
        if not hasattr(self,"clock"):
            self.clock = sf.Clock()
            print("Begin QuickFocus anim")
            
        curtime = self.clock.GetElapsedTime()
        self.postfx.SetParameter("amount",curtime/self.focus_length)
        self.postfx.SetParameter("aspect",defaults.resolution[0]/defaults.resolution[1])
        
        if curtime > self.focus_length and not self.on_close is None: # sanity check
            print("End QuickFocus anim")
            
            self.on_close(self)
            self.on_close = None   

# vim: ai ts=4 sts=4 et sw=4