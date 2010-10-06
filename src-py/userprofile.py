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


import defaults
import os

def SetProfile(p):
    defaults.cur_user_profile = p
    defaults.cur_user_profile_dir = os.path.join(defaults.udata_dir,defaults.cur_user_profile)
    
    try:
        os.mkdir(defaults.cur_user_profile_dir)
    except:
        pass # if already there
    
    # check if we can write to this folder
    try:
        with open(os.path.join(defaults.cur_user_profile_dir,"check.txt"),"wt") as w:
            w.write("Blubb")
    except IOError:
        print("Failure writing to {0}, check access rights".format(defaults.cur_user_profile_dir))
        raise
    
    print("Set user profile folder: {0}".format(defaults.cur_user_profile_dir))
                    

def LoadPreviousProfile():
    try:
        SetProfile(open(os.path.join(defaults.udata_dir,"current.txt"),"rt").read().strip())
    except:
        print("Failure to read previous profile, taking default profile")
        SetProfile(defaults.def_user_profile)
        
        
def SetupSelectionGUI(on_done):
    on_done()
        
        