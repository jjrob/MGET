Releasing MGET
==============

This page contains notes on setting MGET's version number and the steps for
issuing a new MGET release.


Setting the version number
--------------------------

We do not manually write the version number into any source files. Instead, we
use `git tags <https://git-scm.com/book/en/v2/Git-Basics-Tagging>`__ to attach
the version number to a commit, and then rely on `setuptools_scm
<https://pypi.org/project/setuptools-scm/>`__ to extract the version number
from the git tag and store it in the appropriate places. We use
setuptools_scm's `default versioning scheme
<https://setuptools-scm.readthedocs.io/en/latest/usage/#default-versioning-scheme>`__
which guesses a unique, incremented version number based on the most recent
tag in the repository and the number of revisions since it was created. What
this is, and what you should do, depends where you are in the release cycle.

When starting development of a new major or minor release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After making your first commit, add an `annotated tag
<https://stackoverflow.com/questions/11514075/what-is-the-difference-between-an-annotated-and-unannotated-tag>`__
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
<https://stackoverflow.com/questions/5480258/how-can-i-delete-a-remote-tag>`__.
If need be, you can also `tag an older commit
<https://stackoverflow.com/questions/4404172/how-to-tag-an-older-commit-in-git>`__.


Steps to issue a new release of MGET
------------------------------------

Step 1: Manually build and test on Linux and Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Be especially sure to test on Windows with ArcGIS Pro. Currently our automated
tests on GitHub do not install ArcGIS, so the only way the ArcGIS-dependent
parts of MGET get tested is when it is done manually. All tests should pass on
both platforms. After you are done, you should be confident that no additional
commits to code will occur. (If you do discover a problem in a subsequent
step, don't worry, you can still correct it.)

Step 2: Manually build the documentation and check it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pay extra attention to any new functions or those with changed metadata.

Step 3: Update RELEASE_NOTES.md
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Insure RELEASE_NOTES.md has all of the bullet points needed for the release.
Update the release's header line to include the a link to the soon-to-be
created tag and the date, similar to this::

    ## [v3.1.0](https://github.com/jjrob/MGET/releases/tag/v3.1.0) - 2024-10-10

Commit and push your changes.

Step 4: Tag the release 
~~~~~~~~~~~~~~~~~~~~~~~

As described in the previous section, create a tag with the version number
unadorned with ``.devX``, like this::

    git tag -a v3.1.0 -m "Completed development of v3.1.0"

If you neglected to push the RELEASE_NOTES.md commit above yet, push it and
the tag like this::

    git push --follow-tags

If you just need to push the tag, do it like this::

    git push origin <tag_name>

Step 5: Run the "Build and test wheels" GitHub Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manually run the `Build and test wheels
<https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml>`__ GitHub
Action. After it completes, it will trigger the `Test data products
<https://github.com/jjrob/MGET/actions/workflows/test-data-products.yml>`__
Action. Make sure these Actions complete successfully. If any fail and you
need to make additional code changes, delete the tag from your local repo
(``git tag -d <tag_name>``) and also from the remote origin repo (``git push
-d origin <tag_name>``) and start over from Step 1.

For extra safety, to ensure the wheels produced by the GitHub Action are good,
you can download their artifacts containing the wheels and perform additional
testing, as desired. This is particularly useful to do on Windows with ArcGIS
Pro, as we do not yet have ArcGIS integrated into the `Build and test wheels
<https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml>`__ Action.

Step 6: Run the "Publish to PyPI" GitHub Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manually run the `Publish to PyPI
<https://github.com/jjrob/MGET/actions/workflows/publish-to-pypi.yml>`__
GitHub Action. This will require you to obtain the `run_id` of the successful
run of the `Build and test wheels
<https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml>`__ Action
above and input as a parameter. Publish to PyPI will obtain the artifacts from
that successful run and publish them to http://pypi.org/project/mget3.

.. important::
    After triggering Publish to PyPI to run, as an additional step, you'll
    also need to approve the workflow run before it will actually execute.
    This is to prevent anyone other than the MGET repo owners from triggering
    this action or accessing the security token needed to perform it.

Step 7: Create the GitHub Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to https://github.com/jjrob/MGET/releases and click *Draft a new
   release*.

2. Select the appropriate tag from the drop-down, e.g. ``v3.1.0``.

3. For *Release title*, put the version number including the "v", e.g.
   ``v3.1.0``.

4. For *Describe this release*, paste in the text::

       For details, please check the [Release Notes](https://github.com/jjrob/MGET/blob/main/RELEASE_NOTES.md).

5. Download the Linux and Windows assets of the successful `Build and test
   wheels
   <https://github.com/jjrob/MGET/actions/workflows/build-wheels.yml>`__
   Action above and decompress them into a directory. You do not need to
   download the sdist asset.

6. Attach (upload) the ``.whl`` files to the release. At the time of this
   writing, at which we only built MGET for Linux and Windows for the x86-64
   platform, there were three ``.whl`` files per version of Python that was
   supported (two for Linux, one for Windows).

7. Click *Publish release*.

Step 8: Update the PyPI version gist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update `this gist's JSON
<https://gist.github.com/jjrob/bcc799a93aa3adcf1d234cb1eae659fb>`__ with the
proper version number. This JSON drives the version PyPI version number badge
in README.md. If the supported Python versions or platforms changed, also
update those gists.

Step 9: Check Read the Docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Read the Docs <https://readthedocs.org/projects/mget/>`__ should
automatically rebuild MGET's documentation when a new release is published on
GitHub and update the `"stable" docs
<https://mget.readthedocs.io/en/stable/>`__ to that latest release. Check that
this has happened. If there are problems that require a code change to fix,
even just to the documentation files, you will have to increment MGET's
version number and create a completely new release starting from Step 1.

Step 10: Update the conda-forge build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
    This section still needs to be written.
