#!/bin/env python3

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [compilelevels.py]
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
import os, sys


input_folder = os.path.join('..','data','levels')
output_folder = os.path.join('..','data','levels','optimized')

tile_input_folder = os.path.join('..','data','tiles')
tile_output_folder = os.path.join('..','data','tiles','optimized')

# largest cluster size to look for
max_cluster = [10,10]

# minimum number a specific cluster must occur to be considered
min_occurences = 1

# exclude some levels (i.e. world maps), they have custom logic for tile optimization
exclude_levels = [(lambda n:30000<=n<40000)]

# tile classes that don't appear here are never considered for clustering
allowed_classes = ['Tile']


def include_level(index):
    return not any(ex(index) for ex in exclude_levels)

def partition(seq,length):
    for n in range(len(seq)//length):
        yield seq[n*length:(n+1)*length]
        
def arrowsplit(input,splitset):
    res = [input]
    for n in splitset:
        newres = []
        for elem in res:
            newres += elem.split(n) 
        res = newres
    return res
        
def include_tile(name):
    return not not name.strip() and any(c in allowed_classes for c in arrowsplit(tiles.get(name,[''])[0],' (='))

def clear_folder(folder):
    for the_file in os.listdir(folder):
        if the_file == 'dummy.txt':
            continue
        
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
            
clear_folder(tile_output_folder)
clear_folder(output_folder)

# load all tiles upfront
tiles = {}
for tile in os.listdir(os.path.join(tile_input_folder)):
    if os.path.splitext(tile)[1] == '.txt':
        with open(os.path.join(tile_input_folder,tile),'rt') as ip:
            tiles[tile[:2]] = ip.read().split('\n',1)
        
 
level_clusters = {}
level_maps = {}
level_shebangs = {}
cluster_count = {}

tilecnt = 0
    
for fname in os.listdir(input_folder):
    name,ext = os.path.splitext(fname)
    if ext != '.txt':
        continue
    
    try:
        idx = int(name)
    except TypeError:
        continue
    
    if not include_level(idx):
        continue
        
    fullp = os.path.join(input_folder,fname)
    with open(fullp, 'rt') as lfile:
        lines = lfile.read().split('\n')
        if len(lines) < 2:
            continue
        
        level_shebangs[idx] = lines[0]
        lines = lines[1:]
        print('** process level {0}'.format(idx))
        
        # skip empty lines at the end of the files - who knows which tool added them for whatever reason ...
        for n,l in reversed(list(enumerate(lines))):
            if not l.strip('. \r'):
                lines = lines[:n]
            else:
                break
            
        if not lines:
            continue
            
        # gather a grid indexable by x,y tuples containing either None or
        # the name of a tile for each cell. Any tiles present in the grid
        # are later considered for clustering
        lmap,lorigmap = [],[]
        maxlen = max(len(line)//3 for line in lines)
        for n in range(len(lines)+max_cluster[1]):
            lmap.append([None]*(maxlen + max_cluster[0]))
            if n < len(lines)+1: # one extra line even here
                lorigmap.append([None]*(maxlen))
        
        for y,line in enumerate(lines):
            for x,triple in enumerate(partition(line,3)):
                color,tile = triple[0],triple[1:3]
                
                lorigmap[y][x] = color,tile
                if not include_tile(tile):
                    continue
                
                lmap[y][x] = tile
                
        level_maps[idx] = lmap,lorigmap
        
        clusters = level_clusters[idx] = {}
        for y,line in enumerate(lmap):
            for x,tile in enumerate(line):
                
                if tile is None:
                    continue
                
                tilecnt += 1
                
                min_x = [max_cluster[0]+1]*max_cluster[1]
                for yy in range(max_cluster[1]):
                    yyy = yy+y
                    for xx in range(max_cluster[0]):
                        xxx = xx+x
                        
                        if lmap[yyy][xxx] != tile:
                            break
                    else:
                        xx += 1
                    min_x[yy] = min(xx,*min_x)
                    
                # make a good guess based on the cluster area
                cx,cy = sorted(((x,y+1) for y,x in enumerate(min_x)),key=lambda x:x[0]*x[1])[-1]
                if cx*cy <= 1:
                    continue
                
                clusters[(x,y)] = (tile,cx,cy)
                cluster_count[(tile,cx,cy)] = cluster_count.setdefault((tile,cx,cy),0)+1
                
                for yy in range(cy):
                    for xx in range(cx):
                        if xx>0 or yy>0:
                            lmap[yy+y][xx+x] = None
                
cluster_count = dict((k,v) for k,v in cluster_count.items() if v > min_occurences)
print('*DONE collecting possible clusters, considered {0} tiles and got {1} suitable clusters'.format(tilecnt,len(cluster_count)))
#for k,v in cluster_count.items():
#    print(k,v)
    
import random
def unique_rand_3(history=set()): # *not* suited for too many attempts ;-)
    table = 'ABCDEFGHIJKLMNOPQRSTUVQXYZ0123456789'
    while 1:
        r = random.choice(table)+random.choice(table)+random.choice(table)
        if not r in history:
            history.add(r)
            return r
           
# for all clusters, locate the corresponding tile files and generate cluster tiles for them
cluster_tile_names = {}
for tile,cx,cy in cluster_count:
    assert cx>1 or cy>1
    shebang,contents = tiles[tile]

    newname = ('##' if cx>1 else '$$')+unique_rand_3() 
    cluster_tile_names[(tile,cx,cy)] = newname
                       
    with open(os.path.join(tile_output_folder,newname+'.txt'),'wt') as op:
        op.write(shebang+'\n')
        lines = [c.rstrip() for c in contents.split('\n')]
        for n,l in reversed(list(enumerate(lines))):
            if not l.strip():
                lines = lines[:n]
            
        if not lines:
            continue
            
        justlen = max(len(l) for l in lines)
        lines_new = '\n'.join( (c.ljust(justlen))*cx for c in lines)
        fulltile = (lines_new+('\n' if lines_new[-1] != '\n' else ''))
        
        # for tiles which start with ____, drop one line to make them look like a continuous row
        if all(c in ('_ ') for c in lines[0]):
            fulltile += '\n'.join(fulltile.split('\n')[1:])*(cy-1)
        else:
            fulltile = fulltile*cy
        
        op.write(fulltile)
    
print('*DONE writing cluster tiles')

# for all levels, spit out optimized versions
for index,map in level_maps.items():
    newmap,origmap = map
    cluster = level_clusters[index]
    
    with open(os.path.join(output_folder,'{0}.txt'.format(index)),'wt') as op:
        op.write(level_shebangs[index]+'\n')
        
        for y,origline in enumerate(origmap):
            for x,orig in enumerate(origline):
                if orig is None:
                    op.write('.  ')
                    continue
                    
                color,tile = orig
                
                if (x,y) in cluster:
                    oldtile,cx,cy = cluster[(x,y)]
                    
                    try:
                        newname = cluster_tile_names[( oldtile,cx,cy)]
                        for yy in range(cy):
                            for xx in range(cx):
                                try:
                                    if xx>0 or yy>0:
                                        origmap[yy+y][xx+x] = '.','  '
                                except IndexError:
                                    pass
                        
                        if newname[:2]=='##':
                            origline[x+1]=newname[2],newname[3:]
                        elif newname[:2]=='$$':
                            origmap[y+1][x]=newname[2],newname[3:]
                            
                        tile = newname[:2]
                    
                    except KeyError:
                        pass # this happens if the cluster failed the min occurences test
                                    
                op.write(color)
                op.write(tile)
            op.write('\n')
                
print('*DONE writing optimized levels')    
    
    
    
    
    
