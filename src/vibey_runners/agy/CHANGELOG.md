# Changelog

## [0.4.1](https://github.com/adammatthewsteinberger/agyloop/compare/agyloop-v0.4.0...agyloop-v0.4.1) (2026-08-20)


### Bug Fixes

* preserve executable bit when overwrite_site_packages_harness patches the stock binary ([#27](https://github.com/adammatthewsteinberger/agyloop/issues/27)) ([cf9936e](https://github.com/adammatthewsteinberger/agyloop/commit/cf9936e3d9ca39374ee15061e50f66c00c4724a4))
* prevent silent failures in CLI gateway and improve harness diagnostics ([#25](https://github.com/adammatthewsteinberger/agyloop/issues/25)) ([c3699b9](https://github.com/adammatthewsteinberger/agyloop/commit/c3699b902263534db40c5751c0cac1aab61bf1a1))


### Documentation

* engagement refresh — README, community files, metadata ([#28](https://github.com/adammatthewsteinberger/agyloop/issues/28)) ([3d19968](https://github.com/adammatthewsteinberger/agyloop/commit/3d1996839bddab3c9440bad57256c50de4d4e824))
* update links for renamed repos (vibey-bootstrap, vibey-skills, engineering-influence-skills) ([#30](https://github.com/adammatthewsteinberger/agyloop/issues/30)) ([ca4d42e](https://github.com/adammatthewsteinberger/agyloop/commit/ca4d42e6960c940ff56bba7613a3d3ddb8022c93))

## [0.4.0](https://github.com/adammatthewsteinberger/agyloop/compare/agyloop-v0.3.0...agyloop-v0.4.0) (2026-08-16)


### Features

* add antigravity sdk agent gateway ([900d042](https://github.com/adammatthewsteinberger/agyloop/commit/900d042e28d06b738dab4db33a8173dd19d49c23))
* add run resume doctor CLI ([f98acdc](https://github.com/adammatthewsteinberger/agyloop/commit/f98acdce88a62e43e1399e1c5d262ba708560ad2))
* classify gemini resource exhausted variants ([2ae0646](https://github.com/adammatthewsteinberger/agyloop/commit/2ae064697b3c806bd1adacdeddd7fd20df4f264e))
* port autonomous runner ([7ca8d7c](https://github.com/adammatthewsteinberger/agyloop/commit/7ca8d7c707088f4637c143d157488ea48e8db695))
* port domain run loop and waiting ([ee3797e](https://github.com/adammatthewsteinberger/agyloop/commit/ee3797e0a4b98cb910f16eb47807c54f2e555904))
* ship ops CLI, Vertex REST, config, and classifier fixtures ([aa7abab](https://github.com/adammatthewsteinberger/agyloop/commit/aa7abab93248bb0b33a8a845379361dbdd6edabd))
* ship ramp, savepoints, CLI gateway, REST, and docs ([866b6ca](https://github.com/adammatthewsteinberger/agyloop/commit/866b6caee7c2495d21787118c6c9971cbe107a71))
* structured completion via antigravity ([91a796e](https://github.com/adammatthewsteinberger/agyloop/commit/91a796e4035538fc18d37b185acf7bf9af0bb86a))
* wire adaptive waiting for gemini quotas ([0f6e2da](https://github.com/adammatthewsteinberger/agyloop/commit/0f6e2da4c142380eeb63512566ba352d0a78a1aa))


### Bug Fixes

* count capacity probes against the budget ledger ([9b57614](https://github.com/adammatthewsteinberger/agyloop/commit/9b57614f5bc85cf44ecb3d711893d124af992532))
* deny ask_question via OnInteractionHook ([e136971](https://github.com/adammatthewsteinberger/agyloop/commit/e13697106a4687a1410ca8c165da1fc2ebd85151))
* do not clear conversation_id on resume preflight ([3fcdca0](https://github.com/adammatthewsteinberger/agyloop/commit/3fcdca07cec86235579d4dd89c0ad6067ed13cce))
* do not treat invalid structured output as missing ([ab7e1b1](https://github.com/adammatthewsteinberger/agyloop/commit/ab7e1b1689c02d78d8e474572a0afa5611e29480))
* gateway-aware capacity probe, --run-id, interfaces/, verbosity, and capacity forecasting ([#5](https://github.com/adammatthewsteinberger/agyloop/issues/5)) ([90f4473](https://github.com/adammatthewsteinberger/agyloop/commit/90f4473de07ecb8129f64ce510d71a0d613e6f3d))
* honor GOOGLE_API_KEY on SDK and stop empty CLI continues ([2197340](https://github.com/adammatthewsteinberger/agyloop/commit/2197340cefb7c20ebb019e3b1e119236024c38cb))
* include skip-permissions warning on all unsafe refusals ([2b49aa8](https://github.com/adammatthewsteinberger/agyloop/commit/2b49aa84db504120cfd121b65ab96b9c1cfbc092))
* notify on window wait and honor no-probe in domain ([24e2418](https://github.com/adammatthewsteinberger/agyloop/commit/24e24184616e3d05c4619f84d1cbf86b711345af))
* pin empty MCP and honor strict-autonomy ([2225151](https://github.com/adammatthewsteinberger/agyloop/commit/2225151392d43a0598268f4471c7c2140cd99138))
* refuse stop and prompt on inactive runs ([11e0351](https://github.com/adammatthewsteinberger/agyloop/commit/11e035199216c1300aaa0076f4fd04cabe63dbbd))
* refuse unsafe-skip-permissions on the SDK run path ([64fc055](https://github.com/adammatthewsteinberger/agyloop/commit/64fc055c9aaca11a20a2024c4fce4009dece4c6d))
* reject malformed structured completion payloads ([265677d](https://github.com/adammatthewsteinberger/agyloop/commit/265677d61782dbf9cc3215a53068a75087b34a4a))
* resume from plan.md and degrade conversation failures ([aef5592](https://github.com/adammatthewsteinberger/agyloop/commit/aef5592f9850d7e6f6b2a3f128339ef7081c5773))
* retarget withdrawn flash-lite sidecar and fail closed on 404 ([af4e352](https://github.com/adammatthewsteinberger/agyloop/commit/af4e352941828a4c79d0e1a889062aba15191b09))
* stop outranks mixed control batches ([ffb2627](https://github.com/adammatthewsteinberger/agyloop/commit/ffb26279801487780c3e17553d9375e05b9c13b1))
* sync uv.lock with the 0.3.0 version bump ([a2c5d86](https://github.com/adammatthewsteinberger/agyloop/commit/a2c5d863fdba515d508f4ff7f9061e4ded64acb5))
* sync uv.lock with the 0.3.0 version bump ([8a34fbc](https://github.com/adammatthewsteinberger/agyloop/commit/8a34fbc2fc62095a8717b5951f1aa0cfdc39e77d))


### Documentation

* add agyloop design and implementation plans ([d7e3e9c](https://github.com/adammatthewsteinberger/agyloop/commit/d7e3e9c9fb9da2b6b8145ec3b6e2e10a8e1b8829))
* add public FOSS surface for GitHub, Pages, and PyPI ([7d00a81](https://github.com/adammatthewsteinberger/agyloop/commit/7d00a810053c45e184b1daeb5ae22ce507c8f5ce))
* defer gemini rest surface ([c46a2e5](https://github.com/adammatthewsteinberger/agyloop/commit/c46a2e5c3266570ff8c3ed5b69b422f567dbaa16))
* security and polish agyloop ([cbde1c5](https://github.com/adammatthewsteinberger/agyloop/commit/cbde1c5d476d08f53ffb5fe7338da8a0d109cbc0))

## [0.4.0](https://github.com/adammatthewsteinberger/agyloop/compare/agyloop-v0.3.0...agyloop-v0.4.0) (2026-08-16)


### Features

* add antigravity sdk agent gateway ([900d042](https://github.com/adammatthewsteinberger/agyloop/commit/900d042e28d06b738dab4db33a8173dd19d49c23))
* add run resume doctor CLI ([f98acdc](https://github.com/adammatthewsteinberger/agyloop/commit/f98acdce88a62e43e1399e1c5d262ba708560ad2))
* classify gemini resource exhausted variants ([2ae0646](https://github.com/adammatthewsteinberger/agyloop/commit/2ae064697b3c806bd1adacdeddd7fd20df4f264e))
* port autonomous runner ([7ca8d7c](https://github.com/adammatthewsteinberger/agyloop/commit/7ca8d7c707088f4637c143d157488ea48e8db695))
* port domain run loop and waiting ([ee3797e](https://github.com/adammatthewsteinberger/agyloop/commit/ee3797e0a4b98cb910f16eb47807c54f2e555904))
* ship ops CLI, Vertex REST, config, and classifier fixtures ([aa7abab](https://github.com/adammatthewsteinberger/agyloop/commit/aa7abab93248bb0b33a8a845379361dbdd6edabd))
* ship ramp, savepoints, CLI gateway, REST, and docs ([866b6ca](https://github.com/adammatthewsteinberger/agyloop/commit/866b6caee7c2495d21787118c6c9971cbe107a71))
* structured completion via antigravity ([91a796e](https://github.com/adammatthewsteinberger/agyloop/commit/91a796e4035538fc18d37b185acf7bf9af0bb86a))
* wire adaptive waiting for gemini quotas ([0f6e2da](https://github.com/adammatthewsteinberger/agyloop/commit/0f6e2da4c142380eeb63512566ba352d0a78a1aa))


### Bug Fixes

* count capacity probes against the budget ledger ([9b57614](https://github.com/adammatthewsteinberger/agyloop/commit/9b57614f5bc85cf44ecb3d711893d124af992532))
* deny ask_question via OnInteractionHook ([e136971](https://github.com/adammatthewsteinberger/agyloop/commit/e13697106a4687a1410ca8c165da1fc2ebd85151))
* do not clear conversation_id on resume preflight ([3fcdca0](https://github.com/adammatthewsteinberger/agyloop/commit/3fcdca07cec86235579d4dd89c0ad6067ed13cce))
* do not treat invalid structured output as missing ([ab7e1b1](https://github.com/adammatthewsteinberger/agyloop/commit/ab7e1b1689c02d78d8e474572a0afa5611e29480))
* gateway-aware capacity probe, --run-id, interfaces/, verbosity, and capacity forecasting ([#5](https://github.com/adammatthewsteinberger/agyloop/issues/5)) ([90f4473](https://github.com/adammatthewsteinberger/agyloop/commit/90f4473de07ecb8129f64ce510d71a0d613e6f3d))
* honor GOOGLE_API_KEY on SDK and stop empty CLI continues ([2197340](https://github.com/adammatthewsteinberger/agyloop/commit/2197340cefb7c20ebb019e3b1e119236024c38cb))
* include skip-permissions warning on all unsafe refusals ([2b49aa8](https://github.com/adammatthewsteinberger/agyloop/commit/2b49aa84db504120cfd121b65ab96b9c1cfbc092))
* notify on window wait and honor no-probe in domain ([24e2418](https://github.com/adammatthewsteinberger/agyloop/commit/24e24184616e3d05c4619f84d1cbf86b711345af))
* pin empty MCP and honor strict-autonomy ([2225151](https://github.com/adammatthewsteinberger/agyloop/commit/2225151392d43a0598268f4471c7c2140cd99138))
* refuse stop and prompt on inactive runs ([11e0351](https://github.com/adammatthewsteinberger/agyloop/commit/11e035199216c1300aaa0076f4fd04cabe63dbbd))
* refuse unsafe-skip-permissions on the SDK run path ([64fc055](https://github.com/adammatthewsteinberger/agyloop/commit/64fc055c9aaca11a20a2024c4fce4009dece4c6d))
* reject malformed structured completion payloads ([265677d](https://github.com/adammatthewsteinberger/agyloop/commit/265677d61782dbf9cc3215a53068a75087b34a4a))
* resume from plan.md and degrade conversation failures ([aef5592](https://github.com/adammatthewsteinberger/agyloop/commit/aef5592f9850d7e6f6b2a3f128339ef7081c5773))
* retarget withdrawn flash-lite sidecar and fail closed on 404 ([af4e352](https://github.com/adammatthewsteinberger/agyloop/commit/af4e352941828a4c79d0e1a889062aba15191b09))
* stop outranks mixed control batches ([ffb2627](https://github.com/adammatthewsteinberger/agyloop/commit/ffb26279801487780c3e17553d9375e05b9c13b1))
* sync uv.lock with the 0.3.0 version bump ([a2c5d86](https://github.com/adammatthewsteinberger/agyloop/commit/a2c5d863fdba515d508f4ff7f9061e4ded64acb5))
* sync uv.lock with the 0.3.0 version bump ([8a34fbc](https://github.com/adammatthewsteinberger/agyloop/commit/8a34fbc2fc62095a8717b5951f1aa0cfdc39e77d))


### Documentation

* add agyloop design and implementation plans ([d7e3e9c](https://github.com/adammatthewsteinberger/agyloop/commit/d7e3e9c9fb9da2b6b8145ec3b6e2e10a8e1b8829))
* add public FOSS surface for GitHub, Pages, and PyPI ([7d00a81](https://github.com/adammatthewsteinberger/agyloop/commit/7d00a810053c45e184b1daeb5ae22ce507c8f5ce))
* defer gemini rest surface ([c46a2e5](https://github.com/adammatthewsteinberger/agyloop/commit/c46a2e5c3266570ff8c3ed5b69b422f567dbaa16))
* security and polish agyloop ([cbde1c5](https://github.com/adammatthewsteinberger/agyloop/commit/cbde1c5d476d08f53ffb5fe7338da8a0d109cbc0))

## [0.3.0](https://github.com/adammatthewsteinberger/agyloop/compare/agyloop-v0.2.0...agyloop-v0.3.0) (2026-08-16)


### Features

* add antigravity sdk agent gateway ([900d042](https://github.com/adammatthewsteinberger/agyloop/commit/900d042e28d06b738dab4db33a8173dd19d49c23))
* add run resume doctor CLI ([f98acdc](https://github.com/adammatthewsteinberger/agyloop/commit/f98acdce88a62e43e1399e1c5d262ba708560ad2))
* classify gemini resource exhausted variants ([2ae0646](https://github.com/adammatthewsteinberger/agyloop/commit/2ae064697b3c806bd1adacdeddd7fd20df4f264e))
* port autonomous runner ([7ca8d7c](https://github.com/adammatthewsteinberger/agyloop/commit/7ca8d7c707088f4637c143d157488ea48e8db695))
* port domain run loop and waiting ([ee3797e](https://github.com/adammatthewsteinberger/agyloop/commit/ee3797e0a4b98cb910f16eb47807c54f2e555904))
* ship ops CLI, Vertex REST, config, and classifier fixtures ([aa7abab](https://github.com/adammatthewsteinberger/agyloop/commit/aa7abab93248bb0b33a8a845379361dbdd6edabd))
* ship ramp, savepoints, CLI gateway, REST, and docs ([866b6ca](https://github.com/adammatthewsteinberger/agyloop/commit/866b6caee7c2495d21787118c6c9971cbe107a71))
* structured completion via antigravity ([91a796e](https://github.com/adammatthewsteinberger/agyloop/commit/91a796e4035538fc18d37b185acf7bf9af0bb86a))
* wire adaptive waiting for gemini quotas ([0f6e2da](https://github.com/adammatthewsteinberger/agyloop/commit/0f6e2da4c142380eeb63512566ba352d0a78a1aa))


### Bug Fixes

* count capacity probes against the budget ledger ([9b57614](https://github.com/adammatthewsteinberger/agyloop/commit/9b57614f5bc85cf44ecb3d711893d124af992532))
* deny ask_question via OnInteractionHook ([e136971](https://github.com/adammatthewsteinberger/agyloop/commit/e13697106a4687a1410ca8c165da1fc2ebd85151))
* do not clear conversation_id on resume preflight ([3fcdca0](https://github.com/adammatthewsteinberger/agyloop/commit/3fcdca07cec86235579d4dd89c0ad6067ed13cce))
* do not treat invalid structured output as missing ([ab7e1b1](https://github.com/adammatthewsteinberger/agyloop/commit/ab7e1b1689c02d78d8e474572a0afa5611e29480))
* gateway-aware capacity probe, --run-id, interfaces/, verbosity, and capacity forecasting ([#5](https://github.com/adammatthewsteinberger/agyloop/issues/5)) ([90f4473](https://github.com/adammatthewsteinberger/agyloop/commit/90f4473de07ecb8129f64ce510d71a0d613e6f3d))
* honor GOOGLE_API_KEY on SDK and stop empty CLI continues ([2197340](https://github.com/adammatthewsteinberger/agyloop/commit/2197340cefb7c20ebb019e3b1e119236024c38cb))
* include skip-permissions warning on all unsafe refusals ([2b49aa8](https://github.com/adammatthewsteinberger/agyloop/commit/2b49aa84db504120cfd121b65ab96b9c1cfbc092))
* notify on window wait and honor no-probe in domain ([24e2418](https://github.com/adammatthewsteinberger/agyloop/commit/24e24184616e3d05c4619f84d1cbf86b711345af))
* pin empty MCP and honor strict-autonomy ([2225151](https://github.com/adammatthewsteinberger/agyloop/commit/2225151392d43a0598268f4471c7c2140cd99138))
* refuse stop and prompt on inactive runs ([11e0351](https://github.com/adammatthewsteinberger/agyloop/commit/11e035199216c1300aaa0076f4fd04cabe63dbbd))
* refuse unsafe-skip-permissions on the SDK run path ([64fc055](https://github.com/adammatthewsteinberger/agyloop/commit/64fc055c9aaca11a20a2024c4fce4009dece4c6d))
* reject malformed structured completion payloads ([265677d](https://github.com/adammatthewsteinberger/agyloop/commit/265677d61782dbf9cc3215a53068a75087b34a4a))
* resume from plan.md and degrade conversation failures ([aef5592](https://github.com/adammatthewsteinberger/agyloop/commit/aef5592f9850d7e6f6b2a3f128339ef7081c5773))
* retarget withdrawn flash-lite sidecar and fail closed on 404 ([af4e352](https://github.com/adammatthewsteinberger/agyloop/commit/af4e352941828a4c79d0e1a889062aba15191b09))
* stop outranks mixed control batches ([ffb2627](https://github.com/adammatthewsteinberger/agyloop/commit/ffb26279801487780c3e17553d9375e05b9c13b1))


### Documentation

* add agyloop design and implementation plans ([d7e3e9c](https://github.com/adammatthewsteinberger/agyloop/commit/d7e3e9c9fb9da2b6b8145ec3b6e2e10a8e1b8829))
* add public FOSS surface for GitHub, Pages, and PyPI ([7d00a81](https://github.com/adammatthewsteinberger/agyloop/commit/7d00a810053c45e184b1daeb5ae22ce507c8f5ce))
* defer gemini rest surface ([c46a2e5](https://github.com/adammatthewsteinberger/agyloop/commit/c46a2e5c3266570ff8c3ed5b69b422f567dbaa16))
* security and polish agyloop ([cbde1c5](https://github.com/adammatthewsteinberger/agyloop/commit/cbde1c5d476d08f53ffb5fe7338da8a0d109cbc0))

## [0.2.0](https://github.com/adammatthewsteinberger/agyloop/compare/v0.1.0...v0.2.0) (2026-08-16)


### Features

* add antigravity sdk agent gateway ([900d042](https://github.com/adammatthewsteinberger/agyloop/commit/900d042e28d06b738dab4db33a8173dd19d49c23))
* add run resume doctor CLI ([f98acdc](https://github.com/adammatthewsteinberger/agyloop/commit/f98acdce88a62e43e1399e1c5d262ba708560ad2))
* classify gemini resource exhausted variants ([2ae0646](https://github.com/adammatthewsteinberger/agyloop/commit/2ae064697b3c806bd1adacdeddd7fd20df4f264e))
* port autonomous runner ([7ca8d7c](https://github.com/adammatthewsteinberger/agyloop/commit/7ca8d7c707088f4637c143d157488ea48e8db695))
* port domain run loop and waiting ([ee3797e](https://github.com/adammatthewsteinberger/agyloop/commit/ee3797e0a4b98cb910f16eb47807c54f2e555904))
* ship ops CLI, Vertex REST, config, and classifier fixtures ([aa7abab](https://github.com/adammatthewsteinberger/agyloop/commit/aa7abab93248bb0b33a8a845379361dbdd6edabd))
* ship ramp, savepoints, CLI gateway, REST, and docs ([866b6ca](https://github.com/adammatthewsteinberger/agyloop/commit/866b6caee7c2495d21787118c6c9971cbe107a71))
* structured completion via antigravity ([91a796e](https://github.com/adammatthewsteinberger/agyloop/commit/91a796e4035538fc18d37b185acf7bf9af0bb86a))
* wire adaptive waiting for gemini quotas ([0f6e2da](https://github.com/adammatthewsteinberger/agyloop/commit/0f6e2da4c142380eeb63512566ba352d0a78a1aa))


### Bug Fixes

* count capacity probes against the budget ledger ([9b57614](https://github.com/adammatthewsteinberger/agyloop/commit/9b57614f5bc85cf44ecb3d711893d124af992532))
* deny ask_question via OnInteractionHook ([e136971](https://github.com/adammatthewsteinberger/agyloop/commit/e13697106a4687a1410ca8c165da1fc2ebd85151))
* do not clear conversation_id on resume preflight ([3fcdca0](https://github.com/adammatthewsteinberger/agyloop/commit/3fcdca07cec86235579d4dd89c0ad6067ed13cce))
* do not treat invalid structured output as missing ([ab7e1b1](https://github.com/adammatthewsteinberger/agyloop/commit/ab7e1b1689c02d78d8e474572a0afa5611e29480))
* gateway-aware capacity probe, --run-id, interfaces/, verbosity, and capacity forecasting ([#5](https://github.com/adammatthewsteinberger/agyloop/issues/5)) ([90f4473](https://github.com/adammatthewsteinberger/agyloop/commit/90f4473de07ecb8129f64ce510d71a0d613e6f3d))
* honor GOOGLE_API_KEY on SDK and stop empty CLI continues ([2197340](https://github.com/adammatthewsteinberger/agyloop/commit/2197340cefb7c20ebb019e3b1e119236024c38cb))
* include skip-permissions warning on all unsafe refusals ([2b49aa8](https://github.com/adammatthewsteinberger/agyloop/commit/2b49aa84db504120cfd121b65ab96b9c1cfbc092))
* notify on window wait and honor no-probe in domain ([24e2418](https://github.com/adammatthewsteinberger/agyloop/commit/24e24184616e3d05c4619f84d1cbf86b711345af))
* pin empty MCP and honor strict-autonomy ([2225151](https://github.com/adammatthewsteinberger/agyloop/commit/2225151392d43a0598268f4471c7c2140cd99138))
* refuse stop and prompt on inactive runs ([11e0351](https://github.com/adammatthewsteinberger/agyloop/commit/11e035199216c1300aaa0076f4fd04cabe63dbbd))
* refuse unsafe-skip-permissions on the SDK run path ([64fc055](https://github.com/adammatthewsteinberger/agyloop/commit/64fc055c9aaca11a20a2024c4fce4009dece4c6d))
* reject malformed structured completion payloads ([265677d](https://github.com/adammatthewsteinberger/agyloop/commit/265677d61782dbf9cc3215a53068a75087b34a4a))
* resume from plan.md and degrade conversation failures ([aef5592](https://github.com/adammatthewsteinberger/agyloop/commit/aef5592f9850d7e6f6b2a3f128339ef7081c5773))
* retarget withdrawn flash-lite sidecar and fail closed on 404 ([af4e352](https://github.com/adammatthewsteinberger/agyloop/commit/af4e352941828a4c79d0e1a889062aba15191b09))
* stop outranks mixed control batches ([ffb2627](https://github.com/adammatthewsteinberger/agyloop/commit/ffb26279801487780c3e17553d9375e05b9c13b1))


### Documentation

* add agyloop design and implementation plans ([d7e3e9c](https://github.com/adammatthewsteinberger/agyloop/commit/d7e3e9c9fb9da2b6b8145ec3b6e2e10a8e1b8829))
* add public FOSS surface for GitHub, Pages, and PyPI ([7d00a81](https://github.com/adammatthewsteinberger/agyloop/commit/7d00a810053c45e184b1daeb5ae22ce507c8f5ce))
* defer gemini rest surface ([c46a2e5](https://github.com/adammatthewsteinberger/agyloop/commit/c46a2e5c3266570ff8c3ed5b69b422f567dbaa16))
* security and polish agyloop ([cbde1c5](https://github.com/adammatthewsteinberger/agyloop/commit/cbde1c5d476d08f53ffb5fe7338da8a0d109cbc0))

## [0.1.0](https://github.com/adammatthewsteinberger/agyloop/releases/tag/v0.1.0) (2026-08-13)

First public release of **agyloop**: an unattended Google Antigravity /
Gemini runner that never blocks on a human and never treats billing
exhaustion as a short waitable RPM window.

### Features

- Autonomous SDK gateway (`google-antigravity`) with optional `agy` CLI adapter
- Five-member capacity classifier (ADR 0003): Available, WindowExhausted,
  TransientThrottle, CreditsExhausted, AuthenticationFailed
- Git savepoints, mid-run control, generated Gemini REST (`agyloop api`)
- Input-detection retarget off withdrawn `gemini-2.5-flash-lite`
- Fail-closed on empty turns that 404 a withdrawn model
- `run.exception` on the per-run event stream; `turn.completed.cost_usd`
  matches the labeled ledger estimate
