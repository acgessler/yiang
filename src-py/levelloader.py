#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [level.py]
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
import collections
import os
import itertools
import math
import operator
import builtins

# My own stuff
import defaults
import validator
from level import Level
from tileloader import TileLoader

# LevelLoader maintains a global cache, so we need to protect 
# it to avoid concurrency problems.
if defaults.no_threading:
    import dummy_threading as threading
else:
    import threading 
    
    
class LevelLoader:
    """Loads levels from their disk representations into memory"""
    
    cache = {}
    name_cache = {}
    
    @staticmethod
    def BuildLevelPath(index):
        """Obtain the (relative) path to the file containing the
        tile setup for a specific level, which is identified by
        its number"""
        original = os.path.join(defaults.data_dir, "levels", str(index) + ".txt")
        if defaults.load_optimized_levels:
            path = os.path.join(defaults.data_dir, "levels","optimized", str(index) + ".txt")
            if os.path.exists(path):
                # stat both the original and the optimized file and see which is newer
                try:
                    time_orig,time_opti = os.stat(original).st_mtime,os.stat(path).st_mtime
                except OSError:
                    # stat() is not supported with fs redirection being active
                    time_orig,time_opti = 0,0
                    
                if time_orig > time_opti:
                    print('ignoring optimized version for level {0}, the original level file is newer'.format(index))
                else:
                    print('got valid optimized data for level {0}'.format(index))
                    return path
            
            else:
                print('failed to locate optimized version for level {0}'.format(index))
        
        return original
    
    @staticmethod
    def GuessLevelName(index):
        """Try to guess the name of the level with index 'index'.
        The function tries to extract the name from the level's
        shebang line, it does not actually interpret or load it."""
        
        if index in LevelLoader.name_cache:
            return LevelLoader.name_cache[index]
            
        # try to obtain the written name of the level by
        # skimming through its shebang line looking
        # for name="..."
        file = LevelLoader.BuildLevelPath(index)
        LevelLoader.name_cache[index] = name = "Level {0}".format(index)
        try:
            with open(file,"rt") as file:
                import re
                look = re.search(r"name=(?:_\()?[\"'](.+?)[\"']\)?",file.read(250))
                if not look is None:
                    LevelLoader.name_cache[index] = name = builtins.__dict__["_"] ( look.groups()[0] )
                    print("Guess level name for {0}: {1}".format(index,name))
        except IOError:
            # LevelLoader will take care of this error, we don't bother for now
            pass
        
        return name
    
    @staticmethod
    def EnumLevelIndices():
        """Enumerate all known level numbers in no special order.
        Note that the number 0 is reserved and never assigned.
        There may be gaps within the set of assigned numbers.
        The functin yields 2-tuples: (index,ro) here ro is
        a boolean flag that specifies whether the level can
        be written to, True indicates read-only access."""
        
        import re
        reg = re.compile(r"^(\d+)\.txt$")
        dir = os.path.join(defaults.data_dir,"levels")
        for file in os.listdir(dir):
            m = re.match(reg,file)
            if m:
                yield int( m.groups()[0] ), (getattr(os.path,"is_archived",lambda x: False)(os.path.join(dir, file)))
                                
    @staticmethod
    def ClearCache(clear=None):
        """Clear all cached levels. If one of them is reloaded,
        a guarantee is made that its contents will be fetched
        from disk and not from an in-memory cache. Call this
        function after external changes occured to the level
        file. Note that the tile cache needs to be cleared
        separately by calling TileLoader.ClearCache(). You
        can limit the cache cleanup to a specific set of
        levels by specifying their numbers as first
        parameter."""
        
        if not clear:
            LevelLoader.cache = {}
            LevelLoadeer.name_cache = {}
            return
        
        for n in clear:
            p = LevelLoader.BuildLevelPath(n)
            
            try:
                del LevelLoader.cache[p]
                del LevelLoader.name_cache[n]
            except KeyError:
                pass
        return
    
    @staticmethod
    def LoadLevel(level, game, no_loadscreen=False):
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
        
        if not no_loadscreen and not defaults.no_threading:
            from loadscreen import LoadScreen
            lv = LoadScreen.Load(LevelLoader.LoadLevel,level,game,no_loadscreen=True)
            if lv:
                lv.used_loadscreen = True
            return lv
       
        file = LevelLoader.BuildLevelPath(level)
        lines = LevelLoader.cache.get(file, None)
        if lines is None:
            try:
                print("Loading level from " + file)
                with open(file, "rt", encoding='cp1252') as f:
                    lines = f.read().split("\n", 1)

                    LevelLoader.cache[file] = lines
                      
            except IOError:
                print("Could not open level file " + file + " for reading")

            except AssertionError as err:
                print("Level file " + file + " is not well-formatted:")
                traceback.print_exc()

        if lines is None or len(lines) != 2:
            return None

        replace = {
            "<out>"  : "level",
            "<raw>"  : 'r"""' + lines[1].rstrip() + ' """',
            "<game>" : "game",
            "<level>"  : "level"
        }

        l = lines[0]
        for k, v in replace.items():
            l = l.replace(k, v)
        tempdict = dict(locals())
        try:
            exec(l, globals(), tempdict)
        except:
            print("exec() fails loading level {0}, executing line: {1} ".format(file, l))
            print(traceback.format_exc())
            return None
            
        lv = tempdict.get("level", None)
        if lv and isinstance(lv,Level) and game.GetGameMode() == 3: # Game.EDITOR:
            # in editor mode, store the level's full text in the Level instance itself
            lv.editor_raw = lines[1].rstrip()
            lv.editor_shebang = lines[0]
            
        return lv

# vim: ai ts=4 sts=4 et sw=4