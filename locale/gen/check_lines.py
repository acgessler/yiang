#! /usr/bin/env python
#Check if some strings are not translated

#---Settings START---

filename = "messages_ger.po"
counter = 0
notcounter = 0
linelist = list()
search_row = False
row_start = 0
row_start_counter = 0
row_last = 0

#---Settings END---


file = open("./"+filename,"r")
lines = file.readlines()
file.close()
print("Lines to check: ",len(lines))
for linenr in range(len(lines)):
    line = lines[linenr]
    if line.find('msgstr') != -1:
        counter += 1
        if line == 'msgstr ""\n' and lines[linenr+1] == '\n':
            notcounter += 1
            row_last = linenr
            if search_row == False:
                search_row = True
                row_start = linenr
                row_start_counter = notcounter
        else:
            if search_row == True:
                search_row = False
                if notcounter != row_start_counter:
                    linelist.append(str(row_start+1)+'-'+str(row_last+1))
                else:
                    linelist.append(str(row_start+1))
                
            
print('untranslated Lines: ',notcounter,'out of ',counter)
print(linelist)
