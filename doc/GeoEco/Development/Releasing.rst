Releasing MGET
==============

.. Note:: 
    This page still need to be fleshed out. While we are still getting the
    project up and running on GitHub, we plan to release MGET manually. This
    includes uploading the wheels to `PyPI <https://pypi.org/>`_ and uploading
    the docuemtation to `Read the Docs <https://docs.readthedocs.io/>`_. As
    development progresses, we aim to automate these procedures with GitHub's
    automation features. We're holding off from documenting all of this while
    it is still in flux.

Setting the version number
--------------------------

.. Note:: 
    This section needs to be reviewed, especially after we sort out automated
    builds on GitHub.

We do not manually write the version number into any source files. Instead, we
use `git tags <https://git-scm.com/book/en/v2/Git-Basics-Tagging>`_ to attach
the version number to a commit, and then rely on `setuptools_scm
<https://pypi.org/project/setuptools-scm/>`_ to extract the version number
from the git tag and store it in the appropriate places. We use
setuptools_scm's `default versioning scheme
<https://setuptools-scm.readthedocs.io/en/latest/usage/#default-versioning-scheme>`_
which guesses a unique, incremented version number based on the most recent
tag in the repository and the number of revisions since it was created. What
this is, and what you should do, depends where you are in the release cycle.

When starting development of a new major or minor release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After making your first commit, add an `annotated tag
<https://stackoverflow.com/questions/11514075/what-is-the-difference-between-an-annotated-and-unannotated-tag>`_
with the format ``vX.Y.0.dev0``, where ``X`` and ``Y`` are the major and minor
version numbers, respectively, e.g.::

    git tag -a v3.0.0.dev0 -m "Starting development of v3.0.0"

Note that you should still include the full three digits for the major, minor,
and patch numbers, e.g. ``v3.0.0.dev0``, even if some of them are ``0``. If
you now build (after you added the tag but before you have made any other
commits), setuptools-scm will set the version number to that of the tag.

When starting the development of a patch release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this situation, because of some clever behavior of setuptools_scm, you do
not need to do anything to maintain the version number. When setuptools_scm
examines the git history and finds that the most recent tag has the format
``vX.Y.Z`` with no ``.dev`` on the end, it knows that was a final release and
thus assumes that the next commit will start a patch release. It automatically
increments the patch number ``Z`` to ``Z``+1 and adds ``.dev0``. So if your
the most recent tag was ``v3.0.0``, the version number will become
``v3.0.1.dev0``. You do not need to manually create a tag for this to occur.

When continuing development of a release (committing more changes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As you commit more changes while developing a release, you also do not need to
do anything to maintain the version number. When you build, setuptools-scm
will access the git history, determine how many commits have happened since
the most recent final release, and append ``.devX`` to the build number, where
``X`` is the number of commits you are from the most recent tag.

After making the final commit for a release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After committing the final code change for a release, tag it with the version
number unadorned with ``.devX``, like this::

    git tag -a v3.0.0 -m "Completed development of v3.0.0"

Note that you should still include the full three digits for the major, minor,
and patch number, e.g. ``v3.0.0``, even if some of them are ``0``. As above,
if you now build (before you have made any other commits), setuptools-scm will
set the version number to that of the tag.

Pushing tags to the origin repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When it is time to push your changes back to the origin repo, note that by
default, ``git push`` does not push tags. To push the tag in addition to the
commit, use::

    git push --follow-tags

If you just need to push the tag itself, e.g. because you already pushed the
committed code, you can use::

    git push origin <tag_name>

If you need to delete a tag from your local repo, use ``git tag -d <tag_name>``.
If you already pushed it and need to delete it from the origin repo, `see here
<https://stackoverflow.com/questions/5480258/how-can-i-delete-a-remote-tag>`_.
If need be, you can also `tag an older commit
<https://stackoverflow.com/questions/4404172/how-to-tag-an-older-commit-in-git>`_.
