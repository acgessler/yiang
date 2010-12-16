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
sys.path.append(os.path.join("..","src-py"))

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
    
    (0xff,0xcd,0x0)   : "og1",
    (0xff,0x90,0x0)   : "Pd1", 
    
    (0x0,0x0,0x0)   : "gg1", ## city locations  
})

large_tiles = {
    ("bw1") : { (2,2) : "bw2", (4,4) : "bw3", (6,6) : "bw0" },
    ("gg1") : { (2,2) : "gg2", (4,4) : "gg3", (2,1) : "gg4", (1,2) : "gg5"},
    ("dd1") : { (2,2) : "dd2", (4,4) : "dd3", (2,1) : "dd4", (1,2) : "dd5"},
    ("og1") : { (2,2) : "og2", (4,4) : "og3", (2,1) : "og4", (1,2) : "og5"},
    ("Pd1") : { (2,2) : "Pd2", (4,4) : "Pd3", (2,1) : "Pd4", (1,2) : "Pd5"},
    ("~d1") : { (2,2) : "~d2", (4,4) : "~d3"} 
}


def main():
    for level in (30000,30001,30002,30003):
        try:
            process_map(level)
        except IOError:
            print("Failure processing level {0}, IOError occured".format(level))
            
    
def process_map(level):
    path = os.path.join( defaults.data_dir, "levels", str(level) )
    level_file = os.path.join(defaults.data_dir,"levels",str(level)+".txt")
    level_template = open(os.path.join(path, "shebang_template.txt"),"rt").read()
    
    bm = Bitmap(os.path.join( path, "map.bmp" ))
    bm.output()
    
    output = ""
    cells, orig, overlap = [],[],[]
    
    # dump all city locations to a separate text file
    citypos = open(os.path.join(path,"city_pos_dump.txt"),"wt")
    
    w,h = bm.width,bm.height
    for y in range(h):
        cells.append([])
        orig.append([])
        overlap.append([1]*w)
        for x in range(w):
            col = tuple( reversed( bm.get_pixel_color(x,y) ))
            cells[-1].append(color_dict[col]) # bgr - rgb
            orig[-1].append(cells[-1][-1])
            
            if col == (0,0,0):
                citypos.write("{0} {1} \n".format(x,y))
                
    citypos.close()
                 
    
    # look for optimization opportunities. Just a quick implementation,
    # I won't bother solving the packaging problem *again* ...
    for y in range(h):
        for x in range(w):
            thiscell = cells[y][x]
            d = large_tiles.get(thiscell)
            if d is None:
                continue
            
            def area(x,y):
                return x*y
            
            for k,v in sorted( d.items(), key=lambda e:e[0][0]*e[0][1], reverse=True ):
                ww,hh = k
                ww = min(x+ww,w-1)-x
                hh = min(y+hh,h-1)-y
                for yy in range(hh):
                    for xx in range(ww):
                        if cells[yy+y][xx+x] != thiscell:
                            if area(*k)>4:
                                """
                                # hack: split 2x1 and 1x2 tiles into pieces if this
                                # helps us place a larger one
                                if cells[yy+y][xx+x] == ".  ":
                                    yyy,xxx = yy+y,xx+x
                                    xmax,ymax = 0,0
                                    while yyy > 0:
                                        yyy -= 1
                                        xxxx = xxx-1 if yyy==yy+y else xxx
                                        while cells[yyy][xxxx]  == ".  ":
                                            xxxx -= 1
                                            if xxxx == 0:
                                                break
                                        else:
                                            # yyy,xxxx is the piece to be split
                                            break
                                            
                                    for k,v in sorted( d.items() ):
                                        if v[0] == cells[yyy][xxxx][0]:
                                            break
                                    else:
                                        break
                                    
                                    continue
                                """
                                if orig[yy+y][xx+x][0] == v[0] and overlap[yy+y][xx+x] == 1 and \
                                    area(*[k for k,v in d.items() if orig[yy+y][xx+x]==v][0]) <= 4:
                                    
                                    overlap[yy+y][xx+x] += 1
                                    continue
                                    
                            break
                    else:
                        continue
                    break
                else:
                    print("match: {0} {1} for {2} at {3}\{4}".format(k[0],k[1],cells[y][x],x,y))
                    cells[y][x] = v 
                    for yy in range(0,hh):
                        for xx in range(0,ww):
                            if yy+xx > 0:
                                cells[y+yy][x+xx] = ".  "
                                orig[y+yy][x+xx] = v 
                            
                    break
    
    cnt = 0
    for row in cells:
        for cell in row:     
            if cell != ".  ":
                cnt += 1
            output += cell
            
        output += "\n"
            
    with open(level_file,"wt") as out:
        out.write(level_template+output)
        
        
    # process extra_items.txt
    # this task is now done by CampaignLevel at runtime! 
    
    # with open(os.path.join(path,"extra_items.txt"),"rt") as extra:
    #    lines = [l.split(" ") for l in extra.read().split("\n") if len(l) > 0 and not l[0] == "#"]
    #    for x,y,e in lines:
    #        cells[int(y)][int(x)] = e[:3]
    #        print("place entity {0} at {1}/{2}".format(e,x,y))
        
    print("***DONE*** level {0}, wrote output file, {1} tiles".format(level,cnt))

if __name__ == "__main__":
    main()


