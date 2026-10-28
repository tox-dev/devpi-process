# Security policy

devpi-process is a Python library that starts a throwaway devpi server, creates indexes on it, and uploads packages, for
use in tests. This policy says how to report a security problem and how we decide whether a report is one.

## Reporting a vulnerability

**Do not open a public issue for a security problem.** Use
[GitHub's private vulnerability reporting](https://github.com/tox-dev/devpi-process/security/advisories/new). If you do
not have a GitHub account, or you are a Tidelift subscriber, report through the
[Tidelift security contact](https://tidelift.com/security) instead; Tidelift coordinates the fix and the disclosure with
us. If neither works for you, email [gaborjbernat@gmail.com](mailto:gaborjbernat@gmail.com).

Include what the attacker controls and what they gain, the steps or a proof of concept, and the versions and platform
you tested. Write the report yourself; unreviewed tool or model output takes longer to triage.

## What to expect

Volunteers maintain devpi-process, with no on-call rotation. We aim to acknowledge a report within **5 working days**
and assess it within **15 working days**. Fixes are developed in a private fork attached to the draft advisory, ship in
a new release, and the advisory, with a CVE requested through GitHub, goes out with that release. The default embargo is
**90 days** from the report; we agree any change with the reporter. We credit reporters in the advisory under the name
they choose, or not at all. There is no bug bounty.

## Supported versions

Only the latest release receives fixes. Confirm the problem reproduces on it before reporting.

## Vulnerability or bug

A report is a vulnerability when an attacker who controls only an input that the [threat model](THREAT_MODEL.md) lists
as untrusted breaks a guarantee devpi-process makes. A report that first needs control of something the threat model
trusts, such as the test code that drives it or the devpi tools it runs, is a bug: we fix it in the open and publish no
advisory. Classify by who supplies the dangerous input, not by how bad the outcome sounds.

**In scope**

- devpi-process starting the server on an interface other than localhost when the caller passes no `start_args`.
- devpi-process running a program other than the `devpi-init`, `devpi-server` and `devpi` in the interpreter's scripts
  directory, or passing caller data to them as anything but separate arguments.
- Server data written outside the directory the caller passed.

**Out of scope**

- Using devpi-process as a production package index: it is a test helper.
- Other local users reaching the server's port or reading its command line on a shared machine (see accepted risks).
- Vulnerabilities in devpi itself; report them to [devpi](https://github.com/devpi/devpi).

If you cannot tell which side a finding falls on, report it privately and we will decide.
