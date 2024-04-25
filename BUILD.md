# Building MGET

These notes are mainly intended for the MGET development team. If you just
want to install and use MGET, you do not need to build it first: check out the
[installation instructions here](README.md). But if you wish to build it
yourself, read on.

## Building on Linux with setuptools

### Prerequisites

These instructions assume you have the following programs that are usually
already installed as part of your Linux distribution. We suggest you use
whatever was provided with your distribution unless you have a specific reason
not to:

* Git
* Python 3.9 or later
* The C compiler suitable for your version of Python, typically GCC

### Building MGET

Clone the repository. Until we have made the repository public, you may have
to first configure git with your GitHub credentials or SSH key. You can search
the github documetation for instructions on that.

```ShellSession
~$ mkdir dev
~$ cd dev
~/dev$ git clone git@github.com:jjrob/MGET.git
Cloning into 'MGET'...
...
```

Now create and activate a Python virtual environment. This assumes a supported
version of Python 3 is in your PATH. At the time of this writing, MGET
supported Python 3.9 or later.

```ShellSession
~/dev$ cd MGET
~/dev/MGET$ python3 -m venv .venv
~/dev/MGET$ source .venv/bin/activate
(.venv) ~/dev/MGET$ 
```

Install/upgrade packages the that are needed to build:

```ShellSession
(.venv) ~/dev/MGET$ python3 -m pip install -U pip setuptools setuptools_scm build sphinx sphinx_rtd_theme
...
```

Build:

```ShellSession
(.venv) ~/dev/MGET$ python3 -m build
...
```

On success, the sdist (source distribution) and wheels will appear in the
`dist` directory.

## Building on Windows with setuptools

