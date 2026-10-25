# Contributing

Run the tests and type checker with `tox -e 3.15,type`. Run `prek run --all-files` before pushing a pull request.

## Release notes

Add a `changelog.d/+short-name.<type>.md` fragment when a pull request changes what package users can use or observe.
Use one fragment per user-facing change. The release workflow links each fragment to its merged squash pull request.

| Type          | Changelog section | Use for                                                    |
| ------------- | ----------------- | ---------------------------------------------------------- |
| `feature`     | Added             | New capabilities and Python support additions or removals  |
| `change`      | Changes           | Changed behavior that remains available                    |
| `bugfix`      | Fixed             | Corrected behavior                                         |
| `doc`         | Documentation     | Documentation changes users need to know about             |
| `breaking`    | Breaking changes  | Changes that require users to update code or configuration |
| `security`    | Security          | Security fixes users need to act on                        |
| `performance` | Performance       | User-visible speed or resource improvements                |
| `deprecation` | Deprecated        | Supported behavior scheduled for removal                   |
| `removal`     | Removed           | Removed user-facing capabilities other than Python support |
| `packaging`   | Packaging         | Install, wheel, or distribution changes                    |

Use `skip news` for a pull request with no user-facing change. The label can be applied after the pull request opens. A
fragment still has to be valid when the label is present. Dependabot, pre-commit.ci, and repository automation receive
the label when their pull request has no fragment.

Do not write credits in fragments. The release credits come from the commit authors and `Co-authored-by` trailers, and
the prepare workflow runs `release-creator contributors` to add first-time contributors to the changelog.

Pending fragments stay in `changelog.d` until a release. The prepare workflow writes the tagged entries to
`CHANGELOG.md`; maintenance-only releases keep their version heading without a news entry. The GitHub Release uses the
same entries with unwrapped lines. The PyPI upload runs only after the notes render.

`pylock.toml` records the selectable dependency groups for supported Python versions and platforms. The weekly release
lock workflow refreshes it after a seven-day cooldown. Release jobs install the specific tool groups they need from this
lock.
