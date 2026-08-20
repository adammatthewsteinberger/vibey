# Runbook: App Store & Play Store submissions

## Goal

vibey can carry a mobile app (its own — workstream 08 — or a conducted
project's) all the way to store submission: build, sign, upload, listing
metadata, review submission, and status tracking, as a deployment-stage
target alongside the clouds.

## Design

Store submission is a new deploy topology, not a new phase: the deploy
interview gains `service_type: "mobile_store"` with store-specific spec
fields, flowing through the same spec → consent → execute → verify
pipeline (consent matters even more here — a store submission is public
and hard to retract; `scope_digest()` covers bundle id + store + track).

- `application/interfaces/store.py`: `StoreSubmissionPort` —
  `upload_build`, `set_listing`, `submit_for_review`, `get_review_status`,
  `rollout`.
- `infrastructure/appstore/`: App Store Connect API (JWT-signed with the
  operator's API key; ES256). Upload via `xcrun altool`/Transporter for
  the binary; listing + submission via the REST API. macOS runner
  required for iOS builds (this MacBook, or a mac runner in CI).
- `infrastructure/playstore/`: Google Play Developer API (service-account
  JSON); AAB upload + track assignment (`internal` → `production`),
  listing management, review status.
- Build+sign is engine work (fastlane inside the project's worktree),
  submission is adapter work — engines never hold signing keys; the
  adapters read them from the operator-provisioned keychain/secret files.
- `deploy.verify` for stores = poll review status; `deploy.recover` =
  halt rollout / remove from sale where the APIs allow.

## Work items

1. StoreSubmissionPort + in-memory fake + parity tests.
2. Spec extension: `mobile_store` topology fields (bundle id, track,
   listing text/assets refs) + digest coverage.
3. App Store Connect adapter (JWT auth, respx-fixture tests).
4. Play Developer adapter (service-account auth, fixture tests).
5. fastlane provisioning recipe in the agent-surface trees (how engine
   sessions build/sign without touching submission credentials).
6. CLI: `vibey worker --store {memory|appstore|playstore}` + preflights
   (key file exists, API reachable).
7. Live: submit workstream 08's RN app to Play **internal testing** track
   and App Store **TestFlight internal** — real uploads, no public
   release, teardown = expire the builds.

## Verification

Fixture gates green; live internal-track submissions produce real build
IDs + review states fetched back through the port. Consent digest proven
to block a submission when bundle id or track differs from what was
accepted.

## Needs from operator

- Apple Developer Program membership + App Store Connect API key
  (issuer id, key id, .p8).
- Play Console account + service-account JSON with release permission.
- Signing assets (iOS cert/profile, Android keystore) in the local
  keychain/secret store.

## Risks

- Store review timelines are days — `deploy.verify` must park-with-poll,
  never block a worker (poll job with long run_after, like probes).
- Credential blast radius: submission creds live only in adapter config,
  never in worktrees or prompts (prompt-shield + provisioning rules).
- Guideline rejections are human territory: a rejection parks with the
  review notes verbatim.
