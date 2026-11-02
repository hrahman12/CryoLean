# Validation report — 2026-11-01

| Check | Result |
|---|---|
| Full Python regression suite | 111 passed in 314.07 s |
| Frontend contracts and reducer tests | 25 passed |
| Production PyWebView integration | 11 checks passed |
| Anonymous hosted smoke tests | 7 checks passed |
| TypeScript / production Vite build | Passed |
| Linux Lean build / selftest | Passed |
| Linux kernel axiom audit | 48 theorems, standard axioms only |
| Featured coverage matrix | 180 actual Lean evaluations: 113 PASS, 66 FAIL, 1 UNKNOWN |

The full Python run includes existing Lean regression/build tests. The new six
repair tests exercise the real checker, exact candidate hash matching,
unchanged requirements, UNKNOWN exclusion, cross-result/tampering refusal,
stale-catalog rejection, signed receipt restoration and the HTTP transport.

The production desktop test checks automatic repair search, a real recheck,
preservation of the original failure, stale-result invalidation, all four
recorded workflows, live/recorded state separation, and equipment family changes.

The hosted tests run anonymously against the public alias: real PASS, FAIL and
UNKNOWN; the 50 -> 39 flux-line repair with identical verified input hash;
current Linux theorem audit; /api/check; and four available recordings.

Browser QA separately exercised the live repair loop, recorded B's repair,
A's FAIL/UNKNOWN, C's two/three-arm comparison, D's 23-hour schedule and return to
an unchanged live setup. Responsive and WebGL checks are recorded with the
final delivery artifacts; models are illustrative, not dimensional CAD.

Generated local logs: frontend/test-results/python.xml, desktop.json, hosted.json.
The website exposes four existing computed scientific figures with original
data, methodology, captions, units and source notes. They were packaged from
paper/; no missing dimensions or timing measurements were fabricated.
Fresh full-grid run: 44,880 actual Lean evaluations in 38 s (8 workers): 3,118 PASS, 30,299 FAIL, 11,463 UNKNOWN. Recorded CSV and provenance are published under /coverage/.
Final production browser checks: desktop, 820 px tablet and 390 px mobile had no horizontal overflow; both Spin controls responded; no production runtime errors. Screenshot: frontend/test-results/live-repair.jpg. Final desktop integration rerun: all 11 checks passed.
