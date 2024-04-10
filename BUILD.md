# Building MGET

These notes are mainly intended for the MGET development team. If you just
want to install and use MGET, you do not need to build it first: check out the
[installation instructions here](README.md). But if you wish to build it
yourself, read on.

## Building on Linux

Clone the repository:

```{console}
~$ mkdir dev
~$ cd dev
~/dev$ git clone git@github.com:jjrob/MGET.git
Cloning into 'MGET'...
...
```

Create and activate a virtual environment:

```{console}
~/dev$ cd MGET
~/dev/MGET$ python3 -m venv .venv
(.venv) ~/dev/MGET$ source .venv/bin/activate
```

Install/upgrade packages the that are needed to build:

```{console}
(.venv) ~/dev/MGET$ python3 -m pip install -U pip setuptools setuptools_scm build sphinx sphinx_rtd_theme
...
```

Build:

```{console}
(.venv) ~/dev/MGET$ python3 -m build
...
```

On success, the sdist (source distribution) and wheels will appear in the
`dist` directory.

## Build warnings and errors you can safely ignore

After the sdist (source distribution) is built, wheels are built from it.
During that stage, you may see the following error one or more times.
Apparently, this is OK to ignore. See pypa/setuptools_scm#997 and
pypa/packaging-problems#742 for more information.

```{console}
ERROR setuptools_scm._file_finders.git listing git files failed - pretending there aren't any
```

You may also ignore the following warning, which appears to occur because the
source tree includes `.gitignore` but we use `MANIFEST.in` to prune it from
the distribution. The build process first excludes it from the sdist, and then
seems to complain when it can't be found when the wheels are built from the
sdist.

```{console}
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

