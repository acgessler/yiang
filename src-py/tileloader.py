#!/usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [tile.py]
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

# Python Core
import traceback
import random
import itertools
import os
import collections

# My own stuff
import defaults
from tile import Tile
from entity import Entity
from game import Game

# TileLoader maintains a global cache, so we need to protect 
# it to avoid concurrency problems.
if defaults.no_threading:
    import dummy_threading as threading
else:
    import threading 
    

class TileLoader:
    """Utility class to load static or animated sets of tiles from
    unformatted ASCII text files"""

    cache = {}
    has_cookies = set()
    
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
    def FetchColors():
        if hasattr(TileLoader, "cached_color_dict"):
            return
        
        # this remains as the default color table if we can't read config/color.txt
        color_dict_default = collections.defaultdict(lambda: sf.Color.White, {
            "r" : sf.Color.Red,
            "g" : sf.Color.Green,
            "b" : sf.Color.Blue,
            "y" : sf.Color.Yellow,
            "_" : sf.Color.White,
        })
        
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
        
        
        file_norm = file.replace("/","\\")

        if os.name == 'posix':
            file = file.replace("\\","/")

        # the actual mapping table has been outsourced to config/colors.txt
        TileLoader.FetchColors()

        lines = TileLoader.cache.get(file_norm,None)
        if lines is None:
            # Check if a pre-compiled cache exists in this directory
            dir, name = os.path.split(file)
            if not dir in TileLoader.has_cookies:
                TileLoader.has_cookies.add(dir)
                
                cache = os.path.join(dir,"cooked","tiles.dat")
                import marshal
                try:
                    with open(cache,"rb") as inf:
                        cached = marshal.load(inf)
                        
                    print("Read cooked tiles: {0}, {1} entries".format(cache,len(cached)))
                        
                    TileLoader.cache.update(cached)
                    lines = cached.get(file,None)
                    
                except:
                    print("Failure reading cooked tiles: {0}".format(cache))
                    traceback.print_exc()            
            
        if lines is None:
            try:
                print("Loading tile from "+file)
                with open(file,"rt",encoding='cp1252') as f:
                    lines = f.read().split("\n",1)
                      
            except IOError:
                print("Could not open "+file+" for reading")
                lines = ["<out> = Tile(<raw>,Tile.AUTO,Tile.AUTO,collision=Entity.ENTER)",
                    "(Missing tile: {0})".format(file)
                ]

            except AssertionError as err:
                print("File "+file+" is not well-formatted:")
                traceback.print_exc()

            assert len(lines)==2
            replace = {
                    "<out>"  : "entity",
                    "<raw>"  : 'r"""'+lines[1].rstrip().replace('\"\"\"',
                        '\"\"\" + \'\"\"\"\' + \"\"\"').replace('\\\n','\x5c \n') +' """',
                    "<game>" : "game"
            }

            lines = lines[0]
            for k,v in replace.items():
                lines = lines.replace(k,v)
                
            TileLoader.cache[file_norm] = lines = compile(lines,"<shebang-string>","exec")

        tempdict = dict(locals())

        try:
            exec(lines,globals(),tempdict)
        except:
            print("exec() fails loading tile {0}, executing line: {1} ".format(file,lines))
            # print_exc goes to stderr which does not go to log
            print(traceback.format_exc())
            
        tile = tempdict.get("entity",Tile())
        tile.SetGame(game)
        
        if game.GetGameMode() == Game.EDITOR:
            # in editor mode, store the tile's shebang line in the tile itself
            tile.editor_shebang = lines
        
        return tile
    
# vim: ai ts=4 sts=4 et sw=4
