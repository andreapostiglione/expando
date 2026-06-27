# Security Policy

## Supported Versions

Security fixes target the current `main` branch and the latest public release.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Email the maintainer listed on the GitHub profile or use GitHub private vulnerability
reporting if it is enabled for this repository. Include:

- affected version or commit
- reproduction steps or proof of concept
- expected impact
- relevant logs or configuration snippets with secrets removed

## Security Expectations

- Shell snippets must run only allowlisted executables and must not use shell chaining.
- Plugin and asset paths must stay inside the user's Expando config directory.
- Release appcasts must be signed with Sparkle EdDSA signatures.
- Live keyboard tests must be opt-in and isolated from normal developer machines.
