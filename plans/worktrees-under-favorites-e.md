# A favorite that is a git repo expands to its worktrees

- **Workstream**: [[sonata-server-automation:wt-workstreams]]
- **Created**: 2026-10-21 09:54 UTC
- **Created by**: Opus 5.5 (`claude-opus-5-5`), at Matt's request, from a session in sonata-server-automation ([[sonata-server-automation:worktree-layout]])
- **Written**: 2026-10-21 10:53 UTC
- **Written by**: Opus 5.5 (`claude-opus-5-5`)
- **Latest review**: 2026-10-21 11:25 UTC
- **Latest review by**: Opus 5.5 (`claude-opus-5-5`)
- **Review count**: 1
- **Implemented**: —
- **Implemented by**: —
- **Status**: **reviewed 1×**, ready for /plan-implement; then Matt's hand-over (WF-R1)

Item ids are stable: findings **WF-F*n***, decisions **WF-D*n***, residue
**WF-R*n***. Tests are named by the suites and titles given in *Tests*.
**Snapshot of:** this repo on `master` at `d62a138`, working tree clean.
Upstream's `master` is `aefcf11` (`git ls-remote upstream`, re-read
2026-10-21), the commit `master` is built on (WF-F16). No `upstream/*`
tracking ref has been fetched yet.

## Gates

| Before | Kind | Gate | Why | State |
|---|---|---|---|---|
| writing | human | Matt — decides where the favorites live, since the stub's D1 put them in a folder VS Code deletes on uninstall (WF-F3) | WF-D1 and the hand-over | met 2026-10-21 (chose `/home/claude/.config/project-manager`) |

## Summary

In this fork of Project Manager, a favorite in the Favorites view that is a
git repository with linked worktrees can be expanded to list them. Each
worktree is labelled by its branch, described by where its folder sits, and
opens the way a project does. One whose folder has gone shows a warning
instead. The extension reads the worktrees from git's own records in the
repository's `.git/worktrees` folder, without running git, so it finds them
wherever they live. It watches that folder, so worktrees appear and go
without a reload.

The work also:
- adds two settings, `projectManager.worktrees.showInFavorites` and
  `projectManager.worktrees.collapseItems`, with their strings in all nine
  languages the extension ships;
- gives the fork its own extension id, `mattlightspeed.project-manager`, so
  that a marketplace update cannot replace it, and fixes What's New and the
  extension test for the new id;
- lets the test suite run headless on this server, and adds tests for every
  new branch;
- packages the fork as a VSIX.

Matt then moves his favorites to `~/.config/project-manager`, points the
extension there, swaps the marketplace copy for the fork, and reloads.
Upstream's changes keep coming in by merging alefragnani's `master` into the
fork's `master`.

## Goal

