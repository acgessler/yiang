#!echo not intended for execution
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [level.py]
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

# PySFML
import sf

import time,random,os
from stubs import *

from locked import Door 
from notification import SimpleNotification
from materials import BackgroundImage,BackgroundLight
from player import Player


# quiz data kept in the source to enable automatic translation
quizes = [
    
    # quiz #0 - very beginning of the game
    [
       {
            'question':_('Which of the enemies shown below could you kill assuming you had weapon and ammo? (neither of which can be found in this room, so this question is kind of theoretical)'),
            'a': _('The red one'),
            'b': _('The green one'),
            'c': _('All of them'),
            'd': _('None of them'),
            'correct': 'a'
       },
       {
            'question':_('Which of the ASCII danger barrels below are dangerous for you?'),
            'a': _('The blue and the green one'),
            'b': _('All except the red barrel'),
            'c': _('None of them'),
            'd': _('The red and the yellow one'),
            'correct': 'b'
       },
       {
            'question':_('If you didn\'t know yet, money is the kind of item that seems to affect the number on the left of the dollar sign in the upper status bar. What can you NOT do with it?'),
            'a': _('Loose it by slaying too many ASCII zombies'),
            'b': _('Buy more lives to survive this hell of a torture chamber longer'),
            'c': _('Improve your online highscore and show off how great you are'),
            'd': _('Change your player\'s body color at will'),
            'correct': 'd'
       }
    ],
          
]


def VerifyQuizResult(quiz_result,quiz_source):
    for n,question in enumerate(quiz_source):
        if not n in quiz_result:
            return _('You didn\'t complete question {0} yet. Go back and make your choice!').format(n)
            
        if quiz_result[n]!= question['correct']:
            return _('Your response to question {0} is not correct, \nplease reconsider your choice (you chose {1})'.format(n,quiz_result[n].upper()))
        
    # all is fine -- the answers were correct
    return None


class QuizAsk(BackgroundImage):
    def __init__(self,*args,quiz_id,qid,**kwargs):
        self.qid = qid
        BackgroundImage.__init__(self, *args,halo_img='quiz_stub_questionmark_'+str(qid)+'.png',**kwargs)
    
    
class QuizAskNotification(SimpleNotification):
    def __init__(self,w,h,quiz_id,qid,**kwargs):
        q = quizes[quiz_id][qid]
        text = "{0}\nA: {1}\nB: {2}\nC: {3}\nD: {4}\n".format(q['question'],q['a'],q['b'],q['c'],q['d'])
        SimpleNotification.__init__(self,text,width=w/5,height=h/3,only_once=False,no_blur=True,**kwargs)
        

class QuizChoice(BackgroundImage):
    def __init__(self,*args,qid,letter, **kwargs):
        BackgroundImage.__init__(self, *args,halo_img='quiz_stub_'+letter+'_'+str(qid)+'.png',draworder=800,**kwargs)
        self.letter = letter
        self.qid = qid
        
    def Interact(self, who):
        if isinstance(who,Player):
            if who.level.quiz_results.get(self.qid,' ') != self.letter:
                who.level.quiz_results[self.qid] = self.letter
                    
                pos = self.pos[0]-10,self.pos[1]
                
                from player import InventoryChangeAnimStub
                self.game.AddEntity(InventoryChangeAnimStub(_('You selected option {0} for question #{1}').format(self.letter.upper(),self.qid),
                    pos,
                    color=sf.Color(240,120,0)))
                
                assert hasattr(self,'light')
                
                if self.qid in who.level.quiz_lamp:
                    who.level.quiz_lamp[self.qid].SetColor(sf.Color(0,0,0,0))
                
                who.level.quiz_lamp[self.qid] = self.light
                r0,r1 = random.randint(0,0xff),random.randint(0,0xff)
                self.light.SetColor(sf.Color(r0,r1,max(random.randint(0,0x45),0xff-(r0+r1)),0xb5))
                
        
        return BackgroundImage.Interact(self,who)
    
    def Update(self,time,dtime):
        BackgroundImage.Update(self,time,dtime)
        if not hasattr(self,'light'):
            self.light = self.level.FindClosestOf(self.pos,BackgroundLight,True)
            self.light.SetColor(sf.Color(0,0,0,0))
            self.light.pulse = False
    
    def Draw(self):
        return BackgroundImage.Draw(self)
        
        
class QuizLevel(Level):
        
        def __init__(self,*args,quiz_id=0,**kwargs):
            Level.__init__(self,*args,**kwargs)
            self.quiz_results = {}
            self.quiz_id = quiz_id
            self.quiz_source = quizes[quiz_id]
            self.quiz_lamp = {}
            
class QuizDoor(Door):
   
    def __init__(self, *args, **kwargs):
        Door.__init__(self, *args, **kwargs)
        self.time = sf.Clock()

    def Interact(self, other):
        if isinstance(other,Player) and self.unlocked is False and not hasattr( self, "during_interact" ) and self.time.GetElapsedTime()>0.5:
            inv = other.EnumInventoryItems()
            
            from player import InventoryChangeAnimStub
            
            pos = self.pos[0]-10,self.pos[1]
            
            result = VerifyQuizResult(self.level.quiz_results,self.level.quiz_source)
            if isinstance(result,str):
                self.game.AddEntity(InventoryChangeAnimStub(_('You failed the quiz, dude: {0}').format(result),
                        pos,
                        color=sf.Color.Red))
            else:
                self.game.AddEntity(InventoryChangeAnimStub(_('You completed the quiz successfully!'),
                        pos,
                        color=sf.Color.Green))
                self.Unlock()
        
        self.time = sf.Clock()
        return Entity.ENTER if self.unlocked else Entity.BLOCK
            
            
            
            
            