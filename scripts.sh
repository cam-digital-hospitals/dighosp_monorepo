# git config --global alias.root 'rev-parse --show-toplevel'
alias docker-restart="pushd `git root` && docker compose up -d --build && popd"
alias docker-down="pushd `git root` && docker compose down && popd"
alias dprune="docker system prune --volumes"

alias gitroot='cd `git root`'
alias ppy="poetry run python"
alias plint="poetry run pylint --rcfile=`git root`/.pylintrc"
