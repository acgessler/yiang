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

# Python Core
import os
import itertools

# Our stuff
import defaults
defaults.update_derived()

def partition(seq,num):
    """Partition a given sequence in tuples of size 'num'"""
    assert len(seq)%num == 0
    
    for n in range(len(seq)//num):
        yield seq[n*num:(n+1)*num]
        

def validate_level(lines,idx):
    """Validate a level in its ASCII representation, given a list of lines.
    If an error or a warning is issued, write it to stdout and return
    False if the level does not pass the validation"""
    if len(lines) <= 1:
        print("Level {0}, ERROR: The file has only {1} line, 2 are required".format(idx,len(lines)))
        return False
        
    del lines[0]

    if len(lines)-1>defaults.tiles[1]:
        print("Level {0}, WARN: Level is probably too height - {1} tiles, but maximum visible is {2}".format(
            idx,len(lines),defaults.tiles[1]))

    player,final = False,False
    for n,line in enumerate(lines):
        line = line.rstrip(" \n\t.")
        if not len(line):
            continue
        if len(line)%3 != 0:
            print("Level {0}, ERROR: Line {1} is {2} characters (not divisible by 3)".format(
                idx,n,len(line)))
            return False
            
        for a,b,c in partition(line,3):
            d = b+c
            if b == "." or c == ".":
                print("Level {0}, WARN: '.' in line {1} not aligned to grid (3x1 characters)".format(
                    idx,n))

            if d=="PL":
                player = True
            elif d=="FI":
                final = True

    if player is False:
        print("Level {0}, ERROR: Missing player (*PL) entity".format(idx))
        return False

    if final is False:
        print("Level {0}, ERROR: Missing levelup (*FI) entity".format(idx))
        return False

    print("Level {0}, INFO: validation successful, no problems detected".format(idx))
    return True


def validate_all():
    """Run validation over all levels in data/levels"""

    for level_count in itertools.count(1):
        f = os.path.join(defaults.data_dir,"levels","{0}.txt".format(level_count))
        if not os.path.exists(f):
            break

        try:
            with open(f,"rt") as file:
                validate_level(file.readlines(),level_count)
                                
        except IOError:
            print("Failure opening {0}".format(file))

if __name__ == "__main__":
    validate_all()
    input("Press any key to continue ...")
    
