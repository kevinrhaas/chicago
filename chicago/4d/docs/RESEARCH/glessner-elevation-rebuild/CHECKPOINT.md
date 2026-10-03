# Durable recovery checkpoint

Owner requested intermediate GitHub commits on 2026-10-02. A separate recovery branch preserves unfinished work without changing this active branch.

- Branch: https://github.com/kevinrhaas/chicago/tree/checkpoint/t-1999-glessner-20261002
- Latest saved commit: `525a3cf7cf78172e96dd4adba66156d9a56e3a3e`
- Handoff: https://github.com/kevinrhaas/chicago/blob/checkpoint/t-1999-glessner-20261002/chicago/4d/docs/RESEARCH/glessner-elevation-rebuild/RECOVERY.md
- Ticket T-1999 links both checkpoints.

The snapshot includes the integration, north and roof worktree patches (tracked plus untracked files), five reference review copies, and QA scripts. All patches were checked for clean application to their recorded base. This confirms recoverability only: no completed bake, model validation or source gate is claimed.

Continue pushing substantive checkpoints as this repair advances. Future sessions should read the active branch/current PR first and recover only work missing there.

Integrated model checkpoint: https://github.com/kevinrhaas/chicago/commit/010f2130bd9e807c8d9a75f2a34a8c0d53955c99 on the active steward branch includes the rebuilt full/light package and rendered evidence. Prefer the active branch and its PR over the earlier patch snapshots.
