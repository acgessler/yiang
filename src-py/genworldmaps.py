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
    (0x0,0x0,0xff)   : "bw1",    
    (0x50,0x50,0xff) : "Bw1",    
    (0x0,0xff,0x0)   : "gg1",
    (0x0,0x90,0x0)   : "dd1",
    (0x90,0x90,0x0)  : "~d1",
    (0x0,0x0,0x90)   : "bw1",
    (0x0,0x0,0x0)    : "_c0"                                   
})

large_tiles = {
    ("bw1") : { (2,2) : "bw2", (4,4) : "bw3", (6,6) : "bw0" },
    ("gg1") : { (2,2) : "gg2", (4,4) : "gg3"},
    ("dd1") : { (2,2) : "dd2", (4,4) : "dd3"},
    ("~d1") : { (2,2) : "~d2", (4,4) : "~d3"} 
}

path = os.path.join( defaults.data_dir, "levels", "30000" )
level_file = os.path.join(defaults.data_dir,"levels","30000.txt")
level_template = """<out> = Level(<level>,<game>,<raw>,color=(15,30,15),postfx=[("ingame2.sfx",())],name="Map of the World",gravity=0.0,autoscroll_speed=0.0,scroll=Level.SCROLL_ALL)
"""

def main():
    bm = Bitmap(os.path.join( path, "map.bmp" ))
    bm.output()
    
    output = ""
    cells = []
    
    w,h = bm.width,bm.height
    for y in range(h):
        cells.append([])
        for x in range(w):
            cells[-1].append(color_dict[tuple( reversed( bm.get_pixel_color(x,y) ))]) # bgr - rgb
    
    # look for optimization opportunities. Just a quick implementation,
    # I won't bother solving the packaging problem *again* ...
    for y in range(h):
        for x in range(w):
            thiscell = cells[y][x]
            d = large_tiles.get(thiscell)
            if d is None:
                continue
            
            for k,v in sorted( d.items(), key=lambda e:e[0][0]*e[0][1], reverse=True ):
                ww,hh = k
                ww = min(x+ww,w-1)-x
                hh = min(y+hh,h-1)-y
                for yy in range(hh):
                    for xx in range(ww):
                        if cells[yy+y][xx+x] != thiscell:
                            break
                    else:
                        continue
                    break
                else:
                    print("match: {0} {1} for {2}".format(k[0],k[1],cells[y][x]))
                    cells[y][x] = v 
                    for yy in range(0,hh):
                        for xx in range(0,ww):
                            if yy+xx > 0:
                                cells[y+yy][x+xx] = ".  "
                            
                    break
                
    # Merge with extra_items.txt
    with open(os.path.join(path,"extra_items.txt"),"rt") as extra:
        lines = [l.split(" ") for l in extra.read().split("\n") if len(l) > 0 and not l[0] == "#"]
        for x,y,e in lines:
            cells[int(x)][int(y)] = e
            print("place entity {0} at {1}/{2}".format(e,x,y))
    
    for row in cells:
        for cell in row:     
            output += cell
            
        output += "\n"
            
    with open(level_file,"wt") as out:
        out.write(level_template+output)
        
    print("***DONE*** wrote output file")

if __name__ == "__main__":
    main()


