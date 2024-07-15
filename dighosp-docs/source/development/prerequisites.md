# Prerequisites

## Windows Subsystem for Linux

WSL is recommended for providing a Linux environment on Windows. See the [official Microsoft documentation](https://learn.microsoft.com/en-us/linux/install#install-linux-with-windows-subsystem-for-linux) for installing WSL. To connect Visual Studio Code to WSL, follow [these instructions](https://code.visualstudio.com/docs/remote/wsl-tutorial).

All code snippets below assume a Ubuntu environment. Subsitute `apt` with another package manager if needed.

## Poetry

[Poetry](https://python-poetry.org/) is recommended for handling Python packaging and dependency management.  We can install poetry globally as follows:

```bash
sudo apt install pipx
pipx ensurepath
pipx install poetry

poetry config virtualenvs.in-project true
```

The final line above sets Poetry to create its virtual environments within the directory structure of each managed Poetry project.

Poetry projects can then be created using `poetry new` or `poetry init` and dependencies added using `poetry add`. Other useful commands include `poetry run` and `poetry shell`.

## Docker Desktop

Install Docker Desktop using [these instructions](https://docs.docker.com/get-docker/).