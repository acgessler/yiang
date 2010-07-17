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
import os
import itertools

# PySFML
import sf

# Our stuff
import defaults

class Achievements:
    """Static class to keep track of all achievements which
    the player has earned so far."""
    
    all = dict()
    have = set()
    file = "achievements.txt"
    
    @staticmethod
    def Initialize():
        d = os.path.join( defaults.data_dir,"achievements")
        Achievements.all = dict([f[:-4],None] for f in os.listdir(d ) \
            if os.path.isfile(os.path.join(d,f)) and f[-4:].lower()==".txt") 
        
        try:
            with open(Achievements.file,"rt") as r:
                Achievements.have = Achievements.have | set(f.strip() for f in r.readlines())
                
                print("Current achievements: {0}".format(list(Achievements.have)))
                print("Known achievements: {0}".format(list(Achievements.all.keys())))
        except IOError:
            print("Found no achievements file, seemingly this is the first try :-)")
            Achievements._Flush()
    
    @staticmethod
    def EarnAchievement(name):
        """Award a specific achievement to the player """
        assert name in Achievements.all
        Achievements.have.add(name)
        
        print("Earn achievement: {0}".format(name))
        
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
                print("No information available for achievement {0}".format(name))
                return {name:"Unnamed achievement",desc:"Hey, fix this!"}
            
        return Achievements.all[name]

    @staticmethod
    def _Flush():
        try:
            with open(Achievements.file,"wt") as r:
                for a in Achievements.have:
                    r.write(a+"\n")
        except IOError:
            print("Failed to flush achievements file")
            
            
            
            
            
            
            
            