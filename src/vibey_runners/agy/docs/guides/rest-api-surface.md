# Generated REST surface

`agyloop api` is a 1:1 Click tree over the committed Gemini **Developer**
discovery document (ADR 0015). It is not a hand-written subset.

```bash
agyloop api --help
agyloop api models generate-content --json '{"model":"models/gemini-2.5-pro","contents":[]}'
agyloop api --lane vertex projects locations publishers models generate-content \
  --json '{"model":"projects/PROJECT/locations/us-central1/publishers/google/models/gemini-2.5-flash"}'
```

Developer invokes use HTTPS + `GOOGLE_API_KEY`. `--lane vertex` uses the
committed Gemini subset of `aiplatform:v1` (33 methods, revision `20260801`)
and `GOOGLE_ACCESS_TOKEN`. The drift gate compares each lane's committed
baseline to the registered command paths. OpenAPI lists 91 operations at the
same Developer revision; that mismatch is recorded so the binder stays on
discovery document A.

Regenerate `src/agyloop/infrastructure/api/surface_baseline.json` from
`https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`
when Google revises the inventory.

ADR 0006 recorded why this was originally deferred. ADR 0015 records the
operator override and the gate.
