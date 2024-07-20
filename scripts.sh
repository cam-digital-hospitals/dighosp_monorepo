###############
#  DOCKER
###############

alias docker-restart="pushd `git root`; docker compose up -d --build; popd"
alias docker-down="pushd `git root`; docker compose down; popd"
alias dprune="docker system prune --volumes"

###############
#  GIT
###############

# git config --global alias.root 'rev-parse --show-toplevel'

alias gitroot="cd `git root`"

# Assumes that origin/`whoami`-dev was deleted after closing a pull request (merged to main)
# Deletes the local `whoami`-dev branch and recreates from "main" (after fetch/pull)
new-dev-branch() {
    git checkout main
    git fetch
    git pull
    git branch -D `whoami`-dev
    git remote prune origin
    git checkout -b `whoami`-dev
}

alias gitll="gh repo list --no-archived"
alias gitls="gh repo list --no-archived --json name --jq \".[].name\""

###############
#  POETRY
###############

alias ppy="poetry run python"
alias plint="poetry run pylint --rcfile=`git root`/.pylintrc"

install-all() {
    pushd `git root`
    ls -d */pyproject.toml | xargs -n1 dirname | xargs -I {} poetry -C {} install
    popd
}

version-all() {
    pushd `git root`
    ls -d */pyproject.toml | xargs -n1 dirname | xargs -I {} poetry -C {} version $@
    popd
}
