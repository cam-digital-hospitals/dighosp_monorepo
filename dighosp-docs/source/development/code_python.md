# Coding standards: Python

Use `isort` and `autopep8` to automatically format Python code. A maximum line length of 100 is set for each Python project, using the `pyproject.toml` file:

```toml
[tool.isort]
line_length = 100
color_output = true

[tool.autopep8]
max_line_length = 100
```

Additionally, code quality can be scored using `pylint`:
```bash
poetry run pylint --rcfile=`git root`/.pylintrc $DIR_TO_LINT
```

False positives can be ignored using `# pylint: disable=` within the Python file.
