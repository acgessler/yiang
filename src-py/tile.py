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

# Python Core
import traceback
import random
import itertools

# My own stuff
import defaults
from fonts import FontCache
from game import Entity,Game

class Tile(Entity):
    """Base class for tiles, handles common behaviour, i.e, drawing.
    Extends Entity with more specialized behaviour."""
         
    def __init__(self,text="<no text specified>",width=defaults.tiles_size[0],height=defaults.tiles_size[1],collision=Entity.BLOCK):
        Entity.__init__(self)

        self.collision = collision
        self.text = text
        self.dim = (width//defaults.tiles_size[0],height//defaults.tiles_size[1])
        self._Recache()

    def __str__(self):
        return "Tile, pos: {0}|{1}, text:\n{2}".format(\
            self.pos[0],self.pos[1],self.text)

    def Interact(self,other):
        return self.collision

    def SetColor(self,color):
        Entity.SetColor(self,color)
        self.cached.SetColor(self.color)

    def GetBoundingBox(self):
        if hasattr(self,"shrink_percentage"):
            ssp = 1.0-self.shrink_percentage
            hs = (self.dim[0]*ssp,self.dim[1]*ssp)
            return (self.pos[0]+hs[0]/2,self.pos[1]+hs[1]/2,self.dim[0]-hs[0],self.dim[1]-hs[1])    
            
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])

    def _Recache(self):
        """Cache the tile string from self.text"""
        
        rsize = defaults.letter_size[1]
        font = FontCache.get(rsize)
        self.cached = sf.String(self.text,Font=font,Size=rsize)
        
        self.cached.SetColor(self.color)

    def _ShrinkBB(self,shrink_percentage):
        """Helper function, changes the behaviour of GetBoundingBox()
        to shrink the returne dbounding box by a given percentage
        in all directions. Specifying 0.9 will result in a bounding
        box with a margin of 0.05 percent on each side."""
        self.shrink_percentage = shrink_percentage

    @staticmethod
    def CreateSimple(char,color,pos):
        """Create a tile which consists solely of a particular color,
        in a single color at a specific location."""
        t = Tile((char*defaults.tiles_size[0]+'\n')*defaults.tiles_size[1])
        t.SetColor(color)
        t.SetPosition(pos)

        return t

    def Draw(self):
        """Draw the tile given a Game instance, which defines the
        render target and the coordinate system origin for the tile"""
        self.game._Draw(self.cached,self.pos)

    def DrawRelative(self,offset):
        """Same as Draw(), except it adds an offset to the tile
        position. The offset is specified in tile coordinates"""
        self.game._Draw(self.cached,(self.pos[0]+offset[0],
            self.pos[1]+offset[1]))


class AnimTile(Tile):
    """ Adds simple animation to a Tile, which rotates the
    actual image that is displayed. The animation is either
    played automatically or manually."""

    
    def __init__(self,text,height,frames,speed,states=1,width=0):
        """ Read an animated tile from a text block. Such a textual
        description contains the ASCII images for all frames,
        separated by an empty line for clarity. There can be multiple
        'states', each of which has its own set of frames. States
        are intended for animated tiles which change their
        appearance, i.e due to user input.

            Parameters:
               text Text block
               width Character width of the tile, may be left 0.
               height Character height of the tile
               frames Number of frames in the file
               speed Playback speed, -1 for manual playback. This is
                the total time to play the whole animation, not to
                shift from one frame to the next

            Throws:
                AssertionError
        """

        Tile.__init__(self)
        
        lines = text.split("\n")
        n = 0

        self.texts, self.state = [],0
        for state in range(states):
            self.texts.append([])
            
            for frame in range(frames):
                #assert n+height<=len(lines)
                self.texts[state].append("\n".join(l.rstrip() for l in lines[n:n+height]))
                n += height+1
            n += 1

        self.speed = -1 if speed == -1 else speed / len(self.texts[self.state])
        self.animidx = -1
        self.animofs = 0

        # constraints checking
        for i in range(1,len(self.texts)):
            assert len(self.texts[i]) == len(self.texts[0])

        # update width and height to get a proper bounding box.
        if width==0:
            for text in itertools.chain(*self.texts):
                for line in text.split("\n"):
                    width = max(width,len(line))

        self.dim = (width//defaults.tiles_size[0],height//defaults.tiles_size[1])
                

    def __str__(self):
        return "AnimTile, pos: {0}|{1}, frames: {2}, speed: {3}, text:\n{4}".format(\
            self.pos[0],self.pos[1],
            self.GetNumFrames(),
            self.speed,self.text)

    def SetState(self,state):
        self.state = state % len(self.texts)

    def GetState(self):
        return self.state

    def Next(self):
        """Manually advance to the next frame"""
        self.Set(self.Get()+1)

    def Get(self):
        """Get the current frame index"""
        return self.animidx

    def Set(self,idx):
        """Set the current animation frame """
        self.animofs = idx-self.animidx
        self.animidx = idx

        if self.speed==-1:
            self._UpdateAnim()

    def GetNumFrames(self):
        """Get the number of valid animation frames"""
        return len(self.texts[0])

    def GotoRandom(self):
        """Advance to a random frame"""
        self.Set(random.randint(0,self.GetNumFrames()-1))

    def Update(self,time_elapsed,time_delta):
        """Overridden from Entity"""
       
        if self.speed == -1:
            return
            
        animidx = time_elapsed // self.speed + self.animofs
        if self.animidx == animidx:
            return

        self.animidx = animidx
        self._UpdateAnim()

    def _UpdateAnim(self):
        self.text = self.texts[self.state][int(self.animidx) % self.GetNumFrames()]
        self._Recache()
        

class TileLoader:
    """Utility class to load static or animated sets of tiles from
    unformatted ASCII text files"""

    cache = {}
    
    @staticmethod
    def Load(file,game):
        """Load from a file in the following file format:
          <exec-statement>
          <raw>
        Any occurence of <raw> in the <exec-statement> is replaced by
        <raw>. <out> in the Python line denotes the output object,
        one may use 'entity' as well. Other substitutions:
        <game> the current Game instance.
        """

        lines = TileLoader.cache.get(file,None)
        if lines is None:
            try:
                print("Loading tile from "+file)
                with open(file,"rt") as f:
                    lines = f.read().split("\n",1)
                    assert len(lines)==2

                    TileLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open "+file+" for reading")

            except AssertionError as err:
                print("File "+file+" is not well-formatted:")
                traceback.print_exc()

        if lines is None:
            return Tile()

        replace = {
            "<out>"  : "entity",
            "<raw>"  : 'r"""'+lines[1].rstrip()+' """',
            "<game>" : "game"
        }

        l = lines[0]
        for k,v in replace.items():
            l = l.replace(k,v)

        #print(l)
        tempdict = dict(locals())

        try:
            exec(l,globals(),tempdict)
        except:
            print("exec() fails loading tile {0}, executing line: {1} ".format(file,l))
            traceback.print_exc()
            
        return tempdict.get("entity",Tile())
