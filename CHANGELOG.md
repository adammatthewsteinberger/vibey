# Changelog

## [0.1.0](https://github.com/adammatthewsteinberger/vibey/compare/vibey-v0.1.0...vibey-v0.1.0) (2026-08-16)


### Features

* add structured logging, a -v ladder, and operator-facing errors ([53ca473](https://github.com/adammatthewsteinberger/vibey/commit/53ca473c29c7d00cb196e6d6abba5c701cf55ff2))
* **azure:** implement AzureClientPort and mutation-guarded adapter (task 10.4) ([34f43c4](https://github.com/adammatthewsteinberger/vibey/commit/34f43c470b491ee844b24ac34e0a152b009cc77d))
* **build:** agent-surface provisioning into BUILD worktrees (task 6.3) ([c3fd680](https://github.com/adammatthewsteinberger/vibey/commit/c3fd680cfe3be1714c589f43f50be43fd88018c7))
* **build:** budget check before effort escalation (task 6.7) ([8d71791](https://github.com/adammatthewsteinberger/vibey/commit/8d71791d49d825b8d876e523bfa1832f4ca13371))
* **build:** build.implement -- engine run, tail, and ledger (task 6.4) ([fa37161](https://github.com/adammatthewsteinberger/vibey/commit/fa371612c29a280a6bb62e8d9a8a7aa7bf8b5355))
* **build:** build.integrate -- merge, gate, isolate-not-rollback (task 6.8) ([c5f9759](https://github.com/adammatthewsteinberger/vibey/commit/c5f97592c27921cc27869bb22631805220c3616a))
* **build:** build.verify -- gates, criterion coverage, diff review (task 6.5) ([a18a123](https://github.com/adammatthewsteinberger/vibey/commit/a18a12311f4414a98c6e18becc6f874e52089ee8))
* **build:** BUILD→REVIEW and BUILD→DESIGN phase guards (task 6.10) ([27c13d1](https://github.com/adammatthewsteinberger/vibey/commit/27c13d171f2619672a8e82c6685599491402e2e2))
* **build:** forced rotation constraint on effort tier crossings (task 6.6) ([be47648](https://github.com/adammatthewsteinberger/vibey/commit/be47648307d5c0a8b4f54ca84976c3813ee49caa))
* **build:** parallelism limiter -- min(config, eligible×2, cpu) (task 6.9) ([b49d0df](https://github.com/adammatthewsteinberger/vibey/commit/b49d0df35d3840ac8b09bd6c10e4e9b4487eff60))
* **build:** real git worktree manager for BUILD work items (task 6.2) ([e363772](https://github.com/adammatthewsteinberger/vibey/commit/e3637723335272fc037170202bd36886d37b9fbc))
* **build:** start M6 -- build.decompose and BUILD-entry wiring (task 6.1) ([b7fa97f](https://github.com/adammatthewsteinberger/vibey/commit/b7fa97f1afa4103d45195377c5482acafe99128e))
* **cli:** implement operational cli commands (task 8.2) ([6e30e8f](https://github.com/adammatthewsteinberger/vibey/commit/6e30e8f807fc0e496d5a40874674b5a76b692fe6))
* **deploy:** add CLI/TUI surfaces for deployment commands (task 10.12) ([c3ec5b4](https://github.com/adammatthewsteinberger/vibey/commit/c3ec5b40db40a57e8a0747aa23e27f07cbb12697))
* **deploy:** add full offline delivery-to-deployment system test (task 10.13) ([4d8f3f5](https://github.com/adammatthewsteinberger/vibey/commit/4d8f3f532a71598cb5a4b3d2631666b40d8e12c8))
* **deploy:** implement deployment retry and escalation ladder (task 10.7) ([3a36710](https://github.com/adammatthewsteinberger/vibey/commit/3a3671069f083bc5d90703ca7833808138f2fed5))
* **deploy:** implement Phase 4 deploy design interview and acceptance (task 10.3) ([ec3a924](https://github.com/adammatthewsteinberger/vibey/commit/ec3a9247021fcbbfb8e88da772460a5174fe14fe))
* **deploy:** implement Phase 5 deploy execution graph handler (task 10.6) ([b6adba0](https://github.com/adammatthewsteinberger/vibey/commit/b6adba0efe0c0055e726fbde53d0563d978bce80))
* **deploy:** implement Phase 6 review demo and failure triage handlers (task 10.10) ([5dc516a](https://github.com/adammatthewsteinberger/vibey/commit/5dc516a6f648458dd4b8556b0754edcfc2162cef))
* **deploy:** implement Phase 6 review loop routing handler (task 10.11) ([3053219](https://github.com/adammatthewsteinberger/vibey/commit/305321919f5559a22d9b7537e430995af2310109))
* **deploy:** implement progressive exposure and recovery evaluation (task 10.8) ([a9d4f71](https://github.com/adammatthewsteinberger/vibey/commit/a9d4f710c8f418af1412ced4f79f8de880dde63b))
* **deploy:** implement runtime verification contract evaluation (task 10.9) ([c4f90eb](https://github.com/adammatthewsteinberger/vibey/commit/c4f90eba393f017e936d302d5161e8d48546ae85))
* **deployment:** implement DeploymentSpec, consent verification, and failure routing (task 10.2) ([032e441](https://github.com/adammatthewsteinberger/vibey/commit/032e44129e098080a8f9414f95606789fc4794ea))
* **design:** wire the DESIGN -&gt; VISUAL_DESIGN/BUILD choice gate into accept ([b1459d1](https://github.com/adammatthewsteinberger/vibey/commit/b1459d11942ee6d8a9ae62af17839aa96ffaf7cd))
* **domain:** add media-provider capability discovery and rotation (5.9/5.10) ([8293d22](https://github.com/adammatthewsteinberger/vibey/commit/8293d22baa179a0c55f4c9c7f575647b72f065c5))
* **domain:** add VISUAL_DESIGN phase and its opt-in guard (M5 task 5.6) ([8f4c1a9](https://github.com/adammatthewsteinberger/vibey/commit/8f4c1a9605da7cbbac3b4b42ff062cbbee2f222c))
* **domain:** add VisualInventory, the screen/state matrix for M5 task 5.7 ([751803f](https://github.com/adammatthewsteinberger/vibey/commit/751803f065278301c4956e3a797c728525573c11))
* **iac:** implement IaC static checks, preflight, and what-if evaluation (task 10.5) ([75fef62](https://github.com/adammatthewsteinberger/vibey/commit/75fef62e00872860e9f3f2debecc38acf975b054))
* implement M1 pure domain (phase machine, rotation, no-loss gate) ([7114e37](https://github.com/adammatthewsteinberger/vibey/commit/7114e37f21b9ee4e0aaa96c66deadc8f9ae9f369))
* implement M2 durable queue and crash-safe workers ([6cbff9b](https://github.com/adammatthewsteinberger/vibey/commit/6cbff9b2f2ef751b25d04ce9f8a92a50bd520693))
* implement M3 engine adapters and conformance suite ([0b6c1cc](https://github.com/adammatthewsteinberger/vibey/commit/0b6c1cc08700fb8bbb70aeb7630bff4991ef9c39))
* implement M4 ledger and handoff -- the no-loss critical path ([df9243f](https://github.com/adammatthewsteinberger/vibey/commit/df9243f17a47847fec2c7c1b9973a5ae95395ac3))
* **notify:** implement desktop notifications and webhook publisher (task 8.4) ([7d2988c](https://github.com/adammatthewsteinberger/vibey/commit/7d2988cb7a1f5f63ab9118bff95c897ac0256ab7))
* **observability:** implement opentelemetry and metrics exports (task 8.3) ([45de50a](https://github.com/adammatthewsteinberger/vibey/commit/45de50abb751084bbcdf21f451ea2d34761ef61b))
* **phase:** expand pure phase machine to deployment stage set (task 10.1) ([cfe7357](https://github.com/adammatthewsteinberger/vibey/commit/cfe7357a9247e68ad4e82c4085b620cbaf843496))
* **review:** implement automated findings pre-triaging (task 7.3) ([8a264ea](https://github.com/adammatthewsteinberger/vibey/commit/8a264ea3c6572651aa2ec2ae10dc2c02032df06a))
* **review:** implement deployment opt-in handoff to deploy design (task 7.8) ([31ff71f](https://github.com/adammatthewsteinberger/vibey/commit/31ff71fc0df982eb5935f8b7f339eb95dfa3a949))
* **review:** implement deployment-choice gate (task 7.7) ([ac9e697](https://github.com/adammatthewsteinberger/vibey/commit/ac9e6977e1c380b040a23ec8b4828d414f20cd9d))
* **review:** implement re-entrant design scoped to findings (task 7.6) ([c916d8c](https://github.com/adammatthewsteinberger/vibey/commit/c916d8cec0d6a2aff4599b79fb5b862a50967128))
* **review:** implement review.collect and ledger-grounded QA (task 7.2) ([b750b81](https://github.com/adammatthewsteinberger/vibey/commit/b750b816fe123035895eaf9d64b8de24121e04be))
* **review:** implement review.demo and deltas projection (task 7.1) ([b88488e](https://github.com/adammatthewsteinberger/vibey/commit/b88488ed8e93c4843fb407a66ddc95e760d05090))
* **review:** implement review.triage classification (task 7.4) ([ecff22f](https://github.com/adammatthewsteinberger/vibey/commit/ecff22fe724dacdbce27db1f7f618062230e481a))
* **review:** wire loopback routing and cycle increment (task 7.5) ([ff2dea9](https://github.com/adammatthewsteinberger/vibey/commit/ff2dea91dbfc3fa53b1666a1240f604d52a95217))
* scaffold M0 repo skeleton, onion contract, CI, and vibey.toml schema ([578421f](https://github.com/adammatthewsteinberger/vibey/commit/578421fa079bb1aa7f6c4889ab53c7a9651639df))
* **security:** implement destructive-command prevention guard (task 9.2) ([dcb8d30](https://github.com/adammatthewsteinberger/vibey/commit/dcb8d30858f02e10faf577e1978aed1068051494))
* **security:** implement hardened container isolation runtime (task 9.1) ([f59f630](https://github.com/adammatthewsteinberger/vibey/commit/f59f630295f61eff4c3b523534bd222d35942308))
* **security:** implement scope-bound mutation guard (task 9.3) ([0fb9eb8](https://github.com/adammatthewsteinberger/vibey/commit/0fb9eb87481ee67405abefe02aeed000d6034fb2))
* **security:** implement untrusted prompt defense and delimiter shielding (task 9.4) ([c7544e4](https://github.com/adammatthewsteinberger/vibey/commit/c7544e44100394596f25c575688c608ce6d76d6c))
* **tui:** implement live dashboard TUI (task 8.1) ([8bec60f](https://github.com/adammatthewsteinberger/vibey/commit/8bec60ff8e39c40f79cf51d314376bdffe52ee8b))
* **tui:** implement replay mode for watch command (task 8.5) ([cdb34dc](https://github.com/adammatthewsteinberger/vibey/commit/cdb34dc01ae3b0cde5ddd7b3ef84f0950fb5c50e))
* **visual:** close the loop -- VISUAL_DESIGN -&gt; BUILD accept/waive (task 5.13) ([508bb71](https://github.com/adammatthewsteinberger/vibey/commit/508bb717830e32c894b981379dbd44678bc5a30a))
* **visual:** wire visual.inventory/visual.plan job handlers and persistence ([6a5231c](https://github.com/adammatthewsteinberger/vibey/commit/6a5231c2d3d33a310aaba6150c160dd94d9d19c8))


### Bug Fixes

* align rotation weights with ADR-0005 ([3f63fcd](https://github.com/adammatthewsteinberger/vibey/commit/3f63fcd9d1c853dcdff16e9796e0c1e2f1e14d46))
* **cli:** repair unreachable `vibey design accept` and cover build_app() paths ([3987618](https://github.com/adammatthewsteinberger/vibey/commit/39876189a11667e915adde0a4e404b4d0604045f))
* **cli:** stabilize CliRunner terminal styling across all CLI test files ([#1](https://github.com/adammatthewsteinberger/vibey/issues/1)) ([ac76131](https://github.com/adammatthewsteinberger/vibey/commit/ac7613169d1308a49dc3325a9460a4f42ad4ba7f))


### Documentation

* add session handoff for continuing after M4 ([78d77b8](https://github.com/adammatthewsteinberger/vibey/commit/78d77b8b804a7653e6a6129bb10d30e80d0533f3))
* add the agyloop invocation, and stop hardcoding one done marker ([068940c](https://github.com/adammatthewsteinberger/vibey/commit/068940ce46bafbb266f6051a0e0b1155b005a73a))
* add the fleet program runbook ([5768382](https://github.com/adammatthewsteinberger/vibey/commit/57683820fc61d13f695ffd4dfc91356dc3c03068))
* make visual and deployment stages opt in ([329dd2b](https://github.com/adammatthewsteinberger/vibey/commit/329dd2bf82140660a367694d47b8cf77bbcf56e7))
* plan six-phase Azure deployment lifecycle ([30047f7](https://github.com/adammatthewsteinberger/vibey/commit/30047f754705e9b7d3dddac03a22c629e59ebf43))
* **security:** document threat model and security policy (task 9.5) ([a254fc1](https://github.com/adammatthewsteinberger/vibey/commit/a254fc1885285ad9cd7b98d5ff9f81ce1963ef3d))
* update README status for M7 completion and format system test ([0cf7bd3](https://github.com/adammatthewsteinberger/vibey/commit/0cf7bd3596e366929dc34e98d543e75329bcbe3c))


### Miscellaneous Chores

* cut the first vibey release ([ee841fa](https://github.com/adammatthewsteinberger/vibey/commit/ee841fa65b92e9911c8bdeb595577ebb1321d82e))
