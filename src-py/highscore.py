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

# Python core
import math
import random
import os

# PySFML
import sf

import defaults

fixed_monsters = 0x198aabc

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

class HighscoreManager:
    """Static class to keep track of the highest highscore
    the game instance has ever happened to encounter, also
    possible highscore rankings will go here."""
    
    record = 0
    file = None
    
    @staticmethod
    def Initialize():
        HighscoreManager.file = HighscoreManager.file or os.path.join(defaults.cur_user_profile_dir,"highscore")
        
        try:
            with open(HighscoreManager.file,"rt") as r:
                HighscoreManager.record = float(CheckIfNonEmpty( r.read())) 
                print("Highscore record is {0}".format(HighscoreManager.record))
        except:
            print("Found no highscore file, seemingly this is the first try or you cheated :-)")
            # failure to hack highscore.txt properly results in 0 :-)
            HighscoreManager._Flush()
            
    @staticmethod
    def InitializeDummy():
        """Setup a dummy implementation for use with the level editor"""
        HighscoreManager.record = 1e10
    
    @staticmethod
    def SetHighscore(score):
        """Submit new highscore, return True if this is a new record"""
        if score>HighscoreManager.record:
            print("Raise highscore record: {0}".format(score))
            HighscoreManager.record=score
            HighscoreManager._Flush()
            
            return True
        
        return False
    
    @staticmethod
    def GetHighscoreRecord():
        """Get highscore record so far"""
        return HighscoreManager.record
    
    
    @staticmethod
    def _Flush():
        try:
            with open(HighscoreManager.file,"wt") as r:
                r.write(StripInvalidCharacters(str(HighscoreManager.record)))
        except IOError:
            print("Failed to flush highscore file")
        
    
    
    
    
    