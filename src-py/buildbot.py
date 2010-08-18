#!/usr/bin/env python3
# -*- coding: UTF_8 -*-

# ///////////////////////////////////////////////////////////////////////////////////
# MGL Framework Python Scripting Interface (v0.1)
# [buildbot.py]
# (c) Alexander Gessler, 2009
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

import sys
from abbrev import *
import operator

caches = dd(lambda:[], {})
seps = {'==':True, '<=':True, '>=':True, '!=':True, '<':True,
    '>':True, '\n':False, '\t':False, ' ':False}

# -----------------------------------------------------------------------------------
class ourdd(dict):
    def __init__ (self, d):
        dict.__init__(self, d)

    def __missing__(self, key):
        # check conversion to integer
        try:
            return int(key)
        except ValueError as v:
            pass

        # check conversion to float
        try:
            return float(key)
        except ValueError as v:
            pass

        # check for boolean constants
        if key == 'True':
            return True
        if key == 'False':
            return False

        # check for string literal
        #if key[]

        raise KeyError()

    def __repr__(self):
        return "<constants>"

# -----------------------------------------------------------------------------------
def single_yield(scope):
    yield scope

# -----------------------------------------------------------------------------------
class Error(BaseException):
    pass

def error(scope, msg):
    print('[bot] ' + msg)
    for t in scope:
        if '_name' in t:
            print('@ ', t['_name'])
        
    raise Error()

def warn(scope, msg):
    print('[bot] ' + msg)
    for t in scope:
        if '_name' in t:
            print('@ ', t['_name'])

# -----------------------------------------------------------------------------------
def tokenize(lines):
    def tokenize_line(line):
        # XXX - terrible
        res, gotone = [], False

        while True:
            mins = []
            for k, v in seps.items():
                n = line.find(k)
                if n != -1:
                    mins.append((n, k, v))

            if not len(mins):
                break

            gotone = True

            n = min(mins, key=operator.itemgetter(0))
            if n[0] > 0:
                res.append(line[:n[0]])
            if n[2]:
                res.append(line[n[0]:n[0] + len(n[1])])

            line = line[n[0] + len(n[1]):]
            
        return line if not gotone else (res + [line] if len(line) else res)

    for line in lines:
        if line[:1]=='#':
            continue

        s = tokenize_line(line)
        if len(s):
            yield s
        
# -----------------------------------------------------------------------------------
def execute(scope, group, args, lines):
    n = 0
    for newscope in group(*args):
        scope += [newscope]

        idle = -1
        for n, item in enumerate(lines):
            if idle > 0:
                idle -= 1
                continue
            
            call = item[0]
            if call == 'end':
                break

            if call[:1] == '#':
                continue

            fa = [scope]
            for arg in item[1:]:
                s = lookup_nofault(scope, arg)
                fa.append(s if not s is None else arg)

            bfnc = 'block_' + call
            if bfnc in globals():
                try:
                    #print(lines[n+1:])
                    idle = execute(scope, globals()[bfnc], fa, lines[n + 1:]) + 1
                except Error as ours:
                    raise
                except BaseException as err:
                    print(err)
                    error(scope, "'%s' received a wrong number/type of arguments" % call)

                continue

            bfnc = 'func_' + call
            if bfnc in globals():
                try:
                    #print(bfnc)
                    globals()[bfnc](*fa)
                except Error as ours:
                    raise
                except BaseException as err:
                    print(err)
                    error(scope, "'%s' received a wrong number/type of arguments" % call)
                        
                continue

            error(scope, 'Unknown callable: %s' % call)

        scope.pop()
    return n


# -----------------------------------------------------------------------------------
def lookup_nofault(scope, name):
    for tt in scope[-1::-1]:
        #print(tt)
        try:
            return tt[name]
        except KeyError:
            pass
    
    return None

# -----------------------------------------------------------------------------------
def lookup(scope, name):
    res = lookup_nofault(scope, name)
    if res is None:
        #print(scope)
        error(scope, 'Name not found: %s' % name)
        return None

    return res

# -----------------------------------------------------------------------------------
def block_group(scope, kind, expr):
    pd = scope[-1]['dir']
    
    #scope,kind,expr = args
    if kind == "wc" or kind == "wildcard":
        expr = expr.replace('*', '[a-zA-Z0-9_]+')
    elif kind == 'type':
        if expr == 'dir':
            for t in old(pd):
                if opid(opj(pd, t)):
                    yield {'~':opj(pd, t)}
        elif expr == 'file':
            for t in old(pd):
                if opif(opj(pd, t)):
                    yield {'~':opj(pd, t)}
        return
        
    elif kind != "re" and kind != "regex":
        error(scope, 'Invalid kind in group statement: %s' % kind)

    import re
    for t in old(scope[-1]['dir']):
        if re.match(expr, t):
            yield {'~':opj(pd, t)}

