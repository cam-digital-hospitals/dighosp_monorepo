# Prerequisites

## Windows Subsystem for Linux

WSL is recommended for providing a Linux environment on Windows. See the [official Microsoft documentation](https://learn.microsoft.com/en-us/linux/install#install-linux-with-windows-subsystem-for-linux) for installing WSL. To connect Visual Studio Code to WSL, follow [these instructions](https://code.visualstudio.com/docs/remote/wsl-tutorial).

All code snippets below assume a Ubuntu environment. Subsitute `apt` with another package manager if needed.

## Docker Desktop

Install Docker Desktop using [these instructions](https://docs.docker.com/get-docker/).

## Pipx

If you attempt to install Python packages system-wide using `pip`, you will probably receive an error:
```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

To avoid this, we can use [`pipx`](https://pipx.pypa.io/stable/):
```bash
sudo apt install pipx
pipx ensurepath
pipx install <main-package>
pipx inject <main-package> <optional-dependency>
```

## Poetry

[Poetry](https://python-poetry.org/) is recommended for handling Python packaging and dependency management.  We can install poetry globally as follows:

```bash
pipx install poetry
poetry config virtualenvs.in-project true
```

The final line above sets Poetry to create its virtual environments within the directory structure of each managed Poetry project.

Poetry projects can then be created using `poetry new` or `poetry init` and dependencies added using `poetry add`. Other useful commands include `poetry run` and `poetry shell`.

The [Poetry Monorepo](https://marketplace.visualstudio.com/items?itemName=ameenahsanma.poetry-monorepo) is useful for managing virtual environment switching when working with multiple Python projects within a single Visual Studio Code project.


## Git setup

### nbstripout

[`nbstripout`](https://pypi.org/project/nbstripout/) strips output from Jupyter notebook (.ipynb) cells upon staging the notebook file in Git. This results in much smaller commits, especially if the notebook contains figures/plots. To install nbstripout:
```bash
pipx instal nbstripout
nbstripout --install --attributes .gitattributes
```

You can also check whether `nbstripout` is already installed for a given repository using `nbstripout --status`.

### git root alias

For convienience, we add an alias to return the root directory of the project:
 ```bash
git config --global alias.root 'rev-parse --show-toplevel'
 ```
 