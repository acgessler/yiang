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
import os
import collections

# My own stuff
import defaults
from fonts import FontCache
from game import Entity,Game




class Tile(Entity):
    """Base class for tiles, handles common behaviour, i.e, drawing.
    Extends Entity with more specialized behaviour."""
    
    AUTO=-1
    AUTO_QUICK=-2
    
    # These caches are a quick attempt to optimize performance.
    # Obvisouly, since these dicts are indexed by full-length
    # tile strings, lookup performance is quite low.
    
    global_dim_cache = {} # stores (dim,ofs) tuples
    global_str_cache = {} # stores sf.String's indexed by (str,rsize) pairs
           
    def __init__(self,text="<no text specified>",width=None,height=None,collision=Entity.BLOCK,draworder=10,rsize=None,halo_img="default",width_ofs=0,height_ofs=0):
        
        # Note: the 'constants' from defaults may change during startup, but 
        # this file may get parsed BEFORE this happens, so we can't
        # access defaults safely from default arguments which are 
        # stored at parse-time.
        height = height or Tile.AUTO
        width  = width  or Tile.AUTO
        rsize  = rsize  or defaults.letter_size[1]
        scale  =  rsize / defaults.letter_size[1] 
            
        Entity.__init__(self)

        self.scale = scale
        self.rsize = rsize
        self.collision = collision
        self.text = text
            
        self.draworder = draworder
        self.halo_img = halo_img
        
        # if either width and height are AUTO, compute the minimum bounding
        # rectangle for all glyph bounding rectangles.
        if width==Tile.AUTO or height==Tile.AUTO:
            self.dim,self.ofs = self._GuessRealBB(self.text)
            
        elif width==Tile.AUTO_QUICK or height==Tile.AUTO_QUICK:
            self.dim,self.ofs = self._GuessRealBB_Quick(self.text)
            
        else:
            self.dim = self._LetterToTileCoords(width,height)
            self.ofs = (width_ofs,height_ofs)
            
        self._Recache()

    def __str__(self):
        return "<Tile, pos: {0}|{1}, text:\n{2}>".format(\
            self.pos[0],self.pos[1],self.text)
        
    #def __repr__(self):
    #    return self.editor_shebang if hasattr(self,"editor_shebang") else self.__str__()
        
    def _LetterToTileCoords(self,*args):
        width,height = args if len(args)==2 else args[0]
        return width*self.scale/defaults.tiles_size[0],\
            height*self.scale/defaults.tiles_size[1]
        
    def _GuessRealBB(self,text):
        """Return adjusted (width,height) (xofs,yofs) tuples
        basing on the current values and 'text' """
        
        
        # XXX Font.Glyph[i].Rectangle() does not seem to provide reliable results
        # XXX I'm guessing this is an issue with PySFML
        """
        font = FontCache.get(self.rsize)
        assert font
        
        t,r,b,l = 0,0,0,0
        
        lines = [e for e in enumerate(self.text.split("\n"))]
        for y,line in lines:
            if len(line)==0:
                continue
            
            if y==0:
                for c in line:
                    gl = font.GetGlyph(ord(c))
                    assert gl
                    
                    t = max(gl.Rectangle.Top,t)
            elif y==len(lines)-1:
                for c in line:
                    gl = font.GetGlyph(ord(c))
                    assert gl
                    
                    b = max(gl.Rectangle.Bottom,t)
                    
            thisone = [e for e in enumerate(line)]
            for y,c in thisone:
                if c==" ":
                    continue
                gl = font.GetGlyph(ord(c))
                assert gl
                    
                l = max(gl.Rectangle.Left,l)
            
            for y,c in reversed(thisone):
                if c==" ":
                    continue
                print(c,ord(c))
                gl = font.GetGlyph(ord(c))
                assert gl
                    
                r = max(gl.Rectangle.Right,r)
        """
        
        res = Tile.global_dim_cache.get(text)
        if not res is None:
            return res
        
        b,r,t,l = 0,0,1e6,1e6
        
        # and because the aboce solution does not work, why not do it manually?
        lookup = collections.defaultdict(lambda : (0.0,0.0,1.0,1.0), {
            "_" : (0.0,0.9,1.0,1.0),
            "-" : (0.0,0.5,1.0,0.7),
            "." : (0.0,0.5,1.0,0.9)
        } )
        
        def do_lookup(c):
            #if c in "abcdefghijklmnopqrstuvwxyz":
            #    return (0.0,0.9,1.0,0.1)
            
            return lookup[c]
        
        space = " \t"
        ls = defaults.tiles_size
        
        lines = [e for e in enumerate(text.split("\n")) if not len(e[1])==0]
        for y,line in lines:
            
            thisone = [e for e in enumerate(line)]
            for x,c in thisone:
                if not c in space:
                    l = min(do_lookup(c)[0]+x,l)
                    break
            
            for x,c in reversed(thisone):
                if not c in space:
                    r = max(do_lookup(c)[2]+x,r)
                    break
                
        out = False
        for y,line in lines:
            for c in line:
                if not c in space:
                    t = min(do_lookup(c)[1]+y,t)
                    out = True
                    break
            if out is True:
                break
                
        out = False
        for y,line in reversed(lines):
            for c in line:
                if not c in space:
                    b = max(do_lookup(c)[3]+y,b)
                    out = True
                    break
            if out is True:
                break
            
        dim = (r-l)*self.scale/ls[0],(b-t)*self.scale/ls[1]  
        ofs = l*self.scale/ls[0],t*self.scale/ls[1]  
        #print(dim,ofs)
        
        Tile.global_dim_cache[text] = dim,ofs
        return dim,ofs
    
    def _GuessRealBB_Quick(self,text):
        """Return adjusted (width,height) (xofs,yofs) tuples
        basing on the current values and 'text' """
        gen = text.split("\n")
        x,y = 0,len(gen)
        
        for line in gen:
            x = max(len(line),x)
            
        return (x,y),(0,0)

    def Interact(self,other):
        return self.collision

    def SetColor(self,color):
        Entity.SetColor(self,color)
        for elem in self.cached:
            elem[1].SetColor(self.color)
            
    def SetDim(self,dim):
        self.dim = dim
        self._Recache()
        
    def GetDrawOrder(self):
        # unlike most other kinds of Entities, the draw order is
        # freely configurable here.
        return self.draworder

    def GetBoundingBox(self):
        return self.cached_bb 
    
    def GetBoundingBoxAbs(self):
        return self.cached_bb_abs
    
    def _UpdateBB(self):
        if hasattr(self,"shrink_percentage"):
            ssp = 1.0-self.shrink_percentage
            hs = (self.dim[0]*ssp,self.dim[1]*ssp)
            self.cached_bb = b = (self.pos[0]+hs[0]/2,self.pos[1]+hs[1]/2,self.dim[0]-hs[0],self.dim[1]-hs[1])       
        else:
            self.cached_bb = b = (self.pos[0],self.pos[1],self.dim[0],self.dim[1])
        self.cached_bb_abs = (b[0],b[1],b[0]+b[2],b[1]+b[3])
    
    def GetBoundingBox_EditorCatalogue(self): # Special logic for use within the editor
        return (self.pos[0],self.pos[1],self.dim[0],self.dim[1])
    
    def _GetHaloImage(self):
        return Entity._GetHaloImage(self,self.halo_img)

    def _Recache(self):
        """Cache the tile string from self.text with font size self.rsize"""
        res = Tile.global_str_cache.get((self.rsize,self.text))
        if res is None:
            font = FontCache.get(self.rsize)
            res = sf.String(self.text,Font=font,Size=self.rsize)
            
            Tile.global_str_cache[(self.rsize,self.text)] = res
        
        self.cached = [(True,res)]
        
        img = self._GetHaloImage()
        if not img is None:
            self.cached.append((False,sf.Sprite(img)))
            self.cached[-1][1].Resize(self.dim[0] * defaults.tiles_size_px[0],self.dim[1] * defaults.tiles_size_px[1])
            
    def _EnumCached(self):
        return [e[1] for e in self.cached]

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
        lv = self.game.GetLevel()
        for offsetit, elem in reversed(self.cached): 
            
            elem.SetColor(self.color)
            if offsetit is True:
                lv.DrawSingle(elem,(self.pos[0]-self.ofs[0],self.pos[1]-self.ofs[1]))
            else:
                lv.DrawSingle(elem,self.pos)

    def DrawRelative(self,offset):
        """Same as Draw(), except it adds an offset to the tile
        position. The offset is specified in tile coordinates"""
        lv = self.game.GetLevel()
        for offsetit, elem in self.cached: 
            elem.SetColor(self.color)
            lv.DrawSingle(elem,(self.pos[0]+offset[0],self.pos[1]+offset[1]))


