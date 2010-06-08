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

# PySFML
import sf

class KeyMapping:
    """Implements a configurable key mapping"""

    mapping = {
        "move-left"     : sf.Key.Left,
        "move-right"    : sf.Key.Right,
        "move-up"       : sf.Key.Up,
        "move-down"     : sf.Key.Down,
        "move-left"     : sf.Key.Left,
        "menu-up"       : sf.Key.Up,
        "menu-down"     : sf.Key.Down,
        "menu-left"     : sf.Key.Left,
        "menu-right"    : sf.Key.Right,
        "debug-godmode" : sf.Key.X,
        "debug-showbb"  : sf.Key.B,
        "debug-showinfo": sf.Key.D,
        "debug-allowup" : sf.Key.G,
        "level-new"     : sf.Key.N,
        "debug-kill"    : sf.Key.K,
        "debug-gameover": sf.Key.Q,
        "escape"        : sf.Key.Escape,
        "accept"        : sf.Key.Return
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
                        #print("'{0}'".format(k),sf.Key.__dict__[v])
                        attr = sf.Key.__dict__[v] #eval("sf.Key.{0}".format(v)) 
                    except AttributeError:
                        print("{0}:{1}: Key value {2} is not known".format(file,n,v))
                        continue

                    cls.mapping[k] = attr
                    #print(attr,cls.mapping[k],id(attr),id(cls.mapping[k]))
                    print("{0}:{1}: Remap {2} action to {3} key".format(file,n,k,v))
                    
        except IOError:
            print("Failure reading key bindings from {0}".format(file))
        #print(cls.mapping)

    @classmethod
    def Get(cls,name):
        """Query the SFML key constant for a specific action"""
        return cls.mapping[name]

    
                

