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
import collections

# Our stuff
import defaults
defaults.update_derived()

from bitmaploader import Bitmap

color_dict = collections.defaultdict(lambda : ".  ", {
    (0x0,0x0,0xff)   : "bg1",    
    (0x0,0xff,0x0)   : "gg1",
    (0x0,0x90,0x0)   : "dg1",
    (0x0,0x0,0x0)    : "_c0"                                   
})

path = os.path.join( defaults.data_dir, "levels", "30000" )
level_file = os.path.join(defaults.data_dir,"levels","30000.txt")
level_template = """<out> = Level(<level>,<game>,<raw>,color=(15,30,15),postfx=[("ingame2.sfx",())],name="Map of the World",gravity=0.0,autoscroll_speed=0.0,scroll=Level.SCROLL_ALL)
"""

def main():
    bm = Bitmap(os.path.join( path, "map.bmp" ))
    bm.output()
    
    output = ""
    
    w,h = bm.width,bm.height
    for y in range(h):
        for x in range(w):
            output += color_dict[tuple( reversed( bm.get_pixel_color(x,y) ))] # bgr - rgb
        output += "\n"
            
    with open(level_file,"wt") as out:
        out.write(level_template+output)

if __name__ == "__main__":
    main()