class AnimTile(Tile):
    """ Adds simple animation to a Tile, which rotates the
    actual image that is displayed. The animation is either
    played automatically or manually."""

    
    def __init__(self,text,height,frames,speed,states=1,width=Tile.AUTO,draworder=20,
        randomize=False,noloop=False, 
        *args, **kwargs):
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

        Tile.__init__(self,draworder=draworder,*args, **kwargs)
        
        assert states > 0 and frames > 0
        
        lines = text.split("\n")
        n = 0

        self.texts, self.cached_sizes, self.state = [],[],0
        for state in range(states):
            self.texts.append([])
            self.cached_sizes.append([])
            
            for frame in range(frames):
                #assert n+height<=len(lines)
                self.texts[state].append("\n".join(l.rstrip() for l in lines[n:n+height]))
                self.cached_sizes[state].append( (self._LetterToTileCoords(width,height), (0.0,0.0) ) if width > 0 else
                     (self._GuessRealBB if width == Tile.AUTO else self._GuessRealBB_Quick) 
                        (self.texts[state][-1]
                ))
                n += height+1
            n += 1

        self.SetSpeed(speed)
        self.animidx = -1
        self.animofs = 0
        self.noloop = noloop

        # constraints checking
        for i in range(1,len(self.texts)):
            assert len(self.texts[i]) == len(self.texts[0])

        self.dim,self.ofs = self.cached_sizes[0][0]
        if randomize is True:
            self.GotoRandom()
            
    def SetSpeed(self,speed):
        """Change the playback speed of the animation. The
        given duration is for the whole set of frames, in
        seconds. Pass -1 to animate manually."""
        self.speed = -1 if speed == -1 else speed / len(self.texts[self.state])

    def __str__(self):
        return "<AnimTile, pos: {0}|{1}, frames: {2}, speed: {3}, text:\n{4}>".format(\
            self.pos[0],self.pos[1],
            self.GetNumFrames(),
            self.speed,self.text)

    def SetState(self,state):
        self.state = state % len(self.texts)
        self.animofs = self.animidx = 0
        self.reset_anim = True

    def GetState(self):
        return self.state

    def Next(self):
        """Manually advance to the next frame"""
        self.Set(self.Get()+1)

    def Get(self):
        """Get the current frame index"""
        return  int(min(self.GetNumFrames()-1,self.animidx) \
            if self.noloop else self.animidx % self.GetNumFrames()
        )

    def Set(self,idx):
        """Set the current animation frame """
        self.animidx = idx
        self.reset_anim = True

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
            
        try:
            delattr(self,"reset_anim")
            self._UpdateAnim()
        except AttributeError:
            animidx = time_elapsed // self.speed + self.animofs
            if self.animidx == animidx:
                return
    
            self.animidx = animidx
            self._UpdateAnim()

    def _UpdateAnim(self):
        idx = self.Get()
            
        self.text = self.texts[self.state][idx]
        self._Recache()
        self.level._MarkEntityAsMoved(self)
        
        self.dim,self.ofs = self.cached_sizes[self.state][idx]
        self._UpdateBB()
        