Matt opens repos from Project Manager's **Favorites** view, grouped by tags:
one tag per project folder, plus `Standalone`
([[sonata-server-automation:worktree-layout#wl-f10|WL-F10]]). Git worktrees
are about to become permanent, all in one layout,
`<parent of the main checkout>/worktrees/<repo>/<branch slug>`
([[sonata-server-automation:worktree-layout#wl-d1|WL-D1]]). This fork makes
each favorite that is a git repo with linked worktrees expandable in
Favorites. Its children are those worktrees, and each opens as a project
does.

Upstream has no nesting in Favorites. Its PR #986, open and unreviewed, nests
worktrees in the Git view only. Matt rejected the Git view because it does not
group as Favorites does
([[sonata-server-automation:worktree-layout#wl-d6|WL-D6]]).

## Scope

**In:**
- the Favorites tree: collapsible favorites, a worktree node, and its menus;
- reading a repo's linked worktrees from git's records, with no git process;
- labels, descriptions and order of the children; missing trees;
- two settings, with their strings in every language the extension ships;
- refreshing when trees are added or removed;
- the fork's extension id, and the fixes that the id change needs;
- running the test suite on this server;
- packaging the fork, and the hand-over that installs it in place of the
  marketplace copy, with the favorites moved to a folder no extension owns;
- the branch layout, and how the fork stays in step with upstream.

**Out:**
- where worktrees go: SSA's [[sonata-server-automation:wt-01-worktree-layout]]
  and claude-setup's [[claude-setup:plan-links-worktree-layout]];
- the Git view, which PR #986 covers;
- creating or removing worktrees from the extension;
- README and CHANGELOG changes (WF-D15);
- upstream defects this plan notices but does not need to fix: WF-F8,
  WF-F14, WF-F18.

### Decided (Matt, 2026-10-21)

- **D1 — The fork takes its own extension id**, so a marketplace update
  cannot replace it. Keeping upstream's id would have meant turning off
  auto-update and versioning above upstream (`package.json:5` is `13.1.1`).
  - **Amended 2026-10-21 by Matt** after WF-F3. The stub also said to point
    `projectManager.projectsLocation` back at the existing favorites folder,
    `/home/claude/.vscode-server/data/User/globalStorage/alefragnani.project-manager`.
    VS Code deletes that folder once the marketplace copy is uninstalled.
    The favorites are therefore copied to `/home/claude/.config/project-manager/`,
    and `projectManager.projectsLocation` points there. This is recorded as
    **WF-D1**.

## Dependencies

None. Reading git's records does not depend on where trees sit, so this plan
waits on no other unit of [[sonata-server-automation:wt-workstreams]]. It
works for the trees still beside their repo and for trees in the layout.

## Method: verified and assumed

- **Code** was read at the cited lines in this repo at `d62a138`.
- **Git's record format** was read on this server's four clones with linked
  worktrees (WF-F2), and in git's own source: `worktree.c`
  `get_linked_worktree()`, on git/git `master`, fetched 2026-10-21. It was
  also read in the git-scm docs `gitrepository-layout` and `git-worktree`.
- **VS Code's behaviour** was read in the shipped code of the VS Code server
  that this account runs, 1.141.1 (`~/.vscode-server/cli/servers/Stable-7baac39…/server/out/`).
  It was also read in the test build that `@vscode/test-electron` downloaded,
  1.143.0 (`.vscode-test/vscode-linux-x64-1.143.0`). Both are minified, so
  these cites quote code, not file lines.
- **The test baseline** and **packaging** were run (WF-F11, WF-F12).
- **PR #986** was read through GitHub's API at its head `13e6a17`.
- **`fs.watch` events** were measured with real `git worktree` commands on
  git 2.43.0 (WF-F10).
- **In review 1**, every cited line was re-read at `d62a138`, and these were
  re-run:
  - the suite, with this plan's headless launch arguments (WF-F11);
  - a probe in the VS Code test host: finding the extension by path, the
    icon theme, the locale, setting round-trips and defaults (WF-F18), and
    What's New;
  - `vsce ls` outside the sandbox (WF-F12);
  - Node's `statSync`, `readFileSync` and `fs.watch` behaviour on Node 24.18.0;
  - git's `get_linked_worktree()` and `should_prune_worktree()` in
    `worktree.c` on git/git `master`, fetched 2026-10-21;
  - PR #986's files, through GitHub's API (WF-F6).
- Anything not checked this way is listed under *Assumed, not verified*.

## Findings

<a id="wf-f1"></a>**WF-F1. The Favorites tree treats every element as a tag
and every favorite as a leaf.**
- `StorageProvider.getChildren` (`src/sidebar/storageProvider.ts:81-211`)
  builds each favorite as a `ProjectNode` with
  `TreeItemCollapsibleState.None`: under a tag (`:113`), and at the root in
  list view (`:195`).
- Given any element, it lists `getProjectsByTag(element.label)` (`:90`).
- `ProjectNode` (`src/sidebar/nodes.ts:17-98`) sets `contextValue` to
  `ProjectNodeKind` when it has an icon, else `ConfigNodeKind` (`:28-33`).
  It sets `resourceUri` to `projectManager-view:<path>` (`:35-38`), which the
  ✔ decoration matches against the current project
  (`src/sidebar/decoration.ts:10-14`).
- Every item menu is keyed on `viewItem == ProjectNodeKind`
  (`package.json:594-655`).
- Tag expansion is remembered in `globalState` under
  `projectsExplorerFavorites.tagsExpansionState`
  (`storageProvider.ts:32`, `:39-71`). It is written from
  `Providers.handleStorageTreeViewExpansionChange` (`src/sidebar/providers.ts:92-102`).

<a id="wf-f2"></a>**WF-F2. Git's records give every linked worktree, its
folder and its branch.**
- Each linked worktree has `<common git dir>/worktrees/<id>/`, holding:
  - `gitdir`: the path of the tree's `.git` file;
  - `commondir`: usually `../..`;
  - `HEAD`.

  The tree's own `.git` file reads `gitdir: <that record folder>`.
- Git reads a record in `get_linked_worktree()`. It reads `gitdir` and treats
  an empty or unreadable file as invalid. It trims trailing whitespace and
  strips a `/.git` suffix. A path that is still relative is resolved against
  `worktrees/<id>/`, through `strbuf_realpath_forgiving`. That last case
  arises with `worktree.useRelativePaths` (git-worktree docs), which is not
  available on this host's git 2.43.0.
- `get_worktrees_internal()` tries every entry of `worktrees/` except `.` and
  `..`, files included. A file fails at reading `<entry>/gitdir` and is
  skipped.
- A `gitdir` holding only whitespace is not empty to `strbuf_read_file`. Git
  then lists a worktree whose path is the record folder itself, and
  `should_prune_worktree()` calls it prunable ("invalid gitdir file").
- A record whose `gitdir` points nowhere is what `git worktree list` calls
  `prunable` ("gitdir file points to non-existent location"), and what
  `git worktree prune` removes (git-worktree docs). `should_prune_worktree()`
  first returns "keep" for a record with a `locked` file, so a locked
  worktree whose folder is gone is never pruned.
- On this server (read 2026-10-21), every clone with linked worktrees has one
  record, with an absolute `gitdir` and `commondir` `../..`:

| Main checkout | Record | Tree (`gitdir` minus `/.git`) | Branch (record `HEAD`) |
|---|---|---|---|
| `/usr/share/nginx/sites/passwave/passwave-web` | `passwave-web-main` | `/usr/share/nginx/sites/passwave/passwave-web-main` | `main` |
| `/usr/share/nginx/sites/sonata/sonata-modulate` | `sonata-modulate-master` | `/usr/share/nginx/sites/sonata/sonata-modulate-master` | `master` |
| `/usr/share/nginx/sites/passwave/passwave-scan-app` | `passwave-scan-app-update-v1` | `/usr/share/nginx/sites/passwave/passwave-scan-app-update-v1` | `update-v1` |
| `/usr/share/nginx/sites/passwave/passwave-core` | `passwave-core-update-v1` | `/usr/share/nginx/sites/passwave/passwave-core-update-v1` | `update-v1` |

- `getGitBranch` (`src/utils/git.ts:14-57`) already follows a tree's `.git`
  file to the record's `HEAD` (`:26-37`). It returns the branch, or
  `undefined` when HEAD is detached or unreadable.

<a id="wf-f3"></a>**WF-F3. VS Code deletes an extension's global-storage
folder once no version of that id remains.**
- In the VS Code server's `server-main.js` (1.141.1),
  `deleteExtensionsMarkedForRemoval()` scans the user extensions. For each id
  with no version left that is not marked removed, it calls
  `beforeRemovingExtension`.
- The extension-management service wires that callback to
  `postUninstall`. `postUninstall` runs the extension's `vscode:uninstall`
  script, if any, and then `rm(getExtensionStoragePath(e))`, which is
  `<defaultProfile.globalStorageHome>/<id lower-cased>`.
- On this server that path is
  `/home/claude/.vscode-server/data/User/globalStorage/alefragnani.project-manager/`.
  It holds `projects.json` (35 favorites) and `projects_cache_git.json`.
- So the stub's D1 and its "the marketplace copy is uninstalled" together
  would delete the favorites. This was raised with Matt, who chose WF-D1.
- The deletion is not done at uninstall. `deleteExtensions` only marks the
  extension (`setExtensionsForRemoval`). `deleteExtensionsMarkedForRemoval`
  runs inside the scanner's `cleanUp()`, which the server runs when it starts
  and when a client asks for it over the `cleanUp` channel call
  (`server-main.js`, 1.141.1). Exactly when a client asks was not traced.

<a id="wf-f4"></a>**WF-F4. `globalState` lives with the client, keyed by
extension id, and cannot be carried over.**
- The extension host's storage class proxies every read and write to
  `MainThreadStorage` (`extensionHostProcess.js`, 1.141.1: `this._proxy=t.getProxy(W.MainThreadStorage)`,
  `$initializeExtensionStorage`, `$setValue`). The server's
  `data/User/globalStorage/` holds no `state.vscdb` (listed 2026-10-21).
- No extension API reads another extension's `globalState`. The store is
  keyed by extension id wherever it lives, so the keys below start empty
  under the new id whether or not the client holds them.
- These keys start empty under the new id:
  - `viewAsList` (`src/extension.ts:129-130`): it defaults to `true`, so
    Favorites first shows as a list;
  - `filterByTags`;
  - `recent`: the Recent sort's stack;
  - `hideGitWelcome`;
  - `projectsExplorerFavorites.tagsExpansionState`;
  - What's New's `project-manager.version` and
    `project-manager.whatsNew.shown`
    (`vscode-whats-new/src/Manager.ts:47-48`).

<a id="wf-f5"></a>**WF-F5. Three places name the extension by
`alefragnani`.**
- `registerWhatsNew` passes `"alefragnani", "project-manager"`
  (`src/whats-new/commands.ts:14`). `WhatsNewManager.showPageInActivation`
  then calls `vscode.extensions.getExtension(`${publisher}.${name}`)!` and
  reads `.packageJSON.version` (`Manager.ts:83-87`). Under another publisher
  this rejects. Activation does not fail, because `registerWhatsNew` does not
  await it (`commands.ts:16`). But `showPage()` (`Manager.ts:90-94`) then
  throws, and the `projectManager.whatsNew` command throws with it.
- The `extension/context` menu's `when` is
  `extension == alefragnani.project-manager && extensionStatus == installed`
  (`package.json:660`).
- The extension test looks itself up as
  `getExtension('alefragnani.project-manager')`
  (`src/test/suite/extension.test.ts:22`).
- `name` feeds What's New's state keys (`Manager.ts:47-48`) and its logo
  path, `images/vscode-${name}-logo-readme.png` (`Manager.ts:103`).
- `StandardLinksProvider('alefragnani.project-manager')`
  (`src/sidebar/helpAndFeedbackView.ts:11`) only builds links, to upstream's
  pages.

<a id="wf-f6"></a>**WF-F6. PR #986 maps scanned projects to their repo, the
other direction from this plan.** It was opened 2026-09-24 and updated
2026-09-28. It is open and unmerged, with no reviews or comments. It has 1
commit, head `13e6a17`, base `f4562ba`.
- Its `getGitWorktreeParents(projectPaths)` takes the Git view's scanned
  paths. It matches each linked tree to a scanned repo through `commondir`,
  and drops trees whose repo was not scanned.
- It refactors `getGitBranch`'s `.git`-file handling into `getGitDir`, in
  `src/utils/git.ts`.
- It adds `projectManager.git.groupWorktrees` (`expanded` | `collapsed` |
  `never`).
- It never enumerates a repo's own `worktrees/` folder, which is what
  Favorites needs: the trees are not favorites.
- Its other edits, read in its patch (review 1):
  - `package.json`: the new setting goes in `projectManager-git`, after
    `git.maxDepthRecursion`;
  - `package.nls*.json`: its strings go after
    `git.showBranchName.enumDescriptions.always` (`package.nls.json:80`);
  - `src/extension.ts`: a `projectManager.git.groupWorktrees` block is
    inserted directly after the `git.showBranchName` block (`:210-213`).
    A block of this plan placed there would conflict with it if upstream
    merges #986. *Specification* therefore places them after the
    `tags.collapseItems` block (`:205-208`), with the five lines `:209-213`
    between the two insertions.

<a id="wf-f7"></a>**WF-F7. A tree item with a command expands only on its
twistie.** VS Code's custom tree view sets
`expandOnlyOnTwistieClick: p => !!p.command || !!p.checkbox || <workbench.tree.expandMode is doubleClick>`
(`workbench.desktop.main.js`, 1.143.0). A favorite made collapsible
therefore still opens on a click on its name.

<a id="wf-f8"></a>**WF-F8. The context-menu "Open" hands
`_projectManager.open` a node where it expects a path.** This was read, not
run.
- A `view/item/context` command receives the tree element.
- `_projectManager.open(projectPath, projectName, profile)`
  (`src/extension.ts:86-95`) calls `buildProjectUri(projectPath)`
  (`src/utils/uri.ts:9-11`). That calls `isRemotePath`, which calls
  `projectPath.startsWith` (`src/utils/remote.ts:14-16`), and a
  `ProjectNode` has no `startsWith`.
- The other node commands read `node.command.arguments[0]` (path) and `[2]`
  (profile):
  - `_projectManager.openInNewWindow` (`extension.ts:96-103`);
  - the three reveal commands (`src/commands/revealFileInOS.ts:11-20`);
  - `projectManager.addToWorkspace#sideBar` (`extension.ts:509-519`).

<a id="wf-f9"></a>**WF-F9. What refreshes Favorites today.**
- A change to `projects.json` (`extension.ts:176-180`).
- A change to `projectManager.git.showBranchName` (`extension.ts:210-213`).
- `projectManager.tags.collapseItems` (`extension.ts:205-208`).
- Window focus while Favorites is visible, only when `git.showBranchName` is
  `onlyInSideBar` or `always` (`providers.ts:81-88`).
- The palette's **Refresh Projects** (`projectManager.refreshProjects`,
  `extension.ts:107`) refreshes the auto-detected views and only retitles
  Favorites (`extension.ts:216-262`). The Favorites view has no refresh
  button (`package.json:472-517`).
- Any `projectManager.git*` change rescans every git base folder
  (`extension.ts:183-189`).

<a id="wf-f10"></a>**WF-F10. `fs.watch` sees worktrees come and go, but not
branch switches.** Measured on git 2.43.0 with Node, against a scratch repo:
- a non-recursive watch on `.git` reported `rename worktrees` when git
  created the `worktrees` folder (first `worktree add`), and when it removed
  it (last `worktree remove` or `prune`);
- a watch on `.git/worktrees` reported `rename <id>` for each record added or
  removed, and `rename worktrees` when the folder itself went;
- other `.git` events (`index`, `HEAD.lock`, logs, refs) arrive under their
  own names;
- nothing fires on either watch when a tree switches branch: that writes
  inside `worktrees/<id>/`.

<a id="wf-f11"></a>**WF-F11. The test baseline, and what `npm test` needs on
this server.** Recorded 2026-10-21 at `d62a138`, after
`git submodule update --init` and `npm ci`:
- `npm run lint`: 0 errors, 52 warnings (`@typescript-eslint/no-explicit-any`
  and similar, in existing files);
- `npm run build` and `npm run test-compile`: compiled successfully;
- the suite: **85 passing, 0 failing**, on VS Code 1.143.0.
  - It reached that only outside Claude's sandbox. Inside bubblewrap,
    Electron dumps core even for `code --version`.
  - It needed `ELECTRON_RUN_AS_NODE` unset. The variable is inherited from
    the VS Code extension host that runs Claude Code, and it makes the
    downloaded VS Code start as plain Node ("Cannot find module
    …/testworkspace").
  - It needed `--ozone-platform=headless`. This host has no X server, no
    `DISPLAY` and no `xvfb-run` ("Missing X server or $DISPLAY").
  - `@vscode/test-electron` 3.1.0 already passes `--no-sandbox`
    (`node_modules/@vscode/test-electron/out/runTest.js:54-56`). It spawns
    VS Code with `Object.assign({}, process.env, extensionTestsEnv)`
    (`:83-89`). It puts `launchArgs` ahead of its own arguments (`:73-75`).
  - Review 1 re-ran the suite outside the sandbox through `runTests`, with
    `ELECTRON_RUN_AS_NODE` unset and `launchArgs`
    `['./testworkspace', '--ozone-platform=headless']`: **85 passing**. That
    is the mechanism WF-D12 adopts.
- The submodule step had to run outside the sandbox, which guards
  `.git/config`.
- Upstream CI runs `xvfb-run -a npm test` on Linux
  (`.github/workflows/main.yml:45`), so `DISPLAY` is set there.

<a id="wf-f12"></a>**WF-F12. Packaging works with `@vscode/vsce` 4.0.0
outside the sandbox.**
- `npx --yes @vscode/vsce@4.0.0 package` built 110 files, 2.13 MB.
  `plans/**` and `AGENTS.md` are left out by `.vscodeignore`.
- Inside the sandbox, vsce's secret scan fails with `EACCES` on the
  sandbox's placeholder files in the repo root (`.bash_profile`, `.bashrc`,
  …), which exist only inside it. Inside it, `vsce ls` also lists them, and
  `.claude/*`.
- Outside the sandbox (review 1), `vsce ls` lists 108 files and none whose
  name starts with a dot. The 110 of a package add `[Content_Types].xml` and
  `extension.vsixmanifest`. The repo root holds an untracked `.claude/`
  folder there too, holding only an empty `.cc-writes/`. `.vscodeignore`
  does not leave out `.claude/`, so a file put there later would be
  packaged. *Verification* checks for that.
- vsce 4.0.0 was published 2026-09-14 and needs Node ≥ 22.
- Building runs `vscode:prepublish` (`webpack --mode production`) into
  `dist/`, which git ignores (`.gitignore`).

<a id="wf-f13"></a>**WF-F13. What is installed and configured today.** Read
2026-10-21:
- `alefragnani.project-manager` 13.1.0, from the gallery
  (`~/.vscode-server/extensions/extensions.json`). The VS Code server is
  1.141.1, whose `code-server --list-extensions` lists it beside
  `anthropic.claude-code` and `zaucy.symlink-follow`.
- Two VS Code servers were running when review 1 listed the processes,
  1.141.0 (`Stable-2a59476…`) and 1.141.1 (`Stable-7baac39…`). They serve
  different windows, and share `~/.vscode-server/extensions/` and
  `~/.vscode-server/data/`. This session's `code` resolves to 1.141.0's
  remote CLI. Its `--help` lists `--install-extension <ext-id | path>`, with
  `--force`, and `--uninstall-extension <ext-id>`.
- The manifest's `extensionKind` is `["ui", "workspace"]`
  (`package.json:24-27`). VS Code runs such an extension on the client when
  a copy is installed there. The copy that runs today is the server's: its
  `projects.json` holds server paths, and was last written 2026-10-21 09:40.
  Whether Matt's client also has a disabled copy cannot be seen from the
  server. The hand-over checks.
- `projectManager.*` settings live in
  `/home/claude/.vscode-server/data/Machine/settings.json`, which is plain
  JSON. `projectManager.projectsLocation` is not set.
- With the location unset, `getFilePathFromAppData` (`src/utils/path.ts:159-186`)
  would first use `/var/local/Code/User/projects.json` or
  `~/.config/Code/User/projects.json` if either existed. Neither does.
  `~/.config/Code` holds only `agent-host/`.
- A set location is used as `<location>/projects.json`
  (`extension.ts:489-498`). The setting is not re-read until reload: the
  configuration handler (`extension.ts:182-214`) ignores it.

<a id="wf-f14"></a>**WF-F14. Tag view drops a favorite's profile.**
`ProjectStorage.getProjectsByTag` (`src/storage/storage.ts:206-214`) maps
`label` and `description` only. `map()` (`:178-187`) and
`getProjectsByTags` (`:216-230`) include `profile`. So in tag view, a favorite
opens with no profile (`storageProvider.ts:121`). This is upstream's
behaviour, and its worktree children inherit it.

<a id="wf-f15"></a>**WF-F15. How tests reach the code.**
- The extension under test runs from `dist/extension.js`
  (`package.json:50`). Tests import `out/src/...` directly, so they get
  their own module instances, including their own `Container`.
- `ProjectNode` with an icon calls `getIconPath`. Under the default icon
  theme (`vs-seti`, `src/utils/icons.ts:12-16`), that builds
  `Uri.joinPath(Container.context.extensionUri, …)` (`icons.ts:33-45`).
  `createMockContext()` gives only `globalState`
  (`src/test/suite/mocks/MockMemento.ts:25-28`).
- No existing test constructs a `ProjectNode`.

<a id="wf-f16"></a>**WF-F16. Where the fork stands against upstream.**
- `git ls-remote upstream refs/heads/master` is `aefcf11`, which is
  `origin/master` and the parent of this repo's two plan commits: `fb5606f`
  (plan tooling) and `d62a138` (this stub).
- `fb5606f` also rewrote line 4 of upstream's plan
  [[expose-public-extension-api]], turning a path into a name reference.
- `.vscodeignore` already leaves out `plans/**` (upstream commit `d4f6790`).

<a id="wf-f17"></a>**WF-F17. Localisation coverage.**
- Manifest strings: `package.nls.json` has 120 keys. `az`, `pt-br`, `uk` and
  `zh-cn` have 120, `fr` and `zh-tw` have 109, and `cs` and `ru` have 94.
  Every file has the `tags.collapseItems` keys (anchor:
  `projectManager.configuration.tags.collapseItems.enumDescriptions.startCollapsed`,
  `package.nls.json:106`).
- Runtime strings: `l10n/bundle.l10n.json` and all 8 language bundles have
  the same 49 keys. Each bundle ends without a newline after its closing
  `}`.

<a id="wf-f18"></a>**WF-F18. A setting whose key extends another setting's
key loses its default.** Run in the test host, 1.143.0 (review 1):
- `projectManager.tags` is an array setting (`package.json`, in
  `projectManager-general`). `projectManager.tags.collapseItems` extends its
  key.
- VS Code builds the settings tree by splitting keys on dots
  (`extensionHostProcess.js`, 1.143.0: `let o=t.split("."),i=o.pop()…`). An
  array counts as an object there, so `collapseItems` is set as a property of
  the default `[]`. The property does not survive serialisation to the
  extension host.
- So `getConfiguration("projectManager").inspect("tags.collapseItems")` has
  no `defaultValue`, and `get("tags.collapseItems")` is `undefined` even 15 s
  after start-up. `sortList`'s default (`"Name"`) does arrive.
- A user value set where `projectManager.tags` is not also set does arrive
  (`update(…, Global)` then `get` gave `alwaysCollapsed`). Matt's machine
  settings do set `projectManager.tags` (WF-F13). That such a value is then
  lost is inferred, not run.
- Upstream's code survives the lost default because it always passes its own
  fallback, `get<string>("tags.collapseItems", "startExpanded")`
  (`storageProvider.ts:141`, `providers.ts:95`).
- Of the manifest's keys, only `projectManager.tags` is a prefix of another
  key. Nothing is named `projectManager.worktrees`, so this plan's two keys
  are not affected. WF-D9 keeps it that way.

## Decisions

<a id="wf-d1"></a>**WF-D1. The fork has its own id. The favorites move to
`/home/claude/.config/project-manager/`, and `projectManager.projectsLocation`
points there (Matt, 2026-10-21).**
- This amends the stub's D1 after WF-F3.
- The folder belongs to no extension id, so uninstalling either copy cannot
  delete it, and it survives a wipe of `~/.vscode-server`.
- Because both copies read the same setting, rolling back to the marketplace
  copy keeps the favorites.
- Rejected:
  - `~/.vscode-server/data/User/project-manager`, lost with `~/.vscode-server`;
  - keeping the old folder and disabling the marketplace copy, which keeps
    updating, and whose later uninstall would delete the favorites.

<a id="wf-d2"></a>**WF-D2. The id is `mattlightspeed.project-manager`.**
- Only `publisher` changes (`package.json:6`): `alefragnani` becomes
  `mattlightspeed`, the owner of `origin`. vsce accepts letters, digits and
  hyphens.
- `name` stays `project-manager`, because What's New's keys and logo path
  derive from it (WF-F5).
- `displayName` stays "Project Manager". The Extensions view already shows
  the publisher.
- `version` stays upstream's, so that a release's version bump merges as
  upstream wrote it (WF-R8). A rebuilt VSIX of the same version is installed
  with `--force`.

<a id="wf-d3"></a>**WF-D3. The marketplace copy is uninstalled, not disabled.**
- Both copies contribute the same setting, command and view ids.
- Once WF-D1 has moved the favorites out, the uninstall deletes only
  upstream's Git-view cache.

<a id="wf-d4"></a>**WF-D4. Nothing in `globalState` is carried over.** It
cannot be: WF-F4. The hand-over tells Matt what resets, chiefly that
Favorites opens as a list until he clicks **View as Tags** once.

<a id="wf-d5"></a>**WF-D5. Worktrees are read by a new module,
`src/utils/worktrees.ts`, which mirrors git's reader. `src/utils/git.ts` is
not touched, and PR #986 is neither rebased onto nor copied.**
- #986 answers the reverse question (WF-F6), and is unmerged and unreviewed.
- It rewrites `git.ts`, so any edit there would conflict with it, or with
  whatever upstream merges in its place. A new file never conflicts.
- The new module reuses `getGitBranch` as it stands.
- Its `.git`-file reading duplicates `getGitBranch`'s seven lines, rather
  than refactoring them. Once upstream merges #986 or another shared helper,
  the duplicate can go (WF-R20).
- It differs from git's reader in three places, on purpose:
  - a `gitdir` holding only whitespace is skipped. Git would list the record
    folder itself as a worktree (WF-F2), which no one could open;
  - a relative `gitdir` is resolved with `path.resolve`, not through
    symlinks as `strbuf_realpath_forgiving` does. Only the path shown
    differs;
  - like git, it tries every entry of `worktrees/` and skips those whose
    `gitdir` cannot be read. It does not filter by entry type first.

<a id="wf-d6"></a>**WF-D6. A favorite's children are the linked worktrees of
its clone, except the favorite itself. The main checkout is never a child.**
- From a main checkout, that is every record in `.git/worktrees/`.
- From a favorite that is itself a linked tree, `commondir` leads to the same
  records, and the favorite's own record is skipped.
- Leaving out the main checkout keeps one rule, with no guess at whether
  `dirname(commondir)` is a working tree (bare clones, `.bare` layouts).
  The main checkout has its own favorite.

<a id="wf-d7"></a>**WF-D7. A record whose tree is gone is shown, marked
missing, with no command.**
- Hiding it would mask a broken state that `git worktree prune` fixes in one
  command.
- The extension already flags a missing favorite rather than hiding it:
  `indicateInvalidPaths`, `src/utils/path.ts:145-153`.
- It costs a row only while the state is broken.
- It counts as missing when `<tree>/.git` no longer exists. That is git's
  `prunable` test (WF-F2), and it also catches a folder whose `.git` file was
  deleted.
- A locked worktree whose folder is gone, for example one on unmounted
  media, is also shown missing. Git never prunes it (WF-F2), so the tooltip
  says that prune removes the record unless the worktree is locked.

<a id="wf-d8"></a>**WF-D8. Labels, descriptions, icons and order.**
- **Label:** the branch, or the folder's name when HEAD is detached or the
  tree is missing.
- **Description:** where the tree is.
  - It is the tree's path relative to the favorite's parent folder, or the
    absolute path when that relative path climbs out: it is `..`, or starts
    with `..` and a separator. A folder whose own name starts with `..`
    does not climb out.
  - On Windows, `path.relative` between two drives returns the absolute
    target (`path.win32.relative("C:\\a\\b", "D:\\x\\y")` is `D:\x\y`, run
    on Node 24), so that case needs no test of its own.
  - In the WL-D1 layout it reads `worktrees/passwave-web/main`. A tree
    outside the layout stands out, for example `passwave-web-main`.
  - A detached tree is `"{0} (detached)"`, and a missing one
    `"{0} (missing)"`.
- **Tooltip:** `ProjectNode`'s, which is label, path and kind. A missing tree
  says instead that its folder is gone and that `git worktree prune` removes
  the record.
- **Icon:** codicon `git-branch`, or `warning` when missing, whatever the
  icon theme.
- **Order:** by label, case-insensitive with numeric runs compared as
  numbers, then by path.
- **`projectManager.git.showBranchName`** still describes favorites by
  their branch, as before. A child's label already is its branch.

<a id="wf-d9"></a>**WF-D9. Two settings, under `projectManager.worktrees`.**
- `projectManager.worktrees.showInFavorites` (boolean, default `true`)
  turns the nesting off.
- `projectManager.worktrees.collapseItems` takes `tags.collapseItems`'s four
  modes, with default `startCollapsed`. With that default Favorites looks as
  it does today until a repo is expanded.
- `start*` modes remember each favorite's state by path, under the
  `globalState` key `projectsExplorerFavorites.worktreesExpansionState`,
  kept apart from the tags' key.
- The namespace stays out of `projectManager.git`, whose every change
  rescans all git base folders (WF-F9).
- No setting is ever named `projectManager.worktrees` itself, or the two
  keys would lose their defaults as `tags.collapseItems` does (WF-F18).

<a id="wf-d10"></a>**WF-D10. Refreshing.**
- **A watcher.** `fs.watch` on each enabled local favorite's common git
  folder, filtered to `worktrees`, and on its `worktrees/` folder when it
  exists. Changes are debounced 300 ms into one refresh of Favorites (WF-F10).
- **Window focus** while Favorites is visible, now also when nesting is on.
- **A settings change** under `projectManager.worktrees`.
- **The palette's "Refresh Projects"**, which now also refreshes Favorites.
- `vscode.workspace.createFileSystemWatcher` was not chosen. A base outside
  the workspace means VS Code's recursive watcher over the whole `.git`. It
  is harder to drive from a unit test, and buys nothing over two
  non-recursive watches.
- Branch switches inside a tree, and folders deleted by hand, show at the
  next focus or refresh (WF-R2).

<a id="wf-d11"></a>**WF-D11. A worktree node's menus.**
- It gets **Open in New Window** (inline and in the menu), **Reveal in File
  Manager / Finder / Explorer** and **Add to Workspace**. All read
  `node.command.arguments`, which a worktree node fills like a favorite's
  (WF-F8).
- It does not get the menu's **Open**: a click opens it, and the menu entry
  passes a node where a path is wanted (WF-F8, WF-R3).
- It does not get the favorites-only entries: Delete, Rename, Edit Tags,
  Disable.
- A missing node has no command and no menu.

<a id="wf-d12"></a>**WF-D12. `npm test` learns to run headless.**
- `src/test/runTest.ts` deletes `ELECTRON_RUN_AS_NODE` from its own
  environment before spawning VS Code.
- On Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY`, it adds
  `--ozone-platform=headless`.
- CI, which sets `DISPLAY` through `xvfb-run`, is unaffected.
- On this server, `npm test` and `vsce package` still run outside Claude's
  sandbox (WF-F11, WF-F12, WF-R10).

<a id="wf-d13"></a>**WF-D13. One trunk.**
- `master` holds upstream, plus this repo's plans, plus the fork's commits.
- The work is committed in four groups, so that the feature stays one
  cherry-pick away from an upstream PR, which is deferred (WF-R7). See
  *Commits*.
- Upstream comes in by merge. See *Staying in step with upstream*.
- A separate upstream-shaped branch, kept now, would double every sync for a
  PR nobody has asked for.

<a id="wf-d14"></a>**WF-D14. Matt makes the swap.**
- The implementer builds and checks the VSIX.
- Matt copies the favorites, sets the location, uninstalls, installs and
  reloads, as one sequence. The steps change his live editor, and the copy
  must not go stale before the swap.

<a id="wf-d15"></a>**WF-D15. No README or CHANGELOG change.** Both are
upstream's, and edits there would conflict on every release. The settings'
descriptions document the feature. An upstream PR would add a README
section (WF-R7).

<a id="wf-d16"></a>**WF-D16. New files follow the repo's conventions.**
- They carry the standard copyright header that
  `.github/copilot-instructions.md` ("Code Quality") requires of production
  files. New test files carry it too, as the existing tests do.
- Four-space indentation, double quotes and semicolons.
- `l10n.t` for runtime strings, and `%key%` for manifest strings.

## Specification

### Files

| File | Change |
|---|---|
| `src/utils/worktrees.ts` | **new**: `LinkedWorktree`, `getGitCommonDir`, `getLinkedWorktrees` |
| `src/sidebar/worktreeWatcher.ts` | **new**: `WorktreeWatcher` |
| `src/sidebar/nodes.ts` | gains `WorktreeNode` |
| `src/sidebar/storageProvider.ts` | collapsible favorites, project children, worktree expansion state, watcher, `dispose` |
| `src/sidebar/providers.ts` | disposes the provider; focus refresh; remembers a favorite's expansion |
| `src/extension.ts` | Refresh Projects refreshes Favorites; reacts to `projectManager.worktrees` settings |
| `src/whats-new/commands.ts` | publisher and name from the manifest |
| `src/test/runTest.ts` | headless on a Linux host with no display |
| `package.json` | publisher; What's New menu id; two settings; six menu entries |
| `package.nls.json` + 8 `package.nls.<lang>.json` | six setting strings |
| `l10n/bundle.l10n.json` + 8 `l10n/bundle.l10n.<lang>.json` | three runtime strings |
| `src/test/suite/mocks/MockMemento.ts` | `createMockContext` gains `extensionUri` |
| `src/test/suite/mocks/worktreeFixtures.ts` | **new**: fixture builders and `waitFor` |
| `src/test/suite/extension.test.ts` | finds itself by path; one new test |
| `src/test/suite/worktrees.test.ts` | **new** |
| `src/test/suite/worktreeNode.test.ts` | **new** |
| `src/test/suite/worktreeWatcher.test.ts` | **new** |
| `src/test/suite/storageProviderWorktrees.test.ts` | **new** |
| `src/test/suite/manifest.test.ts` | **new** |

Nothing is deleted. `src/utils/git.ts`, `src/storage/storage.ts` and the
existing tests' assertions do not change.

### `src/utils/worktrees.ts` (new)

The standard header, then this module:

```ts
import fs = require("fs");
import path = require("path");
import { getGitBranch } from "./git";

export interface LinkedWorktree {
    path: string;
    branch: string | undefined;
    missing: boolean;
}

export function getGitCommonDir(projectPath: string): string | undefined {
    try {
        const gitPath = path.join(projectPath, ".git");
        const gitStat = fs.statSync(gitPath, { throwIfNoEntry: false });
        if (!gitStat) {
            return undefined;
        }
        if (gitStat.isDirectory()) {
            return gitPath;
        }

        const gitFileContent = fs.readFileSync(gitPath, "utf8").trim();
        if (!gitFileContent.startsWith("gitdir: ")) {
            return undefined;
        }
        const gitDir = path.resolve(projectPath, gitFileContent.substring(8));

        const commonDirFile = path.join(gitDir, "commondir");
        if (!fs.existsSync(commonDirFile)) {
            return gitDir;
        }
        return path.resolve(gitDir, fs.readFileSync(commonDirFile, "utf8").trim());
    } catch {
        return undefined;
    }
}

export function getLinkedWorktrees(projectPath: string): LinkedWorktree[] {
    const commonDir = getGitCommonDir(projectPath);
    if (!commonDir) {
        return [];
    }

    const worktreesDir = path.join(commonDir, "worktrees");
    let recordNames: string[];
    try {
        recordNames = fs.readdirSync(worktreesDir);
    } catch {
        return [];
    }

    const favoritePath = comparablePath(projectPath);
    const worktrees: LinkedWorktree[] = [];
    for (const recordName of recordNames) {
        const worktreePath = readWorktreePath(path.join(worktreesDir, recordName));
        if (!worktreePath || comparablePath(worktreePath) === favoritePath) {
            continue;
        }
        const missing = !fs.existsSync(path.join(worktreePath, ".git"));
        worktrees.push({
            path: worktreePath,
            branch: missing ? undefined : getGitBranch(worktreePath),
            missing
        });
    }
    return worktrees.sort((a, b) => a.path.localeCompare(b.path));
}

// Reads a record the way git's get_linked_worktree() (worktree.c) does: trailing
// whitespace and a "/.git" suffix are dropped, and a relative path is relative
// to the record's own folder. Unlike git, a gitdir of only whitespace is not
// taken as the record folder itself.
function readWorktreePath(recordDir: string): string | undefined {
    let gitdir: string;
    try {
        gitdir = fs.readFileSync(path.join(recordDir, "gitdir"), "utf8").trimEnd();
    } catch {
        return undefined;
    }
    if (gitdir === "") {
        return undefined;
    }
    if (gitdir.endsWith("/.git")) {
        gitdir = gitdir.slice(0, -"/.git".length);
    }
    return path.resolve(recordDir, gitdir);
}

function comparablePath(fsPath: string): string {
    try {
        return fs.realpathSync(fsPath);
    } catch {
        return path.resolve(fsPath);
    }
}
```

Notes for the implementer:
- `getGitCommonDir` returns `undefined` for any path without a readable
  `.git`. For remote URIs and `.code-workspace` files, `statSync` with
  `throwIfNoEntry: false` returns `undefined`, `ENOTDIR` included (run on
  Node 24, 2026-10-21). The `catch` takes the remaining errors, such as an
  unreadable `.git` or `commondir`. Callers still skip remote paths first, so
  no filesystem call is made for them.
- `getLinkedWorktrees` returns trees sorted by path. Display order is the
  provider's (WF-D8).
- An entry of `worktrees/` that is a file fails in `readWorktreePath`
  (`ENOTDIR` on `<entry>/gitdir`) and is skipped, as git skips it (WF-D5).
- `fs.statSync(…, { throwIfNoEntry: false })` and statements before `super()`
  (below) were compiled with the repo's TypeScript 5.9.3 at target ES2020,
  2026-10-21.

### `WorktreeNode` (appended to `src/sidebar/nodes.ts`)

- Imports: add `import path = require("path");` as the first import, `l10n`
  to the existing `vscode` import (alphabetical: after `IconPath`), and
  `import { LinkedWorktree } from "../utils/worktrees";` after the
  `../utils/remote` import.
- Append, after `NoTagNode`:

```ts
export class WorktreeNode extends ProjectNode {

    public readonly worktree: LinkedWorktree;

    constructor(worktree: LinkedWorktree, projectPath: string, profile: string | undefined) {
        const label = worktree.branch ?? path.basename(worktree.path);
        super(label, TreeItemCollapsibleState.None, undefined, {
            name: label,
            path: worktree.path,
            detail: describeWorktree(worktree, projectPath)
        }, worktree.missing ? undefined : {
            command: "_projectManager.open",
            title: "",
            arguments: [ worktree.path, label, profile ]
        });

        this.worktree = worktree;
        this.iconPath = worktree.missing ? ThemeIcons.warning : ThemeIcons.git_branch;
        this.contextValue = worktree.missing ? "WorktreeMissingNodeKind" : "WorktreeNodeKind";
        if (worktree.missing) {
            const explanation = l10n.t("The folder of this worktree no longer exists. `git worktree prune` removes its record, unless the worktree is locked.");
            this.tooltip = new MarkdownString(`${explanation}\n\n_${worktree.path}_`);
        }
    }
}

function describeWorktree(worktree: LinkedWorktree, projectPath: string): string {
    const relativePath = path.relative(path.dirname(projectPath), worktree.path);
    const climbsOut = relativePath === ".." || relativePath.startsWith(`..${path.sep}`);
    const location = climbsOut ? worktree.path : relativePath;
    if (worktree.missing) {
        return l10n.t("{0} (missing)", location);
    }
    if (!worktree.branch) {
        return l10n.t("{0} (detached)", location);
    }
    return location;
}
```

- The `icon` argument is `undefined`, so `ProjectNode` never resolves a
  theme icon file for it (WF-F15). The constructor then sets `iconPath` and
  `contextValue` itself.
- `resourceUri` and the default tooltip come from `ProjectNode`
  (`nodes.ts:35-43`).
- `ThemeIcons.git_branch` and `ThemeIcons.warning` exist in
  `vscode-ext-codicons` (`node_modules/vscode-ext-codicons/lib/index.d.ts`).

### `src/sidebar/worktreeWatcher.ts` (new)

The standard header, then this module:

```ts
import fs = require("fs");
import path = require("path");
import { Disposable } from "vscode";

interface WatchedGitDir {
    gitDirWatcher: fs.FSWatcher;
    worktreesWatcher: fs.FSWatcher | undefined;
}

export class WorktreeWatcher implements Disposable {

    private readonly watched = new Map<string, WatchedGitDir>();
    private pendingChange: NodeJS.Timeout | undefined;

    constructor(private readonly onDidChange: () => void, private readonly delayMs = 300) { }

    public watch(commonDirs: string[]): void {
        const wanted = new Set(commonDirs);
        for (const commonDir of [ ...this.watched.keys() ]) {
            if (!wanted.has(commonDir)) {
                this.forget(commonDir);
            }
        }
        for (const commonDir of wanted) {
            if (!this.watched.has(commonDir)) {
                this.watchGitDir(commonDir);
            }
        }
    }

    public dispose(): void {
        this.watch([]);
        clearTimeout(this.pendingChange);
        this.pendingChange = undefined;
    }

    private watchGitDir(commonDir: string): void {
        let gitDirWatcher: fs.FSWatcher;
        try {
            gitDirWatcher = fs.watch(commonDir, (_event, filename) => {
                if (!filename || filename === "worktrees") {
                    this.rewatchWorktrees(commonDir);
                    this.scheduleChange();
                }
            });
        } catch {
            return;
        }
        gitDirWatcher.on("error", () => this.forget(commonDir));
        this.watched.set(commonDir, { gitDirWatcher, worktreesWatcher: this.watchWorktrees(commonDir) });
    }

    private watchWorktrees(commonDir: string): fs.FSWatcher | undefined {
        try {
            const worktreesWatcher = fs.watch(path.join(commonDir, "worktrees"), () => this.scheduleChange());
            worktreesWatcher.on("error", () => worktreesWatcher.close());
            return worktreesWatcher;
        } catch {
            return undefined;
        }
    }

    private rewatchWorktrees(commonDir: string): void {
        const watched = this.watched.get(commonDir);
        if (!watched) {
            return;
        }
        watched.worktreesWatcher?.close();
        watched.worktreesWatcher = this.watchWorktrees(commonDir);
    }

    private forget(commonDir: string): void {
        const watched = this.watched.get(commonDir);
        if (!watched) {
            return;
        }
        watched.gitDirWatcher.close();
        watched.worktreesWatcher?.close();
        this.watched.delete(commonDir);
    }

    private scheduleChange(): void {
        clearTimeout(this.pendingChange);
        this.pendingChange = setTimeout(() => {
            this.pendingChange = undefined;
            this.onDidChange();
        }, this.delayMs);
    }
}
```

- `watchWorktrees` returns `undefined` when there is no `worktrees/` folder
  yet. The git-folder watcher arms it when git creates the folder.
- `!filename` covers platforms where Node gives no file name: the safe
  answer is to refresh.

### `src/sidebar/storageProvider.ts`

- **Imports.** Add `getGitCommonDir, getLinkedWorktrees` from
  `"../utils/worktrees"`, and `WorktreeWatcher` from `"./worktreeWatcher"`.
  Add `WorktreeNode` to the `./nodes` import.
- **Class line.** It becomes
  `export class StorageProvider implements vscode.TreeDataProvider<ProjectNode | TagNode>, vscode.Disposable {`.
- **Fields**, after `TAGS_EXPANSION_STATE_KEY` (`:32`):

```ts
    private static readonly WORKTREES_EXPANSION_STATE_KEY = "projectsExplorerFavorites.worktreesExpansionState";
    private readonly worktreeWatcher = new WorktreeWatcher(() => this.refresh());
```

- **Expansion state, generalised by key.** `:39-71` is replaced by private
  helpers and public wrappers. The tags' public signatures and behaviour are
  unchanged, so the existing 20 tag tests still hold.
  - `private static getExpansionState(stateKey: string): Record<string, boolean>`
    is `getTagExpansionState`'s body, with `stateKey` in place of the tags'
    key.
  - `private static getCollapsibleState(stateKey: string, id: string, behavior: string): vscode.TreeItemCollapsibleState`
    is `getTagCollapsibleState`'s current switch, reading
    `getExpansionState(stateKey)[id]`.
  - `private static async setExpanded(stateKey: string, id: string, expanded: boolean): Promise<void>`
    is `setTagExpanded`'s body, with `stateKey`.
  - `public static async resetTagExpansionState()` is unchanged.
  - `public static getTagCollapsibleState(tagId, behavior)` returns
    `getCollapsibleState(TAGS_EXPANSION_STATE_KEY, tagId, behavior)`.
  - `public static async setTagExpanded(tagId, expanded)` awaits
    `setExpanded(TAGS_EXPANSION_STATE_KEY, tagId, expanded)`.
- **New public statics:**

```ts
    public static showsWorktrees(): boolean {
        return vscode.workspace.getConfiguration("projectManager").get<boolean>("worktrees.showInFavorites", true);
    }

    public static refreshesOnWindowFocus(): boolean {
        const showGitBranch = vscode.workspace.getConfiguration("projectManager").get<string>("git.showBranchName", "never");
        return showGitBranch === "onlyInSideBar" || showGitBranch === "always" || StorageProvider.showsWorktrees();
    }

    public static async resetWorktreesExpansionState(): Promise<void> {
        await Container.context.globalState.update(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, {});
    }

    public static getWorktreesCollapsibleState(projectPath: string): vscode.TreeItemCollapsibleState {
        if (!StorageProvider.showsWorktrees() || isRemotePath(projectPath) || getLinkedWorktrees(projectPath).length === 0) {
            return vscode.TreeItemCollapsibleState.None;
        }
        const behavior = vscode.workspace.getConfiguration("projectManager").get<string>("worktrees.collapseItems", "startCollapsed");
        return StorageProvider.getCollapsibleState(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, projectPath, behavior);
    }

    public static async rememberWorktreesExpansion(projectPath: string, expanded: boolean): Promise<void> {
        const behavior = vscode.workspace.getConfiguration("projectManager").get<string>("worktrees.collapseItems", "startCollapsed");
        if (behavior === "startExpanded" || behavior === "startCollapsed") {
            await StorageProvider.setExpanded(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, projectPath, expanded);
        }
    }
```

- **`getChildren`.** Its first statement, before `// loop !!!`:

```ts
        if (element instanceof ProjectNode) {
            return Promise.resolve(this.getWorktreeNodes(element));
        }
```

- **The two favorite-node sites** (`:113` and `:195`). Each
  `vscode.TreeItemCollapsibleState.None` becomes
  `StorageProvider.getWorktreesCollapsibleState(projectPath)`.
  `projectPath` is already in scope at both (`:110`, `:192`).
- **Root branch.** In `} else { // ROOT` (`:127`), the first statement is
  `this.watchFavoritesWorktrees();`, before the empty-storage return.
- **New private methods and `dispose`:**

```ts
    private getWorktreeNodes(element: ProjectNode): WorktreeNode[] {
        const projectPath = element.preview.path;
        if (element instanceof WorktreeNode || !StorageProvider.showsWorktrees() || isRemotePath(projectPath)) {
            return [];
        }
        const profile = element.command.arguments[ 2 ];
        return getLinkedWorktrees(projectPath)
            .map(worktree => new WorktreeNode(worktree, projectPath, profile))
            .sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base", numeric: true })
                || a.preview.path.localeCompare(b.preview.path));
    }

    private watchFavoritesWorktrees(): void {
        const commonDirs: string[] = [];
        if (StorageProvider.showsWorktrees()) {
            for (const project of <ProjectInQuickPickList>this.projectSource.map()) {
                const projectPath = PathUtils.expandHomePath(project.description);
                const commonDir = isRemotePath(projectPath) ? undefined : getGitCommonDir(projectPath);
                if (commonDir) {
                    commonDirs.push(commonDir);
                }
            }
        }
        this.worktreeWatcher.watch(commonDirs);
    }

    public dispose(): void {
        this.worktreeWatcher.dispose();
    }
```

  `projectSource.map()` lists every enabled favorite, whatever the tag
  filter (`src/storage/storage.ts:178-187`). A favorite hidden by the filter
  is still watched, which costs nothing.

  `getWorktreeNodes` reads the profile as `element.command.arguments[ 2 ]`,
  the idiom of the node commands (`extension.ts:96-103`). Every favorite
  node has a command (`storageProvider.ts:118-122`, `:201-205`), a
  `WorktreeNode` returns before the read, and `tsconfig.json` sets no
  `strictNullChecks`.

### `src/sidebar/providers.ts`

- **`registerStorageTreeViewListeners` (`:73-90`).**
  - `this.storageProvider` becomes the first item pushed to
    `Container.context.subscriptions`, so its watchers close on deactivation.
  - The focus listener (`:81-88`) becomes:

```ts
            // Refresh git branch and worktree info when window gains focus and sidebar is visible
            vscode.window.onDidChangeWindowState(async (state) => {
                if (!state.focused || !this.storageTreeView.visible) {
                    return;
                }
                if (StorageProvider.refreshesOnWindowFocus()) {
                    this.storageProvider.refresh();
                }
                const showGitBranch = vscode.workspace.getConfiguration("projectManager").get<string>("git.showBranchName", "never");
                if (showGitBranch === "onlyInSideBar" || showGitBranch === "always") {
                    this.gitProvider.refresh();
                }
            }),
```

- **`handleStorageTreeViewExpansionChange` (`:92-102`)** gains, after the
  `TagNode` block:

```ts
        } else if (element instanceof ProjectNode) {
            await StorageProvider.rememberWorktreesExpansion(element.preview.path, state === "expanded");
        }
```

  The `if (element instanceof TagNode) { … }` closing brace becomes `}`
  followed by this `else if`.

### `src/extension.ts`

- **Line 107** becomes:

```ts
    vscode.commands.registerCommand("projectManager.refreshProjects", () => {
        providerManager.storageProvider.refresh();
        refreshProjects(true, true);
    });
```

- **The configuration handler**, after the `tags.collapseItems` block
  (`:205-208`) and its blank line, ahead of the `git.showBranchName` block.
  PR #986 inserts after the `git.showBranchName` block, so this placement
  keeps the two apart (WF-F6):

```ts
        if (cfg.affectsConfiguration("projectManager.worktrees.collapseItems")) {
            await StorageProvider.resetWorktreesExpansionState();
        }

        if (cfg.affectsConfiguration("projectManager.worktrees")) {
            providerManager.refreshStorageTreeView();
        }
```

### `src/whats-new/commands.ts`

Line 14's `.registerContentProvider("alefragnani", "project-manager", provider)`
becomes `.registerContentProvider(publisher, name, provider)`, preceded in
`registerWhatsNew` by:

```ts
    const { publisher, name } = Container.context.extension.packageJSON;
```

`ExtensionContext.extension` exists in VS Code ≥ 1.55, and `engines.vscode`
is `^1.78.0` (`package.json:8`).

### `src/test/runTest.ts`

In `main()`, inside the `try`, before `extensionDevelopmentPath`:

```ts
        // Set when the tests are started from a terminal of VS Code itself (an agent running in its
        // extension host, for example); it would make the downloaded VS Code start as plain Node.
        delete process.env.ELECTRON_RUN_AS_NODE;
```

Then `launchArgs` becomes:

```ts
        // A Linux host with no display, such as a server or CI without xvfb, runs VS Code headless.
        const headless = process.platform === "linux" && !process.env.DISPLAY && !process.env.WAYLAND_DISPLAY;
        ...
            launchArgs: [
                './testworkspace',
                ...(headless ? [ '--ozone-platform=headless' ] : [])
            ]
```

The file keeps its single quotes, as it has them today.

### `package.json`

- `:6` `"publisher": "alefragnani",` becomes `"publisher": "mattlightspeed",`.
- `:660` `"when": "extension == alefragnani.project-manager && extensionStatus == installed"`
  becomes `"when": "extension == mattlightspeed.project-manager && extensionStatus == installed"`.
- **In `projectManager-general`'s properties**, after
  `projectManager.git.showBranchName` (`:848-864`), add the following. It is
  the section's last property today, so its closing `}` at `:864` gains a
  comma. The file indents with tabs.

```json
"projectManager.worktrees.showInFavorites": {
	"type": "boolean",
	"default": true,
	"description": "%projectManager.configuration.worktrees.showInFavorites.description%"
},
"projectManager.worktrees.collapseItems": {
	"type": "string",
	"default": "startCollapsed",
	"enum": [
		"alwaysExpanded",
		"alwaysCollapsed",
		"startExpanded",
		"startCollapsed"
	],
	"enumDescriptions": [
		"%projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysExpanded%",
		"%projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysCollapsed%",
		"%projectManager.configuration.worktrees.collapseItems.enumDescriptions.startExpanded%",
		"%projectManager.configuration.worktrees.collapseItems.enumDescriptions.startCollapsed%"
	],
	"description": "%projectManager.configuration.worktrees.collapseItems.description%"
}
```

- **At the end of `menus["view/item/context"]`**, after the
  `projectManager.addToFavorites` entry (`:650-654`), add six entries. Each
  `when` is `view == projectsExplorerFavorites && viewItem == WorktreeNodeKind`,
  plus the platform clause shown:

| `command` | `group` | extra `when` |
|---|---|---|
| `_projectManager.openInNewWindow` | `inline` | — |
| `_projectManager.openInNewWindow` | `navigation` | — |
| `_projectManager.revealInFinder#sideBar` | `navigation@2` | `&& isMac` |
| `_projectManager.revealInExplorer#sideBar` | `navigation@2` | `&& isWindows` |
| `_projectManager.revealInFileManager#sideBar` | `navigation@2` | `&& isLinux` |
| `projectManager.addToWorkspace#sideBar` | `workspace` | — |

No entry names `WorktreeMissingNodeKind`. No command is added, so the
`commandPalette` section is unchanged.

### Strings

**Manifest strings.** Add these to `package.nls.json`, immediately after
`projectManager.configuration.tags.collapseItems.enumDescriptions.startCollapsed`
(`:106`):

| Key | English |
|---|---|
| `projectManager.configuration.worktrees.showInFavorites.description` | `Show the linked Git worktrees of each favorite project under it in the Favorites view.` |
| `projectManager.configuration.worktrees.collapseItems.description` | `Controls whether favorite projects with worktrees in the Favorites view start expanded or collapsed, and whether their state is remembered.` |
| `projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysExpanded` | `Favorite projects with worktrees are always expanded.` |
| `projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysCollapsed` | `Favorite projects with worktrees are always collapsed.` |
| `projectManager.configuration.worktrees.collapseItems.enumDescriptions.startExpanded` | `Favorite projects with worktrees start expanded, but remember your last expand/collapse state.` |
| `projectManager.configuration.worktrees.collapseItems.enumDescriptions.startCollapsed` | `Favorite projects with worktrees start collapsed, but remember your last expand/collapse state.` |

**Runtime strings.** Add these to `l10n/bundle.l10n.json`, at the end, each
mapped to itself as the file does:
- `{0} (missing)`
- `{0} (detached)`
- ``The folder of this worktree no longer exists. `git worktree prune` removes its record, unless the worktree is locked.``

**Translations.** The same keys go into each of the 8 languages: `az`, `cs`,
`fr`, `pt-br`, `ru`, `uk`, `zh-cn`, `zh-tw`.
- In `package.nls.<lang>.json`, they sit at the same anchor.
- In `l10n/bundle.l10n.<lang>.json`, they go at the end.
- Each translation is written by the implementer, following
  `.github/skills/vscode-ext-localization/SKILL.md`. Use the file's own
  `tags.collapseItems` strings as the model: the same verbs for
  expanded/collapsed/remember, with "favorite projects with worktrees" in
  place of "tag groups", in the file's own words for "favorite" and
  "project".
- Keep `Git`, `worktree`, `git worktree prune` and `{0}` as they are.
- Do not translate keys.
- The files keep four-space indentation and UTF-8. The `l10n` bundles keep
  ending without a newline after `}` (WF-F17). Adding at the end means a
  comma after what is now the last entry.
- `manifest.test.ts` checks that every key is present and non-empty.

### `src/test/suite/mocks/MockMemento.ts`

`createMockContext()` (`:25-28`) returns
`{ globalState, extensionUri: vscode.Uri.file(path.resolve(__dirname, "..", "..", "..", "..", "..")) }`.
That is the extension root, from `out/src/test/suite/mocks/`. Add
`import * as path from "path";`. Existing callers are unaffected.

## Order of work

Each step ends with `npm test` green, run as in *Verification*, at the
passing count shown.

0. **Bootstrap**, if `vscode-whats-new/` or `node_modules/` is empty:
   `git submodule update --init`, then `npm ci`. The submodule step runs
   outside Claude's sandbox (WF-F11). Expect 85 passing.
1. **Test runner** (`src/test/runTest.ts`, WF-D12). Expect **85**.
2. **Fork identity** (WF-D2, WF-F5):
   - `package.json:6` and `:660`;
   - `src/whats-new/commands.ts`;
   - `extension.test.ts`: lookup by path, plus the What's New test;
   - create `manifest.test.ts` with M4.

   Expect **87**.
3. **Reading records**: `src/utils/worktrees.ts`, `worktreeFixtures.ts`,
   `worktrees.test.ts`. Expect **111**.
4. **Worktree node**:
   - `WorktreeNode` in `nodes.ts`;
   - the three runtime strings in all 9 bundles;
   - `createMockContext`'s `extensionUri`;
   - `worktreeNode.test.ts`;
   - M6 in `manifest.test.ts`.

   Expect **122**.
5. **Watcher**: `worktreeWatcher.ts`, `worktreeWatcher.test.ts`. Expect
   **134**.
6. **Tree, settings and wiring**:
   - the two settings in `package.json`, and the six manifest strings in all
     9 `package.nls*.json`;
   - `storageProvider.ts`, `providers.ts`, `extension.ts`;
   - `storageProviderWorktrees.test.ts`;
   - M1, M2 and M5.

   Expect **157**.
7. **Menus**: the six `view/item/context` entries, and M3. Expect **158**.
8. **Finish**: lint, build, package, and the checks in *Verification*. Then
   the hand-over.

## Tests

"Fails before" means it fails on the tree as it stands before its step. A
test of a module that does not exist yet fails to compile, which fails
`npm test`'s `test-compile`. Every new test passes after its step.

### Fixtures: `src/test/suite/mocks/worktreeFixtures.ts` (new)

The mocha glob `**/**.test.js` (`src/test/suite/index.ts`) does not load this
file as a suite.

- `makeTempDir(prefix: string): string`: `fs.mkdtempSync` under
  `os.tmpdir()`, returned through `fs.realpathSync`.
- `removeTempDir(dir: string): void`: `fs.rmSync(dir, { recursive: true, force: true })`.
- `makeMainCheckout(parent: string, name: string, branch = "main"): string`
  creates `<parent>/<name>/.git/HEAD` = `ref: refs/heads/<branch>\n`, and
  returns `<parent>/<name>`.
- `toGitPath(fsPath: string): string` joins `fsPath`'s segments with `/`,
  as git writes paths on every platform. It changes nothing on Linux.
- `addLinkedWorktree(commonDir: string, id: string, worktreePath: string, options: { branch?: string; detached?: boolean; createTree?: boolean; relativeGitdir?: boolean } = {}): string`.
  It returns the record folder, `<commonDir>/worktrees/<id>`, and writes:
  - `gitdir`: `toGitPath(path.join(worktreePath, ".git"))`, or, when
    `relativeGitdir`, `toGitPath` of that path relative to the record
    folder, plus `\n`;
  - `commondir`: `../..\n`;
  - `HEAD`: `0123456789abcdef0123456789abcdef01234567\n` when `detached`,
    else `ref: refs/heads/<branch ?? "main">\n`.

  Unless `createTree === false`, it also creates `worktreePath`, with
  `.git` = `gitdir: <toGitPath(record folder)>\n`.
- `waitFor(predicate: () => boolean, timeoutMs = 2000): Promise<void>`
  polls every 25 ms and rejects with `Error("timed out")`.
- `sleep(ms: number): Promise<void>`.

Each suite makes its fixtures in a fresh temp dir per test, and removes it in
`teardown`. The suites of `worktrees.test.ts`, `worktreeWatcher.test.ts` and
`storageProviderWorktrees.test.ts` are written as
`suite("…", function () { this.timeout(5000); … })`.
Mocha's default of 2000 ms equals `waitFor`'s, so without the change a slow
event would fail on mocha's timeout, before `waitFor` could report it.
New test files use no `any`, so that they add no lint warning
(*Verification*): a cast to a private member goes through `unknown`, as in
W9.

### `src/test/suite/worktrees.test.ts` (new): 24 tests

All fail before step 3, since the module does not exist.

Suite **"getGitCommonDir"**, with `root = makeTempDir("worktrees-")`:
- **G1** `returns undefined for a folder without .git`: a plain folder gives
  `undefined`, and so does an existing file `<root>/x.code-workspace`.
- **G2** `returns the .git folder of a main checkout`: `makeMainCheckout`,
  then `strictEqual(getGitCommonDir(repo), path.join(repo, ".git"))`.
- **G3** `follows a linked worktree's .git file and commondir to the clone's .git folder`:
  record `feat`, tree `<root>/worktrees/repo/feat`. The tree gives
  `<repo>/.git`.
- **G4** `resolves a relative gitdir line against the project folder`: a
  tree whose `.git` reads `gitdir: ../../../repo/.git/worktrees/feat`. It
  gives `<repo>/.git`.
- **G5** `returns the folder a .git file names when it has no commondir`:
  `<sub>/.git` = `gitdir: <root>/modules/sub`, and `<root>/modules/sub/`
  has no `commondir`. It gives `<root>/modules/sub`.
- **G6** `returns undefined for a .git file without a gitdir line`: `.git`
  = `not a gitdir\n` gives `undefined`.
- **G7** `returns undefined when commondir cannot be read`: G3's layout,
  with the record's `commondir` replaced by a folder of that name. Reading
  it throws `EISDIR` on every platform, and the tree gives `undefined`. It
  covers the `catch`.

Suite **"getLinkedWorktrees"**:
- **L1** `returns [] for a folder that is not a git repository`: `[]`.
- **L2** `returns [] when the clone has no worktrees folder`:
  `makeMainCheckout` only, gives `[]`.
- **L3** `returns [] for an empty worktrees folder`: `<repo>/.git/worktrees/`
  created empty, gives `[]`.
- **L4** `lists each linked worktree with its path and branch, sorted by path`:
  - records `b` and then `a`, with trees `<root>/worktrees/repo/zeta`
    (branch `zeta`) and `<root>/worktrees/repo/alpha` (branch `feature/alpha`);
  - `deepStrictEqual` to
    `[{ path: <…/alpha>, branch: "feature/alpha", missing: false }, { path: <…/zeta>, branch: "zeta", missing: false }]`.
- **L5** `marks a record whose folder is gone as missing, with no branch`:
  `createTree: false` gives `[{ path, branch: undefined, missing: true }]`.
- **L6** `marks a folder whose .git file was removed as missing`: the tree
  is created, then its `.git` is unlinked. It gives `missing: true` and
  `branch: undefined`.
- **L7** `gives no branch for a detached HEAD`: `detached: true` gives
  `missing: false` and `branch: undefined`.
- **L8** `resolves a relative gitdir record against its own folder`:
  `relativeGitdir: true` gives the absolute tree path.
- **L9** `drops trailing whitespace and the /.git suffix, as git does`: the
  record's `gitdir` is overwritten with `<tree>/.git \n\t\n`. It gives
  `path === <tree>`.
- **L10** `takes a gitdir with no /.git suffix as the folder itself`:
  `gitdir` = `<tree>\n` gives `path === <tree>`.
- **L11** `skips a record with no gitdir file`: a record folder with only
  `HEAD`. The result has length 0.
- **L12** `skips a record whose gitdir file is empty or only whitespace`:
  - `gitdir` of 0 bytes gives length 0, as in git;
  - `gitdir` = ` \n` gives length 0, where git would list the record
    folder (WF-D5).
- **L13** `ignores entries of the worktrees folder that are not folders`: a
  file `<repo>/.git/worktrees/stray` beside one valid record gives length 1.
  Reading `stray/gitdir` fails with `ENOTDIR`, which covers that path
  through `readWorktreePath`'s `catch`.
- **L14** `from a linked worktree, lists the clone's other linked worktrees but not itself`:
  records `a` and `b`, called with tree `a`. The paths are `[<b>]`.
- **L15** `recognises the favorite itself through a symlink`: a symlink
  `<root>/link-a` → tree `a`, made with
  `fs.symlinkSync(<tree a>, <root>/link-a, "junction")` (the type is
  ignored outside Windows, and needs no rights there). Called with the link,
  the paths are `[<b>]`.
- **L16** `lists the worktrees of a clone whose .git file has no commondir`:
  G5's layout, plus a record under `<root>/modules/sub/worktrees/x` with a
  tree. Length 1.
- **L17** `agrees with git worktree list --porcelain`. It is a
  `function () { … }` test, so that `this.skip()` is available. Skip it when
  `execFileSync("git", ["--version"])` throws.
  - Run git through `execFileSync("git", args, { env })`, isolated from the
    machine's git:
    - `env` is `process.env` without any `GIT_*` variable, so that a run
      from inside a git hook cannot act on the outer repo, plus
      `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL=<root>/gitconfig`, an
      empty file, so that no user's hooks, signing or default branch apply;
    - every call starts `-c user.name=t -c user.email=t@t -c init.defaultBranch=main`.
  - The calls, with `<repo>` = `<root>/repo`:
    - `init <repo>`;
    - `-C <repo> commit --allow-empty -m init`;
    - `-C <repo> worktree add -b feat-a <root>/worktrees/repo/feat-a`;
    - `-C <repo> worktree add -b feat-b <root>/elsewhere`.

    Then remove `<root>/elsewhere` with `fs.rmSync`.
  - Parse `git -C <repo> worktree list --porcelain`, dropping the first
    stanza, which is the main tree.
  - Each side's paths go through `path.resolve`, since git prints `/`
    separators. The set of `worktree` paths then equals
    `getLinkedWorktrees(<repo>)`'s.
  - For each tree, `branch refs/heads/X` gives `X`, matching `branch`
    whenever not `missing`.
  - A `prunable` line is present exactly for `missing`.

### `src/test/suite/worktreeNode.test.ts` (new): 10 tests

All fail before step 4. Suite **"WorktreeNode"**: `suiteSetup`
`Container.initialize(createMockContext())`, with
`projectPath = "/sites/passwave/passwave-web"`.
- **N1** `labels a tree by its branch`:
  `{ path: "/sites/passwave/worktrees/passwave-web/feat-x", branch: "feat/x", missing: false }`
  gives `label === "feat/x"`.
- **N2** `labels a detached tree by its folder name and says so`:
  - branch `undefined` gives `label === "feat-x"`;
  - `description === "worktrees/passwave-web/feat-x (detached)"`.
- **N3** `describes a tree by its path relative to the favorite's parent folder`:
  N1's tree gives `description === "worktrees/passwave-web/feat-x"`.
- **N4** `describes a tree outside the favorite's parent folder by its absolute path`:
  - tree `/tmp/wt-check` (relative path `../../tmp/wt-check`) gives
    `description === "/tmp/wt-check"`;
  - tree `/sites` (relative path `..`) gives `description === "/sites"`.
- **N5** `opens through _projectManager.open with the tree's path, its label and the favorite's profile`:
  - `command.command === "_projectManager.open"`;
  - `deepStrictEqual(command.arguments, [path, "feat/x", "work"])`.
- **N6** `is a WorktreeNodeKind with a git-branch icon`:
  - `contextValue === "WorktreeNodeKind"`;
  - `(iconPath as ThemeIcon).id === "git-branch"`.
- **N7** `a missing tree has no command, is a WorktreeMissingNodeKind with a warning icon, and says so`:
  - `command === undefined`;
  - `contextValue === "WorktreeMissingNodeKind"`;
  - the icon id is `warning`;
  - `description === "<relative> (missing)"`;
  - `(tooltip as MarkdownString).value` contains `git worktree prune` and
    the path.
- **N8** `is never collapsible`:
  `collapsibleState === TreeItemCollapsibleState.None`.
- **N9** `carries the tree's path in its resourceUri`:
  - `resourceUri.scheme === "projectManager-view"`;
  - `resourceUri.path === <tree path>`.
- **N10** `describes a tree in a folder whose name starts with .. by its relative path`:
  tree `/sites/passwave/..wt/feat` (relative path `..wt/feat`) gives
  `description === "..wt/feat"`.

The English assertions hold because the test host runs in English.

### `src/test/suite/worktreeWatcher.test.ts` (new): 12 tests

All fail before step 5. Suite **"WorktreeWatcher"**:
- Each test makes `commonDir = <tmp>/repo/.git`, and a
  `new WorktreeWatcher(() => calls++, 50)`.
- It disposes the watcher in `teardown`.
- "No call" means `calls` is unchanged after `sleep(400)`.

The tests:
- **W1** `calls back once, after the delay, when worktree records are added`:
  - `worktrees/` exists, and `watch([commonDir])`;
  - `mkdir worktrees/a` and `worktrees/b` back to back;
  - `waitFor(calls === 1)`, then `sleep(300)`, and still `calls === 1`.
- **W2** `calls back when the worktrees folder is created, and keeps watching it`:
  - no `worktrees/`, and `watch`;
  - `mkdir worktrees`, then `waitFor(calls === 1)`;
  - `mkdir worktrees/a`, then `waitFor(calls === 2)`.
- **W3** `calls back when the worktrees folder is removed, and again when it returns`:
  - with `worktrees/a`, `rmSync(worktrees)`, then `waitFor(calls >= 1)`;
  - note `n`, then `mkdir worktrees` and `worktrees/b`, then
    `waitFor(calls > n)`.
- **W4** `ignores other changes in the git folder`: writing `HEAD`,
  `index.lock` and `logs/x` in `commonDir` makes no call.
- **W5** `stops watching a folder dropped from the list`:
  - two clones, `watch([a, b])`, then `watch([b])`;
  - `mkdir a/worktrees` makes no call;
  - `mkdir b/worktrees` gives `waitFor(calls === 1)`.
- **W6** `watching the same folder twice calls back once per change`:
  `watch([a])` twice, then `mkdir a/worktrees`. Exactly 1 call after
  `sleep(400)`.
- **W7** `skips a folder that does not exist`:
  `doesNotThrow(() => watch([<tmp>/nope/.git]))`.
- **W8** `dispose stops every watcher and a pending call`:
  - `watch`, `mkdir worktrees`, then `dispose()` at once;
  - no call, and a later `mkdir worktrees/a` makes no call.
- **W9** `an error from a git-folder watcher stops watching that folder`:
  - after `watch`, reach the private map:
    `(watcher as unknown as { watched: Map<string, { gitDirWatcher: fs.FSWatcher }> }).watched.get(commonDir).gitDirWatcher.emit("error", new Error("x"))`;
  - the map no longer has `commonDir`, and `mkdir worktrees` makes no call.
- **W10** `an error from a worktrees-folder watcher closes it quietly`:
  - with `worktrees/`, emit `"error"` on `worktreesWatcher`;
  - `doesNotThrow`, and the git-folder watcher still works: removing
    `worktrees` gives a call.
- **W11** `rewatching a folder that is no longer watched does nothing`:
  `(watcher as unknown as { rewatchWorktrees(commonDir: string): void }).rewatchWorktrees(<tmp>/nope/.git)`
  does not throw, and makes no call. It covers `rewatchWorktrees`'s guard,
  which no real event reaches: a closed `FSWatcher` delivers nothing.
- **W12** `an event without a file name refreshes`:
  - Node gives no file name on some platforms. On Linux it always does, so
    the test replaces `fs.watch` for its duration, through
    `fs as unknown as { watch: unknown }`, and restores it in `finally`;
  - the fake records each listener by path and returns an `EventEmitter`
    with a `close()` method;
  - after `watch([commonDir])`, calling the listener for `commonDir` with
    `("rename", null)` gives `waitFor(calls === 1)`, and the fake was asked
    to watch `<commonDir>/worktrees` again.

### `src/test/suite/storageProviderWorktrees.test.ts` (new): 20 tests

Suite **"StorageProvider worktrees"**:
- `suiteSetup`: `Container.initialize(createMockContext())`, then the same
  three settings resets as `teardown`. Settings written with
  `ConfigurationTarget.Global` land in `.vscode-test/user-data`, which
  persists between runs, so a run that died mid-suite would otherwise leave
  them set.
- `setup`:
  - a temp root;
  - `storage = new ProjectStorage(<root>/projects.json)`, never saved;
  - `provider = new StorageProvider(storage)`;
  - favorites built with `storage.push(name, path, tags, profile)` and the
    fixtures.
- `teardown`:
  - `provider.dispose()`;
  - reset `worktrees.showInFavorites`, `worktrees.collapseItems` and
    `git.showBranchName` with
    `getConfiguration("projectManager").update(key, undefined, ConfigurationTarget.Global)`;
  - `Container.context.globalState.update("viewAsList", undefined)`;
  - `await StorageProvider.resetWorktreesExpansionState()` and
    `resetTagExpansionState()`;
  - remove the temp root.

The tests:
- **S1** `a favorite with linked worktrees starts collapsed`: in list view,
  `repo` with one record gives the root node `repo` with
  `collapsibleState === Collapsed`. Fails before: `None`.
- **S2** `a favorite with no linked worktrees, or not a repository, is not collapsible`:
  a main checkout with no records, and a plain folder, are both `None`.
  Passes before; a regression guard.
- **S3** `a remote favorite is not collapsible and has no children`:
  rootPath `vscode-remote://ssh-remote+host/srv/x` gives `None`, without
  throwing, and `getChildren(<its node>)` gives `[]`. Both pass before, the
  second by accident, as S8 does. After the change, the second covers the
  remote guard in `getWorktreeNodes`.
- **S4** `expanding a favorite lists its worktrees as WorktreeNodes sorted by label`:
  - records with branches `gamma10`, `Beta`, `gamma9` and `alpha`;
  - `getChildren(repoNode)` gives `alpha, Beta, gamma9, gamma10`, each an
    `instanceof WorktreeNode`.
  - Fails before: `getChildren` treats the node as a tag.
- **S5** `worktree children carry the favorite's profile`: in list view, a
  favorite pushed with profile `work`. Each child's `command.arguments[2]`
  is `"work"`. Fails before.
- **S6** `in tag view, a favorite under its tag is collapsible and expands to its worktrees`:
  - `viewAsList` false, and the favorite tagged `Work`;
  - root gives `TagNode` `Work`;
  - its child `repo` is `Collapsed`, and its children are one
    `WorktreeNode`.
  - Fails before.
- **S7** `with worktrees.showInFavorites off, a favorite with worktrees is not collapsible`:
  the setting `false` gives `None`. Passes before.
- **S8** `with worktrees.showInFavorites off, expanding a favorite gives no children`:
  `getChildren(repoNode)` gives `[]`. Passes before, by accident: no tag
  named `repo`.
- **S9** `a WorktreeNode has no children`: `getChildren(<a child>)` gives
  `[]`. Fails before, since `WorktreeNode` does not exist.
- **S10** `alwaysExpanded starts a favorite with worktrees expanded`:
  `collapseItems` `alwaysExpanded` gives `Expanded`.
- **S11** `alwaysCollapsed ignores a remembered expansion`:
  `rememberWorktreesExpansion` cannot store under `alwaysCollapsed`. So store
  under the default `startCollapsed` with
  `rememberWorktreesExpansion(repo, true)`, then switch to
  `alwaysCollapsed`. It gives `Collapsed`.
- **S12** `startCollapsed and startExpanded honour a remembered state`:
  - `startCollapsed` plus a remembered `true` gives `Expanded`;
  - `startExpanded` plus a remembered `false` gives `Collapsed`.
- **S13** `rememberWorktreesExpansion stores the state only for startExpanded and startCollapsed`:
  - under `alwaysExpanded`, `rememberWorktreesExpansion(repo, false)`, then
    switch to `startExpanded`: `Expanded`, so nothing was stored;
  - under `startExpanded`, the same call gives `Collapsed`.
- **S14** `resetWorktreesExpansionState forgets remembered states`: remember
  `true` under `startCollapsed`, reset, then `Collapsed`.
- **S15** `worktree and tag expansion states are stored apart`. Under
  `startCollapsed`, with the tag id equal to the favorite's path:
  - `rememberWorktreesExpansion(repo, true)` leaves
    `getTagCollapsibleState(repo, "startCollapsed")` `Collapsed`;
  - then `resetWorktreesExpansionState()` and `setTagExpanded(repo, true)`
    leave `getWorktreesCollapsibleState(repo)` `Collapsed`.
- **S16** `refreshesOnWindowFocus follows git.showBranchName and worktrees.showInFavorites`:
  - `never` and `false` gives `false`;
  - `never` and `true` gives `true`;
  - `onlyInSideBar` and `false` gives `true`;
  - `always` and `false` gives `true`;
  - `onlyInCommandPalette` and `false` gives `false`.
- **S17** `a new worktree record refreshes the tree`:
  - subscribe to `provider.onDidChangeTreeData`, counting;
  - `await provider.getChildren()`, which arms the watcher;
  - `addLinkedWorktree` creates a record;
  - `waitFor(count >= 1)`.
  - Fails before: no watcher.
- **S18** `with worktrees.showInFavorites off, a new worktree record does not refresh the tree`:
  as S17 with the setting `false`, but `count === 0` after `sleep(800)`.
  Passes before.
- **S19** `git.showBranchName still describes a favorite by its branch`:
  `always`, and the main checkout on `develop`, gives the root node with
  `description === "develop"`. Passes before; a regression guard.
- **S20** `worktrees with the same label are ordered by path`: two detached
  trees, `<root>/b/x` and `<root>/a/x`, both labelled `x`. `getChildren`
  gives the `a` tree first. It covers the comparator's tie-break. Fails
  before.

### `src/test/suite/manifest.test.ts` (new): 6 tests

Suite **"Manifest"**:
- `suiteSetup` finds the extension under test as
  `vscode.extensions.all.find(e => e.extensionPath === path.resolve(__dirname, "..", "..", "..", ".."))`.
  That is the repo root, from `out/src/test/suite/`. It reads
  `packageJSON`.
- `NEW_SETTING_KEYS` is the six keys in *Strings*, and `NEW_RUNTIME_KEYS`
  the three.
- `LANGS` is `["az", "cs", "fr", "pt-br", "ru", "uk", "zh-cn", "zh-tw"]`.

The tests:
- **M1** `contributes projectManager.worktrees.showInFavorites, on by default`:
  the property has `type: "boolean"` and `default: true`, and
  `getConfiguration("projectManager").inspect("worktrees.showInFavorites").defaultValue === true`.
  Added in step 6, and fails before it.
- **M2** `contributes projectManager.worktrees.collapseItems with the tags' modes, startCollapsed by default`:
  its `enum` `deepStrictEqual`s `projectManager.tags.collapseItems`'s
  `enum`, and its default is `"startCollapsed"`. Fails before step 6.
- **M3** `gives worktree nodes only the open-in-new-window, reveal and add-to-workspace menus`:
  - the `view/item/context` entries whose `when` contains
    `viewItem == WorktreeNodeKind`, mapped to `${command}|${group}`, equal
    the six rows' set;
  - no entry's `when` contains `WorktreeMissingNodeKind`;
  - every such `when` starts with `view == projectsExplorerFavorites`.
  - Fails before step 7.
- **M4** `the What's New extension menu names the extension's own id`: the
  `extension/context` entry for `_projectManager.whatsNewContextMenu` has a
  `when` that contains `` `extension == ${extension.id}` ``.
  - Under upstream's id it would pass, since menu and id agree.
  - It fails if `package.json:6` changes without `:660`, which is the slip it
    guards against in step 2.
- **M5** `every new setting string is in each package.nls file`: for
  `package.nls.json` and each `package.nls.<lang>.json`, every key in
  `NEW_SETTING_KEYS` is a non-empty string. Fails before step 6.
- **M6** `every new runtime string is in each l10n bundle`: the same for
  `l10n/bundle.l10n.json` and each `l10n/bundle.l10n.<lang>.json`, with
  `NEW_RUNTIME_KEYS`. Fails before step 4.

### `src/test/suite/extension.test.ts` (changed): 1 new test

- `:22` becomes
  `extension = vscode.extensions.all.find(e => e.extensionPath === path.resolve(__dirname, '..', '..', '..', '..')) as vscode.Extension<any>;`.
  The file already imports `path`.
- **New test** `What's New opens for the extension's own id`:
  `await extension.activate()`, then
  `await assert.doesNotReject(Promise.resolve(vscode.commands.executeCommand('projectManager.whatsNew')))`.
  - The file uses single quotes. The title, which holds apostrophes, may be
    double-quoted.
  - Fails before step 2's `commands.ts` change: with the publisher changed,
    `showPage` reads `packageJSON` of `undefined` (`Manager.ts:83`, `:94`).
  - Under the current id, the command resolved in the review-1 probe.
  - It closes the panel afterwards with
    `vscode.commands.executeCommand('workbench.action.closeActiveEditor')`.
    Activation in the test host also opens a What's New page, since its
    `globalState` starts empty (`Manager.ts:130-150`), and that one may stay
    open. No test depends on the editors.

### Coverage

The tests above cover every branch of the new modules (`worktrees.ts`,
`WorktreeNode`, `worktreeWatcher.ts`), and every new or changed branch in
`storageProvider.ts` and `commands.ts`, and every manifest change. Branch by
branch:
- `getGitCommonDir`: G1-G7. `getLinkedWorktrees`: L1-L3, L13-L15.
  `readWorktreePath`: L8-L12. `comparablePath`'s `catch`: L5, whose tree
  does not exist.
- `WorktreeNode` and `describeWorktree`: N1-N10. Both operands of
  `climbsOut` are covered by N4, its false case by N3 and N10.
- `WorktreeWatcher`: W1-W12. W11 covers `rewatchWorktrees`'s guard and W12
  the `!filename` operand, neither of which a real event on Linux reaches.
- `StorageProvider`: S1-S20. S20 covers the comparator's tie-break.

`runTest.ts` is covered by running: its headless branch on this server, the
other under CI's `xvfb-run`, which this plan does not run.

The event wiring in `providers.ts` and `extension.ts` is not reachable from a
unit test. Creating a second `projectsExplorerFavorites` tree view in the test
host is not supported, and the extension under test has its own module
instances (WF-F15). That wiring is:
- the subscription push;
- the focus listener's two calls;
- the `else if` that calls `rememberWorktreesExpansion`;
- the Refresh Projects lambda;
- the two configuration branches.

The logic they call is tested above (S12-S16, S17), and the wiring itself is
covered by manual checks 1, 4, 5 and 6 in the hand-over.

## Verification

Run these from the repo root with `PATH=/home/claude/.local/node/bin:$PATH`.
The `npm test` and `vsce` commands run **outside Claude's sandbox**
(WF-D12). In a Claude session that means `dangerouslyDisableSandbox`. In
Matt's own terminal it needs nothing extra.

1. `npm run lint`: `0 errors`, and at most 52 warnings.
   - No warning names a file this plan adds.
   - Two files it changes already carry four warnings, which stay as they
     are and no more: `src/test/suite/extension.test.ts:18` and `:22`, and
     `src/test/suite/mocks/MockMemento.ts:9` and `:15`, all
     `no-explicit-any` (run in review 1). The new `:22` keeps its one `any`.
   - No other file this plan changes has a warning today, and none gains one.
2. `npm run build`: `webpack … compiled successfully`.
3. `npm test`, which also runs `pretest`'s compile and lint: `158 passing`,
   `0 failing`, and L17 not skipped on this server, which has git 2.43.0.
4. `git diff --stat` touches only the files in *Files* (plus `plans/`).
   `git status --short` shows the six new test and fixture files and the two
   new source files as untracked.
5. `npx --yes @vscode/vsce@4.0.0 package` writes
   `project-manager-13.1.1.vsix` in the repo root, ignored by `*.vsix`. Then:
   - `unzip -p project-manager-13.1.1.vsix extension/package.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['publisher'], d['name'], d['version'])"`
     prints `mattlightspeed project-manager 13.1.1`;
   - `unzip -l project-manager-13.1.1.vsix | grep -cE 'plans/|AGENTS.md'`
     prints `0`;
   - `unzip -Z1 project-manager-13.1.1.vsix | grep -cE '(^|/)\.'` prints
     `0`: no dotfile, such as `.claude/` (WF-F12), is packaged;
   - `unzip -l project-manager-13.1.1.vsix | grep -c 'extension/dist/extension.js'`
     prints `1`.
6. `python3 plans/tools/plan_links.py --check` passes.

The hand-over below is done when Matt's checks pass.

## Hand-over: installing the fork (Matt)

Run in a terminal of a VS Code window connected to the server. That window
runs as `claude`, and its `code` command is VS Code's remote CLI. Do all
steps in one go, so that no favorite is saved to the old file after the copy.
Two VS Code servers run on this host, for different windows, and share the
installed extensions (WF-F13). So no other window should save a favorite
between steps 1 and 4.

0. First, in the Extensions view, look under **Local - Installed**. The
   extension prefers the client when a copy is there (WF-F13). If Project
   Manager is listed there, disable it for this workspace, or uninstall it
   from the client, before going on. Otherwise it would run beside the
   fork, under the other id.

```bash
# 1. Copy the favorites out of the folder VS Code deletes with the marketplace copy (WF-F3),
#    and keep a frozen copy beside them.
mkdir -p /home/claude/.config/project-manager
cp -p /home/claude/.vscode-server/data/User/globalStorage/alefragnani.project-manager/projects.json \
      /home/claude/.config/project-manager/projects.json
cp -p /home/claude/.config/project-manager/projects.json \
      /home/claude/.config/project-manager/projects.json.pre-fork

# 2. Point the extension at them. Machine settings are plain JSON today (WF-F13);
#    if this fails on a comment, add the line by hand with "Preferences: Open Remote Settings (JSON)".
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path("/home/claude/.vscode-server/data/Machine/settings.json")
s = json.loads(p.read_text())
s["projectManager.projectsLocation"] = "/home/claude/.config/project-manager"
p.write_text(json.dumps(s, indent=2) + "\n")
EOF

# 3. Swap the extensions.
code --uninstall-extension alefragnani.project-manager
code --install-extension /srv/projects/vscode-project-manager/project-manager-13.1.1.vsix --force
```

4. Command Palette → **Developer: Reload Window**, in every window connected
   to this server.

**What to expect:**
- The Extensions view lists **Project Manager** by `mattlightspeed`, 13.1.1,
  under the server's section, and no `alefragnani` copy.
- What's New opens once.
- Favorites reads **Favorites (35)**, as a list. Click **View as Tags** to
  group it again. The recent stack, any tag filter and remembered
  expand/collapse also start afresh (WF-D4).
- The Git view rebuilds its cache under the new id, so its first scan of
  `/usr/share/nginx/sites` runs again.
- `globalStorage/alefragnani.project-manager/` is deleted at VS Code's next
  extension clean-up, when a server starts or a client asks for one
  (WF-F3). That may be some time after the reload. Expect it. The favorites
  now live in `~/.config/project-manager/`, with `projects.json.pre-fork`
  beside them.

**Manual checks:**
1. Favorites with linked worktrees have a twistie, and others do not.
   Clicking a favorite's name still opens it. Expand one and reload: it is
   still expanded. Collapse it and reload: it is collapsed.
2. Expand `passwave-web`. Its child is labelled by the tree's branch and
   described by its location. At the time of writing that is `main`,
   described `passwave-web-main`. Clicking it opens that folder.
3. A child's inline **Open in New Window** works. Its menu shows Open in New
   Window, Reveal in File Manager and Add to Workspace, and nothing else.
4. In a terminal:
   `git -C /srv/projects/vscode-project-manager worktree add /tmp/wt-check -b wt-check`.
   - Within about a second, `vscode-project-manager` (tagged `Standalone`)
     gets a twistie. Expanding it shows a child `wt-check`, described
     `/tmp/wt-check`.
   - Then `rm -rf /tmp/wt-check`, and run **Project Manager: Refresh
     Projects**. The child shows a warning icon, `/tmp/wt-check (missing)`,
     and does nothing on click.
   - Then `git -C /srv/projects/vscode-project-manager worktree prune && git -C /srv/projects/vscode-project-manager branch -D wt-check`.
     The child and the twistie go without a refresh.
5. Set `"projectManager.worktrees.showInFavorites": false`. The twisties
   vanish without a reload. Set it back to `true`.
6. Set `"projectManager.worktrees.collapseItems": "alwaysExpanded"`. Favorites
   with worktrees show expanded (a reload may be needed: WF-R11). Then
   remove the setting.
7. Repeat check 2 in tag view and in list view.
8. With `"projectManager.git.showBranchName": "always"`, favorites still show
   their branch as a description.
9. This one is upstream behaviour, unchanged here. Right-click a favorite
   and choose **Open**, and note whether it opens. It answers WF-R3.

**Rolling back:** `code --uninstall-extension mattlightspeed.project-manager`,
then `code --install-extension alefragnani.project-manager`, then reload.
`projectManager.projectsLocation` keeps both copies on the same favorites.

## Commits (WF-D13)

The implementer does not commit. Matt commits on `master`, in this order:
1. **Run the VS Code tests headless on Linux**: `src/test/runTest.ts`.
2. **Fork identity: publisher mattlightspeed**:
   - `package.json`: the `:6` and `:660` hunks only (`git add -p package.json`);
   - `src/whats-new/commands.ts`;
   - `src/test/suite/extension.test.ts`.
3. **Show linked worktrees under their favorite**: the rest. That is
   `src/utils/worktrees.ts`, `src/sidebar/*`, `src/extension.ts`, the
   remaining `package.json` hunks, `package.nls*.json`, `l10n/*`,
   `src/test/suite/mocks/*`, and the five new test files.
4. **Plans**: `plans/`, with this plan marked implemented and the register
   entries.

Each commit leaves the suite green on top of the ones before it.
`manifest.test.ts` goes wholly in commit 3, M4 included. It finds the
extension by its path, and M4 compares the menu with whatever id the
extension has, so it passes under upstream's id as well. Commit 3 is
therefore the one an upstream PR would cherry-pick, and it needs neither 1
nor 2.

## Staying in step with upstream

- **Merging upstream:**

  ```bash
  git fetch upstream
  git merge upstream/master
  ```

  - `package.json:5-6` conflicts whenever upstream bumps `version`, because
    the line sits beside `publisher` (WF-R8). Keep upstream's `version` and
    `"publisher": "mattlightspeed"`.
  - If upstream edits [[expose-public-extension-api]], take upstream's text
    and run `python3 plans/tools/plan_links.py --convert` (WF-F16).
  - If upstream merges PR #986, its edits sit apart from this plan's in
    `package.json`, `package.nls*.json` and `src/extension.ts` (WF-F6), and
    it does not touch the files this plan adds. Its `getGitDir` in
    `src/utils/git.ts` may then replace `getGitCommonDir`'s `.git`-file
    reading (WF-D5, WF-R20).
- **After a merge:** `git submodule update --init`, `npm ci`, the
  *Verification* steps, then the hand-over's step 3 with the new VSIX, and a
  reload. Steps 1-2 are one-off.
- **An upstream PR** of the feature is deferred (WF-R7).

## Assumed, not verified

- **The context-menu "Open" fails on a node.** This was read in code (WF-F8),
  not run, since it needs the UI. Manual check 9 answers it.
- **A `worktrees.collapseItems` change may not re-apply to rows VS Code has
  already rendered until reload**, as for `tags.collapseItems` (WF-R11).
  This is not checked.
- **The client holds `globalState`.** This is inferred from the extension
  host proxying it to `MainThreadStorage`. The client was not inspected.
  Nothing depends on it (WF-F4).
- **When a client asks the server for its extension clean-up**, which is
  when the old global-storage folder goes (WF-F3). That the server does it
  at start, and what it deletes, was read. The hand-over expects it to be
  late.
- **The remote CLI `code --uninstall-extension` / `--install-extension`.**
  The flags were read in the remote CLI's `--help` (WF-F13). They were not
  run, since running them is the swap.
- **No copy of Project Manager is enabled on Matt's client.** The evidence
  is that the server's copy is the one writing `projects.json` (WF-F13). The
  hand-over's step 0 checks.
- **A favorite gains its twistie on refresh** when its first worktree
  appears, without a reload. This is VS Code's tree reading a changed
  `collapsibleState` for a known row. It was not run. Manual check 4 shows
  it.
- **A `tags.collapseItems` value set in machine settings, beside
  `projectManager.tags`, is lost** (WF-F18). This is inferred from the lost
  default, not run.
- **The translations** are the implementer's. No native speaker reviews
  them.
- **Windows and macOS** path handling in `worktrees.ts`: separators, and case
  in `realpathSync`. Only Linux is run. The fixtures write paths with `/`,
  as git does, so that the tests would not fail on the fixtures alone.

## Residue

| ID | Flavour | Severity | Item | Owner |
|---|---|---|---|---|
| WF-R1 | handover | S1 | Matt installs the fork: checks the client has no Project Manager copy, copies the favorites to `~/.config/project-manager`, sets `projectManager.projectsLocation`, uninstalls the marketplace copy, installs the VSIX, reloads every window, and runs the manual checks (*Hand-over*). Done out of order, the uninstall deletes the favorites (WF-F3) | vscode-project-manager (Matt) |
| WF-R2 | limitation | S3 | A branch switch inside a tree, or a tree folder deleted by hand, shows only at the next window focus, Refresh Projects, settings change or favorites edit, since the watcher sees records come and go only (WF-F10, WF-D10) | vscode-project-manager |
| WF-R3 | open-question | S3 | The context-menu "Open" on a favorite may fail, because it passes the node as a path (WF-F8). Confirm with manual check 9; if confirmed, fix in the fork or report upstream | vscode-project-manager |
| WF-R4 | limitation | S4 | In tag view, favorites and their worktrees open without the favorite's profile, because `getProjectsByTag` drops it (WF-F14). Upstream's behaviour | vscode-project-manager |
| WF-R5 | limitation | S4 | The ✔ badge and the status bar do not mark a worktree window, unless the tree is itself a favorite or auto-detected (`decoration.ts:14`, `statusBar.ts:52-77`) | vscode-project-manager |
| WF-R6 | limitation | S4 | A tree that is also saved as a favorite shows twice: as a favorite, and under its repo | vscode-project-manager |
| WF-R7 | deferred | S4 | Offering the feature upstream: cherry-pick commit 3 onto `upstream/master`, add a README section, and open a PR that accounts for PR #986 | vscode-project-manager |
| WF-R8 | limitation | S4 | Each upstream release conflicts at `package.json:5-6`, where `version` sits beside `publisher`; the resolution is in *Staying in step with upstream* | vscode-project-manager |
| WF-R9 | limitation | S4 | What's New opens once on the fork's first activation, and Help and Feedback's links still lead to upstream's pages (WF-F5) | vscode-project-manager |
| WF-R10 | limitation | S4 | `npm test`, `vsce package` and `git submodule update --init` must run outside Claude's sandbox on this server (WF-F11, WF-F12) | vscode-project-manager |
| WF-R11 | limitation | S4 | A change to `worktrees.collapseItems` may need a reload for rows already shown, as for `tags.collapseItems` (assumed) | vscode-project-manager |
| WF-R12 | limitation | S4 | Path handling on Windows and macOS is not exercised | vscode-project-manager |
| WF-R13 | non-goal | S4 | Worktrees in the Git view, which upstream's PR #986 covers | vscode-project-manager |
| WF-R14 | non-goal | S4 | Creating or removing worktrees from the extension | vscode-project-manager |
| WF-R15 | non-goal | S4 | README and CHANGELOG are left as upstream's (WF-D15) | vscode-project-manager |
| WF-R16 | owned-elsewhere | S3 | Where worktrees go: [[sonata-server-automation:wt-01-worktree-layout]] and [[claude-setup:plan-links-worktree-layout]] | sonata-server-automation, claude-setup |
| WF-R17 | limitation | S3 | Upstream defect, not fixed here: `projectManager.tags.collapseItems` extends the key of the `projectManager.tags` array, so it loses its default, and likely a value set beside `projectManager.tags` (WF-F18). Fix in the fork, by renaming the key, or report upstream | vscode-project-manager |
| WF-R18 | limitation | S4 | Under the new id, `globalState` starts empty: list view, the recent stack, the tag filter, remembered expansion and What's New's keys reset once (WF-F4, WF-D4) | vscode-project-manager |
| WF-R19 | limitation | S4 | The eight translations of the nine new strings are the implementer's, with no native speaker's review (*Strings*) | vscode-project-manager |
| WF-R20 | deferred | S4 | Once upstream merges PR #986 or another shared `.git`-file helper, replace the seven lines `getGitCommonDir` duplicates from `getGitBranch` (WF-D5, *Staying in step*) | vscode-project-manager |

## Review 1 — what changed (2026-10-21)

**Re-verified:** every cited line, at `d62a138`. Also re-run:
- the suite through `runTests` with this plan's launch arguments: 85
  passing;
- a test-host probe;
- `vsce ls` outside the sandbox;
- Node's `fs` behaviour;
- git's `worktree.c`;
- PR #986's patch;
- the VS Code server's clean-up path.

What changed in the plan:
- **Snapshot line**: there is no `upstream/master` ref yet. Upstream's
  `master` is from `git ls-remote`.
- **Findings**:
  - WF-F2: git tries every entry of `worktrees/`. A whitespace-only `gitdir`
    lists the record folder. A locked worktree is never pruned.
  - WF-F3: the storage folder goes at VS Code's next extension clean-up, not
    at uninstall.
  - WF-F4: the server holds no `state.vscdb`, and the reset holds wherever
    the store lives.
  - WF-F6: PR #986's insertion points.
  - WF-F11: the headless mechanism, as run.
  - WF-F12: the package list outside the sandbox, and the untracked
    `.claude/`.
  - WF-F13: two VS Code servers, `extensionKind`, and the remote CLI's flags.
  - WF-F17: the bundles' ends.
  - New **WF-F18**: a key that extends another setting's key loses its
    default.
- **Decisions**:
  - WF-D5 states three deliberate differences from git's reader.
  - WF-D7 covers locked worktrees.
  - WF-D8's climb-out rule is exact, and the redundant `isAbsolute` test is
    dropped.
  - WF-D9 forbids a `projectManager.worktrees` setting.
- **Specification**:
  - `getLinkedWorktrees` no longer filters entries by type.
  - The missing-tree tooltip adds "unless the worktree is locked".
  - `describeWorktree` uses `climbsOut`.
  - `getWorktreeNodes` reads the profile as the node commands do.
  - The `extension.ts` configuration blocks move to after
    `tags.collapseItems`, clear of PR #986.
  - The comma at `package.json:864`, and the bundles' missing final newline.
- **Tests**:
  - The fixtures write `/` paths, as git does, and make a `junction` link.
  - L12 covers 0-byte and whitespace-only files.
  - L17 runs git with its config and `GIT_*` variables isolated, `-b`
    first, and paths normalised.
  - The fs suites set 5 s timeouts, and the new files use no `any`.
  - Added: an N4 `..` case, N10, W11, W12, S3's children, S20, the
    `suiteSetup` resets, and the What's New test's quoting and stray page.
  - The final count is **158** (154 before), with the steps at 87, 111,
    122, 134, 157 and 158. *Coverage* maps each branch to its tests.
- **Verification**:
  - the lint rule names the four existing warnings in the two changed test
    files;
  - 158 passing;
  - a VSIX check for packaged dotfiles.
- **Hand-over**:
  - step 0 checks the client for a local copy;
  - every window is reloaded;
  - the storage folder may go late, and the Git cache is rebuilt;
  - manual checks 1 and 4 test what they meant to test.
- **Staying in step**: what a merge of PR #986 means here.
- **Assumed**:
  - clean-up timing, the remote CLI flags (now read in its help), the
    client copy, the twistie on refresh and WF-F18's machine-settings case
    are each stated;
  - `globalState`'s location no longer matters.
- **Residue**:
  - WF-R1 rises from S2 to S1, since the hand-over out of order deletes the
    favorites (data integrity);
  - WF-R17 to WF-R20 are added.
- **Scope**: WF-F18 is listed among the noticed upstream defects.
- **Summary**: rewritten.
- **Gates**: unchanged. The one `writing` row is met. The body names nothing
  else that must come before implementing.

## Tests to remove after implementation

None. Every test this plan adds stays, and no existing test becomes
redundant.
