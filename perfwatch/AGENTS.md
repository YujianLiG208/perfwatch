# Project Implementation Code of Conduct

These instructions apply to every implementation phase and every agent working
in this repository.

## Execution Visibility Requirements

Work in foreground-observable mode.

Before making changes:

1. Print a short execution plan.
2. List the files expected to be read.
3. List the files expected to be created or modified.
4. List the commands expected to be run.

During implementation:

1. Before each command, print the exact command.
2. After each command, summarize the result.
3. If a command fails, print the failure, explain the likely cause, and do not
   hide it.
4. Do not continue silently after failures.

For code changes:

1. After editing each file, print a concise summary of what changed.
2. Show the important function names or CLI arguments added.
3. Do not dump entire files unless necessary.

For validation:

1. Run validation commands in the terminal.
2. Print the exact command used.
3. Print a PASS or FAIL result.
4. Generate or update the report files.
5. End with a final checklist.

Do not perform large hidden batches of work. Do not claim completion without
showing commands and validation output.

## Interaction Rules

Do not perform a full phase as one hidden batch.

Work in small visible increments:

1. Inspect files.
2. Report findings.
3. Edit one logical group of files.
4. Report changes.
5. Run one validation command.
6. Report the result.
7. Continue.

After every two or three commands, pause and summarize the current state.

If any command fails, stop and ask for confirmation before changing strategy,
unless the fix is limited to the current workspace and clearly safe.

## Environment and Tooling Failure Stop Rule

If a failure is unrelated to the program code, stop the current stage
immediately. This includes an environment that is not loaded correctly,
permission errors, dependency or tool startup timeouts, an undiscoverable
compiler or SDK, and a shell environment mismatch.

After such a failure:

1. Do not retry automatically or run any diagnostic command.
2. Do not switch shells, directories, flags, or tools; install dependencies;
   create alternative build or test directories; or collect additional logs.
3. Report the blocked command, the exact error, and why it appears to be an
   environment or tooling problem rather than a program-code problem.
4. Provide a concise manual troubleshooting plan with the exact PowerShell
   commands, working directory, and expected results for the owner to use.
5. Wait until the owner reports that the issue is resolved and explicitly
   authorizes work to resume.
6. On resume, rerun only the originally blocked command. Continue the stage
   only after that command succeeds.

If it is unclear whether a failure comes from the program code or the
environment, treat it as an environment failure and stop.

## Required Pipeline

Do not complete an entire work item in one pass. Use the
following pipeline in this exact order:

1. Plan only.
2. Implement visibly.
3. Validate only.
4. Update the process note.
5. Review the Git diff.
6. Commit.

Treat each pipeline item as a separate stage:

- Do not combine, skip, or reorder stages.
- Perform only the work permitted by the current stage.
- Report the current stage's output before entering the next stage.
- During `Plan only`, do not modify implementation files.
- During `Implement visibly`, make changes in small observable increments and
  do not run the full validation suite.
- During `Validate only`, do not make implementation changes. If validation
  fails, report the failure and return to the appropriate earlier stage.
- During `Update the process note`, record implementation and validation
  results in the project's applicable report or process-note file.
- During `Review the Git diff`, inspect and report the complete scoped diff
  before committing.
- During `Commit`, commit only the reviewed scoped changes and report the
  resulting commit identifier.
