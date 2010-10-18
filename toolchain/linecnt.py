#!/usr/bin/env python3
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

import os


def line_count (file):
    i = 0
    with open(file) as f:
        for i, l in enumerate(f):
            pass
        
    return i + 1


def line_count_all(group,root,extensions=[".py",".cpp",".h",".hpp",".cxx",".c"]):
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for file in filenames:
            if not os.path.splitext(file)[-1].lower() in extensions:
                continue

            t = os.path.join(dirpath,file)
            cnt = line_count(t)
            print("{0} {1} lines".format(t,cnt))
            total += cnt
        
    print("="*60)
    print("Group {1} has {0} lines".format(total,group))
    print("="*60 + "\n")
    return total

if __name__ ==  '__main__':
    tot = 0
    
    tot += line_count_all("game-python",os.path.join("..","src-py"))
    tot += line_count_all("game-cpp",os.path.join("..","src-cpp"))
    tot += line_count_all("toolchain",".")
    tot += line_count_all("locale",os.path.join("..","locale","gen"))
    
    print("\n\nEst. total LOC: {0}".format(tot))
    input("Press any key to continue")
    
    
    
    
    