class TileLoader:
    """Utility class to load static or animated sets of tiles from
    unformatted ASCII text files"""

    cache = {}
    
    @staticmethod
    def GetColor(index):
        """Lookup a color index, return the RGBA color."""
        return TileLoader.cached_color_dict[index]
    
    @staticmethod
    def LoadFromTag(tag,game):
        """Shortcut to load a tile from a 3-character tag,
        consisting of a one-char color code and a two-char
        type code"""
        
        assert len(tag)==3
        ccode, tcode = tag[0], tag[1:]
        
        tlbase = os.path.join(defaults.data_dir, "tiles")
        
        tile = TileLoader.Load(tlbase + "/" + tcode + ".txt", game)
        tile.SetColor(TileLoader.GetColor(ccode))
        
        # (HACK) Editor mode: store color and type code in order to
        # save the level again later this day.
        if game.GetGameMode() == 3:
            tile.editor_ccode = ccode
            tile.editor_tcode = tcode
            
        return tile
    
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
        
        # this remains as the default color table if we can't read config/color.txt
        color_dict_default = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })

        # the actual mapping table has been outsourced to config/colors.txt
        if not hasattr(TileLoader, "cached_color_dict"):

            def complain_on_fail():
                # this is just the last fallback to avoid KeyError's
                print("Encountered unknown color key")
                return sf.Color.White
            
            TileLoader.cached_color_dict = collections.defaultdict(complain_on_fail, color_dict_default)
            try:
                with open(os.path.join(defaults.config_dir, "colors.txt"), "rt") as scores:
                    for n, line in enumerate([ll for ll in scores.readlines() if len(ll.strip()) and ll[0] != "#"]):
                        code, col = [l.strip() for l in line.split("=")]

                        assert len(col) in (6,8)
                        TileLoader.cached_color_dict[code] = sf.Color(
                            int(col[0:2], 16), 
                            int(col[2:4], 16), 
                            int(col[4:6], 16), 
                            int(col[6:8], 16) if len(col)==8 else 255 
                        )

                print("Caching colors.txt file, got {0} dict entries".format(len(TileLoader.cached_color_dict)))

            except IOError:
                print("Failure reading colors.txt file")
            except AssertionError:
                print("color.txt is not well-formed: ")
                traceback.print_exc()

        lines = TileLoader.cache.get(file,None)
        if lines is None:
            try:
                print("Loading tile from "+file)
                with open(file,"rt") as f:
                    lines = f.read().split("\n",1)
                      
            except IOError:
                print("Could not open "+file+" for reading")
                lines = ["<out> = Tile(<raw>,Tile.AUTO,Tile.AUTO,collision=Entity.ENTER)","(Missing tile: {0})".format(file)]

            except AssertionError as err:
                print("File "+file+" is not well-formatted:")
                traceback.print_exc()

            assert len(lines)==2
            replace = {
                    "<out>"  : "entity",
                    "<raw>"  : 'r"""'+lines[1].rstrip().replace('\"\"\"','\"\"\" + \'\"\"\"\' + \"\"\"') +' """',
                    "<game>" : "game"
            }

            lines = lines[0]
            for k,v in replace.items():
                lines = lines.replace(k,v)
                
            TileLoader.cache[file] = lines = compile(lines,"<shebang-string>","exec")

        #print(l)
        tempdict = dict(locals())

        try:
            exec(lines,globals(),tempdict)
        except:
            print("exec() fails loading tile {0}, executing line: {1} ".format(file,lines))
            traceback.print_exc()
            
        tile = tempdict.get("entity",Tile())
        tile.SetGame(game)
        
        if game.GetGameMode() == Game.EDITOR:
            # in editor mode, store the tile's shebang line in the tile itself
            tile.editor_shebang = lines
        
        return tile
