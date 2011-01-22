#! /usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# YIANG (v2.0)
# [cpptools.py]
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

import os
import re
import itertools

class CppError(Exception):
    """Custom exception type used by the utilities in this module"""
    
    def __init__(self,msg):
        Exception.__init__(self)
        self.msg = msg
        
    def __str__(self):
        return "CppError - "+self.msg
        

class Preprocessor:
    """Minimal cpp re-implementation"""
    
    include_re = re.compile(r'include\s*(\<|\")([a-zA-Z0-9_.]+)(\>|\")',re.DOTALL)
    define_re = re.compile(r'define\s+(\w+)\s*(\w+)',re.DOTALL)
    ifdef_re = re.compile(r'ifdef\s+(\w+)',re.DOTALL)
    ifndef_re = re.compile(r'ifndef\s+(\w+)',re.DOTALL)
    endif_re = re.compile(r'endif',re.DOTALL)
    else_re = re.compile(r'else',re.DOTALL)
    elif_re = re.compile(r'elif\s+(.*)',re.DOTALL)
    if_re = re.compile(r'if\s+(.*)',re.DOTALL)
    undef_re = re.compile(r'undef\s+(.*)',re.DOTALL)
    error_re = re.compile(r'error\s+(.*)',re.DOTALL)
    
    @staticmethod
    def Preprocess(lines,env,dirs=[os.getcwd()]):
        """Preprocess a text file according to the 'usual' behaviour of
        cpp, the C preprocessor.
        
        Parameters:
          lines -- Lines of the input files. This can also be the path to an input file.
          env -- List of macro definitions. Each entry can be either
             a single value (#define <value>), a 2-tuple (name,value)
             or a single statement containing an 'equal' character, 
             such as "name=value".
          dir -- Search directories for include files
          
         Throws:
           CppError -- if something goes wrong.
           
         Returns:
           Preprocessed list of lines.
        """
        env2 = []
        # idea: accept virtually everything.
        for e in env:
            if not isinstance(e,tuple):
                e = e.split("=")
                if len(e)!=2:
                    e = (e,"")
                
            env2.append(e if len(e)==2 else (e[0],""))
        env = dict(env2)
        
        if isinstance(lines,str):
            try:
                with open(lines,"rt") as file:
                    lines = file.readlines()
            except IOError:
                raise CppError("Failure reading input file {0}".format(lines))
        
        return Preprocessor._DoSingleFile( env, dirs, Preprocessor._LineIter(lines),[])      
        
    @staticmethod
    def _LineIter(lines):
        for n,line in enumerate(lines):
            if not len(line):
                continue
            yield (n,line)

    @staticmethod
    def _EvalExpression(expression,env):

        # yes, that's a bit hacky
        # XXX add support for (defined) tests
        replace = {
            "&&" : "and",
            "||" : "or",
            "true" : "True",
            "false" : "False",
        }
            
        for k,v in itertools.chain(env.items(),replace.items()):
            expression = expression.replace(k,v)

        return eval(expression)
        
    @staticmethod
    def _DoSingleFile(env,dirs,myiter,output,match=False):

        nested = []
        for index,line in myiter:

            active = not nested or nested[-1][0] is True
            if line[0] != "#":
                if active is True:
                    output.append(line)

                continue
            
            s = line[1:].strip()
            
            # include
            matched = re.match(Preprocessor.include_re,s)
            if not matched is None:
                if active is False:
                    continue

                l,ifile,r = matched.groups()
                if l=='"' and r != l or l == "<" and r != ">":
                    raise CppError("Line {0}: unbalanced quotes in include statement: {1}".format(index,ifile))

                for dir in dirs:
                    fname = os.path.join(dir,ifile)
                    try:
                        file = open(fname,"rt")
                    except IOError:
                        continue

                    lines = Preprocessor._LineIter(file.readlines())
                    file.close()
                    break
                else:
                    raise CppError("Line {0}: failure resolving include file: {1}".format(index,ifile))  
                output += Preprocessor._DoSingleFile( env, dirs,lines,[])
                continue
                
            # define
            matched = re.match(Preprocessor.define_re,s)
            if not matched is None:
                if active is True: 
                    env[matched.groups()[0].strip()] = matched.groups()[1].strip()
                continue

            # undef
            matched = re.match(Preprocessor.undef_re,s)
            if not matched is None:
                if active is True:
                    del env[matched.groups()[0].strip()]
                continue

            # error
            matched = re.match(Preprocessor.error_re,s)
            if not matched is None:
                if active is True:
                    raise CppError("Line {0}: {1}".format(index,matched.groups()[0]))
                continue
                
            # ifdef
            matched = re.match(Preprocessor.ifdef_re,s)
            if not matched is None:

                match = matched.groups()[0].strip() in env
                nested += [[match,match]]
                continue
            
            # ifndef
            matched = re.match(Preprocessor.ifndef_re,s)
            if not matched is None:

                match = not matched.groups()[0].strip() in env
                nested += [[match,match]]
                continue

            # if
            matched = re.match(Preprocessor.if_re,s)
            if not matched is None:

                match = Preprocessor._EvalExpression(matched.groups()[0].strip(),env)
                nested += [[match,match]]
                continue

            # endif
            matched = re.match(Preprocessor.endif_re,s)
            if not matched is None:
                if not nested:
                    raise CppError("Line {0}: Unmatched #endif".format(index))
                    
                nested.pop()
                continue

            # elif
            matched = re.match(Preprocessor.elif_re,s)
            if not matched is None:
                if not nested:
                    raise CppError("Line {0}: Unmatched #elif".format(index))

                nested[-1][0] = False
                if nested[-1][1] is False:
                    if Preprocessor._EvalExpression(matched.groups()[0].strip(),env) is True:
                        nested[-1] = [True,True]
                
                continue

            # else
            matched = re.match(Preprocessor.else_re,s)
            if not matched is None:
                if not nested:
                    raise CppError("Line {0}: Unmatched #else".format(index))

                nested[-1] = [not nested[-1][1],not nested[-1][1]]
                continue

            raise CppError("Line {0}: Unknown preprocessor directive: #{1}".format(index,s))

        if nested:
            raise CppError("Line {0}: Unexpected EOF, not all open tags are closed".format(index))

        return output
            
            
def test_it():

    bdir = os.path.join("..","test","cpp")
    
    d = {}
    res = Preprocessor.Preprocess(os.path.join(bdir,"testcase1.txt"),[("FOO_DEFINED","1"),("BAR_DEFINED","2")],[bdir])
    exec("\n".join(res),d)
    assert d["fine"]==5
    print("Test1 passed")

    d = {}
    res = Preprocessor.Preprocess(os.path.join(bdir,"testcase2.txt"),[("FOO_DEFINED","1"),("BAR_DEFINED","2")],[bdir])
    exec("\n".join(res),d)
    assert d["fine"]==6
    print("Test2 passed")

    d = {}
    res = Preprocessor.Preprocess(os.path.join(bdir,"testcase3.txt"),[("FOO_DEFINED","0"),("BAR_DEFINED","2")],[bdir])
    exec("\n".join(res),d)
    assert d["fine"]==2
    print("Test3 passed")
            
if __name__ == "__main__":
    test_it()
            
            
            
            
            
            
            
            

            
            
            
            
            
            
            
            

# vim: ai ts=4 sts=4 et sw=4