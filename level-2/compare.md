# By hand, then the agent

Module 2.3. The agent's run is in a separate public repository,
[bonnergaylord/agent-practice](https://github.com/bonnergaylord/agent-practice), with
the pull request at
[agent-practice#1](https://github.com/bonnergaylord/agent-practice/pull/1).

## What I did by hand

To be straight about it: Module 2.2 was not purely by hand. I directed Claude Code to run
the commands, and I read the output and the resulting history. What came out is this
repository:

- **First commit:** `git init -b main`, then `git add .` and the first commit of the
  starter kit plus my Level 1 PDFs.
- **Repository:** `gh repo create --public --source . --push` created it and pushed in
  one step.
- **Pull request:** a branch `add-noi-summary` added the Module 1.5 Skill. It went
  through PR #1, merged with a merge commit, then `git checkout main` and `git pull`.
- **Conflict:** an edit to `notes.md` on GitHub's `main`, plus a conflicting edit on a
  local branch `conflicting-edit`. The merge stopped with CONFLICT, and I resolved it to
  one line that keeps both edits.
- **`gi-verify.txt`:** committed and pushed.

The difference that matters for this module: in 2.2 the commands ran as a few large
batches, and I read the result afterward. Nobody checked a diff between steps.

## What the agent did

In Module 2.3 I gave a fresh Claude Code agent four steps, one at a time. I read the diff
after each step before giving the next.

| Step | What I asked | What it ran | What I found in the diff |
| --- | --- | --- | --- |
| 1 | Make `notes.md` with a heading and the Cedar Ridge line, init on `main`, first commit | `printf ... > notes.md`, `git init -b main`, `git add notes.md`, `git commit` | Matched, plus a blank line between the heading and the data line that I did not ask for |
| 2 | Branch `add-cap-rate`, add the in-place NOI and going-in cap rate to the line, commit | `git checkout -b add-cap-rate`, `sed -i` on the line, `git diff`, `git commit` | **The line dropped "in-place" and "going-in"; the commit message kept them.** See below. |
| 3 | Create a public repo, push both branches, open a PR, don't merge | `gh repo create --public --source=. --remote=origin`, two `git push -u`, `gh pr create` | Only `notes.md` changed. The PR body added "Do not merge until reviewed", which now sits in the merged record. |
| 4 | Merge with a merge commit, switch to `main`, pull | `gh pr merge 1 --merge`, `git switch main`, `git pull` | Clean. The merge commit has two parents, and it left the branch undeleted because I didn't ask. |

Ways the agent worked differently from my 2.2 run:

- **It checked state before acting:** `git status`, `git log --all --graph` and
  `gh repo view` ran before creating anything.
- **It previewed the edit:** it ran `git diff` before `git commit` in step 2.
- **It used different commands:** `git switch` instead of `git checkout`, and it pushed
  each branch separately instead of using `gh repo create --push`.
- **It was inconsistent with its own commit trailer.** The first commit has no
  `Co-Authored-By` line, and the second does. It noticed this and offered to rewrite the
  first commit.

## One thing the agent could have done better, and what I changed

In step 2 I asked for the line to end with the **in-place NOI** and the **going-in cap
rate**. The agent's commit `769429a` is titled "Add in-place NOI and going-in cap rate to
Cedar Ridge", but the line it actually wrote was:

```
Cedar Ridge, 12 units, asking 1750000, NOI 98100, cap rate 5.61%
```

**The commit message described my request, not its diff.** Read on its own, the message
says the labels are there, and they are not. Those labels are not decoration. A bare
"NOI" on a listing line can be read as a pro forma or stabilized figure. Module 1.3 was
about exactly that distinction.

I caught it with `git diff HEAD~1 HEAD` and rejected the line. I fixed it myself on the
same branch, as its own commit, so the history shows both the miss and the correction:

```
9bca3ab Label the NOI as in-place and the cap rate as going-in
-Cedar Ridge, 12 units, asking 1750000, NOI 98100, cap rate 5.61%
+Cedar Ridge, 12 units, asking 1750000, in-place NOI 98100, going-in cap rate 5.61%
```

Only then did I let the agent push and open the PR. When I told it, the agent agreed its
message had overstated the change.

## What I would check first next time

1. **Read the commit message against the changed line, word by word.** Run `git show
   HEAD` and check every qualifier and unit in the message against the `+` line. The
   agent's mistake hid in the gap between the two.
2. **Look for changes I didn't ask for**, such as blank lines, reformatting, and line
   endings. On Windows, Git's "LF will be replaced by CRLF" warning means it can rewrite
   every line of a file, and the diff would show the whole file as changed.
3. **Read the PR description as well as the code.** The description becomes part of the
   permanent record when the PR merges.
