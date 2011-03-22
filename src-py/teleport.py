#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [teleport.py]
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


from stubs import *
from player import Player
from posteffect import FadeInOverlay,FadeOutOverlay
from enemy import SmallTraverser

# Python stuff
import operator


class Sender(AnimTile):
    """The sender teleport brick transports the player to the
    closest receiver brick with the same color"""

    def __init__(self,text,height=3,frames=5,speed=4.0):
        AnimTile.__init__(self,text,height,frames,speed)

    def Interact(self,other):
        if isinstance(other, Player) or isinstance(other, SmallTraverser):
            lv = self.game.GetLevel()
            assert not lv is None
            
            mypos = self.pos
            
            target = self.level.FindClosestOfSameColor(self.pos,Receiver,self.color)
            if not target:
                print("Failed to find teleport target, my color is {0}".format(self.color))
                
            else:
                if isinstance(other, Player):
                    self.TeleportPlayer(target,other)
                else:
                    self.TeleportSmallTraverser(target,other)
                
                # don't know why this was once needed - it just
                # causes unneeded flickering.
                #raise NewFrame()
        
        return Entity.ENTER
    
    def TeleportSmallTraverser(self,target,st):
        """Teleport 'st' to 'target', which must be a Receiver brick"""
        assert isinstance(target,Receiver)
        assert isinstance(st,SmallTraverser)
        
        print("Teleport SmallTraverser to {0} at position {1}".format(target,target.pos))
        target.OnDoTeleportSmallTraverser(self,st)
        
    
    def TeleportPlayer(self,target,player):
        """Teleport 'player' to 'target', which must be a Receiver brick"""
        assert isinstance(target,Receiver)
        assert isinstance(player,Player)
        
        # Don't fade out entirely if the target of the teleport
        # is within the current view.
        fade_time, fade_end = (0.7, 0.75) if self.game.GetLevel().IsVisible( target.pos ) else (1.0, 0.0)
        
        def fadeback(x):
            
            def unsuspender(x):
                Renderer.RemoveDrawable(x)
                #self.game.PopSuspend()
            
            Renderer.RemoveDrawable(x)
            Renderer.AddDrawable(FadeInOverlay(fade_time=fade_time*0.4,
                fade_start=fade_end,on_close=unsuspender))
            self.game.PopSuspend()
            
            print("Teleport Player to {0} at position {1}".format(target,target.pos))
            target.OnDoTeleport(self,player)
            player.Protect(defaults.teleport_protection_time)
            
        self.game.PushSuspend()
        Renderer.AddDrawable(FadeOutOverlay(fade_time=fade_time,fade_end=fade_end,on_close=fadeback))
                              
        

    def GetVerboseName(self):
        return _("a sender teleport brick")
    
    
class Receiver(AnimTile):
    """The receiver teleport brick acts as target for teleports"""
    
    def __init__(self,text,height=3,frames=5,speed=4.0):
        AnimTile.__init__(self,text,height,frames,speed)
        
    def Interact(self,other):
        return Entity.ENTER
    
    def OnDoTeleport(self,source,player):
        player.SetPositionAndMoveView(self.pos,defaults.teleport_origin_distance)
        
    def OnDoTeleportSmallTraverser(self,source,st):
        st.SetPosition(self.pos)

    def GetVerboseName(self):
        return _("a receiver teleport brick")
    
    
class ReceiverRotateRight(Receiver):
    """This receiver rotates the incoming velocity vector
    of the player by 90 degrees to the right"""
    
    def __init__(self,text,height=3,frames=5,speed=4.0):
        Receiver.__init__(self, text, height, frames, speed)
    
    def OnDoTeleport(self,source,player):
        Receiver.OnDoTeleport(self,source,player)

        velabs = (player.vel[0]**2+player.vel[1]**2)**0.5
        player.vel = [velabs*1.5,0]
        
    def OnDoTeleportSmallTraverser(self,source,st):
        st.SetPosition(self.pos)
        
        if st.direction == Entity.DIR_HOR:
            st.vel = abs(st.vel)
            
        else:
            st.vel = -st.vel
        
        st.direction = 1-st.direction

    def GetVerboseName(self):
        return _("a receiver right-rotating teleport brick")
    
    
class ReceiverRotateLeft(Receiver):
    """This receiver rotates the incoming velocity vector
    of the player by 90 degrees to the left"""
    
    def __init__(self,text,height=3,frames=5,speed=4.0):
        Receiver.__init__(self, text, height, frames, speed)
    
    def OnDoTeleport(self,source,player):
        Receiver.OnDoTeleport(self,source,player)
        velabs = (player.vel[0]**2+player.vel[1]**2)**0.5
        player.vel = [-velabs*1.5,0]
        
    def OnDoTeleportSmallTraverser(self,source,st):
        st.SetPosition(self.pos)
        
        if st.direction == Entity.DIR_VER:
            st.vel = abs(st.vel)
            
        else:
            st.vel = -st.vel
        
        st.direction = 1-st.direction

    def GetVerboseName(self):
        return _("a receiver left-rotating teleport brick")
    
    
    
    
    
    
    
    
    
    

# vim: ai ts=4 sts=4 et sw=4
