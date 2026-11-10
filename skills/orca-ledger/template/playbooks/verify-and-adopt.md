# Verify and adopt

## 1. Compare

Approach, evidence, size of the change, risk, and files that should not be there.

## 2. Verify

The main session confirms with code and tests. A worker's report is not verification, and two workers agreeing is not verification — they share a prior. Where `rules/<repo>.md` exists, check it was followed.

## 3. Adopt

Adopt one, combine parts, or reject both. If you combined them, verify the combined result again.

## 4. Hand it to the user

Your job ends with the adopted change visible in the user's own checkout. You do not commit it.

First look at the target checkout's state and at any session running in that folder, and write the original state and how to undo it into `state.md`. If changes from another topic, or unrelated changes, overlap the target files, stop and ask.

Normally:

```text
git merge --squash <adopted-branch>
```

If there are staged changes, or the user's branch already contains the same work and conflicts, do not merge. Copy over only the files the adopted branch changed, and only if the user has not touched them:

```text
base=$(git merge-base HEAD <adopted-branch>)
files=$(git diff --name-only "$base" <adopted-branch>)
git diff --name-only "$base" HEAD -- $files     # must print nothing
git status --porcelain -- $files                # must print nothing
git restore --source=<adopted-branch> --staged --worktree -- $files
```

If either check prints a file, the user changed it too: stop and ask. Do not overwrite it. Never take the file list from `git diff <user-branch> <adopted-branch>`: that also lists the user's own changes since the branch point, and restoring them reverts the user's work.

Never rewrite history on the user's branch, even if it has pushed commits. Afterwards, `git diff --cached <adopted-branch> -- $files` should be empty.

The user reviews it in their own editor, drops what they do not want, and commits.

Then go to `playbooks/cleanup.md`.
