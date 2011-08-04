#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [player.py]
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

import os

from stubs import *

class Anim:    
    """Single animation of the player entity, used in conjunction with `AnimSet`"""
    
    modi = ('repeat','stop','goto')
    
    def __init__(self,fname):
        self.fname = fname
        self.frame = 0
        with open(fname,'rt') as inp:
            lines = inp.readlines()
            if len(lines) <= 1:
                raise Exception('too few lines')
            
            
            self.framecnt,self.framelen,self.mode = [s.strip() for s in lines[0].split(';') if len(s.strip())]
            self.framecnt = int(self.framecnt)
            self.framelen = float(self.framecnt) if defaults.debug_player_anims else float(self.framelen) 
            
            if self.framecnt == 0:
                raise Exception('need at least one frame')
            
            if not self.mode.split('=')[0] in Anim.modi:
                raise Exception('animation mode not supported: ' + self.mode)
            
            frames = '\n'.join(s.rstrip() for s in lines[1:]).split('\n\n')
            if len(frames) < self.framecnt:
                raise Exception('too few frames, expected ' + str(self.framecnt))
            
            frames = frames[:self.framecnt]
            if len(set(n.count('\n') for n in frames)) != 1:
                raise Exception('all frames must have the same y size')
            
            self.tiles = [Tile(f,halo_img=None,permute=False) for f in frames]
            
    def __str__(self):
        return "[Anim " + self.fname + '}'
    
    def GetTile(self):
        return self.tiles[self.frame]
    
    def Select(self):
        pass
    
    def Deselect(self):
        self.frame = 0
        try:
            delattr(self,'started')
        except AttributeError:
            pass
    
    def Update(self,time,dtime):
        if not hasattr(self,'started'):
            self.started = time
        
        diff = time-self.started
        if (self.mode == 'stop' or self.mode[:4] == 'goto') and diff >= self.framelen:
            self.frame = self.framecnt-1
            if self.mode[:4] == 'goto':
                assert self.mode[4] == '='
                return self.mode[5:]
            
            return
        
        self.frame = int(((diff % self.framelen)/self.framelen)*self.framecnt)
                
    
class AnimSet:
    """Class to keep track of all the animations for the player. Players have
    significantly more complex animations as the rest of the entities,
    so I'm introducing a dedicated solution at this point."""
    def __init__(self,name):
        self.name = name
        self.active = None
        
        self.anims = {}
        print('start loading AnimSet: ' + name)
        
        # scan the directory for all animations
        base = os.path.join(defaults.data_dir,"external_anims",name)
        for thisfile in os.listdir(base):      
            fname,ext = os.path.splitext(thisfile)
            if ext.lower() == '.txt':
                full = os.path.join(base,thisfile)
                try:
                    self.anims[fname] = self._LoadAnimFile(full)
                    print('got animation ' + fname)
                except Exception as e:
                    print('failed to load animation {0}, got exception: {1}'.format(fname,e))
                    
        print('finish loading AnimSet: {0}, got {1} animsets with totally {2} frames'.format(name,len(self.anims),sum(s.framecnt for s in self.anims.values())))
        print(self.anims)
              
    def _LoadAnimFile(self,f):
        return Anim(f)
            
    def __str__(self):
        return "[AnimSet " + self.name + '}'
    
    def Select(self,name):
        if name == self.active:
            return
        
        if not self.active is None:
            self.anims[self.active].Deselect()
        
        self.active = name
        self.anims[self.active].Select()
        
    def GetCurrent(self):
        return self.active
    
    def GetCurrentTile(self):
        assert self.active in self.anims
        return self.anims[self.active].GetTile()
    
    def UpdateCurrentTile(self,time,dtime):
        assert self.active in self.anims
        newone = self.anims[self.active].Update(time,dtime)
        if isinstance(newone,str):
            print('auto: ' + newone)
            self.Select(newone)
    
    def ConfigureTilesGlobally(self,callback):
        [[callback(t) for t in a.tiles] for a in self.anims.values()]

