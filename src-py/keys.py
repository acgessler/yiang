#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [keys.py]
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

# PySFML
import sf

class KeyMapping:
    """Implements a configurable key mapping"""

    mapping = {
        "move-left"     : "Left",
        "move-right"    : "Right",
        "move-up"       : "Up",
        "move-down"     : "Down",
        "move-left"     : "Left",
        "menu-up"       : "Up",
        "menu-down"     : "Down",
        "menu-left"     : "Left",
        "menu-right"    : "Right",
        "debug-godmode" : "X",
        "debug-godmode-addlive" : "O",
        "debug-godmode-addscore" : "I",
        "debug-showbb"  : "B",
        "debug-showinfo": "D",
        "debug-allowup" : "G",
        "level-new"     : "N",
        "debug-kill"    : "K",
        "debug-gameover": "Q",
        "escape"        : "Escape",
        "accept"        : "Return",
        "interact"      : "Return",
        "shoot"         : "LControl",
        "yes"           : "Y",
        "no"            : "N",
    }

    @classmethod
    def LoadFromFile(cls,file):
        """Load a set of key bindings from a particular file"""
        print("Loading key bindings from {0}".format(file))

        try:
            with open(file,"rt") as f:
                for n,line in enumerate(f):
                    if not len(line.strip()) or line[0]=="#":
                        continue
                    
                    try:
                        k,v = line.split("=")
                    except:
                        print("{0}: failure processing line {1}: {2}".format(file,n,line))
                        continue

                    k = k.strip()
                    v = v.strip()
                    if not k in cls.mapping:
                        print("{0}:{1}: Key name {2} is not known".format(file,n,k))
                        continue

                    try:
                        sf.Key.__dict__[v] 
                    except AttributeError:
                        print("{0}:{1}: Key value {2} is not known".format(file,n,v))
                        continue

                    cls.mapping[k] = v
                    #print(attr",cls.mapping[k]",id(attr)",id(cls.mapping[k]))
                    print("{0}:{1}: Remap {2} action to {3} key".format(file,n,k,v))
                    
        except IOError:
            print("Failure reading key bindings from {0}".format(file))
        #print(cls.mapping)

    @classmethod
    def Get(cls,name):
        """Query the SFML key constant for a specific action"""
        return getattr( sf.Key, cls.mapping[name])

    @classmethod
    def GetString(cls,name):
        """Query the string key name specific action"""
        return cls.mapping[name] 

    
                

# vim: ai ts=4 sts=4 et sw=4