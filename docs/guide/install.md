# Install & Update

Chenin is a single command-line tool that also launches the app. Installing it takes two
steps: install `uv`, then install Chenin with it.

## 1. Install uv

`uv` is the Python installer Chenin uses. It also installs Python itself, so you do not
need Python beforehand.

**Windows** — open PowerShell (Start menu, type "PowerShell") and paste:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux** — open a terminal and paste:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then **close the terminal and open a new one** — the installer changes your `PATH`, and
the change only applies to new terminals. Check it worked:

```sh
uv --version
```

If that prints a version number, you are done with this step.

## 2. Install Git

Chenin is fetched from GitHub, and `uv` uses Git to do it. On macOS and most Linux
installs it is already there — check with `git --version`. On Windows, install it from
[git-scm.com/download/win](https://git-scm.com/download/win) and accept the defaults.

## 3. Install Chenin

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git
```

Check it worked:

```sh
chenin --help
```

To install a specific branch instead of the released one — for instance to try features
that are not merged yet:

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git@dev
```

## 4. Launch the app

```sh
chenin app
```

Your browser opens on `http://localhost:8501`. Leave the terminal window open — closing it
stops the app. Press `Ctrl+C` in the terminal when you are finished.

To use a different port (for instance if 8501 is already taken):

```sh
chenin app --port 8600
```

## Updating

```sh
uv tool upgrade chenin
```

If you installed from a branch, re-run the install command with the same `@branch` suffix;
`upgrade` follows whatever you originally asked for.

## Uninstalling

```sh
uv tool uninstall chenin
```

## If you have never used a terminal

Three commands cover almost everything you will need.

| Command | What it does |
|---|---|
| `cd path/to/folder` | Move into a folder. `cd ..` goes back up one level. |
| `ls` (macOS/Linux) or `dir` (Windows) | List what is in the current folder. |
| `pwd` (macOS/Linux) or `cd` (Windows, alone) | Show which folder you are currently in. |

Paths with spaces need quotes: `cd "C:\Users\me\My Cores"`.

You can usually drag a folder from the file explorer onto the terminal window to paste its
full path.

## Running Chenin without installing it

If you have the source checked out and just want to try it:

```sh
git clone https://github.com/Ezacuak/chenin.git
cd chenin
uv sync
uv run chenin app
```

`uv sync` creates an isolated environment from the committed lockfile, so this cannot
disturb any other Python you have installed.
