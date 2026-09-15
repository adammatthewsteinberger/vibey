# Changelog

## [0.6.1](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.6.0...claudeloop-v0.6.1) (2026-08-20)


### Miscellaneous Chores

* cut 0.6.1 -- the tz-aware wind-down fix must ship ([8a90aea](https://github.com/adammatthewsteinberger/claudeloop/commit/8a90aead5671ece34bc8e05cd3869322ef9f4682))

## [0.6.0](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.5...claudeloop-v0.6.0) (2026-08-20)


### Features

* add `claudeloop wind-down`, the soft stop ([c2c2952](https://github.com/adammatthewsteinberger/claudeloop/commit/c2c2952d2db79f974aa6ef513c9d6c0511da5236))
* add a -v/-q verbosity ladder and third-party log control ([8d11fc6](https://github.com/adammatthewsteinberger/claudeloop/commit/8d11fc668a7f709b24c21312ee7af42a2928a453))
* add capacity forecasting (measurement only, disabled by default) ([d6e4fea](https://github.com/adammatthewsteinberger/claudeloop/commit/d6e4feadb7a4656ebaca913f45342ab9ca400d7a))
* add the WindDownAndFinish decision and the handoff marker ([de0978a](https://github.com/adammatthewsteinberger/claudeloop/commit/de0978a39a7372e3b6a415f5ad6002881818e1e0))
* let the caller name a run with --run-id ([ae11738](https://github.com/adammatthewsteinberger/claudeloop/commit/ae117384abbf78813f56ebe84b4f084615051968))
* wire the wind-down path through the runner ([93de25d](https://github.com/adammatthewsteinberger/claudeloop/commit/93de25d79870f53f66a0a62cbff97503d9ecb08e))


### Bug Fixes

* **test:** use timezone.utc, not datetime.UTC, on the 3.10 floor ([caece3d](https://github.com/adammatthewsteinberger/claudeloop/commit/caece3ddb9501c43a300fc5b77d43cee193d80c3))


### Documentation

* add GEMINI.md and .agent/rules/ Antigravity surface ([#33](https://github.com/adammatthewsteinberger/claudeloop/issues/33)) ([6a14cd5](https://github.com/adammatthewsteinberger/claudeloop/commit/6a14cd58a3dc9481fa0503defd3a59ed08f41979))
* complete the public FOSS surface ([#22](https://github.com/adammatthewsteinberger/claudeloop/issues/22)) ([5344210](https://github.com/adammatthewsteinberger/claudeloop/commit/53442108da13a6e70c759404eaa72b941007eef7))
* engagement refresh — README, community files, metadata ([#34](https://github.com/adammatthewsteinberger/claudeloop/issues/34)) ([8a4a110](https://github.com/adammatthewsteinberger/claudeloop/commit/8a4a110b890ef7fb8b7238264b5758cfbe858f71))
* **readme:** engagement refresh — matched-set layout, live badges, related projects, author footer ([8a4a110](https://github.com/adammatthewsteinberger/claudeloop/commit/8a4a110b890ef7fb8b7238264b5758cfbe858f71))
* update links for renamed repos ([#35](https://github.com/adammatthewsteinberger/claudeloop/issues/35)) ([8ca82c8](https://github.com/adammatthewsteinberger/claudeloop/commit/8ca82c8238a9f376fbe3db66e6a3a3b3c1bbafe4))
* update links for renamed repos (vibey-bootstrap, vibey-skills, engineering-influence-skills) ([8ca82c8](https://github.com/adammatthewsteinberger/claudeloop/commit/8ca82c8238a9f376fbe3db66e6a3a3b3c1bbafe4))

## [0.5.5](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.4...claudeloop-v0.5.5) (2026-08-13)


### Bug Fixes

* **agent:** require error phrasing for spend-limit classification ([df00023](https://github.com/adammatthewsteinberger/claudeloop/commit/df000235c5e27055fd2de12049fd50928f03613e))

## [0.5.4](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.3...claudeloop-v0.5.4) (2026-08-13)


### Bug Fixes

* **ops:** spend-limit capacity, progress wait, savepoint messages, reset ([dc53513](https://github.com/adammatthewsteinberger/claudeloop/commit/dc53513662077a5074315fb84cb1f8ff62765117))

## [0.5.3](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.2...claudeloop-v0.5.3) (2026-08-12)


### Bug Fixes

* **ops:** skip empty savepoint commits and keep stream-ui chat full ([#16](https://github.com/adammatthewsteinberger/claudeloop/issues/16)) ([86f9849](https://github.com/adammatthewsteinberger/claudeloop/commit/86f984970441036fd2e6ecfdf80d7c0fb1c20cfa))

## [0.5.2](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.1...claudeloop-v0.5.2) (2026-08-12)


### Bug Fixes

* **agent:** resume without session_id conflict and clarify blocked_on ([#14](https://github.com/adammatthewsteinberger/claudeloop/issues/14)) ([6621be5](https://github.com/adammatthewsteinberger/claudeloop/commit/6621be5ffb7cc32b245ab096341ee93f086ee2e3))

## [0.5.1](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.5.0...claudeloop-v0.5.1) (2026-08-12)


### Bug Fixes

* **agent:** UTC-safe rate-limit waits and billing_error as credits ([678d988](https://github.com/adammatthewsteinberger/claudeloop/commit/678d988dcc51d60c70b7bc68cb640d0cfc4d243a))
* **api:** bind pagination scalars from stringified Omit unions ([b262826](https://github.com/adammatthewsteinberger/claudeloop/commit/b2628267be59429e71a6081f794ad5645da05dfa))

## [0.5.0](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.4.0...claudeloop-v0.5.0) (2026-08-12)


### Features

* **ops:** add mid-run control plane and run snapshot handoff ([83c6b77](https://github.com/adammatthewsteinberger/claudeloop/commit/83c6b7708899b27e5e30603cb77165e43c89e33b))

## [0.4.0](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.3.1...claudeloop-v0.4.0) (2026-08-10)


### Features

* **cli:** show manual-page help on root --help ([3a6a0a2](https://github.com/adammatthewsteinberger/claudeloop/commit/3a6a0a274e17d985000a01d02a994185ff8920a1))

## [0.3.1](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.3.0...claudeloop-v0.3.1) (2026-08-10)


### Bug Fixes

* **docs:** use absolute URLs in README for PyPI project page ([1a083a1](https://github.com/adammatthewsteinberger/claudeloop/commit/1a083a1087ca0ccda23414eea798110c050010c1))

## [0.3.0](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.2.1...claudeloop-v0.3.0) (2026-08-10)


### Features

* **api:** add generated Anthropic SDK REST surface (M4) ([1b0a601](https://github.com/adammatthewsteinberger/claudeloop/commit/1b0a601c6f1387fdd40982e2dc1793cdd8b61121))

## [0.2.1](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.2.0...claudeloop-v0.2.1) (2026-08-10)


### Bug Fixes

* **ci:** adopt GitHub Actions v5 for Pages and release-please ([c5f5744](https://github.com/adammatthewsteinberger/claudeloop/commit/c5f5744fc7b9f6f6d88b4a55432f51288927c828))

## [0.2.0](https://github.com/adammatthewsteinberger/claudeloop/compare/claudeloop-v0.1.0...claudeloop-v0.2.0) (2026-08-10)


### ⚠ BREAKING CHANGES

* rename package from autoclaude to claudeloop

### Features

* build M2 -- a genuinely working autonomous CLI ([feca00d](https://github.com/adammatthewsteinberger/claudeloop/commit/feca00d6955587b966b59d036d4bd041a826463f))
* FOSS release infrastructure, documentation, and Claude skills ([cd154f4](https://github.com/adammatthewsteinberger/claudeloop/commit/cd154f43d3ba9f6e21687e43f0fb02734080bf9c))
* initial autoclaude M1 domain core ([3f7417e](https://github.com/adammatthewsteinberger/claudeloop/commit/3f7417ecc15101b3c4d76a08f3bcc9df0d54c524))


### Bug Fixes

* **cli:** make help tests color-stable under Rich ([a63d9cf](https://github.com/adammatthewsteinberger/claudeloop/commit/a63d9cfad48dd230c51dfa648d3e8177cc3b54b6))
* refine agent autonomy path and sync M2 docs ([0781cc5](https://github.com/adammatthewsteinberger/claudeloop/commit/0781cc571afc96602b1e26d79fe717b96f9ec003))


### Code Refactoring

* rename package from autoclaude to claudeloop ([3a97b83](https://github.com/adammatthewsteinberger/claudeloop/commit/3a97b83007f018f88786b220e719545f955bbc60))

## Changelog

All notable changes to this project are documented in this file.

This file is maintained automatically by
[release-please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/) history — see
[`docs/contributing/release-process.md`](docs/contributing/release-process.md).
**Do not hand-edit entries below this line**; release-please will overwrite
manual changes on its next run.

<!-- release-please starts and maintains a `## [x.y.z]` section here on every release -->