# -----------------------------------------------------------------------------------
def block_if(scope, *args):
    e0 = args[0]
    if len(args) == 1:
        # if single_boolean_expression
        if e0 == 'True' or e0 != '0':
            yield {}
            scope[-1]['_doelse'] = False
            return

    if len(args) != 3:
        error(scope, 'Invalid syntax for if: expect "if e0" or "if e0 op e1"')
        
    e1, op = args[2], args[1]
    ops = {
        '==': lambda x, y:x == y,
        '<':  lambda x, y:x < y,
        '>':  lambda x, y:x > y,
        '<=': lambda x, y:x <= y,
        '>=': lambda x, y:x >= y,
        '!=': lambda x, y:x != y,
        'endswith' : lambda x, y:x[-len(y):] == y,
        '!endswith' : lambda x, y:x[-len(y):] != y,
        'contains' : lambda x, y:x.find(y) != -1,
        '!contains' : lambda x, y:x.find(y) == -1,
        }

    if args[1] not in ops:
        error(scope, 'Unknown operation in if statement: %s' % op)
        return

    if ops[op](e0, e1):
        yield {}
        scope[-1]['_doelse'] = False
        return
        
    scope[-1]['_doelse'] = True
    return

# -----------------------------------------------------------------------------------
def block_else(scope):
    if not '_doelse' in scope[-1]:
        error(scope, 'Unexpected else')
        return
    
    if scope[-1]['_doelse'] == True:
        yield {}
        
    scope[-1]['_doelse'] = False


# -----------------------------------------------------------------------------------
def block_elseif(scope, expr0, op, expr1):
    if not '_doelse' in scope[-1]:
        warn('Unexpected else')
        return
    
    if scope[-1]['_doelse'] == True:
        for t in block_if(scope, expr0, op, expr1):
            yield {}
        
    scope[-1]['_doelse'] = False

# -----------------------------------------------------------------------------------
def func_build(scope, file):
    if file.find('\\') != -1 or file.find('/') != -1:
        nxt = file
    else:
        nxt = opj(lookup(scope, 'dir'), file)
    try:
        lines = open(opj(nxt, '$build'), 'rt').readlines()
    except:
        warn(scope, 'Failure building %s, $build file not found' % nxt)
        return

    print('BUILD %s/@build' % nxt)
    execute(scope, single_yield, [{'dir':nxt, '_name':file}], list(tokenize(lines)))


# -----------------------------------------------------------------------------------
def func_run(scope, *args):
    file = args[0]
    func = args[1] if len(args) > 1 else None
    print('RUN %s.%s()' % (file, func))
    
    myd = lookup(scope, 'dir')
    sys.path.insert(0, myd)

    try:
        mod = __import__(file)
    except ImportError as imp:
        warn(scope, 'Failure importing %s' % file)
        del sys.path[0]
        return

    if not func is None:
        prv = os.getcwd()
        for tt in sys.path:
            try:
                for mm in old(tt):
                    if mm == file + '.py':
                        os.chdir(tt)
            except:
                pass
        try:
            mod.__dict__[func](*args[2:])
        except BaseException as e:
            print(e)
            warn(scope, 'Failure calling %s.%s()' % (file, func))
        os.chdir(prv)
    
    del sys.path[0]

# -----------------------------------------------------------------------------------
def func_print(scope, *args):
    print(*args)
    
# -----------------------------------------------------------------------------------
def func_set(scope, var, val):
    ss = lookup_nofault(scope, val)
    print('SET ', var, ' = ', val)
    scope[-1][var] = ss if ss else val

# -----------------------------------------------------------------------------------
def func_push(scope, cache, *args):
    if not len(args):
        error('Not enough arguments to push')
    
    print('PUSH %s to %s' % (args[-1], cache))
    caches[cache].append(args)

# -----------------------------------------------------------------------------------
def main():
    try:
        execute([ourdd({'caches':caches})], single_yield, [{'dir':'.'}], [['build', '..']])
    except Error as err:
        print('[bot] Exiting with errors')
        return

    print('[bot] Bot run successful!')

    # needs to be called manually with RUN xxx
"""
    builders = []
    for t in old('.'):
        if opse(t)[-1]=='.py' and t.find('__builder__')==0:
            try:
                bld = __import__(t[0:-3])
            except:
                continue

            print('Load builder: %s'%t)
            builders.append(bld)


    print('[bot] Loaded %s builders!'%len(builders))
    for bd in builders:
        bd.main(caches)
"""
        

            
    

if __name__ == '__main__':
    main()
    input('All done, waiting for keystroke ')

# vim: ai ts=4 sts=4 et sw=4
