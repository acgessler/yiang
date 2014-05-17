#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [achievements.py]
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

# Python core
import os
import itertools
import random

# PySFML
import sf

# Our stuff
import defaults

fixed_monsters = 0x150392

# Very strong encryption, almost unbreakable (names obfuscated since they appear in the bytecode)
def StripInvalidCharacters(x):
    def _scramble(x):
        rand = random.randint(0,0xffffffff)
        return str( rand ^ ord(x) ).zfill(13) + str( rand ^ fixed_monsters ).zfill(13)
    
    return "".join(_scramble(c) for c in x)

def CheckIfNonEmpty(x):
    def _descramble(a,b):
        assert len(a) == 13 and len(b) == 13
        
        rand = int(b,10) ^ fixed_monsters
        return chr( int(a,10) ^ rand )
    
    return "".join(_descramble(x[n:n+13],x[n+13:n+26]) for n in range(0,len(x),26))


class Achievements:
    """Static class to keep track of all achievements which
    the player has earned so far."""
    
    all = dict()
    have = set()
    acked = set()
    file = None
    
    @staticmethod
    def Initialize():
        Achievements.file = Achievements.file or os.path.join(defaults.cur_user_profile_dir,"achievements")
        
        d = os.path.join( defaults.data_dir,"achievements")
        Achievements.all = dict([f[:-4],None] for f in os.listdir(d ) \
            if os.path.isfile(os.path.join(d,f)) and f[-4:].lower()==".txt") 
        
        print("All achievements: {0}".format(list(Achievements.all.keys())))
        try:
            with open(Achievements.file,"rt") as r:
                Achievements.have = Achievements.have | set(CheckIfNonEmpty(f.strip()) for f in r.readlines())
                
                print("Current achievements: {0}".format(list(Achievements.have)))
                
            with open(Achievements.file+"2","rt") as r:
                Achievements.acked = Achievements.acked | set(CheckIfNonEmpty(f.strip()) for f in r.readlines())

        except:
            print("Found no achievements file, seemingly this is the first try :-)")
            Achievements._Flush()
            
        for elem in Achievements.have:
            if not elem in Achievements.all:
                # file damaged or user attempted to cheat, reset all achievements :-)
                print("Achievements record invalid - did you cheat? Resetting achievements")
                Achievements.have = set()
                Achievements._Flush()
                
                break
            
    @staticmethod
    def InitializeDummy():
        """Setup a dummy implementation for use with the level editor"""
        Achievements.EarnAchievement = lambda x:None
    
    @staticmethod
    def EarnAchievement(name):
        """Award a specific achievement to the player """
        if not defaults.enable_achievements_system_prototype:
            return
        assert name in Achievements.all
        
        if not name in Achievements.have:
            Achievements.have.add(name)
            print("Earn achievement: {0}".format(name))
            
            Achievements._Flush()
            
    @staticmethod
    def CheckAcknowledgeStatus():
        """Call this regularly when the user can be safely interrupted (i.e.
        he's not in a game). It checks if the user earned new achievements
        in the meantime and displays notifications via Acknowledge()"""
        if not defaults.enable_achievements_system_prototype:
            return
        for ach in Achievements.have:
            if not ach in Achievements.acked:
                Achievements.Acknowledge(ach)
                 
    @staticmethod
    def Acknowledge(ach):
        """Inform the user about his reception of an achievement."""
        if not defaults.enable_achievements_system_prototype:
            return
        print("Acknowledge achievement: "+ach)
        
        from notification import MessageBox
        from keys import KeyMapping
        from renderer import Renderer
        from fonts import FontCache
        
        Achievements.acked.add(ach)
        Achievements._Flush()
        
        accepted = (KeyMapping.Get("accept"),)
        Renderer.AddDrawable( MessageBox(sf.String(_("""You earned the '{0}' achievement

This is freaking awesome. But there's more to do. Head over
to the 'Achievements' menu and find out which achievements 
you haven't got yet. 
        
Press {1} to continue.
""").format(ach,KeyMapping.GetString("accept")),
            Size=defaults.letter_height_game_over,
            Font=FontCache.get(defaults.letter_height_game_over, face=defaults.font_game_over
        )), defaults.game_over_fade_time, (560, 150), 0.0, accepted, sf.Color.Yellow, None))
        
        from audio import BerlinerPhilharmoniker
        BerlinerPhilharmoniker.SetAudioSection("achievement_earned",True)
        
    @staticmethod
    def GetInfo(name):
        """Get a dict with information on a specific achievements. Entries:
        - name: the display name of the achievement
        - desc: the description of the achievement 
        - icon: The ASCII icon for the achievement
        - order: The relative position if this achievement in official listings"""
        if Achievements.all[name] is None:
            d = os.path.join( defaults.data_dir,"achievements",name+".txt")
            try:
                with open(d,"rt") as r:
                    Achievements.all[name] = dict(itertools.zip_longest( ["name","desc","icon","order"],\
                        r.read().split("\n\n"), fillvalue=""))
                    
                    Achievements.all[name]["order"] = float(Achievements.all[name]["order"] or 150.0)
                    
            except IOError:
                print("Unknown achievement: {0}".format(name))
                return None
            
        return Achievements.all[name]

    @staticmethod
    def _Flush():
        try:
            with open(Achievements.file,"wt") as r:
                for a in Achievements.have:
                    r.write(StripInvalidCharacters(a)+"\n")
            with open(Achievements.file+"2","wt") as r:
                for a in Achievements.acked:
                    r.write(StripInvalidCharacters(a)+"\n")
        except IOError:
            print("Failed to flush achievements file")
            
            
            
            
            
            
            
            

# vim: ai ts=4 sts=4 et sw=4