#!/usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# MGL Framework Python Scripting Interface (v0.1)
# [filebot.py]
# (c) Alexander Gessler, 2010
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
import shutil
import traceback

# Target directory to cpy all the files to.
target = os.path.join("..","final","root")


def copy_files(files):
    for file in files:
        dst = os.path.join( target, file.replace("..\\","") )
        try:
            os.makedirs(os.path.split(dst)[0])
        except OSError:
            pass # exists already
        try:
            shutil.copy(file, dst)
            print("Copy {0} to {1}".format(file,dst))
        except:
            print("Failure copying {0} to {1}".format(file,dst))
            #traceback.print_exc()


def archive_files(files):
    from archiver import Writer
    
    af = os.path.join(target,"cooked.dat")
    with Writer(af) as archive:
        for file in files:
            try:
                archive.AddFile(file)
            except:
                print("Failure adding {0} to archive {1}".format(file,af))
                #traceback.print_exc()
        af.Finalize()


def main(caches):
    
    if "files" in caches:
        copy_files(caches["files"])
        
    if "archive_files" in caches:
        archive_files(caches["archive_files"])
         


