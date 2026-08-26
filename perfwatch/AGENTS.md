# Project Implementation Code of Conduct

These instructions apply to every agent and work item in this repository,
including Phase 8 and Phase 9.

## Core Rules

- Prefer the smallest direct implementation that satisfies the current work
  item. Do not add speculative abstractions or dependencies.
- Inspect the affected flow before editing it. Preserve unrelated user changes.
- Keep work observable with a short opening plan, milestone updates, exact
  validation commands, and a final scoped-diff summary. Do not narrate every
  routine command or pause after an arbitrary number of commands.
- Use the minimum sufficient validation: one focused regression check for each
  non-trivial behavior, plus the relevant final gate for the affected area.
- Report failures honestly. A program-code failure may be diagnosed and fixed
  within the approved scope; an environment or tooling failure requires a stop
  as defined below.

## Select the Pipeline Per Work Item

Classify each work item before changing implementation files. Phase membership,
file count, or line count alone does not determine the pipeline.

Use the default three-stage pipeline unless the work item meets the six-stage
risk criteria below. If risk becomes apparent during implementation, stop,
report the new risk, and upgrade the remaining work to the six-stage pipeline.

## Default Three-Stage Pipeline

Use this pipeline for ordinary, reversible work with a bounded impact:

1. **Scope and assess risk.** Inspect the relevant code and callers, state the
   intended outcome and acceptance check, list the expected files, and confirm
   that no six-stage trigger applies. A small change needs only a short plan.
2. **Implement and verify iteratively.** Edit the smallest logical group of
   files and run focused checks while working. Fix in-scope program-code
   failures in this stage; do not create an administrative return loop between
   editing and focused validation.
3. **Run the final gate and review.** Run the relevant final validation, inspect
   the complete scoped Git diff, update durable product or operator
   documentation only when behavior changed, and report the result. Commit only
   when the owner has requested or approved a local commit.

The three stages are milestones, not mandatory approval pauses. Continue
through them autonomously unless a stop condition below applies.

Typical three-stage work includes isolated UI changes, mock or fixture updates,
focused parser or service bug fixes with a regression check, tests, lint
configuration, documentation synchronization, backward-compatible optional API
fields, and small reversible refactors.

## Six-Stage Risk Criteria

Use the six-stage pipeline when any hard trigger applies:

- database schema migration, destructive cleanup, retention behavior, or
  persistent-format changes;
- authentication, authorization, secrets, encryption, privacy, or another
  security boundary;
- installer, system service, automatic update, artifact signing, release
  publication, or production deployment;
- a breaking API, configuration, database, serialization, or persisted-data
  contract;
- concurrency, transaction, or crash-recovery behavior that can leave durable
  state inconsistent;
- an operation whose failure can cause material data loss, security exposure,
  financial impact, or an unrecoverable external change.

Also use it when at least two of these risk indicators apply:

- the change spans three or more components, languages, or runtimes;
- multiple real callers or external consumers depend on the changed contract;
- rollback is difficult or cannot restore the previous state completely;
- validation requires physical hardware, an operating-system matrix, or an
  external service;
- a material requirement or acceptance boundary must be frozen before coding;
- the result is a distributable or release-gating artifact.

When uncertain, state the evidence for the classification. Do not upgrade a
task merely because it is large, and do not keep the three-stage pipeline when
a hard trigger is present.

## High-Risk Six-Stage Pipeline

For a work item selected as high risk, use these stages in order:

1. **Plan only.** Inspect the full affected flow and callers. Define scope,
   interfaces, risks, rollback or recovery, validation, documentation, and
   exact commit or delivery boundaries. Do not modify implementation files.
2. **Implement visibly.** Make small scoped changes and run focused checks, but
   do not perform the final acceptance gate or unrelated cleanup.
3. **Validate only.** Run the approved acceptance commands without changing
   implementation files. An in-scope program-code failure returns the work to
   Stage 2; after the fix, rerun the affected validation before continuing.
4. **Record durable evidence.** Update the applicable process note with risk
   decisions, migration or recovery instructions, validation evidence, and
   remaining limitations. Do not record a command-by-command transcript.
5. **Review the complete diff.** Check all scoped changes, compatibility,
   generated output, secrets, rollback assumptions, validation evidence, and
   commit boundaries. Resolve findings by returning to the appropriate stage.
6. **Commit or hand off.** Commit only the reviewed scope when a local commit is
   already authorized, then report its identifier and worktree state. Otherwise
   stop and present the reviewed changes for owner approval. A local commit does
   not authorize push, release, deployment, publication, or another external
   write.

Stage 1 has a mandatory approval stop before Stage 2. Stage 5 has an approval
stop only when the commit was not already authorized or when the next action is
external, destructive, or release-affecting. The other stage boundaries require
a concise progress report, not an automatic wait for owner input.

## Stop Conditions

Stop and request owner direction when:

- an unresolved ambiguity would materially change behavior, an interface, data
  format, acceptance criteria, or scope;
- a discovered requirement expands the approved work materially;
- the six-stage plan reaches the Stage 1 approval gate;
- a commit has not been authorized, or the next action would push, publish,
  deploy, release, modify an external system, destroy data, or be difficult to
  recover;
- a new production dependency or elevated permission is required and was not
  already approved;
- an environment or tooling failure occurs, including a permission error,
  dependency or tool startup failure, undiscoverable compiler or SDK, shell
  mismatch, or unavailable required hardware.

For an environment or tooling failure, do not retry, switch tools or shells,
install dependencies, change flags, create alternate build directories, or run
further diagnostics. Report the blocked command, exact error, working
directory, likely environmental cause, and concise owner-run recovery commands.
Resume only after the owner reports resolution and authorizes continuation;
then rerun only the originally blocked command.

Do not stop merely for read-only inspection, safe in-scope local edits, focused
tests, a diagnosable program-code failure, or a routine milestone update.

## Phase 8 and Phase 9 Application

Apply the classification independently to every Phase 8 and Phase 9 work item:

- Phase 8 live Windows collection may use three stages for a bounded collector
  implementation, but uses six when it changes shared contracts, spans multiple
  runtimes, or requires physical-hardware release evidence.
- Phase 8 packaging, release artifacts, checksum publication, installers,
  services, signing, and publication use six stages.
- An isolated transparent-overlay UI change normally uses three stages; system
  integration, packaged startup, privileges, or shared-contract changes use six.
- Phase 9 packaged full-flow and physical-hardware release acceptance use six
  stages. An isolated visual check or documentation correction uses three.

The purpose of the six-stage path is risk control and durable traceability. It
must not be used as a default ceremony for ordinary work.