Typically, Windows users of MGET will also be ArcGIS Pro users, in which case
they will want to use conda to install MGET from
(conda-forge)[https://conda-forge.org/] into their ArcGIS-provided copy of
Anaconda Python. For those users, you need to build MGET with conda rather thn
setuptools.

This section is for building MGET for users who want to install it from the
[Python Package Index](https://pypi.org) into a stand-alone copy of
traditional (non-Anaconda) Python that they installed themselves. In this
situation, you need to build a traditional wheel with setuptools, which they
will install using pip or a similar utility.

### Prerequisites

Before proceeding, you should make sure you have the following installed:

* A Git client that can access GitHub. [GitHub
  Desktop](https://desktop.github.com/) is probably the easiest solution if
  you don't mind working from a GUI. If you prefer the command line, we
  recommend [Git for windows](https://git-scm.com/download/win) but it may be
  more challenging to set up to access GitHub. You will likely need to install
  [PuTTY](https://putty.org/) and configure it to access GitHub over SSH using
  a public/private key pair.

* [Git for Windows](https://git-scm.com/download/win). This is necessary
  because the build process needs to use git command line tools. [GitHub
  Desktop](https://desktop.github.com/) will not work, although you may
  install it in addition to Git for Windows.

* Git for Windows must be configured to access GitHub over SSH. This used to
  require also installing a separate SSH client such as PuTTY, but with
  Windows 10 and other modern versions of windows you can use the built-in
  OpenSSH:

  * [Enable the `ssh-agent` service](https://stackoverflow.com/a/68386656),
    start it, and set it to start automatically when Windows starts. This
    service is needed by SSH during authentication but it is disabled by
    default.

  * If you do not already have an SSH key installed in your GitHub account,
    [generate one with `ssh-keygen`](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key).
    `ssh-keygen` is part of OpenSSH and should run fine on modern versions of
    Windows. You can run `ssh-keygen` and other SSH utilities from a regular
    Windows Command Prompt or PowerShell. You do not need to use Git Bash.
    After generating the key, extract the public part from the `.pub` file and
    use it to add a new SSH key in your user settings on github.com.

    * If you already have an SSH key set up in GitHub, you should not generate
      a new key. Instead, you need to find out where your existing key is
      stored (perhaps on a different machine) and copy the private key file
      into `C:\Users\<name>\.ssh`.

  * At this point, the newly-generated or copied private key should be in
    `C:\Users\<name>\.ssh`. Now add it to the `ssh-agent` with the command
    `ssh-add <path to private key file>`.

  * Now instruct Git to use Windows's copy of OpenSSH for SSH access from now
    on by running `git config --global core.sshCommand C:/Windows/System32/OpenSSH/ssh.exe`.
    This may not be necessary if you instructed the Git for Windows Installer
    to do this for you. But there's no harm in running this command anyway.

* [Python](https://www.python.org) 3.9 or later 
  * Use the "Windows installer (64-bit)" to install it
  * If you already have ArcGIS installed, be careful about accepting the
    installer's defaults. For example, you may not want to associate your
    version of Python with .py files if ArcGIS's Anaconda Python is already
    associated with them.

* The C/C++ compiler [recommended by
  Python](https://wiki.python.org/moin/WindowsCompilers) for compiling C/C++
  extension modules for Python 3.9 and later. At the time of this writing, the
  recommended compiler was Microsoft Visual C++ version 14.x. For our own
  builds, we used the most recent compiler available, version 14.3, which was
  that included with Visual Studio 2022. (We used the free Visual Studio 2022
  Community Edition.) However, it was also acceptable to use version 14.2
  which was available in the "Build Tools for Visual Studio 2019" (also free),
  which did not require installing a the full release of Visual Studio. For
  those looking to minimize installation time and complexity, that may be a
  better option than Visual Studio.

### Building MGET

> [!NOTE]
> All of the following console commands were run from the Windows Command
> Prompt. If you want to use PowerShell or Git Bash, you will have to adjust
> the commands accordingly.

First, clone the repository. If you have not configured Git to access GitHub
with SSH, please see the instructions above first.

```
C:\Users\Jason>md Documents\dev

C:\Users\Jason>cd Documents\dev

C:\Users\Jason\Documents\dev>git clone git@github.com:jjrob/MGET.git
Cloning into 'MGET'...
...
```

Assuming that completes without error, next you should create and activate a
Python virtual environment. In this example, I explicitly invoked `python.exe`
using the full path to the installation directory on my machine. You may have
installed it in a different place, or you may have your Python installation
directory in your PATH environment variable, making it unnecessary to specify
the full path to the executable.

```
C:\Users\Jason\Documents\dev>cd MGET

C:\Users\Jason\Documents\dev\MGET>C:\Python39\python.exe -m venv .venv

C:\Users\Jason\Documents\dev\MGET>.venv\Scripts\activate.bat

(.venv) C:\Users\Jason\Documents\dev\MGET>
```

> [!IMPORTANT]
> When you activated the virtual environment with `activate.bat`, it put the
> virtual environment's `Scripts` directory in the PATH. From now on, you will
> run `python.exe` without specifying a full path, so that you use the
> `python.exe` from the virtual environment. The `where` command shows that it
> will be used:

```
(.venv) C:\Users\Jason\Documents\dev\MGET>where python
C:\Users\Jason\Documents\dev\MGET\.venv\Scripts\python.exe
C:\Users\Jason\AppData\Local\Microsoft\WindowsApps\python.exe
```

Now you can proceed with installing/upgrading the packages the that are needed
to build MGET:

```
(.venv) C:\Users\Jason\Documents\dev\MGET>python -m pip install -U pip setuptools setuptools_scm build sphinx sphinx_rtd_theme
...
```

Build:

```
(.venv) C:\Users\Jason\Documents\dev\MGET>python -m build
...

## Build warnings and errors you can safely ignore

After the sdist (source distribution) is built, wheels are built from it.
During that stage, you may see the following error one or more times.
Apparently, this is OK to ignore. See pypa/setuptools_scm#997 and
pypa/packaging-problems#742 for more information.

```
ERROR setuptools_scm._file_finders.git listing git files failed - pretending there aren't any
```

You may also ignore the following warning, which appears to occur because the
source tree includes `.gitignore` but we use `MANIFEST.in` to prune it from
the distribution. The build process first excludes it from the sdist, and then
seems to complain when it can't be found when the wheels are built from the
sdist.

```
warning: no previously-included files matching '.gitignore' found anywhere in distribution
```

## Setting the version number

We do not manually write the version number into any source files. Instead, we
use [git tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging) to attach
the version number to a commit, and then rely on
[setuptools_scm](https://pypi.org/project/setuptools-scm/) to extract the
version number from the git tag and store it in the appropriate places.
We use setuptools_scm's 
[default versioning scheme](https://setuptools-scm.readthedocs.io/en/latest/usage/#default-versioning-scheme),
which guesses a unique, incremented version number based on the most recent
tag in the repository and the number of revisions since it was created. What
this is, and what you should do, depends where you are in the release cycle.

### When starting development of a new major or minor release

After making your first commit, add an 
[annotated tag](https://stackoverflow.com/questions/11514075/what-is-the-difference-between-an-annotated-and-unannotated-tag)
with the format `vX.Y.0.dev0`, where `X` and `Y` are the major and minor
version numbers, respectively, e.g.:

```
git tag -a v3.0.0.dev0 -m "Starting development of v3.0.0"
```

Note that you should still include the full three digits for the major, minor,
and patch numbers, e.g. `v3.0.0.dev0`, even if some of them are `0`. If you
now build (after you added the tag but before you have made any other
commits), setuptools-scm will set the version number to that of the tag.

### When starting the development of a patch release

In this situation, because of some clever behavior of setuptools_scm, you do
not need to do anything to maintain the version number. When setuptools_scm
examines the git history and finds that the most recent tag has the format
`vX.Y.Z` with no `.dev` on the end, it knows that was a final release and thus
assumes that the next commit will start a patch release. It automatically
increments the patch number `Z` to `Z`+1 and adds `.dev0`. So if your the most
recent tag was `v3.0.0`, the version number will become `v3.0.1.dev0`. You do
not need to manually create a tag for this to occur.

### When continuing development of a release (committing more changes)

As you commit more changes while developing a release, you also do not need to
do anything to maintain the version number. When you build, setuptools-scm
will access the git history, determine how many commits have happened since
the most recent final release, and append `.devX` to the build number, where
`X` is the number of commits you are from the most recent tag.

### After making the final commit for a release

After committing the final code change for a release, tag it with the version
number unadorned with `.devX`, like this:

```
git tag -a v3.0.0 -m "Completed development of v3.0.0"
```
Note that you should still include the full three digits for the major, minor,
and patch number, e.g. `v3.0.0`, even if some of them are `0`. As above, if
you now build (before you have made any other commits), setuptools-scm will
set the version number to that of the tag.

### Pushing tags to the origin repo

When it is time to push your changes back to the origin repo, note that by
default, `git push` does not push tags. To push the tag in addition to the
commit, use:

```
git push --follow-tags
```

If you just need to push the tag itself, e.g. because you already pushed the
committed code, you can use:

```
git push origin <tag_name>
```

If you need to delete a tag from your local repo, use `git tag -d <tag_name>`.
If you already pushed it and need to delete it from the origin repo,
[see here](https://stackoverflow.com/questions/5480258/how-can-i-delete-a-remote-tag).
If need be, you can also 
[tag an older commit](https://stackoverflow.com/questions/4404172/how-to-tag-an-older-commit-in-git).

# Building MGET's documentation

MGET uses Sphinx to automate the production of HTML documentation with the
[Read the Docs theme](https://sphinx-rtd-theme.readthedocs.io/). After
building MGET (see above), you can build the documentation like this:

## Building the documentation on Linux

Continue with the virtual environment you [created
above](#building-on-linux-with-setuptools) in order to build MGET with
setuptools. Now install the GeoEco package you just built into that virtual
environment (removing the build that's already installed, if it exists):

```ShellSession
(.venv) ~/dev/MGET$ python3 -m pip uninstall mget3       # Optional: uninstall existing build
...
(.venv) ~/dev/MGET$ python3 -m pip install dist/*.whl    # Replace *.whl with the wheel you just built
...
```

That was necessary so that Sphinx can import the GeoEco modules. Now you can
build the HTML with Sphinx:

```ShellSession
(.venv) ~/dev/MGET$ cd doc/GeoEco/
(.venv) ~/dev/MGET/doc/GeoEco$ rm -r _autodoc _build    # Optional: clean existing build of documentation
(.venv) ~/dev/MGET/doc/GeoEco$ make html
...
```

## Building the documentation on Windows 

Continue with the virtual environment you [created
above](#building-on-windows-with-setuptools) in order to build MGET with
setuptools. Now install the GeoEco package you just built into that virtual
environment (removing the build that's already installed, if it exists):

```
(.venv) C:\Users\Jason\Documents\dev\MGET>python -m pip uninstall mget3       # Optional: uninstall existing build
...
(.venv) C:\Users\Jason\Documents\dev\MGET>python -m pip install dist/*.whl    # Replace *.whl with the wheel you just built
...
```

That was necessary so that Sphinx can import the GeoEco modules. Now you can
build the HTML with Sphinx:

```
(.venv) C:\Users\Jason\Documents\dev\MGET>cd doc/GeoEco/
(.venv) C:\Users\Jason\Documents\dev\MGET\doc\GeoEco>rmdir /s/q _autodoc _build    # Optional: clean existing build of documentation
(.venv) C:\Users\Jason\Documents\dev\MGET\doc\GeoEco>make html
...

Assuming no errors occur, the root page of the documentation will be
`_build\html\Index.html`.
