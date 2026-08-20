# Changelog

## [0.1.1](https://github.com/adammatthewsteinberger/vibey/compare/vibey-v0.1.0...vibey-v0.1.1) (2026-08-20)


### Features

* budget brake and escalation grants -- the last dead-end parks ([#56](https://github.com/adammatthewsteinberger/vibey/issues/56)) ([138483c](https://github.com/adammatthewsteinberger/vibey/commit/138483c430e60c7190ab9c1d132ad50352f9fe17))
* **e1:** live engine adapters, rotation wiring, full worker, two-mode harness ([#17](https://github.com/adammatthewsteinberger/vibey/issues/17)) ([3d05a8a](https://github.com/adammatthewsteinberger/vibey/commit/3d05a8ae2204fb0d50ca97010002f6edb3934862))
* make per-job engine rotation live in the worker (Phase 4) ([#41](https://github.com/adammatthewsteinberger/vibey/issues/41)) ([074d279](https://github.com/adammatthewsteinberger/vibey/commit/074d279621081f2b4b5d8545c68ce6b385dc5b0d))
* paid live worker test, and the two real-engine bugs it caught ([#44](https://github.com/adammatthewsteinberger/vibey/issues/44)) ([c3885f7](https://github.com/adammatthewsteinberger/vibey/commit/c3885f7173b8d82bd3399715f808e05f5cc700fb))
* prevent parallel-item merge conflicts and stale-finding loop-backs ([#49](https://github.com/adammatthewsteinberger/vibey/issues/49)) ([812fdd7](https://github.com/adammatthewsteinberger/vibey/commit/812fdd7930d1ad1e82e92c649a3123d22b8ff598))
* real Azure deploy path via the az CLI, behind an explicit flag ([#57](https://github.com/adammatthewsteinberger/vibey/issues/57)) ([a254f23](https://github.com/adammatthewsteinberger/vibey/commit/a254f23dca57f4f5d8fa8ef30e132d169aa98986))
* serialize concurrent integrates with a Postgres advisory lock (Phase 6) ([#43](https://github.com/adammatthewsteinberger/vibey/issues/43)) ([f9e519b](https://github.com/adammatthewsteinberger/vibey/commit/f9e519bfe87661174472e7cce1271d0519581a22))
* turn deterministic verify failures into a bounded repair loop ([#48](https://github.com/adammatthewsteinberger/vibey/issues/48)) ([f793e8b](https://github.com/adammatthewsteinberger/vibey/commit/f793e8bb46ae9c1f43f42109d5f303ff95cec857))
* verification discipline in prompts, and a race-proof conformance verdict check ([#54](https://github.com/adammatthewsteinberger/vibey/issues/54)) ([b98bf81](https://github.com/adammatthewsteinberger/vibey/commit/b98bf815cd737c44c36de4a1a94fd4a7b0014ccf))
* wire wind-down handoff into the worker (Phase 5) ([#42](https://github.com/adammatthewsteinberger/vibey/issues/42)) ([021f6d2](https://github.com/adammatthewsteinberger/vibey/commit/021f6d28c37f5a93b8b978c9f518b78a4caeef4f))
* worker phase 0 -- rotation-blocking bug fix, phase-aware ledger, queue primitives ([#37](https://github.com/adammatthewsteinberger/vibey/issues/37)) ([028cc6f](https://github.com/adammatthewsteinberger/vibey/commit/028cc6f4e45e7ce681e8c9a0be9a3bb5b9109fb0))
* worker phase 1 -- vibey worker dispatches for real through every phase handler ([#38](https://github.com/adammatthewsteinberger/vibey/issues/38)) ([92e4c1c](https://github.com/adammatthewsteinberger/vibey/commit/92e4c1c5a7258592b6b0c28aa0c1d9600a208dfc))
* worker phase 2 -- close the job chain end to end, DONE(local) reachable ([#39](https://github.com/adammatthewsteinberger/vibey/issues/39)) ([20eb081](https://github.com/adammatthewsteinberger/vibey/commit/20eb08139742deddda43ddbdf2fbc4becce06c41))
* worker phase 3 -- deployment spec/consent persistence, DONE(deployed) reachable ([#40](https://github.com/adammatthewsteinberger/vibey/issues/40)) ([f89a46d](https://github.com/adammatthewsteinberger/vibey/commit/f89a46d42360c67161431c1e05771367579f26cf))
* zero-touch answer contracts for interview and exhausted-repair gates ([#53](https://github.com/adammatthewsteinberger/vibey/issues/53)) ([4d40202](https://github.com/adammatthewsteinberger/vibey/commit/4d40202c15d3b43c315f1f440bb0ad974c853785))


### Bug Fixes

* a completed repair session resolves its finding, breaking the repair livelock ([#59](https://github.com/adammatthewsteinberger/vibey/issues/59)) ([c4ef91d](https://github.com/adammatthewsteinberger/vibey/commit/c4ef91dac043ff539958ea3027d95272e4d77b01))
* a gate command that cannot start is a failing gate, not a vibey failure ([#61](https://github.com/adammatthewsteinberger/vibey/issues/61)) ([b708c7d](https://github.com/adammatthewsteinberger/vibey/commit/b708c7d34de727a0015ea21a3634f6d922b96ccd))
* a positive rotation weight must never round down to zero ([#51](https://github.com/adammatthewsteinberger/vibey/issues/51)) ([7e3d463](https://github.com/adammatthewsteinberger/vibey/commit/7e3d463fcc3e07ca7dac5de7fa693ba75511b38f))
* bound the integrate repair loop and give repairs actionable merge instructions ([#52](https://github.com/adammatthewsteinberger/vibey/issues/52)) ([6b186cc](https://github.com/adammatthewsteinberger/vibey/commit/6b186cc08acff70937617764bc25ad9b94b1cab4))
* budget brake now reads the real spend engines write on TurnCompleted ([#58](https://github.com/adammatthewsteinberger/vibey/issues/58)) ([d3248e4](https://github.com/adammatthewsteinberger/vibey/commit/d3248e44e0c2225e226e3a6130abc61b8e548912))
* four autonomy blockers from the live demo's observability class ([#46](https://github.com/adammatthewsteinberger/vibey/issues/46)) ([39c6388](https://github.com/adammatthewsteinberger/vibey/commit/39c6388c642bcb5315146efb1d4dfa5e0c0e2688))
* implement help_text so the flags conformance check can run at all, fix two broken descriptors it found ([#33](https://github.com/adammatthewsteinberger/vibey/issues/33)) ([c923345](https://github.com/adammatthewsteinberger/vibey/commit/c923345d0d805a62b00b7378cfdd25797765d063))
* isolate engine sessions from the orchestrator's Python environment ([#47](https://github.com/adammatthewsteinberger/vibey/issues/47)) ([dc254ee](https://github.com/adammatthewsteinberger/vibey/commit/dc254ee0a77f309a3a5a394a24a7170435b0ad6b))
* map claudeloop's real event_type strings, same fabrication as agyloop's ([#32](https://github.com/adammatthewsteinberger/vibey/issues/32)) ([89ff3fc](https://github.com/adammatthewsteinberger/vibey/commit/89ff3fc132285b9636109f52c1093e01f1e878a6))
* normalize model-produced work item ids to the worktree shape ([#45](https://github.com/adammatthewsteinberger/vibey/issues/45)) ([f688918](https://github.com/adammatthewsteinberger/vibey/commit/f6889185cae4d9d8ce259054f4af5ed14397bdaf))
* only capacity Defers open circuits, and open circuits actually probe ([#50](https://github.com/adammatthewsteinberger/vibey/issues/50)) ([717c797](https://github.com/adammatthewsteinberger/vibey/commit/717c7971bd6569384c434ebfb405567fc8a26f82))
* reassert core.bare=false after land.sh removes the last worktree ([#31](https://github.com/adammatthewsteinberger/vibey/issues/31)) ([f6ae923](https://github.com/adammatthewsteinberger/vibey/commit/f6ae9231a6b7d09f81fa14a544b333f483c6e6db))
* replace codexloop/cursorloop's fabricated LOOP_EVENT_MAP entries with source-verified vocabulary ([#34](https://github.com/adammatthewsteinberger/vibey/issues/34)) ([1bac413](https://github.com/adammatthewsteinberger/vibey/commit/1bac413dfb67529ae4ff9be69a0b590594031b13))
* replace vague conformance prompt with trivially-completable task ([#23](https://github.com/adammatthewsteinberger/vibey/issues/23)) ([b21cd57](https://github.com/adammatthewsteinberger/vibey/commit/b21cd57777ba0bf78da28aefdbd19807b062121d))
* root LoopProcessAdapter run_dir under the run's own worktree, not adapter base_dir ([#21](https://github.com/adammatthewsteinberger/vibey/issues/21)) ([48fd270](https://github.com/adammatthewsteinberger/vibey/commit/48fd27023fff6eb82046ccff4acba38cbdd5841f))
* stop overriding claudeloop's --permission-mode to acceptEdits ([#12](https://github.com/adammatthewsteinberger/vibey/issues/12)) ([b383ae9](https://github.com/adammatthewsteinberger/vibey/commit/b383ae9f0f9de9c4d65070b71ecccd43e31efd9a))
* two production-blocking bugs found by a real subprocess conformance test ([#36](https://github.com/adammatthewsteinberger/vibey/issues/36)) ([9088919](https://github.com/adammatthewsteinberger/vibey/commit/9088919bd2b2970d40ae5aa7a9f738a4fb7cd1f9))


### Documentation

* fifteen expansion runbooks -- the platform buildout, dogfooded through vibey itself ([#60](https://github.com/adammatthewsteinberger/vibey/issues/60)) ([8bc4484](https://github.com/adammatthewsteinberger/vibey/commit/8bc44843e835f74ba9aefcf3344678bba42558a7))
* **provision:** refer to the marketplace by its new name, vibey-skills ([#26](https://github.com/adammatthewsteinberger/vibey/issues/26)) ([3abeeb4](https://github.com/adammatthewsteinberger/vibey/commit/3abeeb4b822a54c585104fa34b8860e491536afb))
* queue agyloop SDK harness handshake investigation (c3) ([#24](https://github.com/adammatthewsteinberger/vibey/issues/24)) ([373bdfe](https://github.com/adammatthewsteinberger/vibey/commit/373bdfe97e2008f124c7494cb7c6af26a63009e3))
* queue dogfooded investigation of the real-engine conformance timeout ([#22](https://github.com/adammatthewsteinberger/vibey/issues/22)) ([1479cc6](https://github.com/adammatthewsteinberger/vibey/commit/1479cc65f23bea7bcc16e0c99a58f66bfe8c6846))
* queue investigation of LoopProcessAdapter still failing against a healthy agyloop ([#25](https://github.com/adammatthewsteinberger/vibey/issues/25)) ([538d9ee](https://github.com/adammatthewsteinberger/vibey/commit/538d9ee596e3b5d481b382b9ab31070c6c0c24b7))
* queue loop_events.py agyloop event-type mapping fix ([#28](https://github.com/adammatthewsteinberger/vibey/issues/28)) ([e6c90f2](https://github.com/adammatthewsteinberger/vibey/commit/e6c90f20ef07de93ed15cfa099bde26484520226))
* rename e1-loop-event-map plan to match run.sh's REPO-suffix convention ([#29](https://github.com/adammatthewsteinberger/vibey/issues/29)) ([c4df145](https://github.com/adammatthewsteinberger/vibey/commit/c4df14583894e44b5cc380c182f398ab107a5ea0))
* strengthen E1 plan against premature Done declarations ([#13](https://github.com/adammatthewsteinberger/vibey/issues/13)) ([95b1e8c](https://github.com/adammatthewsteinberger/vibey/commit/95b1e8c4464005cbc0e03e4fb1fd8d47b87384d8))
* teach the runbook the zero-touch contracts ([#55](https://github.com/adammatthewsteinberger/vibey/issues/55)) ([9df8690](https://github.com/adammatthewsteinberger/vibey/commit/9df8690e793eb15548b28e0bfa67bf4ef3292ac7))
* update loop_events.py verification status now that both sinks are wired ([#35](https://github.com/adammatthewsteinberger/vibey/issues/35)) ([301b3f5](https://github.com/adammatthewsteinberger/vibey/commit/301b3f53d059561240eb3cb5a8fd0b909220fbd0))

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
