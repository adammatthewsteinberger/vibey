# Changelog

## [0.3.1](https://github.com/adammatthewsteinberger/codexloop/compare/v0.3.0...v0.3.1) (2026-08-20)


### Bug Fixes

* wire event sink into CodexExecGateway for real runs ([#30](https://github.com/adammatthewsteinberger/codexloop/issues/30)) ([a584737](https://github.com/adammatthewsteinberger/codexloop/commit/a58473720d8baaae25fcef84df2d659355d0424f))


### Documentation

* engagement refresh — README, community files, metadata ([#28](https://github.com/adammatthewsteinberger/codexloop/issues/28)) ([30a352e](https://github.com/adammatthewsteinberger/codexloop/commit/30a352e98b5e65d4b3885ff07c9ebcd655f2d4fc))
* update links for renamed repos (vibey-bootstrap, vibey-skills, engineering-influence-skills) ([#29](https://github.com/adammatthewsteinberger/codexloop/issues/29)) ([61cb571](https://github.com/adammatthewsteinberger/codexloop/commit/61cb571534e5f4b50ed25c417af147f9b584a3d5))

## [0.3.0](https://github.com/adammatthewsteinberger/codexloop/compare/v0.2.0...v0.3.0) (2026-08-16)


### Features

* add a -v/-q verbosity ladder and third-party log control ([b58dfc0](https://github.com/adammatthewsteinberger/codexloop/commit/b58dfc017ce9af34af07cb390ea9a8efd67435d3))
* add capacity forecasting (measurement only, disabled by default) ([c2a362b](https://github.com/adammatthewsteinberger/codexloop/commit/c2a362bcbd111e7f87e5fb2534eb1687e50dc42d))
* add the wind-down decision to the run loop state machine ([033b5b2](https://github.com/adammatthewsteinberger/codexloop/commit/033b5b2ecece721832f31cd08e103738c193c812))
* let the caller name a run with --run-id ([e22c2d0](https://github.com/adammatthewsteinberger/codexloop/commit/e22c2d05c03db5be84ecbbd544da418130c1023c))


### Bug Fixes

* **tests:** remove residual SHA-collision flake in savepoints test ([#20](https://github.com/adammatthewsteinberger/codexloop/issues/20)) ([b375f71](https://github.com/adammatthewsteinberger/codexloop/commit/b375f71ba5ebda62f178bdc39bb619418932dedf))

## [0.3.0](https://github.com/adammatthewsteinberger/codexloop/compare/v0.2.0...v0.3.0) (2026-08-16)


### Features

* add a -v/-q verbosity ladder and third-party log control ([b58dfc0](https://github.com/adammatthewsteinberger/codexloop/commit/b58dfc017ce9af34af07cb390ea9a8efd67435d3))
* add capacity forecasting (measurement only, disabled by default) ([c2a362b](https://github.com/adammatthewsteinberger/codexloop/commit/c2a362bcbd111e7f87e5fb2534eb1687e50dc42d))
* add the wind-down decision to the run loop state machine ([033b5b2](https://github.com/adammatthewsteinberger/codexloop/commit/033b5b2ecece721832f31cd08e103738c193c812))
* let the caller name a run with --run-id ([e22c2d0](https://github.com/adammatthewsteinberger/codexloop/commit/e22c2d05c03db5be84ecbbd544da418130c1023c))


### Bug Fixes

* **tests:** remove residual SHA-collision flake in savepoints test ([#20](https://github.com/adammatthewsteinberger/codexloop/issues/20)) ([b375f71](https://github.com/adammatthewsteinberger/codexloop/commit/b375f71ba5ebda62f178bdc39bb619418932dedf))

## [0.2.0](https://github.com/adammatthewsteinberger/codexloop/compare/v0.1.1...v0.2.0) (2026-08-14)


### Features

* add app-server rate-limit probe client ([a30ef93](https://github.com/adammatthewsteinberger/codexloop/commit/a30ef9377685ef9aea8f5096e1759b0f6293574e))
* add application ports and fakes ([33e721d](https://github.com/adammatthewsteinberger/codexloop/commit/33e721d0dab21b38c614ab71ea7c3e47a8126fb3))
* add autonomous runner and run/resume use cases ([bd36f45](https://github.com/adammatthewsteinberger/codexloop/commit/bd36f457548c5969f0fd37453c2d1ab5727d3302))
* add backoff and adaptive wait policy ([43c70c6](https://github.com/adammatthewsteinberger/codexloop/commit/43c70c68396255e10c61907497c53dd0d1c2ba63))
* add bootstrap and core CLI commands ([6b6aafc](https://github.com/adammatthewsteinberger/codexloop/commit/6b6aafc94f8d2513282389f154682b1b5a97bcee))
* add capacity value objects ([1aa3fed](https://github.com/adammatthewsteinberger/codexloop/commit/1aa3fede743d6c5db518f869d03826788c64da5b))
* add clock, logging, config, rundir, state, and lock adapters ([8f7e4ad](https://github.com/adammatthewsteinberger/codexloop/commit/8f7e4ad1aad0f9a754e7ff5777898bfe5a35c5cd))
* add codex argv builder ([42ab842](https://github.com/adammatthewsteinberger/codexloop/commit/42ab8426e676b0c6b59bb655bfc94e4a607338ba))
* add control plane, savepoints, and ops CLI ([512e03f](https://github.com/adammatthewsteinberger/codexloop/commit/512e03f24eddf226425326b992eacc4732f1bc7b))
* add ephemeral read-only exec capacity probe ([427620b](https://github.com/adammatthewsteinberger/codexloop/commit/427620bda645389caf571bcef010d269d3457093))
* add error hierarchy and OpenAI error-code taxonomy ([1bf5aa2](https://github.com/adammatthewsteinberger/codexloop/commit/1bf5aa2f2805c80aeba0f37fbe6da1dcb4a59585))
* add generated OpenAI REST CLI surface with drift gate ([53320f8](https://github.com/adammatthewsteinberger/codexloop/commit/53320f82512869b43075d6eeaf3f6fe73a06a3dd))
* add optional app-server gateway, stream UI, docs, and release scaffolding ([23bfddf](https://github.com/adammatthewsteinberger/codexloop/commit/23bfddfb169cfb37e8fe60a9a80bd7f9b644bba9))
* add plan, budget, session, profile, approval, and control types ([07a8188](https://github.com/adammatthewsteinberger/codexloop/commit/07a8188207fa6fbac5f85114d891b266b6be1bf9))
* add read-only CODEX_HOME rollout tail ([071d6ab](https://github.com/adammatthewsteinberger/codexloop/commit/071d6abe526935893d7d330909e96a308e5203b2))
* add run-loop state machine ([582144f](https://github.com/adammatthewsteinberger/codexloop/commit/582144fcd2b5d3c327f6af36c74307a9a8818966))
* add scripted system harness and test-agent gate ([68a7ebf](https://github.com/adammatthewsteinberger/codexloop/commit/68a7ebf9483013f5e7fae4ff98ff2b0f5da843f0))
* add three-layer completion evaluation ([eee2cc3](https://github.com/adammatthewsteinberger/codexloop/commit/eee2cc3a70562126c438e1a1ba842abca9aa0db6))
* classify turn signals into capacity states ([f7c4162](https://github.com/adammatthewsteinberger/codexloop/commit/f7c4162048b62f83a7b7ea3f99474605f18376ef))
* implement codexloop M1–M5 (onion runner + REST + docs) ([1dbef91](https://github.com/adammatthewsteinberger/codexloop/commit/1dbef9118097d8b8210f6a770df8c4c05956f6ce))
* parse codex exec JSONL events ([1cdc76c](https://github.com/adammatthewsteinberger/codexloop/commit/1cdc76c754f0e0f023f7dc94472be59f9776d3f5))
* supervise codex subprocess with concurrent pumps ([1c95f6e](https://github.com/adammatthewsteinberger/codexloop/commit/1c95f6e6fe628daefe0256e5ba5fb921bfd595a5))
* translate JSONL and drive codex exec gateway ([6a1842c](https://github.com/adammatthewsteinberger/codexloop/commit/6a1842c3bab3b9eb57d052b2bb8f1c45b919b69f))
* wire composite capacity probe and adaptive wait loop ([ab682b1](https://github.com/adammatthewsteinberger/codexloop/commit/ab682b16130829e3ae7a523597213c33509dec22))


### Bug Fixes

* jitter throttle waits above Retry-After ([666a4e6](https://github.com/adammatthewsteinberger/codexloop/commit/666a4e6c3d73f277946e866d33866091c225e1c8))
* only break session locks for known-dead pids ([712b0f4](https://github.com/adammatthewsteinberger/codexloop/commit/712b0f4a4b25d83ba27c0ca53d8278e6961efbd9))
* pin release-please to main ([4c974a2](https://github.com/adammatthewsteinberger/codexloop/commit/4c974a243f98d0790325929fd124c4aca72f04f7))
* pin release-please to main and Node 24 action ([cf19789](https://github.com/adammatthewsteinberger/codexloop/commit/cf19789c9ed4fc179f88ef6176f8b05859d05cb8))
* preserve remaining work across capacity-rejected turns ([d2d10c3](https://github.com/adammatthewsteinberger/codexloop/commit/d2d10c36a93084a36f48509433d9bb6865172fde))
* resolve all-digit SHA prefixes as save-point SHAs ([43cdde7](https://github.com/adammatthewsteinberger/codexloop/commit/43cdde7d5f65910c06ef6273e64987a391ce0488))
* seal onion contracts and order drain before signals ([cecf827](https://github.com/adammatthewsteinberger/codexloop/commit/cecf827e841d11df0fb34c71724415970da3ab7d))
* stabilize CI help and process-group cancel tests ([3fe2c6d](https://github.com/adammatthewsteinberger/codexloop/commit/3fe2c6d09f94adb0de528a74364a0d9d177ee77b))
* terminate fatals, apply mid-run controls, harden ops edges ([9171835](https://github.com/adammatthewsteinberger/codexloop/commit/91718359a07f5e25ffd1366c7ea8bbfba51b0a01))
* treat ControlCommand as the inbox union and wrap parse errors ([0885204](https://github.com/adammatthewsteinberger/codexloop/commit/08852040d2a48a14eb5b7b750fa5d02bb9314e4b))
* unstick version CI and keep TestPyPI on develop ([a4cf78e](https://github.com/adammatthewsteinberger/codexloop/commit/a4cf78eb32a622af03f707a5654c8da708a81f83))
* version CI + TestPyPI only from develop ([01d7695](https://github.com/adammatthewsteinberger/codexloop/commit/01d7695de87849b949ffd6e275b1f79126f9f2c6))


### Documentation

* deploy MkDocs site to GitHub Pages ([bce3384](https://github.com/adammatthewsteinberger/codexloop/commit/bce33843a1eb7f2579fea6d895b9966abcf5f11e))
* GitHub Pages MkDocs site ([e1c286b](https://github.com/adammatthewsteinberger/codexloop/commit/e1c286bef14b63f5b337548eb99bad94b917f21a))

## [0.1.1](https://github.com/adammatthewsteinberger/codexloop/compare/v0.1.0...v0.1.1) (2026-08-14)


### Bug Fixes

* pin release-please to main ([4c974a2](https://github.com/adammatthewsteinberger/codexloop/commit/4c974a243f98d0790325929fd124c4aca72f04f7))
* pin release-please to main and Node 24 action ([cf19789](https://github.com/adammatthewsteinberger/codexloop/commit/cf19789c9ed4fc179f88ef6176f8b05859d05cb8))
* unstick version CI and keep TestPyPI on develop ([a4cf78e](https://github.com/adammatthewsteinberger/codexloop/commit/a4cf78eb32a622af03f707a5654c8da708a81f83))
* version CI + TestPyPI only from develop ([01d7695](https://github.com/adammatthewsteinberger/codexloop/commit/01d7695de87849b949ffd6e275b1f79126f9f2c6))


### Documentation

* deploy MkDocs site to GitHub Pages ([bce3384](https://github.com/adammatthewsteinberger/codexloop/commit/bce33843a1eb7f2579fea6d895b9966abcf5f11e))
* GitHub Pages MkDocs site ([e1c286b](https://github.com/adammatthewsteinberger/codexloop/commit/e1c286bef14b63f5b337548eb99bad94b917f21a))

## 0.1.0 (2026-08-13)


### Features

* add app-server rate-limit probe client ([a30ef93](https://github.com/adammatthewsteinberger/codexloop/commit/a30ef9377685ef9aea8f5096e1759b0f6293574e))
* add application ports and fakes ([33e721d](https://github.com/adammatthewsteinberger/codexloop/commit/33e721d0dab21b38c614ab71ea7c3e47a8126fb3))
* add autonomous runner and run/resume use cases ([bd36f45](https://github.com/adammatthewsteinberger/codexloop/commit/bd36f457548c5969f0fd37453c2d1ab5727d3302))
* add backoff and adaptive wait policy ([43c70c6](https://github.com/adammatthewsteinberger/codexloop/commit/43c70c68396255e10c61907497c53dd0d1c2ba63))
* add bootstrap and core CLI commands ([6b6aafc](https://github.com/adammatthewsteinberger/codexloop/commit/6b6aafc94f8d2513282389f154682b1b5a97bcee))
* add capacity value objects ([1aa3fed](https://github.com/adammatthewsteinberger/codexloop/commit/1aa3fede743d6c5db518f869d03826788c64da5b))
* add clock, logging, config, rundir, state, and lock adapters ([8f7e4ad](https://github.com/adammatthewsteinberger/codexloop/commit/8f7e4ad1aad0f9a754e7ff5777898bfe5a35c5cd))
* add codex argv builder ([42ab842](https://github.com/adammatthewsteinberger/codexloop/commit/42ab8426e676b0c6b59bb655bfc94e4a607338ba))
* add control plane, savepoints, and ops CLI ([512e03f](https://github.com/adammatthewsteinberger/codexloop/commit/512e03f24eddf226425326b992eacc4732f1bc7b))
* add ephemeral read-only exec capacity probe ([427620b](https://github.com/adammatthewsteinberger/codexloop/commit/427620bda645389caf571bcef010d269d3457093))
* add error hierarchy and OpenAI error-code taxonomy ([1bf5aa2](https://github.com/adammatthewsteinberger/codexloop/commit/1bf5aa2f2805c80aeba0f37fbe6da1dcb4a59585))
* add generated OpenAI REST CLI surface with drift gate ([53320f8](https://github.com/adammatthewsteinberger/codexloop/commit/53320f82512869b43075d6eeaf3f6fe73a06a3dd))
* add optional app-server gateway, stream UI, docs, and release scaffolding ([23bfddf](https://github.com/adammatthewsteinberger/codexloop/commit/23bfddfb169cfb37e8fe60a9a80bd7f9b644bba9))
* add plan, budget, session, profile, approval, and control types ([07a8188](https://github.com/adammatthewsteinberger/codexloop/commit/07a8188207fa6fbac5f85114d891b266b6be1bf9))
* add read-only CODEX_HOME rollout tail ([071d6ab](https://github.com/adammatthewsteinberger/codexloop/commit/071d6abe526935893d7d330909e96a308e5203b2))
* add run-loop state machine ([582144f](https://github.com/adammatthewsteinberger/codexloop/commit/582144fcd2b5d3c327f6af36c74307a9a8818966))
* add scripted system harness and test-agent gate ([68a7ebf](https://github.com/adammatthewsteinberger/codexloop/commit/68a7ebf9483013f5e7fae4ff98ff2b0f5da843f0))
* add three-layer completion evaluation ([eee2cc3](https://github.com/adammatthewsteinberger/codexloop/commit/eee2cc3a70562126c438e1a1ba842abca9aa0db6))
* classify turn signals into capacity states ([f7c4162](https://github.com/adammatthewsteinberger/codexloop/commit/f7c4162048b62f83a7b7ea3f99474605f18376ef))
* implement codexloop M1–M5 (onion runner + REST + docs) ([1dbef91](https://github.com/adammatthewsteinberger/codexloop/commit/1dbef9118097d8b8210f6a770df8c4c05956f6ce))
* parse codex exec JSONL events ([1cdc76c](https://github.com/adammatthewsteinberger/codexloop/commit/1cdc76c754f0e0f023f7dc94472be59f9776d3f5))
* supervise codex subprocess with concurrent pumps ([1c95f6e](https://github.com/adammatthewsteinberger/codexloop/commit/1c95f6e6fe628daefe0256e5ba5fb921bfd595a5))
* translate JSONL and drive codex exec gateway ([6a1842c](https://github.com/adammatthewsteinberger/codexloop/commit/6a1842c3bab3b9eb57d052b2bb8f1c45b919b69f))
* wire composite capacity probe and adaptive wait loop ([ab682b1](https://github.com/adammatthewsteinberger/codexloop/commit/ab682b16130829e3ae7a523597213c33509dec22))


### Bug Fixes

* jitter throttle waits above Retry-After ([666a4e6](https://github.com/adammatthewsteinberger/codexloop/commit/666a4e6c3d73f277946e866d33866091c225e1c8))
* only break session locks for known-dead pids ([712b0f4](https://github.com/adammatthewsteinberger/codexloop/commit/712b0f4a4b25d83ba27c0ca53d8278e6961efbd9))
* preserve remaining work across capacity-rejected turns ([d2d10c3](https://github.com/adammatthewsteinberger/codexloop/commit/d2d10c36a93084a36f48509433d9bb6865172fde))
* seal onion contracts and order drain before signals ([cecf827](https://github.com/adammatthewsteinberger/codexloop/commit/cecf827e841d11df0fb34c71724415970da3ab7d))
* stabilize CI help and process-group cancel tests ([3fe2c6d](https://github.com/adammatthewsteinberger/codexloop/commit/3fe2c6d09f94adb0de528a74364a0d9d177ee77b))
* terminate fatals, apply mid-run controls, harden ops edges ([9171835](https://github.com/adammatthewsteinberger/codexloop/commit/91718359a07f5e25ffd1366c7ea8bbfba51b0a01))
* treat ControlCommand as the inbox union and wrap parse errors ([0885204](https://github.com/adammatthewsteinberger/codexloop/commit/08852040d2a48a14eb5b7b750fa5d02bb9314e4b))
