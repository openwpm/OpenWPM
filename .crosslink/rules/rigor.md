## Reasons

The code you are producing is production grade code in sensitive systems where people's jobs and human safety might be on the line. You must treat it with the rigor and respect it deserves.

## Implementation Rigor (MANDATORY — Priority 2: Correctness)

Every implementation you produce must be complete, correct, and production-ready. These standards apply to all code, all languages, all tasks.

### Complete implementations

Every function body must contain a working implementation. Use `todo!()`, `unimplemented!()`, `pass`, `...`, or empty bodies only when raising a tracked issue for later completion (`raise NotImplementedError("Reason — see issue #N")`). Stub code without a tracked issue is incomplete work.

### Own your warnings

You are the only one writing code. When `cargo check`, `cargo clippy`, `npm run lint`, `tsc`, or any other tool produces warnings after your changes, those warnings are yours. You introduced them — either in this change or a previous iteration within the same session. Fix them before considering the task done. Run the linter after every change, not just at the end.

### Choose correctness over convenience

When you know the correct approach and a simpler-but-wrong alternative, implement the correct one. "Good enough for now" is acceptable only when the correct approach is genuinely out of scope and you document why with a crosslink comment (`--kind decision`).

### Cryptographic correctness

When implementing cryptography or security-sensitive code:
- Generate fresh nonces, IVs, and salts for every operation using a cryptographic RNG (`OsRng`, `getrandom`, `crypto.getRandomValues`)
- Use well-audited libraries (`ring`, RustCrypto, `libsodium`, Web Crypto API) and follow their documented patterns exactly
- Authenticate all ciphertext (use AEAD modes like AES-GCM or ChaCha20-Poly1305)
- Use current algorithms: AES-256-GCM, Ed25519, X25519, SHA-256/SHA-3, Argon2id for password hashing
- Implement the real thing — simulations and mockups are not acceptable when real cryptography is requested

### Error handling discipline

- Propagate errors to the appropriate handling level. Use `?`, `Result`, `try/catch` — the language's native error mechanism.
- When suppressing an error intentionally (`let _ = ...`), add a comment explaining why it's safe. Mark it with `// INTENTIONAL:` so reviewers know it was deliberate.
- Use typed, domain-specific errors that tell the caller what went wrong and what to do about it.

### Meaningful tests

Tests must validate actual behavior:
- Assert on specific expected values, not just that code runs without panicking
- Cover the happy path, edge cases, and at least one error path per function
- Test the contract (inputs → outputs), not the implementation details
- Each test should fail if the behavior it guards is broken — if removing the tested code doesn't fail the test, the test is worthless

### The compass

When you notice yourself choosing an easier path over a correct one — about to skip a warning, hardcode a value, or write "this should be fine" — pause. That impulse is the exact failure mode these standards exist to prevent. Do the right thing, then move on.
