# Reporting issues

Include the following information:

- python version
- operating system
- *minimal* reproducing example, both server and client

Formatting rules:

- put \`backticks\` around function names, in particular for magic methods such as __call__... oops, I mean `__call__`
- put [code fences](1) (\```CODE\```) around log text, stack traces, or exceptions
- make use of [github flavoured markdown](2) to structure your post
- **do not attach zip files** if at all possible.

There are several reasons for the last point:

- zipped code is not visible email notifications, nor when looking directly at the issue in the web interfaces. It requires first downloading and extracting the code into a suitable folder and then alt-tabbing between issue and code (or switching workspaces). This is very annoying and will drastically reduce your chances of getting a response.
- if the code is too much to be included in the issue body, this is probably a sign that you didn't sufficiently try to create a *minimal* example anyway.
- inline code can be searched from the web and quickly looked at by others to check whether they have a related problem
- inline code is trivial during an issue migration/backup and doesn't impose the extra complexity that attached files have


# Contributing code

In your pull request,

- reference previous related issues and/or pull-requests
- make use [closing keywords](3), such as  e.g. "Resolves #XYZ" or "Closes #XYZ"
- if there was no previous issue, please include a clear problem description
- include a test case

Coding style:

- adhere to [PEP8](4) and [PEP257](5) (I know, this has not been followed so far, but I would like it for new code)

Commits:

- commits should be reversible, independent units
- use descriptive titles
- add an explaining commit message unless the modification is trivial
- commit summaries are sentences that start with a capitalized verb and don't end with a dot, e.g. "Add feature XYZ"
- see also: [A Note About Git Commit Messages](6).


[1]: https://help.github.com/articles/creating-and-highlighting-code-blocks/
[2]: https://help.github.com/articles/basic-writing-and-formatting-syntax/
[3]: https://help.github.com/articles/closing-issues-using-keywords/
[4]: https://www.python.org/dev/peps/pep-0008/
[5]: https://www.python.org/dev/peps/pep-0257/
[6]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
