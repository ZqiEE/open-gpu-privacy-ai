# Security Notes

This project is not production ready yet. The current implementation is a local MVP.

## Safe scope

The current node client executes only simulated jobs. Do not run arbitrary untrusted code on contributor machines.

## Required before public nodes

- Node authentication
- Signed task payloads
- Sandboxed execution
- Resource isolation
- Result verification beyond heuristics
- Rate limiting
- Abuse monitoring
- Transport encryption
- Persistent identity and revocation

## Privacy baseline

- Keep memory local by default
- Let users wipe memory
- Avoid storing unnecessary prompts
- Separate user identity from node identity where possible

## Non-goals

This project should not be used for evading laws, hiding illegal activity, or running unsafe compute workloads.
