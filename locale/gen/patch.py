
with open("messages.pot","r") as inp:
    text = inp.readlines()

with open("messages.pot","w") as outp:
    with open("header_template.txt","r") as tpl:
        text[:15] = tpl.readlines()
        outp.write("".join(text))

print("*done*")
        
        
