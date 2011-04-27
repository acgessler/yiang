#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [locked.py]
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

# My own stuff
from stubs import *


class FloatingNotification:
    
    def __init__(self,alpha_scale=1.0):
        self.alpha_scale = alpha_scale
    
    def DrawNotification(self,text=_('(no text specified)'),scale=1.0):
        scale = max(0,min(1,scale*self.alpha_scale))
        
        r,g,b = self.color.r,self.color.g,self.color.b
        fg = sf.Color(r//4,g//4,b//4,int(0xff*scale))
        bg = sf.Color(r//2,g//2,b//2,int(0xff*scale))
        
        pos = list(self.level.ToCameraDeviceCoordinates((self.pos[0]+self.dim[0]/2,self.pos[1]+self.dim[1]/2)))
        pos[0] = max(240,pos[0])
        bb = pos[0]-200,pos[1]+5,pos[0],pos[1]+19
        shape = sf.Shape()
        shape.AddPoint(bb[0], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[1],fg,bg )
        shape.AddPoint(bb[2], bb[3],fg,bg )
        shape.AddPoint(bb[0], bb[3],fg,bg )
        
        shape.SetOutlineWidth(2)
        shape.EnableFill(True)
        shape.EnableOutline(True)
        Renderer.app.Draw(shape)
        
        rsize = 8
        text = sf.String(text,Font=FontCache.get(rsize),Size=rsize)
        text.SetPosition(bb[0]+10,bb[1]+3)
        text.SetColor(sf.Color(0xff,0xff,0xff,int(0xd0*scale)))
        Renderer.app.Draw(text)
        
        