
###
# 
# @File   : all.bash   
# @Date   : 2020-02-22 12:23   
# @Brief  : Entry point to source all bash comp scripts
#           in this repo.
# 
###

MY_PATH="$(dirname "$BASH_SOURCE")"

[[ -f "${MY_PATH}/adbw_comp.bash" ]] && . "${MY_PATH}/adbw_comp.bash"
[[ -f "${MY_PATH}/code-run_comp.bash" ]] && . "${MY_PATH}/code-run_comp.bash"
[[ -f "${MY_PATH}/create_comp.bash" ]] && . "${MY_PATH}/create_comp.bash"
[[ -f "${MY_PATH}/statistics_comp.bash" ]] && . "${MY_PATH}/statistics_comp.bash"
[[ -f "${MY_PATH}/imageconv_py_comp.bash" ]] && . "${MY_PATH}/imageconv_py_comp.bash"

# End of 'all.bash' 

