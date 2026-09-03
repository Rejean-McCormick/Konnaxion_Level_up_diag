# Konnaxion diagnostic sequences

The order below is part of the diagnostic contract. All Konnaxion campaigns use `execution: sequential`.

| Campaign | Ordered levels |
|---|---|
| source-audit | N00 → N01 → N04 → N11 |
| auth-debug | N00 → N02 → N03 → N04 → N05 → N11 |
| connection-debug | N00 → N01 → N02 → N03 → N04 → N05 → N06 → N11 |
| full-local | N00 → N01 → N02 → N03 → N04 → N05 → N06 → N07 → N10 → N11 |
| backend | N00 → N01 → N02 → N04 → N06 → N11 |
| frontend | N00 → N01 → N03 → N04 → N05 → N11 |
| local-runtime | N00 → N02 → N03 → N04 → N05 → N06 → N11 |
| capsule-local | N00 → N07 → N08 → N11 |
| deployed | N00 → N07 → N08 → N09 → N11 |
| deep | N00 → N01 → N02 → N03 → N04 → N05 → N06 → N07 → N08 → N10 → N11 |
| full | N00 → N01 → N02 → N03 → N04 → N05 → N06 → N07 → N08 → N09 → N10 → N11 |

The recommended escalation sequence is:

`source-audit → auth-debug → connection-debug → full-local`

N11 is intentionally last. It reads only the current campaign's expected levels from the session created by N00.
