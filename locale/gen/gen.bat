mergeall.py
pygettext.py ../../src-py/*.py merged_master.txt
patch.py
copy messages.pot messages_ger_new.po
copy messages.pot messages_eng_new.po

msgmerge.py -U messages_ger.po messages_ger_new.po
msgmerge.py -U messages_eng.po messages_eng_new.po