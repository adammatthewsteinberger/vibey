# Runbook: multi-cloud — AWS and GCP beside Azure, all live-verified

## Goal

The deployment stage set (④–⑥) targets AWS and GCP with the same
consent-gated, spec-driven pipeline Azure has, and all three providers are
proven against real (free/cheap) tenants — including finally executing the
Azure path live, which is currently blocked only on `az login`.

## Current state (verified)

- Azure is real: `AzureClientPort` (`application/interfaces/azure.py:44`),
  ARM renderer (`infrastructure/azure/arm.py`), `AzCliClientAdapter`
  (`infrastructure/azure/az_cli.py`) with digest-bound consent re-verified
  at the mutation boundary; `vibey worker --azure {memory|az}` with an
  `az account show` preflight. Live execution has never run — needs login.
- The domain deployment model (`DeploymentSpec`, `AzureTargetScope`,
  `DeploymentConsent`, `scope_digest()`) is Azure-named but structurally
  vendor-neutral: tenant/subscription/resource-group/region map cleanly to
  account/project/region.

## Design

1. **Generalize the port, keep the wire adapters vendor-specific.**
   Rename-by-addition (never break the protected system test):
   `CloudClientPort` Protocol with `discover_environment`, `execute_plan`,
   `get_resource_status`, `delete_resource`; `AzureClientPort` remains as
   an alias. `TargetScope` grows a `provider: Literal["azure","aws","gcp"]`
   discriminant with provider-shaped scope fields; `scope_digest()` covers
   the provider so consent can never cross clouds.
2. **AWS adapter** (`infrastructure/aws/`): render `DeploymentSpec` →
   CloudFormation template (container topology → ECS on Fargate + ALB when
   ingress enabled; scale from `instances`); execute over the `aws` CLI
   (`aws cloudformation deploy`, `describe-stacks`) with the same
   `CommandExecutor` seam and consent checks as az_cli.py. Preflight:
   `aws sts get-caller-identity`.
3. **GCP adapter** (`infrastructure/gcp/`): container topology → Cloud Run
   (`gcloud run deploy` returns JSON; status via
   `gcloud run services describe`); no template indirection needed — Cloud
   Run is already declarative. Preflight: `gcloud auth print-access-token`.
4. **CLI**: `vibey worker --cloud {memory|az|aws|gcp}` (deprecating
   `--azure` with an alias); deploy interview gains a provider question
   whose default stays `azure`.
5. **Live verification harness**: `tests/live/test_cloud_live.py`, one
   parametrized case per provider, each gated on its own env
   (`VIBEY_AZURE_LIVE`, `VIBEY_AWS_LIVE`, `VIBEY_GCP_LIVE`): deploy the
   hello-world container, poll status to Succeeded/healthy, then
   consent-gated delete. Cost ceiling: smallest SKUs, teardown in
   `finally`, budget alarm on each tenant.

## Work items

1. CloudClientPort + provider-discriminated scope + digest coverage +
   parity tests (Azure alias proven byte-compatible).
2. AWS CloudFormation renderer + fixture tests.
3. AWS CLI adapter + consent + fixtures at the subprocess boundary.
4. GCP Cloud Run adapter + consent + fixtures.
5. CLI `--cloud` + preflights + bootstrap wiring.
6. Deploy interview provider question + spec provider fields.
7. Live tests ×3 + teardown proof.
8. Docs: `docs/guides/deploying.md` gains AWS/GCP sections.

## Verification

Fixture gates green; then three live runs, each producing a real resource
ID, a Succeeded status poll, and a verified teardown (post-delete
discovery shows no residue). Azure live counts as part of this workstream.

## Needs from operator

- `az login` on this machine + a subscription id.
- AWS: free-tier account, IAM user with scoped policy, `aws configure`.
- GCP: free-tier project, `gcloud auth login` + billing enabled (Cloud Run
  free tier covers the hello-world).

## Risks

- Consent replay across providers — killed by provider-in-digest.
- Cloud CLIs drift (04 watches their changelogs).
- Free-tier quotas: keep live tests serialized, one resource at a time.
