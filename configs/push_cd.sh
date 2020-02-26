
# Replace cd with pushd https://gist.github.com/mbadran/130469

# Install:
#   Source me into .bash_profile

# Usage:
#   'cd -' goes back through the stack
#   'cd -l' shows the stack
#   'cd -N' goes back to the Nth directory in stack
#   check out comments among lines below for more features

function push_cd() {
  # typing just `push_cd` will take you $HOME ;)
  if [ -z "$1" ]; then
    push_cd "$HOME"

  # use `push_cd -` to visit previous directory
  elif [ "$1" == "-" ]; then
    if [ "$(dirs -p | wc -l)" -gt 1 ]; then
      current_dir="$PWD"
      popd > /dev/null 2>&1
#      pushd -n $current_dir > /dev/null
    elif [ -n "$OLDPWD" ]; then
      push_cd $OLDPWD
    fi

  # use `push_cd -l` or `push_cd -s` to print current stack of folders
  elif [ "$1" == "-l" ] || [ "$1" == "-s" ]; then
    dirs -v

  # use `push_cd +N` to go to the Nth directory in history (pushing)
  elif [[ "$1" =~ ^+[0-9]+$ ]]; then
    push_cd -g ${1/+/}

  # use `push_cd -N` to go n directories back in history
  elif [[ "$1" =~ ^-[0-9]+$ && "${1/-/}" -ge 1 ]]; then
    for i in `seq 1 ${1/-/}`; do
      popd > /dev/null 2>&1
    done

  # use `push_cd -- <path>` if your path begins with a dash
  elif [ "$1" == "--" ]; then
    shift
    pushd -- "$@" > /dev/null

    # basic case: move to a dir and add it to history
  else
    pushd "$@" > /dev/null

    if [ "$1" == "." ] || [ "$1" == "$PWD" ]; then
      popd -n > /dev/null 2>&1
    fi
  fi

  if [ -n "$CD_SHOW_STACK" ]; then
    dirs -v
  fi
}

alias cd=push_cd


