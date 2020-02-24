
###
# 
# @File   : create_comp.bash   
# @Date   : 2020-02-22 12:23   
# @Brief  :  
# 
###


_create_completion() {
    if [[ "$COMP_CWORD" -eq 1 && "${COMP_WORDS[COMP_CWORD]}" = '-'* ]]
    then
        COMPREPLY=($(compgen -W "-auto -c -cpp -php -perl -python -ruby -sh -bash -s -help --" -- "${COMP_WORDS[COMP_CWORD]}"))
    fi
}

complete -F _create_completion -d create

# End of 'create_comp.bash' 

