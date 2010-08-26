‘simulate JavaScript alert() function
sub alert(prompt)
    MsgBox prompt, 48 , “Sidebar Gadget”
end sub

‘simulate JavaScript confirm() function
function confirm(prompt)
    dim res
    res = MsgBox (prompt, 33, “Sidebar Gadget”)
    if res=1 then
        confirm = true
    else
        confirm = false
    end if
end function

