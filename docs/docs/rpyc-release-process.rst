RPyC Release Process
====================

A walkthrough of doing a RPyC Release.

1. Ensure a clean and current build environment (i.e., ``git pull; git status``)
2. Describe commit history within ``CHANGELOG.rst`` (see `Generate Entry`_)
3. Update ``release_date`` in ``rpyc/version.py`` and bump version (`Semantic Versioning`_ and `Versioning using Hatch`_)
4. Verify changes and run ``export ver=$(python -c 'import rpyc; print(rpyc.__version__)')``, ``git add .``, and ``git push``.
5. Create an Annotated tag: ``git tag -a ${ver} -m "Updated CHANGELOG.rst and version for release ${ver}"``
6. Publish release tag: ``git push origin ${ver}``
7. Install hatch: ``pyenv exec pip install hatch``
8. Clean up any old build artifacts: ``git clean -Xf -- dist/``
9. Create a wheel package: ``pyenv exec hatch -v build``
10. Upload the wheel package: ``pyenv exec hatch -v publish --user=__token__ --auth=${pypi_token} ; history -c && history -w``
11. Create new release such that the notes are from `CHANGELOG.rst` entry (``%s/`#/#/g`` and ``%s/`_//g``)
12. Make sure to add the wheel as an attachment to the release and you are done!

.. _Semantic Versioning: https://semver.org/
.. _Versioning using Hatch: https://hatch.pypa.io/latest/version/
.. _Build using Hatch: https://hatch.pypa.io/latest/build/
.. _Publishing to PyPi using Hatch: https://hatch.pypa.io/latest/build/


.. _Generate Entry:

Generate CHANGELOG.rst Entry
---------------------------------
To create an initial entry draft, run some shell commands.

.. code-block:: bash

    owner="tomerfiliba-org"
    repo="rpyc"
    #url="https://github.com/${owner}/${repo}"
    revisions="$(git rev-list $(pyenv exec hatch version)..HEAD | sed -z 's/\(.*\)\n/\1/;s/\n/|/g')"
    numbers=( $(git log $(pyenv exec hatch version)..HEAD --no-merges --oneline | sed -nE 's/^.*#([0-9]+).*/\1/p' | sort -nu) )
    issue_numbers="$(echo "${numbers[@]}" | sed 's/ /|/g')"
    #
    api_filter() { 
        jq -rc ".[] | select( .${1} | . != null) | select(.${1} | tostring | test(\"${2}\"))" "${3}"
    }
    url="https://api.github.com/repos/${owner}/${repo}"
    params="state=closed&accept=application/vnd.github+json"
    tmp_issues="/tmp/issues.json"
    tmp_pulls="/tmp/pulls.json"
    curl "${url}/issues?${params}" > "${tmp_issues}"
    curl "${url}/pulls?${params}" > "${tmp_pulls}"
    # Pulls
    gh_numbers=( )
    bullets=( )
    url_refs=( )
    while IFS= read -r pull; do
        title="$(echo "${pull}" | jq -r .title)"
        number="$(echo "${pull}" | jq -r .number)"
        pull_url="$(echo "${pull}" | jq -r .html_url)"
        # Add GH number
        gh_numbers+=( "${number}" )
        # Add bullet
        bullets+=( "- \`#${number}\`_ ${title}" )
        # Add url ref
        url_ref=".. _#${number}: ${pull_url}"
        url_refs+=( "${url_ref}" )
    done <<< "$(api_filter "merge_commit_sha" "${revisions}" "${tmp_pulls}")"
    # Issues
    while IFS= read -r issue; do
        title="$(echo "${issue}" | jq -r .title)"
        number="$(echo "${issue}" | jq -r .number)"
        issue_url="$(echo "${issue}" | jq -r .html_url)"
        # Add bullet
        bullets+=( "- \`#${number}\`_ ${title}" )
        # Add url ref
        url_ref=".. _#${number}: ${issue_url}"
        url_refs+=( "${url_ref}" )
    done <<< "$(api_filter "number" "${issue_numbers}" "${tmp_issues}")"

    # Header
    printf '5.X.Y\n=====\n'
    printf 'Date: %s\n\n' "$(date --rfc-3339=date)"
    for bullet in "${bullets[@]}"; do
        printf '%s\n' "${bullet}"
    done
    printf '\n'
    for ref in "${url_refs[@]}"; do
        printf '%s\n' "${ref}"
    done

Once insert this entry at the top of `CHANGELOG.rst`, review what it looks like with `instant-rst`.

.. code-block:: bash

    instantRst -b chromium -p 8612 -f "CHANGELOG.rst"


Misc. References
================
- `Wheel file name convention`_

.. _Wheel file name convention: https://peps.python.org/pep-0427/#file-name-convention
