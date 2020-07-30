
###
# 
# @File   : code-run_comp.bash   
# @Date   : 2020-02-22 12:23   
# @Brief  :  
# 
###

#complete -W "new last again path help" c-run cpp-run bash-run java-run perl-run py2-run py3-run


_c_run_completion() {
    if [[ "$COMP_CWORD" -eq 1 ]]
    then
        COMPREPLY=($(compgen -W "new last again show path help" -- "${COMP_WORDS[1]}"))
    else
        COMPREPLY=($(compgen -W "-Wall -Wextra -g -O0 -O1 -O2 -O3 -std -I -D -U -l -Wa, -Wl, -Wp, -Werror,-W -pedantic -pedantic-errors" -- "${COMP_WORDS[$COMP_CWORD]}"))
        if [[ "${#COMPREPLY[@]}" -eq 1 ]]
        then
            case "${COMPREPLY[0]}" in
                "-std"* | "-D"* | "-U"* | "-Wa,"* | "-Wl,"* | "-Wp,"* | "-Werror,-W"* )
                    type compopt &> /dev/null && compopt -o nospace 2> /dev/null;;
            esac
        fi
    fi
}

complete -F _c_run_completion c-run cpp-run

_java_run_completion() {
    if [[ "$COMP_CWORD" -eq 1 ]]
    then
        COMPREPLY=($(compgen -W "new last again show path help" -- "${COMP_WORDS[1]}"))
    else
        COMPREPLY=($(compgen -W "-g -verbose -deprecation -cp -classpath -source -target -Werror" -- "${COMP_WORDS[$COMP_CWORD]}"))
    fi
}

complete -F _java_run_completion java-run

_other_run_completion() {
    if [[ "$COMP_CWORD" -eq 1 ]]
    then
        COMPREPLY=($(compgen -W "new last again show path help" -- "${COMP_WORDS[1]}"))
    else
        COMPREPLY=()
    fi
}

complete -F _other_run_completion perl-run py2-run py3-run bash-run

# End of 'code-run_comp.bash' 

