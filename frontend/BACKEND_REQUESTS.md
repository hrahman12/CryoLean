# Remaining backend service gap

No new endpoint is required for the desktop product or its guided demos. The
existing PyWebView methods support catalog, checking, details, Z3 search and
comparison. A frontend input manifest suffices for reproducible scenarios.

## Genuine public verification

Vercel currently hosts the static React build. It cannot access a visitor's local
PyWebView bridge. An authenticated Python service with the same existing
`CryoLeanAPI` contract is needed before public visitors can run real Lean/Z3
checks. The frontend deliberately does not invent REST routes, upload local
databases or claim that static hosting provides this service.

A deployable service would need:

- A server-compatible Lean binary built from the pinned source/toolchain and a
  current axiom audit; preserve exact input serialization and the existing
  verdict contract.
- A read-only source catalog, per-request/session result isolation, and no
  public profile-promotion, arbitrary Lean submission or filesystem APIs.
- Authentication/access policy, strict input size and schema checks, bounded
  subprocess/solver time, request/concurrency limits, and explicit error envelopes
  with no compatibility verdict on infrastructure failure.
- Reviewed origin policy and HTTPS transport, plus explicit consent before any
  optional AI service receives experiment descriptions.
- Real integration tests of pass/fail/unknown, coupled models, stored-result
  freshness and candidate-specific Lean verification on the deployed service.

This is an external deployment architecture gap, not a reason to generate
frontend verdicts. Public preview says **Verification unavailable** when a real
bridge is absent. The local full product remains usable and tested.
