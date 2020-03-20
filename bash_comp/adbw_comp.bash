
###
# 
# @File   : adbw_comp.sh   
# @Date   : 2020-02-22 12:23   
# @Brief  :  
# 
###

_adbw_completion_escape() {
    if [[ "$1" = '' ]]
    then
        sed 's/ /\\ /g'
    else
        cat
    fi
}

_adbw_completion_filter_extension() {
    local IFS=$'\n'
    while read name
    do
        shopt -s nocasematch
        if [[ -d "$name" ]]
        then
            echo "$name"
        elif [[ "$name" = *".$1" ]]
        then
            echo "$name"
        fi
    done
}

_adbw_completion_filedir() {
    local cur="$1"
    local quote="$2"
    local IFS=$'\n'
    if [[ "$cur" = '' ]]
    then
        COMPREPLY=( $(adb shell ls -1 2> /dev/null | _adbw_completion_escape "$quote") )
    elif adb shell test -d "'$cur'" 2> /dev/null
    then
        if [[ "$cur" = *'/' ]]
        then
            COMPREPLY=( $(adb shell ls -1d -- "'${cur}'*" 2> /dev/null | _adbw_completion_escape "$quote") )
        else
            COMPREPLY=( $(adb shell ls -1d -- "'${cur}/'*" 2> /dev/null | _adbw_completion_escape "$quote") )
        fi
    elif adb shell test -f "'$cur'" 2> /dev/null
    then
        COMPREPLY=( "$cur" )
    else
        COMPREPLY=( $(adb shell ls -1d -- "${cur}*" 2> /dev/null | _adbw_completion_escape "$quote") )
    fi
    if [[ "${#COMPREPLY[@]}" -eq 1 ]]
    then
        adb shell test -d "'${COMPREPLY[0]}'" 2> /dev/null &&
        COMPREPLY=( "${COMPREPLY[0]}/" $(adb shell ls -1d -- "'${COMPREPLY[0]}/'*" 2> /dev/null | _adbw_completion_escape "$quote"))
    fi
}

_adbw_completion() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local quote=
    if [[ "$cur" = '"'* || "$cur" = "'"* ]]
    then
        quote=${cur:0:1}
        cur=${cur:1}
    fi
    if [[ "$COMP_CWORD" -eq 1 ]]
    then
        type compopt &> /dev/null && compopt +o nospace 2> /dev/null
        COMPREPLY=($(compgen -W "ip devices help version connect disconnect forward ppp reverse push pull sync shell emu install uninstall backup restore bugreport jdwp logcat disable-verity enable-verity keygen remount reboot sideload root unroot usb tcpip start-server kill-server reconnect" -- "${COMP_WORDS[1]}"))
    elif [[ "$COMP_CWORD" -ge 2 && "${COMP_WORDS[1]}" = "pull" ]]
    then
        local IFS=$'\n'
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi 
        if [[ "$cur" != '~'* && "$cur" != './'* && "$cur" != '../'* ]]
        then
            _adbw_completion_filedir "$cur" "$quote"
        fi
        if [[ "$COMP_CWORD" -ge 3 ]]
        then
            COMPREPLY=( "${COMPREPLY[@]}" $(compgen -d -- "$cur" | _adbw_completion_escape "$quote"))
        fi
    elif [[ "$COMP_CWORD" -ge 2 && "${COMP_WORDS[1]}" = "push" ]]
    then
        local IFS=$'\n'
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$COMP_CWORD" -ge 3 && "$cur" != '~'* && "$cur" != './'* && "$cur" != '../'* ]]
        then
            _adbw_completion_filedir "$cur" "$quote"
        fi
        if type _filedir > /dev/null
        then
            _filedir
        else
            COMPREPLY=( "${COMPREPLY[@]}" $(compgen -f -- "$cur" | _adbw_completion_escape "$quote"))
        fi
    elif [[ "${COMP_WORDS[1]}" = "shell" ]]
    then
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$COMP_CWORD" -eq 2 ]]
        then
            COMPREPLY=( $(compgen -W "ls cat echo file env ln cp mv rm touch dumpsys mount umount am pm ps find du df getprop setprop kill pkill killall pgrep date ifconfig chmod chown chgrp freetime mkdir md5sum uname ulimit top reboot grep egrep tar head tail yes" -- "$cur") )
        elif [[ "$COMP_CWORD" -gt 2 ]]
        then
            if [[ "$cur" = '"'* || "$cur" = "'"* ]]
            then
                cur=${cur:1}
            fi
            _adbw_completion_filedir "$cur" "$quote"
        fi
    elif [[ "${COMP_WORDS[1]}" = "install" ]]
    then
        if [[ "$cur" = *'*'* ]]
        then
            return 0
        fi
        if [[ "$COMP_CWORD" -gt 1 ]]
        then
            local IFS=$'\n'
            COMPREPLY=( $(compgen -f -- "$cur" | _adbw_completion_filter_extension 'apk' | _adbw_completion_escape "$quote") )
        fi
    fi
}

complete -F _adbw_completion adb adbw


# End of 'adbw_comp.bash' 

