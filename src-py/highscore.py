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

class HighscoreManager:
    """Static class to keep track of the highest highscore
    the game instance has ever happened to encounter, also
    possible highscore rankings will go here."""
    
    record = 0
    file = "highscore.txt"
    
    @staticmethod
    def Initialize():
        try:
            with open(HighscoreManager.file,"rt") as r:
                HighscoreManager.record = float(r.read())
                print("Highscore record is {0}".format(HighscoreManager.record))
        except IOError:
            print("Found no highscore file, seemingly this is the first try :-)")
            HighscoreManager._Flush()
    
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
                r.write(str(HighscoreManager.record))
        except IOError:
            print("Failed to flush highscore file")
        
    
    
    
    
    