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
import collections
import os

# My own stuff
import defaults
import validator
from fonts import FontCache


class Level:
    """The Level class represents the currently loaded level and is responsible
    for both drawing and updating - also it maintains the list of all entities
    in the level"""
    
    def __init__(self, level, game, lines):
        self.entities, self.entities_add, self.entities_rem = set(), set(), set()
        self.origin = [0, 0]
        self.game = game
        self.level = level
        
        assert self.game
        assert self.level >= 0
        
        spaces = [" ", "\t", "."]
        line_idx, ecnt = 0, 0
        
        self.lines = lines = lines.split("\n")
        assert len(lines) > 0
        
        try:
            for y, line in enumerate(lines):
                line_idx += 1
                line = line.rstrip(" \n\t.")
                if len(line) == 0:
                    continue

                diff = len(lines) - defaults.tiles[1]

                assert len(line) % 3 == 0
                for x in range(0, len(line), 3):
                    ccode = line[x]
                    tcode = line[x + 1] + line[x + 2]

                    if tcode[0] in spaces:
                        continue
                    
                    from tile import TileLoader
                        
                    # read from the private attachment tiles of the level if the tile
                    # code starts with a lower-case character
                    if tcode[0] in "abcdefghijklmnopqrstuvwxyz":
                        tile = TileLoader.Load(os.path.join(defaults.data_dir, "levels", str(level), tcode + ".txt"), self)
                    else:
                        tile = None
                        
                    if tile is None:
                        tile = TileLoader.Load(os.path.join(defaults.data_dir, "tiles", tcode + ".txt"), self)
                            
                        tile.SetColor(LevelLoader.cached_color_dict[ccode])
                        tile.SetPosition((x // 3, y - diff))
                        
                        self.AddEntity(tile)
                        ecnt += 1
                
        except AssertionError as err:
            print("Level " + str(level) + " is not well-formatted (line {0})".format(line_idx))
            traceback.print_exc()

        self.level_size = (x // 3, y)
        print("Got {0} entities for level {1}".format(ecnt, level))
        
        validator.validate_level(self.lines, level)

    def Draw(self,time,dtime):
        """Called by the Game matchmaker class once per frame,
        may raise Game.NewFrame to advance to the next frame
        and skip any other jobs for this frame"""
        for entity in self.entities:
            entity.Update(time, dtime)
                    
        for entity in self.entities:
            entity.Draw()
            
        self._UpdateEntityList()

    def _UpdateEntityList(self):
        """Used internally to apply deferred changes to the entity
        list. Changes are deferred till the end of the frame to
        avoid changing list sizes while iterating through them."""
        for entity in self.entities_rem:
            self.entities.remove(entity)
            
        for entity in self.entities_add:
            self.entities.add(entity)
            
        self.entities_add, self.entities_rem = set(), set()
    
    def GetLevelSize(self):
        """Get the size of the current level, in tiles. The return
        value is a 2-tuple."""
        return self.level_size
    
    def AddEntity(self, entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        entity.SetGame(self.game)
        self.entities_add.add(entity)
        
        try:
            self.entities_rem.remove(entity)
        except KeyError:
            pass
        
    def RemoveEntity(self, entity):
        """Dynamically add an entity to the list of all active
        entities. The operation is deferred until the next
        frame so it is safe to be called from enumeration
        context"""
        self.entities_rem.add(entity)
    
    
class LevelLoader:
    """Loads levels from their disk representations into memory"""
    
    cache = {}
    
    @staticmethod
    def LoadLevel(level,game):
        """Load a particular level, return a valid Level instance on success,
        otherwise None.
        
        File format for level files:
          <exec-statement>
          <raw>
        The <exec-statement> must be a valid python expression of the
        following form:
        ..... <out> = SomeClassInheritingLevel(CTorArgs)
        
        For use with the c'tor, several placeholder arguments are
        supported:
        
        <game> Current Game instance
        <raw> Raw text contents of the file, excluding the 'shebang'
        <level> One-based index of the level
        <out> The returned Level object
        
        To get default behaviour, use:
        <out> = Level(<level>,<game>,<raw>)
        """
        
        print("Loading level from disc: " + str(level))

        # this remains as the default color table if we can't read config/color.txt
        color_dict_default = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })

        # the actual mapping table has been outsourced to config/colors.txt
        if not hasattr(LevelLoader, "cached_color_dict"):

            def complain_on_fail():
                print("Encountered unknown color key")
                return sf.Color.White
            
            LevelLoader.cached_color_dict = collections.defaultdict(complain_on_fail, color_dict_default)
            try:
                with open(os.path.join(defaults.config_dir, "colors.txt"), "rt") as scores:
                    for n, line in enumerate([ll for ll in scores.readlines() if len(ll.strip()) and ll[0] != "#"]):
                        code, col = [l.strip() for l in line.split("=")]

                        assert len(col) == 6
                        LevelLoader.cached_color_dict[code] = sf.Color(int(col[0:2], 16), int(col[2:4], 16), int(col[4:6], 16))

                print("Caching colors.txt file, got {0} dict entries".format(len(LevelLoader.cached_color_dict)))

            except IOError:
                print("Failure reading colors.txt file")
            except AssertionError:
                print("color.txt is not well-formed: ")
                traceback.print_exc()
       
        file = os.path.join(defaults.data_dir, "levels", str(level) + ".txt")
        lines = LevelLoader.cache.get(file,None)
        if lines is None:
            try:
                print("Loading level from "+file)
                with open(file,"rt") as f:
                    lines = f.read().split("\n",1)
                    assert len(lines)==2

                    LevelLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open level file "+file+" for reading")

            except AssertionError as err:
                print("Level file "+file+" is not well-formatted:")
                traceback.print_exc()

        if lines is None:
            return None

        replace = {
            "<out>"  : "level",
            "<raw>"  : 'r"""'+lines[1].rstrip()+' """',
            "<game>" : "game",
            "<level>"  : "level"
        }

        l = lines[0]
        for k,v in replace.items():
            l = l.replace(k,v)

        #print(l)
        tempdict = dict(locals())

        try:
            exec(l,globals(),tempdict)
        except:
            print("exec() fails loading level {0}, executing line: {1} ".format(file,l))
            traceback.print_exc()
            
        return tempdict.get("level",None)
    
    
    
