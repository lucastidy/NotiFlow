## Basic guide on UV

UV is essentially a dependency tracker for python. We are using it to keep track of the dependencies we are using and creating a venv
This doc is aligned with our use cases.

### Adding/Removing a dependency

This adds the dependency to the `pyproject.toml` file.

```
uv add insert-dependency-name
```

This removes the dependency from the `pyproject.toml` file.

```
uv remove insert-dependency-name
```

If you want to add a tool to the project, use:

```
uv tool install insert-tool-name
```

### Running a script

This runs a script with all the dependencies stored in the venv.
**For MacOS and Linux users, don't worry about starting a venv, this command runs the dependencies through the venv.**

```
uv run insert-script-name.py
```

### Using a tool (ruff mainly)

For this project, we are using `ruff` to format and lint the code:

To format using uv use this command *note: `uvx` is not equivalent to `uv`*

```
uvx ruff format .\path\to\file
```

To lint using uv use this command
```
uvx ruff check --fix .\path\to\file
```

### Manual locking and syncing of dependencies (not necessary)

#### Example Scenario

When you are pushing to the repo if you run into a merge conflict related to the dependencies. Say both you and someone else are adding dependencies, the `pyproject.toml` file will **NEED** to be corrected to reflect the correct dependency list. This also means there will be a conflict in the `uv.lock` file. The `uv.lock` file is updated using the commands in this section.

But typically, UV automatically locks and syncs dependencies. But if for whatever reason you need to:

```
uv lock
```

or for a specific dependency:

```
uv lock insert-dependency-name
```

and sync:

```
uv sync
```

or for a specific dependency:

```
uv sync insert-dependency-name
```
