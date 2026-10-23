# Git workflow

This document records the Git workflow practised in Lab 4.

Changes are staged with git add before they are committed.

## Commit convention

Each commit represents one logical change.
Messages use a prefix such as docs, chore, feat or fix,
followed by an imperative description.
Related issue numbers are included for traceability.

## Staging practice

git diff shows unstaged changes.
git diff --staged shows changes prepared for the next commit.
git restore --staged removes changes from staging without deleting the files.