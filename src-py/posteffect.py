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
import os

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
        
    def __str__(self):
        return "PostFX: {0},{1} [sf.PostFX: {2}]".format(self.name,self.env,id(self.pfx))
    
    def Get(self):
        return self.pfx
    
    def SetParameter(self,*args):
        # XXX swallow unused parameters to get rid of SFMl warnings?
        self.pfx.SetParameter(*args)
        
    def SetTexture(self,*args):
        self.pfx.SetTexture(*args)
    

class PostFXCache:
    """Tiny utility to cache all postprocessing effect instances"""
    cached = {}

    @staticmethod
    def Get(name="",env=()):
        assert name

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
                string = Preprocessor.Preprocess( p.readlines(), [], [dir]  )
            except CppError as err:
                print("Failure preprocessing postfx {0},{1}: {2}".format(name,env,err))
                return None
        
            if not pfx.Get().LoadFromMemory("\n".join(string)) is True:
                print("Failure creating postfx {0},{1}.\nCode after preprocessing: {2})".format(name,env,string))
                return None

            pfx.SetTexture("framebuffer", None);
            PostFXCache.cached[(name,env)] = pfx
    
        except IOError:
            print("Cannot access postfx file: {0}".format(name))
            return None
        
        return pfx

class PostFXOverlay(Drawable):
    """A drawable to draw a single postprocessing effect"""
    def __init__(self,postfx,draworder=900):
        Drawable.__init__(self)
        self.postfx = postfx
        self.draworder = draworder
        
    def Draw(self):
        Renderer.app.Draw(self.postfx.Get())
        
    def GetDrawOrder(self):
        return self.draworder
    
    def Get(self):
        return self.postfx.Get()
    
        
        
