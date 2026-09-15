# Managed Git hooks

`commit-msg` normalizes nonconforming subjects to Conventional Commits and enforces
provenance trailers; `pre-push` checks source fingerprints.
`vibey-gh install` configures `core.hooksPath` and chains pre-existing local hooks rather
than discarding them. CI independently verifies committed hook files.
