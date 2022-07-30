RPyC Release Process
====================

A walkthrough of doing a RPyC Release.

1.
2. Describe commit history within `CHANGELOG.rst` (see `Generate Entry`_)
3. Update `version` and `release_date` values for `rpyc/version.py` (`Semantic Versioning`_)
4. Review `git status`, commit changes, and `git push`.
5. Create an Annotated tag: `git tag -a 5.X.Y -m "Updated CHANGELOG.rst and version for release 5.X.Y"`
6. Publish release tag: `git push origin 5.X.Y`

7. Clean up any old build artifacts: `pyenv exec python setup.py clean --all`
8. Create a wheel package: `pyenv exec python setup.py bdist_wheel`
9. Upload the wheel package: `twine upload --repository-url https://upload.pypi.org/legacy/ dist/rpyc-*-any.whl`
10. Create new release such that the notes are from `CHANGELOG.rst` entry.

.. _Semantic Versioning: https://semver.org/

.. _Generate Entry:

Generate CHANGELOG.rst Entry
---------------------------------
To create an initial entry draft, run some shell commands.

.. code-block:: bash

    last_release="1/12/2021"
    log_since="$(git log --since="${last_release}" --merges --oneline)"
    pulls=( $(echo "${log_since}" | sed -n 's/^.*request #\([0-9]*\) from .*$/\1/p') )
    url="https://github.com/tomerfiliba-org/rpyc/pull/"
    printf '5.X.Y\n=====\n'
    printf 'Date: %s\n\n' "$(date --rfc-3339=date)"
    for pull in ${pulls[@]}; do
        printf -- '- `#%d`_\n' "${pull}"
    done
    printf '\n'
    for pull in ${pulls[@]}; do
        printf '.. _#%d: %s%d\n' "${pull}" "${url}" "${pull}"
    done

Once insert this entry at the top of `CHANGELOG.rst`, review what it looks like with `instant-rst`.

.. code-block:: bash

    instantRst -b chromium -p 8612 -f "CHANGELOG.rst"


