# Implementation Rules

- Prefer the smallest direct change that satisfies the current requirement.
- Do not add an abstraction, dependency, configuration option, or test for a hypothetical future
  need.
- Inspect real callers before editing shared code and preserve unrelated user changes.
- For non-trivial behavior, keep one focused regression check plus the relevant final gate.
- Keep durable documentation about current behavior; leave command transcripts and temporary
  machine paths in task history.
- Report program failures accurately. Stop for permission, dependency, toolchain, hardware, or
  environment failures and provide the blocked command and recovery steps.
- Do not commit, push, publish, deploy, delete user data, or perform another external write without
  explicit authorization.
