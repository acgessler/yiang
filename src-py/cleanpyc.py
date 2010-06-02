#!/usr/bin/env python3

# Delete all *.pyc recursively.
import os

def main(root='.'):
    for t in os.listdir(root):
        fullp =os.path.join(root,t)
        if os.path.isdir(t):
            main(fullp)
            continue

        if os.path.splitext(fullp)[-1].lower() == '.pyc':
            os.unlink(fullp)



if __name__ ==  '__main__':
    os.chdir("..")
    main()
