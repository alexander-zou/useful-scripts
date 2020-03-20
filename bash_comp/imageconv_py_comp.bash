#!/usr/bin/env bash

###
# 
# @File   : imageconv_py_comp.bash   
# @Author : alexander.here@gmail.com
# @Date   : 2020-03-06 16:43 CST(+0800)   
# @Brief  :  
# 
###

_imageconv_py_completion() {
    local OPT_LIST="-- -h --path -p --width --col -c --height --row -r --stride -s --scanline -l --input-type -i --output-type -o --input-yuv-color --output-yuv-color --input-yuv-range --output-yuv-range --normalize -n --keep-name -k --force -f --verbose -v -j --jump-through"
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [[ "$COMP_CWORD" -gt 1 ]]
    then
        local last="${COMP_WORDS[COMP_CWORD-1]}"
        case "$last" in
            '-p'|'--path')
                COMPREPLY=( $(compgen -d -- "$cur") )
                return;;
            '-i'|'--input-type'|'-o'|'--output-type')
                COMPREPLY=($(compgen -W "8u 16u 32f bgr rgb rgba bgra yuv nv21 nv12 jpg png bmp" -- "$cur"))
                return;;
            '--input-yuv-color'|'--output-yuv-color')
                COMPREPLY=($(compgen -W "bt601 bt709 bt2020" -- "$cur"))
                return;;
            '--input-yuv-range'|'--output-yuv-range')
                COMPREPLY=($(compgen -W "fullrange fullswing videorange studioswing" -- "$cur"))
                return;;
            '-c'|'--col'|'--width'|'-r'|'--row'|'--height'|'-s'|'--stride'|'-l'|'--scanline'|'-n'|'--normalize'|'-j'|'--jump-through')
                COMPREPLY=()
                return;;
        esac
    fi
    if type -t _filedir > /dev/null 2>&1
    then
        COMPREPLY=($(compgen -W "$OPT_LIST" -- "$cur"))
        _filedir
    else
        COMPREPLY=($(compgen -W "$OPT_LIST" -f -- "$cur"))
    fi
}

complete -F _imageconv_py_completion imageconv.py


# End of 'imageconv_py_comp.bash' 

