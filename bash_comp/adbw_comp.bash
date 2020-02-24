
###
# 
# @File   : adbw_comp.sh   
# @Date   : 2020-02-22 12:23   
# @Brief  :  
# 
###

_adbw_completion_filedir() {
    local cur="$1"
    local IFS=$'\n'
    if [[ "$cur" = '' ]]
    then
        COMPREPLY=( $(adb shell ls -1 2> /dev/null | sed 's/ /\\ /g') )
    elif adb shell test -d "$cur" 2> /dev/null
    then
        if [[ "$cur" = *'/' ]]
        then
            COMPREPLY=( $(adb shell ls -1d -- "${cur}*" 2> /dev/null | sed 's/ /\\ /g') )
        else
            COMPREPLY=( $(adb shell ls -1d -- "${cur}/*" 2> /dev/null | sed 's/ /\\ /g') )
        fi
    elif adb shell test -f "$cur" 2> /dev/null
    then
        COMPREPLY=( "$cur" )
    else
        COMPREPLY=( $(adb shell ls -1d -- "${cur}*" 2> /dev/null | sed 's/ /\\ /g') )
    fi
    if [[ "${#COMPREPLY[@]}" -eq 1 ]]
    then
        adb shell test -d "${COMPREPLY[0]}" 2> /dev/null &&
        COMPREPLY=( "${COMPREPLY[0]}/" $(adb shell ls -1d -- "${COMPREPLY[0]}/*" 2> /dev/null | sed 's/ /\\ /g'))
    fi
}

_adbw_completion() {
    if [[ "$COMP_CWORD" -eq 1 ]]
    then
        type compopt &> /dev/null && compopt +o nospace 2> /dev/null
        COMPREPLY=($(compgen -W "devices help version connect disconnect forward ppp reverse push pull sync shell emu install uninstall backup restore bugreport jdwp logcat disable-verity enable-verity keygen remount reboot sideload root unroot usb tcpip start-server kill-server reconnect" -- "${COMP_WORDS[1]}"))
    elif [[ "$COMP_CWORD" -ge 2 && "${COMP_WORDS[1]}" = "pull" ]]
    then
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local IFS=$'\n'
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$cur" = '"'* || "$cur" = "'"* ]]
        then
            cur=${cur:1}
        fi
        if [[ "$cur" != '~'* && "$cur" != './'* && "$cur" != '../'* ]]
        then
            _adbw_completion_filedir "$cur"
        fi
        if [[ "$COMP_CWORD" -ge 3 ]]
        then
            COMPREPLY=( "${COMPREPLY[@]}" $(compgen -d -- "$cur" | sed 's/ /\\ /g'))
        fi
    elif [[ "$COMP_CWORD" -ge 2 && "${COMP_WORDS[1]}" = "push" ]]
    then
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local IFS=$'\n'
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$cur" = '"'* || "$cur" = "'"* ]]
        then
            cur=${cur:1}
        fi
        if [[ "$COMP_CWORD" -ge 3 && "$cur" != '~'* && "$cur" != './'* && "$cur" != '../'* ]]
        then
            _adbw_completion_filedir "$cur"
        fi
        COMPREPLY=( "${COMPREPLY[@]}" $(compgen -f -- "$cur" | sed 's/ /\\ /g'))
    elif [[ "${COMP_WORDS[1]}" = "shell" ]]
    then
        local cur="${COMP_WORDS[COMP_CWORD]}"
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$COMP_CWORD" -eq 2 ]]
        then
            COMPREPLY=( $(compgen -W "ls cat echo ln cp mv rm touch dumpsys mount umount am pm ps find du df getprop setprop kill pkill killall pgrep date ifconfig chmod chown chgrp freetime mkdir md5sum uname ulimit top reboot tar" -- "$cur") )
        elif [[ "$COMP_CWORD" -gt 2 ]]
        then
            if [[ "$cur" = '"'* || "$cur" = "'"* ]]
            then
                cur=${cur:1}
            fi
            _adbw_completion_filedir "$cur"
        fi
    elif [[ "${COMP_WORDS[1]}" = "install" ]]
    then
        local cur="${COMP_WORDS[COMP_CWORD]}"
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$cur" = '"'* || "$cur" = "'"* ]]
        then
            cur=${cur:1}
        fi
        if [[ "$COMP_CWORD" -gt 1 ]]
        then
            local IFS=$'\n'
            COMPREPLY=( $(compgen -f -- "$cur" | sed 's/ /\\ /g') )
        fi
    fi
}

complete -F _adbw_completion adb adbw


# End of 'adbw_comp.bash' 

