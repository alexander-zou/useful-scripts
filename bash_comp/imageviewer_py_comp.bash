#!/usr/bin/env bash

###
# 
# @File   : imageviewer_py_comp.bash   
# @Author : alexander.here@gmail.com
# @Date   : 2020-03-11 18:38 CST(+0800)   
# @Brief  :  
# 
###

_imageviewer_py_completion() {
    local OPT_LIST="-- -h --help -c --cols --width -r --rows --height -s --scale"
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [[ "$COMP_CWORD" -gt 1 ]]
    then
        local last="${COMP_WORDS[COMP_CWORD-1]}"
        case "$last" in
            '-c'|'--col'|'--width'|'-r'|'--row'|'--height'|'-s'|'--scale')
                COMPREPLY=()
                return;;
        esac
    fi
    COMPREPLY=($(compgen -W "$OPT_LIST" -f -- "$cur"))
}

complete -F _imageviewer_py_completion imageviewer.py


# End of 'imageviewer_py_comp.bash' 

