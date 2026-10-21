# A favorite that is a git repo expands to its worktrees

- **Workstream**: [[sonata-server-automation:wt-workstreams]]
- **Created**: 2026-10-21 09:54 UTC
- **Created by**: Opus 5.5 (`claude-opus-5-5`), at Matt's request, from a session in sonata-server-automation ([[sonata-server-automation:worktree-layout]])
- **Written**: —
- **Written by**: —
- **Latest review**: —
- **Latest review by**: —
- **Review count**: 0
- **Implemented**: —
- **Implemented by**: —
- **Status**: **stub**, awaiting /plan-write

## Gates

None.

## Goal

Matt opens repos from Project Manager's **Favorites** view, grouped by tags,
one tag per project folder plus `Standalone`
([[sonata-server-automation:worktree-layout#wl-f10|WL-F10]]). Git worktrees
are about to become permanent, all in one layout:
`<parent of the main checkout>/worktrees/<repo>/<branch slug>`
([[sonata-server-automation:worktree-layout#wl-d1|WL-D1]]). This fork makes
each favorite that is a git repo with linked worktrees expandable in
Favorites. Its children are those worktrees, each one opening as a project
does.

Upstream has no nesting in Favorites. Its PR #986, open and unreviewed,
nests worktrees in the Git view only, and Matt rejected the Git view because
it does not group as Favorites does
([[sonata-server-automation:worktree-layout#wl-d6|WL-D6]]).

## Scope

- **The tree.** `StorageProvider.getChildren`
  (`src/sidebar/storageProvider.ts:81-209`) builds every favorite as a
  `ProjectNode` with `TreeItemCollapsibleState.None`: under a tag (`:113`),
  and at the root in list view (`:195`). It treats any element it is given
  as a tag (`getProjectsByTag(element.label)`, `:90`). So it needs:
  - project nodes that are collapsible when they have worktrees;
  - a branch for a `ProjectNode` element;
  - a worktree node kind (`src/sidebar/nodes.ts:17-121`) that opens through
    `_projectManager.open`, as a project does, and has a `contextValue` of
    its own for menus.
- **Finding a repo's worktrees from git's own records, with no git
  process.** For a main checkout, each `<rootPath>/.git/worktrees/<id>/gitdir`
  names `<tree>/.git`. A favorite that is itself a linked worktree reaches
  its clone through `commondir`. `getGitBranch` (`src/utils/git.ts:14-56`)
  already follows a `.git` file and gives each tree's branch.
  - A record whose folder is gone is a pruned or missing tree. Whether it is
    hidden or shown as missing is decided while writing.
  - This does not depend on where trees sit, so it works for trees still
    beside their repo and for the layout alike.
  - The extension runs on the server, in the `claude` account's VS Code
    server, so it can read these files directly.
  - PR #986 matches worktrees by `commondir` in `src/utils/git.ts`. Reusing
    its code, or rebasing onto it, is decided while writing.
- **Labels and order.** A child's label is its branch, with the folder as
  its description, or whatever the writer settles. The existing
  `projectManager.git.showBranchName` keeps working. Children are sorted.
  The main checkout itself is not repeated as a child.
- **A setting** to turn the nesting off, with collapse behaviour like
  `projectManager.tags.collapseItems` (`package.json:831`). Localised strings
  follow the repo's `.github/skills/vscode-ext-localization`.
- **When it refreshes.** A tree added or removed by git, SSA or plan_links
  appears without a reload, by watching `.git/worktrees`, or at least on
  "Refresh".
- **Building and installing the fork.** It is packaged as a VSIX and
  installed in the server's VS Code server, where the marketplace copy runs
  today (`/home/claude/.vscode-server/extensions/alefragnani.project-manager-13.1.0`).
  The fork takes an id of its own, so a marketplace update cannot replace
  it (D1). The writer settles:
  - **the new publisher or name** (`package.json:2`, `:6`);
  - **`projectManager.projectsLocation`.** It is set to the folder the
    favorites live in today,
    `/home/claude/.vscode-server/data/User/globalStorage/alefragnani.project-manager`,
    in `/home/claude/.vscode-server/data/Machine/settings.json`, where the
    other `projectManager.*` settings are. The setting takes a folder, not
    a file;
  - **the marketplace copy is uninstalled** when the fork goes in. Both would
    register the same `projectManager.*` settings, command ids and view ids;
  - **what starts afresh** under the new id: its `globalState`, for example
    `viewAsList` and the tags' expansion state (`storageProvider.ts:32`), and
    its caches in global storage. Whether any of that is carried over is
    decided while writing.
- **Staying in step with upstream.**
  - `origin` is `mattlightspeed/vscode-project-manager` and `upstream` is
    `alefragnani/vscode-project-manager`.
  - The plan tooling is committed on `master` (`fb5606f`). That commit also
    rewrote one line of upstream's own plan [[expose-public-extension-api]]
    (a path link into a name reference), so that file will conflict when
    upstream changes it. Upstream keeps its plans in `plans/` too.
  - The writer decides the branch layout: for example `master` following
    upstream plus this repo's plans, and the feature on a branch that could
    become an upstream PR without `plans/`.
- **Tests** go in `src/test/suite/`: a repo with linked worktrees, a pruned
  record, a favorite that is itself a worktree, and nesting turned off. The
  writer checks whether `npm test` (`package.json:1142`) runs on this server:
  the VS Code test host is downloaded, and it may need a display. Node is
  at `/home/claude/.local/node/bin`.
- **The repo's own conventions:** `AGENTS.md` points to
  `.github/copilot-instructions.md`, and `npm run lint`, `npm run build` and
  the Extension Development Host checks come before finishing.

### Decided (Matt, 2026-10-21)

- **D1 — The fork takes its own extension id, and points
  `projectManager.projectsLocation` back at the existing favorites folder.**
  Changing the id moves the extension's global-storage folder, where
  `projects.json` lives. Matt chose to point the setting at the old folder
  rather than keep upstream's id. Keeping the id would mean turning off
  auto-update and versioning above upstream (`package.json:5` is `13.1.1`).

**Out:**
- where worktrees go (SSA's [[sonata-server-automation:wt-01-worktree-layout]],
  claude-setup's [[claude-setup:plan-links-worktree-layout]]);
- the Git view, which PR #986 covers;
- creating or removing worktrees from the extension.

## Dependencies

None. Reading git's records does not depend on the layout, so this plan
waits on no other unit of [[sonata-server-automation:wt-workstreams]].
