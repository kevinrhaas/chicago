# changelog.d — one What's-New entry per PR

A PR adds ONE file here instead of editing `renderers/web/js/changelog.js`:

```json
{
  "title": "Prairie Avenue's 18th-20th block is walkable",
  "kind": "feature",
  "items": [
    "Twelve houses stand on the block, drafted from the 1904 atlas.",
    "Each one is marked as a draft until its own pass refines it."
  ]
}
```

- Name it after the ticket: `T-2250.json`. Only `title`, `kind` and `items` are allowed;
  the number, `ts` and `date` are assigned later.
- `kind` is one of feature, fix, change, chore, add, feat, improvement, improve, polish.
- The What's-New budget in `AGENTS.md` applies (T-3813, 2026-11-27): title ≤ 10 words,
  ≤ 3 items, ≤ 60 words, no item over 25 words. The tab shows the title alone until tapped,
  so the title says what a visitor will see change; reasons and measurements go in the PR.
- Check it: `cd chicago/4d && node tools/changelog-entries.mjs --check`.

After the PR merges, `.github/workflows/chicago-4d-changelog-fold.yml` folds every
pending file into `changelog.js` on `dev` (the latest to land goes on top), stamps it
with `tools/stamp-changelog.mjs`, deletes the file and pushes one commit. Two PRs never
write the same file, so they no longer conflict over the changelog's top line.
