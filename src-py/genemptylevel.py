#!env python3
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
import sys

# Our stuff
import defaults
defaults.update_derived()



def IsYes(inp,default=True):
    return default if len(inp) == 0 else inp.lower()[:1] == "y"

def Abort():
    print("Aborting ...")
    sys.exit(-1)
    

def Main():

    def_floor = "_A0"
    width = int(input("Enter length of level: "))
    height = int(input("Enter height of level:  (max  visible: {0})".format(defaults.max_game_tiles_y)))
    name  = int(input("Enter level number: "))
    
    fname = str(name)+".txt"
    fpath = os.path.join(defaults.data_dir,"levels",fname)
    if os.path.exists(fpath):
        if not IsYes(input("File {0} exists, overwrite? y/N".format(fname)),False):
            Abort()
    
    danger      = IsYes(input("Right-pad with 'danger' barrels? Y/n"),True)
    floor       = IsYes(input("Auto-generate floor? Y/n"),True)
    floor_tile  = input("Floor tile: (default: {0})".format(def_floor)) if floor is True else ""
    stipple     = IsYes(input("Stipple space with dots? Y/n"),True)
    if not floor_tile:
        floor_tile = def_floor
    
    r,g,b = (0,0,0)
    if IsYes(input("Specify player background color Y/n"),True) is True:
        r = max(0,min(255,int(input("PlayerBG color - R: (0-255)"))))
        g = max(0,min(255,int(input("PlayerBG color - G: (0-255)"))))
        b = max(0,min(255,int(input("PlayerBG color - B: (0-255)"))))
    
    summary = """
    SUMMARY
    =============================================================
    Width:         {width}
    Height:        {height}
    
    LevelIdx:      {name}
    File:          {fpath}
    
    PadDanger:     {danger}
    AddFloor:      {floor}
    FloorTile:     {floor_tile}
    SpaceStipple:  {stipple}
    PlayerBgColor: {r} \ {g} \ {b}
    =============================================================
    
    Continue? (Y/n)
    """.format(**globals())
    
    if not IsYes(input(summary),True):
        Abort()
    
    danger_pad = 20
    with open(fpath,"wt") as outfile:
        outfile.write("<out> = Level(<level>,<game>,<raw>,color=({r},{g},{b}))\n".format(**globals()))
        for y in range(height):
    
            s = ""
            if floor is True and y == height-1:
                s += floor_tile*width
            else:
                s += (".  " if stipple is True else "   ") *width
                
            if danger is True:
                s += "rDA"*danger_pad
            
            outfile.write(s+"\n")
            
    print("Done!")

            
if __name__ == "__main__":
    Main()
    
    
