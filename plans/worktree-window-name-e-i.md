# A worktree opens in a window named after its repo

- **Workstream**: [[sonata-server-automation:wt-workstreams]] · names the windows of the trees [[worktrees-under-favorites]] nests
- **Created**: 2026-10-22 12:15 UTC
- **Created by**: Opus 5.5 (`claude-opus-5-5`), at Matt's request, from a session in passwave-core
- **Written**: 2026-10-22 13:04 UTC
- **Written by**: Opus 5.5 (`claude-opus-5-5`)
- **Latest review**: 2026-10-22 13:12 UTC
- **Latest review by**: Fable 5.1 (`claude-fable-5-1`)
- **Review count**: 1
- **Implemented**: 2026-10-22 13:49 UTC
- **Implemented by**: Opus 5.5 (`claude-opus-5-5`)
- **Status**: **implemented (reviewed 1×).** Landed as specified, at 198 passing, with the code of *Specification* unchanged; then Matt's hand-over (WWN-R1)

Item ids are stable: findings **WWN-F*n***, decisions **WWN-D*n***, residue
**WWN-R*n***. Tests are named by the suites and titles given in *Tests*.
**Snapshot of:** this repo on `master` at `091cb48`. The working tree differs
from it only under `plans/`.

## Gates

| Before | Kind | Gate | Why | State |
|---|---|---|---|---|
| implementing | plan | [[worktrees-under-favorites]] implemented | the worktree nodes this plan changes, and the fork they ship in | met 2026-10-21 |

## Summary

In this fork of Project Manager, a linked worktree opened from the Favorites
view, in the same window or a new one, no longer opens as a bare folder.
The extension writes a one-folder `.code-workspace` file for it, named after
the repository and the branch, such as `passwave-core · update-v1`, and
opens that instead. VS Code then names the window, and the Explorer's
heading, after the repository as well as the branch, so that the two
`update-v1` trees on this server can be told apart. The folder inside the
workspace carries the same name, with the branch exactly as git has it.

The files live in the extension's own storage folder on the server, one
subfolder per worktree, so a tree keeps the same file, and VS Code keeps
its editors and layout, from one open to the next. The extension rewrites a
file only when it is out of date, keeps any settings saved into it, and
deletes the files of worktrees that no longer exist. A new setting,
`projectManager.worktrees.openAsWorkspace`, on by default, turns the
behaviour off. In such a window, the status bar, the ✔ badge and Save
Project treat the worktree folder, not the generated file, as the current
project. Favorites that are not worktrees, and the other views, open as
before. A file that cannot be written opens the tree as a folder, with a
warning.

The work adds one source module and its tests, changes the worktree node,
the two open commands, the status bar and the save suggestion, and adds a
setting and a warning with their strings in all nine languages. Matt then
installs the rebuilt VSIX over the fork, reloads, and runs the manual
checks.

## Goal

A worktree opened from the Favorites view opens in a window whose title and
Explorer heading name its repo as well as its branch, such as
`passwave-core · update-v1`, so that the project can be told at a glance.

## Why

Every worktree sits at `<parent of the main checkout>/worktrees/<repo>/<branch
slug>` ([[sonata-server-automation:worktree-layout#wl-d1|WL-D1]]), so its
folder is named by the branch alone. WL-D1 dropped a `<repo>-<slug>` leaf
because Favorites labels do not depend on folder names; window titles do.
VS Code names a folder window after the folder, and Matt opens worktrees from
this fork's Favorites view. So passwave-core's `update-v1` tree opens as a
window called `update-v1`, and so does passwave-scan-app's (WWN-F9).

## Scope

**In:**
- Opening a worktree node from Favorites, by a click or by **Open in New
  Window**, through a single-folder `.code-workspace` file that names the
  folder after its repo and branch, written by the extension when the
  worktree opens.
- Where those files live, their names, when they are rewritten, and when
  they are removed.
- The status bar, the current-project lookup and the Save Project
  suggestion, once the open window is a generated workspace.
- A setting to turn it off, with its strings in every language the
  extension ships.
- Tests for every new branch, and a rebuilt VSIX with Matt's install step as
  the hand-over, as [[worktrees-under-favorites]] did.

**Out:**
- Favorites that are not worktree nodes, including a favorite that is itself
  a linked worktree (WWN-D8), and the Git, VS Code and other locator views.
- The worktree layout and its folder names
  ([[sonata-server-automation:wt-01-worktree-layout]]).
- Showing a name or the ✔ badge for a worktree window that is not itself a
  favorite: that is FU-2026-10-005, left as it stands (WWN-D7).
- Upstream: this is fork-only (WWN-D12).
- README and CHANGELOG, which stay upstream's
  ([[worktrees-under-favorites#wf-d15|WF-D15]]).

### Inherited decisions

Not re-argued here:
- [[worktrees-under-favorites#wf-d2|WF-D2]]: the fork's id is
  `mattlightspeed.project-manager`, version upstream's, installed with
  `--force`. The extension's storage folder follows from the id (WWN-D5).
- [[worktrees-under-favorites#wf-d8|WF-D8]]: a worktree node is labelled by
  its branch, or by its folder's name when HEAD is detached.
- [[worktrees-under-favorites#wf-d9|WF-D9]]: the fork's settings sit under
  `projectManager.worktrees.*`, and none is named `projectManager.worktrees`
  itself.
- [[worktrees-under-favorites#wf-d12|WF-D12]]: `npm test` runs headless, and
  outside Claude's sandbox on this server.
- [[worktrees-under-favorites#wf-d13|WF-D13]] and
  [[worktrees-under-favorites#wf-d14|WF-D14]]: one trunk, the implementer
  does not commit, and Matt installs.
- [[worktrees-under-favorites#wf-d16|WF-D16]]: new files carry the standard
  header, four-space indentation, double quotes, semicolons, `l10n.t` and
  `%key%` strings.
- [[sonata-server-automation:worktree-layout#wl-d1|WL-D1]]: the layout, and
  its leaf named by the branch slug alone.
- The stub's mechanism: a generated single-folder `.code-workspace` file.
  Research found a cheaper route for the title alone, which does not reach
  the Explorer (WWN-F6, WWN-D1).

## Dependencies

- [[worktrees-under-favorites]], implemented 2026-10-21: it adds the worktree
  nodes this plan changes. The fork it built is installed on this server
  (WWN-F9).

## Method: verified and assumed

- **Code** was read at the cited lines in this repo at `091cb48`.
- **VS Code's workbench** was read in the test build that
  `@vscode/test-electron` downloaded, 1.143.0
  (`.vscode-test/vscode-linux-x64-1.143.0/resources/app/out/`), minified, so
  cites quote code. The window title, the Explorer, folder settings and
  workspace trust run in the client, and this server holds no 1.141 client
  build to read: Matt's client is assumed to behave the same, and the
  hand-over checks it.
- **A probe** opened a generated `.code-workspace` file in that 1.143.0 test
  host, outside the sandbox, and recorded what the extension API reports
  (WWN-F3).
- **VS Code's git extension** was read in both server builds on this host,
  1.141.0 and 1.141.1, and in 1.143.0 (WWN-F6).
- **The server's extension host** was read in the same two server builds,
  for how it maps URIs between the client and an extension running on the
  server (WWN-F12).
- **Claude Code's VS Code extension** was read at 2.1.307, the version
  installed (WWN-F7).
- **The test baseline** was run at `091cb48` (WWN-F10).
- **The specification was prototyped** in a scratch copy of the tree, outside
  the repo: the code below compiled, linted with no new warning, and the
  suite ran at **198 passing** with the tests in *Tests* (WWN-F11). Nothing
  in the repo was changed.
- Anything not checked this way is under *Assumed, not verified*.

## Findings

<a id="wwn-f1"></a>**WWN-F1. How a worktree opens today, and why the node
must say it is one.**
- `WorktreeNode` (`src/sidebar/nodes.ts:125-149`) labels a tree by its branch
  or folder (`:130`) and gives it the command `_projectManager.open` with
  `[ worktree.path, label, profile ]` (`:135-139`). A missing tree has no
  command.
- `_projectManager.open(projectPath, projectName, profile)`
  (`src/extension.ts:86-95`) and `_projectManager.openInNewWindow(node)`
  (`:96-103`, reading `node.command.arguments[0]` and `[2]`) both pass the
  path through `buildProjectUri` (`src/utils/uri.ts:9-11`), which only wraps
  it in a URI, to `vscode.openFolder`.
- `_projectManager.open` is also the command of every auto-detected node
  (`src/sidebar/autodetectProvider.ts:43`, `:100`) and of every favorite
  (`src/sidebar/storageProvider.ts:162-166`, `:247-251`). So the open command
  cannot decide by itself that a path is a worktree without changing the Git
  view too, which is out of scope. The node has to carry it.
- `getWorktreeNodes` (`storageProvider.ts:259-269`) builds the nodes. It
  already knows the favorite's path, and returns nothing for a remote one
  (`:261`), so a worktree node's path is always local to the extension host.

<a id="wwn-f2"></a>**WWN-F2. `vscode.openFolder` opens a `.code-workspace`
URI as a workspace.** In 1.143.0 the command builds
`r=B1(i)||i.scheme===Z.untitled?{workspaceUri:i}:{folderUri:i}`, where
`B1(s)` tests that the extension is `.code-workspace`. Its options also take
`noRecentEntry`, which this plan does not pass (WWN-D9).

<a id="wwn-f3"></a>**WWN-F3. A workspace window is titled after its file,
and its Explorer shows its folder by `name`.**
- The label service's `doGetWorkspaceLabel(configPath, options)` strips
  `.code-workspace` from the file's base name and returns `"{0} (Workspace)"`
  (nls 28156) plus the remote suffix, such as ` [SSH: host]`. Short verbosity
  (`verbose: 0`) returns the bare name.
- The window title gives `${rootName}` that label and `${rootNameShort}` the
  short one. Every platform's default `window.title` includes
  `${rootName}`; on Linux it is
  `${dirty}${activeEditorShort}${separator}${rootName}${separator}${profileName}${separator}${appName}`
  (the probe below read it). `window.title` declares no scope, so it is
  window-scoped and can be set in user settings.
- The Explorer view's `get name()` is the same `getWorkspaceLabel(workspace)`,
  and it is the view's heading.
- In a workspace (workbench state 3), the Explorer tree's input is the array
  of roots, not the first root's children
  (`(this.contextService.getWorkbenchState()!==2||t[0].error)&&(i=t)`). Each
  root is built with the workspace folder's `name`
  (`new aS(a.uri,…,a.name)`). `explorer.expandSingleFolderWorkspaces`
  defaults to `true`, so the one root starts expanded.
- When VS Code reads a workspace file, a folder's `path` is resolved against
  the file's own folder, keeping its scheme and authority
  (`a=e.resolvePath(n,r.path)`), and a folder's name is `r.name` or the
  folder's base name.
- **Probe** (1.143.0 test host, a generated file named
  `passwave-core · feat-x.code-workspace` with one folder named
  `passwave-core · feat/x`): `workspace.workspaceFile` had scheme `file`;
  `workspace.name` was `passwave-core · feat-x (Workspace)`;
  `workspaceFolders[0].name` was `passwave-core · feat/x`, slash included;
  `workspace.rootPath` was the folder.

<a id="wwn-f4"></a>**WWN-F4. A workspace window drops the window-scoped
settings of its folder's `.vscode/settings.json`. None exists on this host
today.**
- Folder configuration loads `this.scopes=3===this.workbenchState?Xpe:Rte`,
  where `Rte=[4,5,6,7]` and `Xpe=[5,6,7]`: in a workspace, scope 4, window,
  is not read from a folder. The Settings editor marks such a key "This
  setting cannot be applied in this workspace. It will be applied when you
  open the containing workspace folder directly." (nls 23030).
- An extension setting that declares no scope is window-scoped.
- Of the 35 favorites, only this repo has a `.vscode/settings.json`. It sets
  `files.exclude` (scope 5), `search.exclude` (scope 5) and `files.encoding`
  (scope 6), so it loses nothing. Neither linked worktree on the host has a
  `.vscode/` folder. Read 2026-10-22.

<a id="wwn-f5"></a>**WWN-F5. A workspace's identity is its file's URI, and
trust covers the file as well as the folder.**
- `R0(i){return{id:_9(i),configPath:i}}` with `_9(i)` a hash of
  `i.toString()` (`mainImpl.js`, 1.143.0). VS Code keys a window's saved
  editors, layout and extensions' `workspaceState` by that id. A folder
  window's id comes from the folder's URI instead. So the first open of a
  tree as a workspace starts without that state, and a stable file path then
  keeps it.
- Workspace trust checks `getWorkspaceUris()`, which is the folders plus the
  workspace file when `sxe` holds, that is, when the file is neither untitled
  nor temporary. Unless the remote resolver marks the window trusted, the
  generated file's folder must be trusted too.

<a id="wwn-f6"></a>**WWN-F6. VS Code's own git extension already names a
worktree's repository, for the title only.** In both server builds on this
host (1.141.0 and 1.141.1) and in 1.143.0, the git extension sets
`activeRepositoryName=e.kind==="worktree"&&L&&He.basename(L)||void 0`, where
`L` is the common git folder for a bare clone and its parent otherwise. The
workbench feeds it to `window.title` as `${activeRepositoryName}`, falling
back to the provider's name, which for a repository at a workspace folder's
root is that folder's `name`. A `window.title` such as
`${activeRepositoryName}${separator}${rootName}` therefore names a worktree
window `passwave-core - update-v1` with no code. It leaves the Explorer
heading as `update-v1`, waits for the git extension, and reads
`passwave-web - passwave-web` in a main checkout.

<a id="wwn-f7"></a>**WWN-F7. Claude Code starts its sessions in the first
workspace folder, not beside the workspace file.** In 2.1.307:
- the panels build their session's working directory with
  `kk(workspace.workspaceFolders?.map(V=>V.uri.fsPath)||[])`, where
  `kk($){return jz($[0]||homedir())}`;
- the session list is scoped by `workspaceFolders?.[0]?.uri.fsPath`;
- the IDE lock file lists `workspaceFolders`;
- open panel tabs are kept in `workspaceState` (`panelTabSessions`).

So in a generated workspace the session starts in the worktree, as it does
in a folder window, and its transcripts and auto-memory stay where they
were. Only the list of open panel tabs starts empty once (WWN-F5).

<a id="wwn-f8"></a>**WWN-F8. Four places read `workspace.workspaceFile` as
the current project.**
- `showStatusBar` (`src/statusbar/statusBar.ts:24-27`) takes it, else the
  first folder, as the project to look up and show.
- `updateCurrentProject` (`src/extension.ts:447-460`, the URI at `:448-450`)
  sets `Container.currentProject`, which the ✔ decoration reads
  (`src/sidebar/decoration.ts:14`).
- `getProjectDetails` (`src/utils/suggestion.ts:41-101`, the workspace-file
  branch at `:43-63`) suggests the file's path, and its base name, to Save
  Project.
- `Locators.removeRootPath` (`src/autodetect/locators.ts:117-138`) reads it
  only to tell a remote window apart. Its local filter compares with
  `workspace.rootPath` (`:136`), which in a workspace window is the first
  folder (WWN-F3's probe), so it needs no change.

In a generated workspace, the first three would look up the generated file.
It is never a project, and Save Project would offer it as a favorite.

<a id="wwn-f9"></a>**WWN-F9. This host, read 2026-10-22.**
- Two linked worktrees exist, both on branch `update-v1`:
  `/usr/share/nginx/sites/passwave/worktrees/passwave-core/update-v1` and
  `/usr/share/nginx/sites/passwave/worktrees/passwave-scan-app/update-v1`.
- The 35 favorites (`/home/claude/.config/project-manager/projects.json`)
  are each named after their folder, and none is a linked worktree.
- `mattlightspeed.project-manager` 13.1.1 is installed from a VSIX, and
  `alefragnani.project-manager-13.1.0` is marked obsolete
  (`~/.vscode-server/extensions/extensions.json`, `.obsolete`).
  `projectManager.projectsLocation` is
  `/home/claude/.config/project-manager` in the machine settings. So
  [[worktrees-under-favorites]]'s swap was made, though its register entry
  FU-2026-10-001 still reads `handed-over`.
- The fork's storage folder,
  `/home/claude/.vscode-server/data/User/globalStorage/mattlightspeed.project-manager/`,
  exists and holds `projects_cache_git.json`.

<a id="wwn-f10"></a>**WWN-F10. Test baseline, and what the test host opens.**
Recorded 2026-10-22 at `091cb48`:
- `npm run lint`: 0 errors, 52 warnings;
- `npm test`, outside the sandbox: **158 passing**, 0 failing.

`src/test/runTest.ts:31-34` launches the test host on `./testworkspace`,
which neither exists nor is tracked. The test host therefore opens an empty
window: `workspace.workspaceFolders` is `undefined` in every test. No test
can open a real workspace window, so the logic below takes its inputs as
arguments.

<a id="wwn-f11"></a>**WWN-F11. The prototype.** In a scratch copy of the
tree at `091cb48`, with this plan's code and tests:
- `tsc -p ./` compiled;
- `eslint` gave 0 errors and 52 warnings, none in a new or changed line;
- `npm test` gave **198 passing**, 0 failing, on 1.143.0.

TypeScript compiles each `export function` to `exports.<name> = <name>`, so
one test can replace `currentWorktreeWorkspaceFolder` for
`suggestion.ts`, which calls it through the module object, as
`decoration.test.ts` replaces a `window` function.

<a id="wwn-f12"></a>**WWN-F12. The fork runs on the server, where a remote
window's URIs have scheme `file`.**
- The fork's `extensionKind` is `["ui", "workspace"]` (`package.json:24-27`),
  and it is installed only on the server, under
  `~/.vscode-server/extensions/` (WWN-F9), so it runs in the server's
  extension host. That is also why `getLinkedWorktrees` can read git's
  records of the server's trees at all.
- That host maps every URI crossing to and from the client
  (`out/vs/workbench/api/node/extensionHostProcess.js`, in both server
  builds, 1.141.0 and 1.141.1): incoming,
  `t.scheme==="vscode-remote"?{scheme:"file",path:t.path,…}`; outgoing,
  `t.scheme==="file"?{scheme:"vscode-remote",authority:r,path:t.path,…}`,
  with `r` the window's remote authority.
- So in Matt's windows, `workspace.workspaceFile`, every workspace folder
  and `globalStorageUri` reach the extension with scheme `file` and server
  paths, which is what `findWorktreeWorkspaceFolder` tests for (WWN-D7),
  and `Uri.file(<generated file>)` handed to `vscode.openFolder` reaches
  the client as `vscode-remote://<authority>/…`, by the same mapping a
  favorite's folder URI takes today (`buildProjectUri`, WWN-F1).
- The `vscode-remote` branches of `getProjectDetails` and
  `updateCurrentProject` (WWN-F8) serve the extension when it runs on the
  client, with the window remote, which is not how it runs here.

## Decisions

<a id="wwn-d1"></a>**WWN-D1. A generated single-folder workspace per
worktree, as the stub scoped it.**
- It is the only route that names the Explorer's heading as well as the
  title (WWN-F3).
- Rejected as the mechanism:
  - `window.title` with `${activeRepositoryName}` (WWN-F6), which leaves the
    Explorer as `update-v1` and doubles the name in a main checkout. It stays
    open to Matt as a setting of his own, beside this plan;
  - a `window.title` written into the tree's `.vscode/settings.json`, which
    leaves a file in every worktree and leaves the Explorer unchanged;
  - an extension API, since none sets a window's title.
- What a worktree window then loses, all once or rarely, is in *Residue*:
  its saved state on the first open (WWN-F5), window-scoped folder settings
  (WWN-F4), a trust prompt (WWN-F5), and the `(Workspace)` suffix
  (WWN-F3).

<a id="wwn-d2"></a>**WWN-D2. A setting, `projectManager.worktrees.openAsWorkspace`,
boolean, default `true`.**
- On by default, since the fork is Matt's and he asked for it.
- The switch costs one setting and one string, and gives a way back to
  folder windows for a repo whose window-scoped folder settings matter
  (WWN-F4), or if the suffix or trust prompt are not wanted.
- It is read when a worktree opens, so a change needs no reload. The
  configuration handler's existing refresh on any `projectManager.worktrees`
  change (`src/extension.ts:217-219`) also fires; it is harmless.
- Its key keeps WF-D9's namespace.

<a id="wwn-d3"></a>**WWN-D3. The window is named `<repository> · <label>`.**
- `<label>` is the node's label: the branch, or the folder's name when HEAD
  is detached (WF-D8). It matches what Matt clicked in Favorites.
- `<repository>` is the main checkout's folder name, read from the common
  git folder of the favorite, which its linked trees share
  (`getRepositoryName(projectPath)` in `getWorktreeNodes`): the folder
  above it when its name starts with a dot (`.git`, `.bare`), its name
  without `.git` for a bare `repo.git`, else its name. This is the layout's
  `<repo>` segment, and what VS Code's git extension calls the repository
  (WWN-F6).
- Not the favorite's name: on this host the two are equal (WWN-F9), but the
  children of a favorite that is itself a linked worktree belong to the
  repo, not to that tree.
- The separator ` · ` is the stub's, and is not translated.
- A missing tree has no command, so it never opens and needs no name.

<a id="wwn-d4"></a>**WWN-D4. The file's name is the window name made safe
for a file system; the folder's `name` keeps it exactly.**
- VS Code titles the window from the file's name (WWN-F3), so the file is
  named after the window.
- Each character that Windows forbids in a file name (`< > : " / \ | ? *`)
  and each control character becomes `-`, and trailing dots and spaces go.
  An empty result is `worktree`. `feature/login` becomes `feature-login` in
  the title.
- The folder's `name` holds `passwave-core · feature/login`, so the Explorer's
  root row and the Source Control view show the branch as git has it.

<a id="wwn-d5"></a>**WWN-D5. The files live in the extension's storage
folder, one subfolder per worktree:
`<globalStorageUri>/worktree-workspaces/<key>/<name>.code-workspace`.**
- `<key>` is the first 16 hex digits of the SHA-256 of the tree's resolved
  path. Two trees with the same window name, such as two clones both called
  `passwave-web`, cannot share a file, and a tree keeps its subfolder for
  life.
- On this host the folder is
  `/home/claude/.vscode-server/data/User/globalStorage/mattlightspeed.project-manager/worktree-workspaces/`.
- Every module reaches it through `Container.context`, with no setting read.
- The extension owns the folder. The files can all be rebuilt, so VS Code
  deleting it when the fork is uninstalled
  ([[worktrees-under-favorites#wf-f3|WF-F3]]) costs only what WWN-R8 says.
- Rejected:
  - a folder beside `projects.json`, under `projectManager.projectsLocation`,
    which the stub suggested: it would put generated files beside the
    favorites Matt keeps, would need `getProjectFilePath`, an inner function
    of `activate()`, in three modules, and would move every file, with its
    windows' saved state, whenever the setting changed. Its one gain is that
    the files outlive an uninstall or a rollback;
  - a file beside the tree in the layout, in folders SSA creates with set
    groups and modes, where `ssa-manage worktrees` lists the layout.

<a id="wwn-d6"></a>**WWN-D6. When a file is written, kept and removed.**
- **At each open** of a worktree from Favorites, its file is written only
  when it is missing or its `folders` differ from the expected one folder.
  So an open window is not disturbed, and the file's identity, with the
  window's saved state, holds (WWN-F5).
- **Other keys are kept.** Settings that VS Code saves into the file, from
  the Settings editor's Workspace tab, survive. Only `folders` is the
  extension's.
- **A file that is not a JSON object** (a comment, a trailing comma, `[]`,
  `null`) is replaced whole. VS Code never writes such a file. A hand edit
  does, and loses its other keys (WWN-R6).
- **A branch switch** inside a tree changes its name, so a new file is
  written in the same subfolder. It takes the old file's other keys, when
  the old file parses, and the old file is deleted. The window's saved state
  starts again once (WWN-R2).
- **Pruning.** Before each write, every subfolder whose files name no folder
  that still exists is deleted, including a subfolder with no file or with
  files that do not parse. A tree removed with `git worktree remove` loses
  its file at the next worktree open. A tree whose folder is only out of
  reach for a while is rebuilt at the same path when it is next opened.
- **No atomic write.** The files are a few hundred bytes, and rewritten only
  when out of date; a torn write is replaced at the next open.
- **With the setting off, nothing is written and nothing is pruned.** Files
  left from when it was on stay until it is on again and a worktree opens
  (WWN-R14).

<a id="wwn-d7"></a>**WWN-D7. A generated window's current project is its
worktree folder.**
- The status bar, `updateCurrentProject` and Save Project look up the
  worktree folder, not the generated file (WWN-F8). The status bar then
  finds the tree exactly when a folder window would have: when the tree is a
  favorite or auto-detected.
- Save Project in such a window suggests the worktree's path, named as its
  window, `passwave-core · update-v1`, and never offers the generated file.
- Nothing new is shown when the tree is not a project. Showing the window's
  name in the status bar, and a ✔ on the worktree node, would close
  FU-2026-10-005 for these windows. It is left out: the stub scoped this
  plan to keep finding the worktree, and the status bar's search has no
  test seam (WWN-R7).
- A generated workspace is recognised by place: a `file`-scheme
  `.code-workspace` whose grandparent is the storage folder of WWN-D5.

<a id="wwn-d8"></a>**WWN-D8. Only worktree nodes carry a window name.**
- The name travels as a fourth argument of the node's command, appended
  only when there is one, so favorites and auto-detected nodes, which pass
  three, open as before (WWN-F1).
- A favorite that is itself a linked worktree opens as its folder, as
  before. None exists on this host (WWN-F9); the Favorites view already
  lists every tree under its repo; and naming one would mean reading git's
  records for every favorite at every render. It is a non-goal (WWN-R9).

<a id="wwn-d9"></a>**WWN-D9. Recent keeps an entry for each worktree
workspace.** `noRecentEntry` is not passed (WWN-F2). File › Open Recent then
lists `passwave-core · update-v1 (Workspace)`, which names the repo, where it
listed `update-v1` before. An entry whose file was pruned fails to open
(WWN-R8).

<a id="wwn-d10"></a>**WWN-D10. A file that cannot be written falls back to
the folder, with a warning.** The worktree still opens, as a folder, and
`window.showWarningMessage` says why. A silent fallback would look like the
feature had stopped. Pruning errors take the same path.

<a id="wwn-d11"></a>**WWN-D11. This plan joins
[[sonata-server-automation:wt-workstreams]] as a unit.** It closes the gap
WL-D1's leaf left in the editor, which is the workstream's "how they show",
and it builds on that workstream's fork unit. The index's row and graph edge
are the orchestrator's edit, listed in this writing's report.

<a id="wwn-d12"></a>**WWN-D12. Fork-only.** Upstream's Favorites has no
worktree nodes, so there is nothing to offer until the nesting itself is
offered (WF-R7 of [[worktrees-under-favorites]], FU-2026-10-007).

<a id="wwn-d13"></a>**WWN-D13. Tests drive pure functions.** The test host
opens no folder (WWN-F10), so the logic that reads the window takes the
workspace file, folders and storage folder as arguments
(`findWorktreeWorkspaceFolder`, `projectUriOf`), and the two thin wrappers
that read `vscode.workspace` are tested only as far as an empty window
allows. `buildOpenUri` reads the storage folder through `Container`, which
the tests initialise with a mock context whose `globalStorageUri` is a temp
folder.

## Specification

### Files

| File | Change |
|---|---|
| `src/utils/worktreeWorkspace.ts` | **new**: window names, file names, writing, pruning, the open URI, and recognising a generated window |
| `src/utils/worktrees.ts` | gains `getRepositoryName` |
| `src/sidebar/nodes.ts` | `WorktreeNode` takes a repository name and appends the window name to its command |
| `src/sidebar/storageProvider.ts` | `getWorktreeNodes` passes the repository name |
| `src/extension.ts` | both open commands go through `buildOpenUri`; `updateCurrentProject` uses `currentProjectUri` |
| `src/statusbar/statusBar.ts` | uses `currentProjectUri` |
| `src/utils/suggestion.ts` | `getProjectDetails` suggests a generated window's worktree |
| `package.json` | one setting |
| `package.nls.json` + 8 `package.nls.<lang>.json` | one setting string |
| `l10n/bundle.l10n.json` + 8 `l10n/bundle.l10n.<lang>.json` | one runtime string |
| `src/test/suite/mocks/MockMemento.ts` | `createMockContext` takes an optional storage path |
| `src/test/suite/worktreeWorkspace.test.ts` | **new** |
| `src/test/suite/worktrees.test.ts` | one new suite |
| `src/test/suite/worktreeNode.test.ts` | two new tests |
| `src/test/suite/storageProviderWorktrees.test.ts` | one new test |
| `src/test/suite/manifest.test.ts` | two keys added to its lists; one new test |
| `src/test/suite/suggestion.test.ts` | one new test |

Nothing is deleted. `src/utils/uri.ts`, `src/autodetect/locators.ts`,
`src/sidebar/decoration.ts` and every existing test's assertions stay as
they are.

### `src/utils/worktreeWorkspace.ts` (new)

The standard header, then this module:

```ts
import crypto = require("crypto");
import fs = require("fs");
import path = require("path");
import { isDeepStrictEqual } from "util";
import { l10n, Uri, window, workspace, WorkspaceFolder } from "vscode";
import { Container } from "../core/container";
import { isRemotePath } from "./remote";
import { buildProjectUri } from "./uri";

const WORKSPACE_EXTENSION = ".code-workspace";
const FORBIDDEN_IN_FILE_NAMES = "<>:\"/\\|?*";

type WorkspaceContent = Record<string, unknown>;

export function worktreeWindowName(repositoryName: string, label: string): string {
    return `${repositoryName} · ${label}`;
}

export function opensWorktreesAsWorkspaces(): boolean {
    return workspace.getConfiguration("projectManager").get<boolean>("worktrees.openAsWorkspace", true);
}

export function worktreeWorkspacesFolder(): string {
    return path.join(Container.context.globalStorageUri.fsPath, "worktree-workspaces");
}

// The file name is the window's title, so it stays readable; it must also be valid on Windows,
// which rejects these characters and a name ending in a dot or a space.
export function workspaceFileName(windowName: string): string {
    const safeName = Array.from(windowName, char => char < " " || FORBIDDEN_IN_FILE_NAMES.includes(char) ? "-" : char)
        .join("")
        .replace(/[. ]+$/, "");
    return `${safeName || "worktree"}${WORKSPACE_EXTENSION}`;
}

export function writeWorktreeWorkspace(storageFolder: string, worktreePath: string, windowName: string): string {
    const keyFolder = path.join(storageFolder, worktreeKey(worktreePath));
    const workspaceFile = path.join(keyFolder, workspaceFileName(windowName));
    fs.mkdirSync(keyFolder, { recursive: true });

    const previousFiles = workspaceFilesIn(keyFolder).filter(file => file !== workspaceFile);
    const fileExists = fs.existsSync(workspaceFile);
    const existing = readWorkspaceContent(fileExists ? workspaceFile : previousFiles[ 0 ]);
    const folders = [ { name: windowName, path: worktreePath } ];
    if (!fileExists || !isDeepStrictEqual(existing?.folders, folders)) {
        fs.writeFileSync(workspaceFile, `${JSON.stringify({ ...existing, folders }, null, "\t")}\n`);
    }
    for (const previousFile of previousFiles) {
        fs.rmSync(previousFile, { force: true });
    }
    return workspaceFile;
}

export function pruneWorktreeWorkspaces(storageFolder: string): void {
    let entries: fs.Dirent[];
    try {
        entries = fs.readdirSync(storageFolder, { withFileTypes: true });
    } catch {
        return;
    }
    for (const entry of entries.filter(e => e.isDirectory())) {
        const keyFolder = path.join(storageFolder, entry.name);
        const inUse = workspaceFilesIn(keyFolder).some(file => {
            const folderPath = worktreeFolderOf(file);
            return folderPath !== undefined && fs.existsSync(folderPath);
        });
        if (!inUse) {
            fs.rmSync(keyFolder, { recursive: true, force: true });
        }
    }
}

export function buildOpenUri(projectPath: string, windowName?: string): Uri {
    if (!windowName || isRemotePath(projectPath) || !opensWorktreesAsWorkspaces()) {
        return buildProjectUri(projectPath);
    }
    try {
        const storageFolder = worktreeWorkspacesFolder();
        pruneWorktreeWorkspaces(storageFolder);
        return Uri.file(writeWorktreeWorkspace(storageFolder, projectPath, windowName));
    } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        window.showWarningMessage(l10n.t("Could not write a workspace for this worktree, so it opens as a folder: {0}", reason));
        return buildProjectUri(projectPath);
    }
}

export function findWorktreeWorkspaceFolder(workspaceFile: Uri | undefined, workspaceFolders: readonly WorkspaceFolder[] | undefined,
    storageFolder: string): WorkspaceFolder | undefined {
    if (workspaceFile?.scheme !== "file" || path.extname(workspaceFile.fsPath) !== WORKSPACE_EXTENSION) {
        return undefined;
    }
    if (path.dirname(path.dirname(workspaceFile.fsPath)) !== path.resolve(storageFolder)) {
        return undefined;
    }
    return workspaceFolders?.[ 0 ];
}

export function projectUriOf(workspaceFile: Uri | undefined, workspaceFolders: readonly WorkspaceFolder[] | undefined,
    storageFolder: string): Uri | undefined {
    return findWorktreeWorkspaceFolder(workspaceFile, workspaceFolders, storageFolder)?.uri ?? workspaceFile ?? workspaceFolders?.[ 0 ]?.uri;
}

export function currentWorktreeWorkspaceFolder(): WorkspaceFolder | undefined {
    return findWorktreeWorkspaceFolder(workspace.workspaceFile, workspace.workspaceFolders, worktreeWorkspacesFolder());
}

export function currentProjectUri(): Uri | undefined {
    return projectUriOf(workspace.workspaceFile, workspace.workspaceFolders, worktreeWorkspacesFolder());
}

function worktreeKey(worktreePath: string): string {
    return crypto.createHash("sha256").update(path.resolve(worktreePath)).digest("hex").slice(0, 16);
}

function workspaceFilesIn(folder: string): string[] {
    return fs.readdirSync(folder)
        .filter(name => name.endsWith(WORKSPACE_EXTENSION))
        .map(name => path.join(folder, name));
}

function readWorkspaceContent(workspaceFile: string | undefined): WorkspaceContent | undefined {
    if (!workspaceFile) {
        return undefined;
    }
    try {
        const content: unknown = JSON.parse(fs.readFileSync(workspaceFile, "utf8"));
        return content !== null && typeof content === "object" && !Array.isArray(content) ? content as WorkspaceContent : undefined;
    } catch {
        return undefined;
    }
}

function worktreeFolderOf(workspaceFile: string): string | undefined {
    const folders = readWorkspaceContent(workspaceFile)?.folders;
    const firstPath = Array.isArray(folders) ? (folders[ 0 ] as { path?: unknown } | undefined)?.path : undefined;
    return typeof firstPath === "string" ? path.resolve(path.dirname(workspaceFile), firstPath) : undefined;
}
```

Notes for the implementer:
- The file is written with tabs, as VS Code writes workspace files, and ends
  with a newline. A fresh file is exactly
  `{ "folders": [ { "name": …, "path": … } ] }` in that layout.
- `{ ...existing, folders }` keeps `folders` where an existing file had it,
  and puts it last in a file that had none.
- `worktreeFolderOf` resolves a relative `path` against the file's folder,
  as VS Code does (WWN-F3). The extension always writes an absolute path,
  but VS Code may rewrite the folders as relative when it edits them.
- A pruning error, such as an unreadable subfolder, leaves `buildOpenUri`
  through its `catch`, so the tree opens as a folder with the warning
  (WWN-D10).
- `Array.from` over the name keeps the control-character test out of a
  regular expression, which `eslint:recommended`'s `no-control-regex` would
  reject (`node_modules/eslint-config-vscode-ext/index.js` extends it).
- The catch variable is `any` (`tsconfig.json` sets neither `strict` nor
  `useUnknownInCatchVariables`), so `error instanceof Error` narrows it with
  no `any` written in the source for the lint to flag.

### `src/utils/worktrees.ts`

Insert after `getGitCommonDir` (`:16-41`), before `getLinkedWorktrees`:

```ts
export function getRepositoryName(projectPath: string): string | undefined {
    const commonDir = getGitCommonDir(projectPath);
    if (!commonDir) {
        return undefined;
    }
    const commonDirName = path.basename(commonDir);
    if (commonDirName.startsWith(".")) {
        return path.basename(path.dirname(commonDir));
    }
    return commonDirName.endsWith(".git") ? commonDirName.slice(0, -".git".length) : commonDirName;
}
```

### `src/sidebar/nodes.ts`

- Add `import { worktreeWindowName } from "../utils/worktreeWorkspace";` after
  the `../utils/worktrees` import (`:11`).
- `WorktreeNode`'s constructor (`:129-139`) becomes:

```ts
    constructor(worktree: LinkedWorktree, projectPath: string, profile: string | undefined, repositoryName?: string) {
        const label = worktree.branch ?? path.basename(worktree.path);
        const windowNameArguments = repositoryName ? [ worktreeWindowName(repositoryName, label) ] : [];
        super(label, TreeItemCollapsibleState.None, undefined, {
            name: label,
            path: worktree.path,
            detail: describeWorktree(worktree, projectPath)
        }, worktree.missing ? undefined : {
            command: "_projectManager.open",
            title: "",
            arguments: [ worktree.path, label, profile, ...windowNameArguments ]
        });
```

  The rest of the class is unchanged. A statement before `super()` compiles
  because the class has no parameter properties or initialised fields
  ([[worktrees-under-favorites]] relied on the same).

### `src/sidebar/storageProvider.ts`

- The `../utils/worktrees` import (`:14`) gains `getRepositoryName`.
- In `getWorktreeNodes` (`:259-269`), after `const profile = …` (`:264`):

```ts
        const repositoryName = getRepositoryName(projectPath);
```

  and the `map` (`:266`) becomes
  `.map(worktree => new WorktreeNode(worktree, projectPath, profile, repositoryName))`.

### `src/extension.ts`

- `:21` `import { buildProjectUri } from "./utils/uri";` becomes
  `import { buildOpenUri, currentProjectUri } from "./utils/worktreeWorkspace";`.
  `buildProjectUri` has no other use in this file.
- `:86-87` become:

```ts
    vscode.commands.registerCommand("_projectManager.open", async (projectPath: string, projectName: string, profile: string, worktreeWindowName?: string) => {
        const uri = buildOpenUri(projectPath, worktreeWindowName);
```

- `:97` becomes
  `const uri = buildOpenUri(node.command.arguments[0], node.command.arguments[3]);`.
- In `updateCurrentProject`, `:448-450` become
  `const workspace0 = currentProjectUri();`.

The URI is still built before the switch confirmation, as upstream builds
it, so a cancelled open may leave a written file; the next open reuses it.

### `src/statusbar/statusBar.ts`

- Add `import { currentProjectUri } from "../utils/worktreeWorkspace";` after
  the `../core/project` import (`:12`).
- `:24-26` become `const workspace0 = currentProjectUri();`. The commented
  lines `:20-23` are upstream's and stay.

### `src/utils/suggestion.ts`

- Add `import { currentWorktreeWorkspaceFolder } from "./worktreeWorkspace";`
  after the `./remote` import (`:8`).
- `getProjectDetails` (`:41`) begins, before `// workspaceFile - .code-workspace`:

```ts
    const worktreeFolder = currentWorktreeWorkspaceFolder();
    if (worktreeFolder) {
        return {
            path: worktreeFolder.uri.fsPath,
            name: worktreeFolder.name
        };
    }
```

  This returns the folder's path as the folder-window branch at `:82-85`
  does, and does not take the Codespaces branch at `:72-80`, which builds a
  `vscode-remote://codespaces+…` path for a folder window there (WWN-R15).

### `package.json`

In `projectManager-general`'s properties, after
`projectManager.worktrees.collapseItems` (`:900-916`), whose closing `}` at
`:916` gains a comma. The file indents with tabs:

```json
"projectManager.worktrees.openAsWorkspace": {
	"type": "boolean",
	"default": true,
	"description": "%projectManager.configuration.worktrees.openAsWorkspace.description%"
}
```

No command or menu is added.

### Strings

**Manifest string.** Add to `package.nls.json`, immediately after
`projectManager.configuration.worktrees.collapseItems.enumDescriptions.startCollapsed`
(`:112`):

| Key | English |
|---|---|
| `projectManager.configuration.worktrees.openAsWorkspace.description` | `Open a worktree from the Favorites view as a workspace named after its repository and branch, so that the window title and the Explorer show both. When off, a worktree opens as a plain folder.` |

**Runtime string.** Add to the end of `l10n/bundle.l10n.json`, mapped to
itself as the file does:
`Could not write a workspace for this worktree, so it opens as a folder: {0}`.

**Translations.** The same keys go into each of the 8 languages: `az`, `cs`,
`fr`, `pt-br`, `ru`, `uk`, `zh-cn`, `zh-tw`.
- In `package.nls.<lang>.json` the key sits at the same anchor. In `cs` and
  `ru` the anchor is the file's last entry, so it gains a comma.
- In `l10n/bundle.l10n.<lang>.json` it goes at the end, after a comma on
  what was the last entry.
- The implementer writes each translation, following
  `.github/skills/vscode-ext-localization/SKILL.md`, in the file's own words
  for "worktree", "workspace", "favorite" and "folder" where it has them.
  `{0}` and `Favorites` stay as each file already renders the view's name.
- Each file keeps its own indentation, line endings and final newline or
  lack of one: `fr`'s bundle is CRLF; `package.nls.az`, `uk` and `zh-cn` and
  the `az`, `cs` and `zh-cn` bundles end with a newline; the others do not
  (read 2026-10-22).

### `src/test/suite/mocks/MockMemento.ts`

`createMockContext()` (`:26-29`) becomes:

```ts
export function createMockContext(globalStoragePath?: string): vscode.ExtensionContext {
    const globalState = new MockMemento();
    return {
        globalState,
        extensionUri: vscode.Uri.file(path.resolve(__dirname, "..", "..", "..", "..", "..")),
        globalStorageUri: globalStoragePath === undefined ? undefined : vscode.Uri.file(globalStoragePath)
    } as unknown as vscode.ExtensionContext;
}
```

Existing callers pass nothing and are unaffected.

## Order of work

Each step ends with `npm test` green, run as in *Verification*, at the
passing count shown.

0. **Bootstrap**, if `vscode-whats-new/` or `node_modules/` is empty:
   `git submodule update --init` outside Claude's sandbox, then `npm ci`.
   Expect **158**.
1. **Repository name**: `getRepositoryName` in `worktrees.ts`, and the
   `getRepositoryName` suite in `worktrees.test.ts`. Expect **164**.
2. **Setting and strings**: the setting in `package.json`, the manifest
   string in all 9 `package.nls*.json`, the runtime string in all 9 bundles,
   and `manifest.test.ts` (both lists, and M7). Expect **165**.
3. **Workspace files**: `worktreeWorkspace.ts`, `createMockContext`'s
   parameter, and `worktreeWorkspace.test.ts`. Expect **194**.
4. **Wiring**: `nodes.ts`, `storageProvider.ts`, `extension.ts`,
   `statusBar.ts`, `suggestion.ts`, and N11, N12, S21 and SG1. Expect
   **198**.
5. **Finish**: lint, build, package and the checks in *Verification*. Then
   the hand-over.

Step 2 comes before step 3 because B3 and C3 set the new key, and VS Code
refuses to write a value to a key that no extension contributes
(`validate` throws error 0, "Unable to write to {0} because {1} is not a
registered configuration.", 1.143.0).

## Tests

"Fails before" means it fails on the tree as it stands before its step. A
test of an export that does not exist yet fails to compile, which fails
`npm test`'s `test-compile`. Every new test passes after its step. New test
files carry the standard header, use no `any`, and give fs suites
`this.timeout(5000)`, as [[worktrees-under-favorites]]'s do.

### `src/test/suite/worktrees.test.ts`: suite **"getRepositoryName"**, 6 tests

Each test makes `root = makeTempDir("repository-name-")` and removes it in
`teardown`, with `this.timeout(5000)`. All fail before step 1.
- **R1** `returns undefined for a folder that is not a git repository`:
  `getRepositoryName(root)` is `undefined`.
- **R2** `names a main checkout by its folder`:
  `makeMainCheckout(root, "passwave-core")` gives `"passwave-core"`.
- **R3** `names a linked worktree by its main checkout's folder`: a main
  checkout `passwave-core`, and `addLinkedWorktree(<repo>/.git, "update-v1",
  <root>/worktrees/passwave-core/update-v1, { branch: "update-v1" })`. The
  tree gives `"passwave-core"`.
- **R4** `names a bare clone by its folder without .git`:
  `addLinkedWorktree(<root>/repo.git, "feat", <root>/feat, { branch: "feat" })`.
  The tree gives `"repo"`.
- **R5** `names a clone whose git folder starts with a dot by the folder above it`:
  `addLinkedWorktree(<root>/repo/.bare, "feat", <root>/repo/feat, …)`. The
  tree gives `"repo"`.
- **R6** `names a bare clone without a .git suffix by its folder`:
  `addLinkedWorktree(<root>/repo, "feat", <root>/feat, …)`. The tree gives
  `"repo"`.

### `src/test/suite/manifest.test.ts`: lists extended, 1 new test

- `NEW_SETTING_KEYS` gains
  `"projectManager.configuration.worktrees.openAsWorkspace.description"`,
  and `NEW_RUNTIME_KEYS` gains the runtime string, so M5 and M6 check them
  in all nine files. Both fail before step 2.
- **M7** `contributes projectManager.worktrees.openAsWorkspace, on by default`,
  placed after M2: the property has `type: "boolean"` and `default: true`,
  and `getConfiguration("projectManager").inspect("worktrees.openAsWorkspace").defaultValue`
  is `true`. Fails before step 2.

### `src/test/suite/worktreeWorkspace.test.ts` (new): 29 tests

All fail before step 3, since the module does not exist. Helpers in the
file: `readJson(file)`, `keyFolders(storage)` (the storage folder's entries,
or `[]` when it does not exist), `workspaceFolder(uri, name)` (a
`WorkspaceFolder` with `index: 0`), and `setOpenAsWorkspace(value)`
(`getConfiguration("projectManager").update("worktrees.openAsWorkspace", value, ConfigurationTarget.Global)`).

Suite **"Worktree window names"**:
- **WN1** `worktreeWindowName joins the repository and the label`:
  `("passwave-core", "feature/login")` gives `"passwave-core · feature/login"`.
- **WN2** `workspaceFileName keeps a name that every platform allows`:
  `"passwave-core · update-v1"` gives `"passwave-core · update-v1.code-workspace"`.
- **WN3** `workspaceFileName replaces each character that a file name cannot hold`:
  - `"repo · feature/login"` gives `"repo · feature-login.code-workspace"`;
  - `a<b>c:d"e\f|g?h*i` gives `"a-b-c-d-e-f-g-h-i.code-workspace"`;
  - `"a\u0001b\tc"` gives `"a-b-c.code-workspace"`.
- **WN4** `workspaceFileName drops trailing dots and spaces, and names an empty result`:
  `"repo · x. ."` gives `"repo · x.code-workspace"`, and `"..."` gives
  `"worktree.code-workspace"`.

Suite **"writeWorktreeWorkspace"**: `setup` makes `root`, `storage =
<root>/storage`, and the folder `tree = <root>/worktrees/repo/feat-x`.
- **WW1** `writes a workspace whose one folder is the worktree, named as its window`:
  `writeWorktreeWorkspace(storage, tree, "repo · feat/x")` returns a file
  - named `repo · feat-x.code-workspace`;
  - whose grandparent is `storage`, and whose parent's name matches
    `/^[0-9a-f]{16}$/`;
  - whose content is exactly
    `JSON.stringify({ folders: [ { name: "repo · feat/x", path: tree } ] }, null, "\t") + "\n"`.
- **WW2** `gives each worktree one folder of its own, the same every time`:
  two writes for `tree` return the same path. A write for
  `<root>/elsewhere/feat-x` with the same window name has a different
  parent folder and the same base name.
- **WW3** `leaves an up-to-date file untouched, with its other keys`: after
  a write, overwrite the file with `JSON.stringify` of the expected folders
  plus `settings: { "editor.tabSize": 2 }`, and set its times a minute back
  with `fs.utimesSync`. A second write leaves the content and
  `statSync(file).mtimeMs` as they were.
- **WW4** `replaces the folders of an outdated file and keeps its other keys`:
  the file holds `{ folders: [ { path: "/somewhere/else" } ], settings: {…} }`.
  After a write it `deepStrictEqual`s the expected folders plus the same
  `settings`.
- **WW5** `replaces a file that is not a JSON object`: for each of
  `// edited\n{ "folders": [] }`, `[]` and `null`, written over the file, a
  write leaves exactly `{ folders: [ { name, path: tree } ] }`.
- **WW6** `moves the other keys of the worktree's previous file to its new name, and removes the previous file`:
  write as `"repo · a"`, add `settings` to that file, then write as
  `"repo · b"`. The new file is in the same folder, the old one is gone, and
  the new one holds `folders` named `"repo · b"` plus the `settings`.
- **WW7** `starts afresh when the previous file is not a JSON object, and removes it`:
  as WW6, with the old file's content `not json`. The new file holds only
  `folders`, and the old one is gone.
- **WW8** `throws when its folder cannot be made`: with `<root>/blocked` a
  regular file, a write to storage `<root>/blocked/storage` throws.

Suite **"pruneWorktreeWorkspaces"**: `setup` makes `root` and `storage =
<root>/storage`; `makeTree(name)` creates `<root>/worktrees/repo/<name>`.
- **P1** `removes the folder of a worktree that no longer exists`: write for
  a tree, delete the tree, prune. The file's folder is gone.
- **P2** `keeps the folder of a worktree that exists`: write for a tree,
  prune. The file is still there.
- **P3** `removes a folder whose files name no folder`: subfolders holding
  one `x.code-workspace` each, with `not json`, `{}`,
  `{"folders":[]}` and `{"folders":[{"uri":"x"}]}`, and a subfolder with no
  file. After a prune `keyFolders(storage)` is `[]`.
- **P4** `ignores a file beside the folders, and a storage folder that does not exist`:
  a regular file `<storage>/stray` survives a prune (`keyFolders` is
  `["stray"]`), and pruning `<root>/nowhere` does not throw.

Suite **"Worktree workspace windows"**, with no file system:
`storage = path.resolve("/storage/worktree-workspaces")`, `tree =
Uri.file("/sites/worktrees/repo/feat")`, `treeFolder =
workspaceFolder(tree, "repo · feat")`, and `generated =
Uri.file(<storage>/0123456789abcdef/repo · feat.code-workspace)`.
- **D1** `finds the folder of a generated worktree workspace`:
  `findWorktreeWorkspaceFolder(generated, [treeFolder], storage)` is
  `treeFolder`.
- **D2** `ignores a workspace file that is not one the extension writes`:
  `undefined` for `/home/user/mine.code-workspace`,
  `<storage>/repo · feat.code-workspace`,
  `<storage>/0123456789abcdef/deeper/repo · feat.code-workspace` and
  `<storage>/0123456789abcdef/repo · feat.json`.
- **D3** `ignores a folder window, a remote workspace file and a workspace without folders`:
  `undefined` for a `workspaceFile` of `undefined`; for `generated` with
  scheme `vscode-remote` and authority `ssh-remote+host`; and for
  `generated` with folders `[]` and with folders `undefined`.
- **D4** `projectUriOf takes a worktree workspace's folder, another workspace's file, or a folder window's folder`:
  - `(generated, [treeFolder])` gives `tree`;
  - `(Uri.file("/home/user/mine.code-workspace"), [treeFolder])` gives that
    file;
  - `(undefined, [treeFolder])` gives `tree`;
  - `(undefined, undefined)` gives `undefined`.

Suite **"buildOpenUri"**: `suiteSetup` resets the setting; `setup` makes
`root`, names `globalStorage = <root>/globalStorage` without creating it,
makes the folder `tree = <root>/worktrees/repo/feat`, and calls
`Container.initialize(createMockContext(globalStorage))`; `teardown` resets
the setting and removes `root`. The generated folder is
`<globalStorage>/worktree-workspaces`, which `writeWorktreeWorkspace`'s
`mkdirSync` creates on the first write.
- **B1** `opens a favorite as its folder, and writes nothing`:
  `buildOpenUri(tree).toString()` equals `Uri.file(tree).toString()`, and
  the generated folder does not exist.
- **B2** `opens a worktree through its generated workspace`:
  `buildOpenUri(tree, "repo · feat")` has scheme `file`, its grandparent is
  the generated folder, its base name is `repo · feat.code-workspace`, and
  it exists.
- **B3** `opens a worktree as its folder when worktrees.openAsWorkspace is off`:
  with the setting `false`, the result is `Uri.file(tree)` and the
  generated folder does not exist.
- **B4** `opens a remote path as it always has, and writes nothing`:
  `buildOpenUri("vscode-remote://ssh-remote+host/srv/repo", "repo · feat")`
  equals `Uri.parse` of the same string, and nothing is written.
- **B5** `opens the folder, with a warning, when the workspace cannot be written`:
  - a regular file is written at `globalStorage`, so that `mkdirSync` under
    it fails with `ENOTDIR`;
  - `window.showWarningMessage` is replaced, through
    `vscode.window as unknown as { showWarningMessage: … }`, by a recorder,
    and restored in `finally`;
  - the result is `Uri.file(tree)`, and exactly one warning was shown,
    starting `Could not write a workspace for this worktree, so it opens as a folder: `.
- **B6** `removes the workspaces of worktrees that are gone`: open a second
  folder `gone` through `buildOpenUri`, delete it, then open `tree`. The
  `gone` file's folder no longer exists, and the generated folder holds only
  `tree`'s.

Suite **"Worktree workspace settings and storage"**: `setup` makes `root`
and calls `Container.initialize(createMockContext(root))`; `teardown`
resets the setting and removes `root`.
- **C1** `worktreeWorkspacesFolder is under the extension's global storage`:
  it equals `<root>/worktree-workspaces`.
- **C2** `outside a worktree workspace, the current project is what VS Code reports`:
  `currentWorktreeWorkspaceFolder()` is `undefined`, and
  `currentProjectUri()?.toString()` equals
  `(workspace.workspaceFile ?? workspace.workspaceFolders?.[0]?.uri)?.toString()`.
  In the test host both are `undefined` (WWN-F10); written this way, the
  test also holds if the host ever opens a folder.
- **C3** `opensWorktreesAsWorkspaces is on by default and follows its setting`:
  `true` with the setting reset, `false` after setting it `false`.

### `src/test/suite/worktreeNode.test.ts`: 2 new tests

Fail before step 4: the constructor takes three arguments, so the files do
not compile.
- **N11** `names its window after the repository and the tree's branch`:
  `new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, "work", "passwave-web")`
  has `command.arguments` `deepStrictEqual` to
  `[ treePath, "feat/x", "work", "passwave-web · feat/x" ]`.
- **N12** `names a detached tree's window after the repository and the tree's folder`:
  branch `undefined` and repository `"passwave-web"` give
  `command.arguments[3] === "passwave-web · feat-x"`.

N5 stays as it is: built without a repository name, its arguments are still
the three it asserts, which covers the other side of the spread.

### `src/test/suite/storageProviderWorktrees.test.ts`: 1 new test

- **S21** `worktree children name their window after the repository and their branch`:
  `storage.push("repo", makeRepoWithWorktrees("feat"))`, then the first
  child of `rootNode("repo")` has `command.arguments[3] === "repo · feat"`.
  Fails before step 4: the argument is absent.

### `src/test/suite/suggestion.test.ts`: 1 new test

- **SG1** `getProjectDetails suggests a worktree workspace's worktree, named as its window`:
  - import the module as `import * as worktreeWorkspace from "../../utils/worktreeWorkspace";`,
    and `getProjectDetails` beside the existing imports;
  - replace `currentWorktreeWorkspaceFolder` on it, through
    `worktreeWorkspace as unknown as { currentWorktreeWorkspaceFolder: () => WorkspaceFolder | undefined }`,
    with one returning `{ uri: Uri.file("/sites/passwave/worktrees/passwave-core/update-v1"), name: "passwave-core · update-v1", index: 0 }`,
    and restore it in `finally`;
  - `await getProjectDetails()` `deepStrictEqual`s
    `{ path: <that uri>.fsPath, name: "passwave-core · update-v1" }`.
  - Fails before step 4: the export does not exist.

### Coverage

The tests cover every branch of the new module and of the changed code:
- `getRepositoryName`: R1-R6, one per branch, plus R3 for a linked tree.
- `workspaceFileName`: WN2-WN4, including the empty result.
- `writeWorktreeWorkspace`: a fresh file (WW1), the same file kept (WW2,
  WW3), outdated folders (WW4), a file that is not an object, three ways
  (WW5), a previous file that parses (WW6) or does not (WW7), and a failed
  `mkdir` (WW8).
- `pruneWorktreeWorkspaces`: P1-P4, which reach every branch of
  `worktreeFolderOf` and the missing storage folder.
- `buildOpenUri`: each operand of its guard (B1, B3, B4), success (B2), the
  `catch` (B5), and pruning on the way (B6).
- `findWorktreeWorkspaceFolder` and `projectUriOf`: D1-D4.
- The two wrappers and the settings read: C1-C3.
- `WorktreeNode`'s spread: N11, N12 and the unchanged N5.
- `getWorktreeNodes`' new line: S21. `getProjectDetails`' new branch: SG1.

Not reachable from a unit test, as for [[worktrees-under-favorites]]: the
two open commands' lines in `extension.ts`, `updateCurrentProject`'s line,
and `showStatusBar`'s line. The extension under test has its own module
instances, and the test host opens no window to read. The logic they call
is tested above, and manual checks 1-5 in the hand-over cover the lines.

## Verification

Run from the repo root with `PATH=/home/claude/.local/node/bin:$PATH`. The
`npm test` and `vsce` commands run **outside Claude's sandbox**
([[worktrees-under-favorites#wf-d12|WF-D12]]).

1. `npm run lint`: 0 errors and 52 warnings, the same files as today. No
   warning names a file this plan adds. `MockMemento.ts` keeps its two at
   `:10` and `:16`.
2. `npm run build`: `webpack … compiled successfully`.
3. `npm test`: **198 passing**, 0 failing.
4. `git status --short` shows `src/utils/worktreeWorkspace.ts` and
   `src/test/suite/worktreeWorkspace.test.ts` as the only new files outside
   `plans/`, apart from the sandbox's placeholder entries in the repo root,
   and `git diff --stat` touches only the files in *Files*.
5. `npx --yes @vscode/vsce@4.0.0 package` rewrites
   `project-manager-13.1.1.vsix` in the repo root. Then:
   - `unzip -p project-manager-13.1.1.vsix extension/package.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['publisher'], d['version'], 'projectManager.worktrees.openAsWorkspace' in json.dumps(d))"`
     prints `mattlightspeed 13.1.1 True`;
   - `unzip -l project-manager-13.1.1.vsix | grep -cE 'plans/|AGENTS.md'`
     prints `0`;
   - `unzip -Z1 project-manager-13.1.1.vsix | grep -cE '(^|/)\.'` prints
     `0`.
6. `python3 plans/tools/plan_links.py --check` passes.

The plan is done when the hand-over's checks pass.

## Hand-over: installing the rebuilt fork (Matt)

The fork is already installed (WWN-F9), so this replaces it in place. Run in
a terminal of a VS Code window connected to the server:

```bash
code --install-extension /srv/projects/vscode-project-manager/project-manager-13.1.1.vsix --force
```

Then Command Palette → **Developer: Reload Window**, in every window
connected to this server.

**What to expect:**
- The first time each worktree opens this way, VS Code restores none of the
  editors or layout it had as a folder, and Claude Code's panel opens no old
  tabs. Its past sessions are still listed. From then on the window keeps
  its state (WWN-F5, WWN-F7).
- VS Code may ask whether to trust the authors of the files in the
  generated folder (WWN-F5). Trust it. To be asked only once, add
  `/home/claude/.vscode-server/data/User/globalStorage/mattlightspeed.project-manager/worktree-workspaces`
  under **Workspaces: Manage Workspace Trust** → Trusted Folders.
- The title and the Explorer's heading end in `(Workspace)` (WWN-F3).
  Optional, and not tested here: a `window.title` that uses
  `${rootNameShort}` in place of `${rootName}` drops the suffix, and the
  remote name, in every window.

**Manual checks:**
1. In Favorites, expand `passwave-core` and click `update-v1`. The window
   reloads, titled `… passwave-core · update-v1 (Workspace) …`. The
   Explorer's heading names the same, with one root row,
   `passwave-core · update-v1`, expanded.
2. Expand `passwave-scan-app` and use `update-v1`'s inline **Open in New
   Window**. A new window opens, titled `passwave-scan-app · update-v1`.
3. In that window, open a terminal: `pwd` prints the worktree's folder.
   Start a Claude Code session in the panel and ask it for its working
   directory: the worktree's folder.
4. In that window, run **Project Manager: Save Project**. It suggests
   `passwave-scan-app · update-v1` and the worktree's path. Press Escape.
5. The status bar shows no project there, as before (FU-2026-10-005).
   Click a favorite that is not a worktree, such as `passwave-web`: it
   opens as a folder window named `passwave-web`, as before.
6. `ls /home/claude/.vscode-server/data/User/globalStorage/mattlightspeed.project-manager/worktree-workspaces/*/`
   lists one file for each worktree opened.
7. Set `"projectManager.worktrees.openAsWorkspace": false`, and open a
   worktree: it opens as a folder window named `update-v1`. Remove the
   setting.
8. `git -C /srv/projects/vscode-project-manager worktree add /srv/projects/worktrees/vscode-project-manager/wt-check -b wt-check`,
   which is the tree's place in the layout; git creates the folders above
   it, and `/srv/projects/worktrees/` does not exist today (read
   2026-10-22). Open `vscode-project-manager` › `wt-check` in a new window,
   titled `vscode-project-manager · wt-check`, and close that window. Then
   `git -C /srv/projects/vscode-project-manager worktree remove /srv/projects/worktrees/vscode-project-manager/wt-check && git -C /srv/projects/vscode-project-manager branch -D wt-check`,
   and open any other worktree. Check 6's listing no longer has
   `vscode-project-manager · wt-check.code-workspace`. The empty
   `/srv/projects/worktrees/vscode-project-manager/` is left for the next
   tree, or removed with `rmdir -p`.

**Rolling back:** set `"projectManager.worktrees.openAsWorkspace": false`.
Worktrees then open as folders again, with no reinstall.

## Commits

The implementer does not commit (WF-D13). Matt commits on `master`, in this
order:
1. **Open worktrees in workspaces named after their repo and branch**:
   every file in *Files*.
2. **Plans**: `plans/`, with this plan marked implemented and the register
   entries.

The suite is green after each.

## Assumed, not verified

- **Matt's client behaves as 1.143.0 does** for the window title, the
  Explorer, folder setting scopes and workspace trust (WWN-F2 to WWN-F5).
  This server holds no 1.141 workbench to read. Manual checks 1, 2 and 7
  show it.
- **`Uri.file` of a workspace file, from the server's extension host,
  opens on the server.** The mapping that makes it so was read in the
  server builds (WWN-F12), and a folder's URI takes it today; the open of a
  workspace file over Remote-SSH was not run. Manual checks 1 and 2 show
  it.
- **Opening a workspace already open in another window focuses that
  window**, as for folders. Not checked.
- **A terminal in a one-folder workspace starts in that folder.** Not read
  in code. Manual check 3 shows it.
- **Claude Code keeps starting in the first folder.** Read at 2.1.307, which
  updates often (WWN-F7). Manual check 3 shows it.
- **Workspace trust on Matt's client**: whether it is enabled, what is
  trusted, and whether Remote-SSH marks the window trusted. None can be
  read from the server.
- **The `window.title` suggestion** in the hand-over was not tried.
- **The translations** are the implementer's, with no native speaker's
  review.
- **Windows and macOS.** `findWorktreeWorkspaceFolder` compares paths as
  strings, which a case-insensitive file system could defeat. Only Linux is
  run.

## Residue

| ID | Flavour | Severity | Item | Owner |
|---|---|---|---|---|
| WWN-R1 | handover | S3 | Matt installs the rebuilt VSIX with `--force`, reloads every window, trusts the generated folder if asked, and runs the manual checks (*Hand-over*) | vscode-project-manager (Matt) |
| WWN-R2 | limitation | S3 | The first open of each worktree as a workspace, and the first after a branch switch inside it, starts without its saved editors, layout and extensions' workspace state, which VS Code keys by the workspace file (WWN-F5, WWN-D6) | vscode-project-manager |
| WWN-R3 | limitation | S3 | In a worktree's workspace window, window-scoped settings in the tree's `.vscode/settings.json` do not apply. None exists on this host today; `projectManager.worktrees.openAsWorkspace` set to `false` restores them (WWN-F4) | vscode-project-manager |
| WWN-R4 | limitation | S3 | VS Code may ask once to trust the generated folder, since workspace trust covers the workspace file as well as the folder (WWN-F5) | vscode-project-manager |
| WWN-R5 | limitation | S4 | The window title and Explorer heading carry VS Code's ` (Workspace)` suffix. A user `window.title` with `${rootNameShort}` drops it (WWN-F3) | vscode-project-manager |
| WWN-R6 | limitation | S4 | Only `folders` is the extension's: a generated file that a hand edit makes invalid JSON is replaced whole at the next open, and a folder added to it is dropped then (WWN-D6) | vscode-project-manager |
| WWN-R7 | non-goal | S4 | A worktree window that is not itself a favorite still shows no project in the status bar and no ✔; FU-2026-10-005 stays as it is. Its name could be shown from the generated folder's `name` (WWN-D7) | vscode-project-manager |
| WWN-R8 | limitation | S4 | A Recent entry or a restored window whose generated file was pruned, or deleted with the fork's storage on uninstall, fails to open (WWN-D5, WWN-D9) | vscode-project-manager |
| WWN-R9 | non-goal | S4 | A favorite that is itself a linked worktree opens as its folder, unnamed (WWN-D8) | vscode-project-manager |
| WWN-R10 | non-goal | S4 | Not offered upstream: Favorites there has no worktree nodes; it would go with WF-R7 of [[worktrees-under-favorites]] (WWN-D12) | vscode-project-manager |
| WWN-R11 | limitation | S4 | The test host opens no folder, because `src/test/runTest.ts` launches it on a `./testworkspace` that does not exist, so no test runs in a folder or workspace window (WWN-F10) | vscode-project-manager |
| WWN-R12 | limitation | S4 | The eight translations of the two new strings have had no native speaker's review | vscode-project-manager |
| WWN-R13 | limitation | S4 | Recognising a generated workspace compares paths as strings, untested on case-insensitive file systems (Windows, macOS) | vscode-project-manager |
| WWN-R14 | limitation | S4 | The file is written before the switch confirmation and not atomically, and nothing is pruned while the setting is off: a torn, unused or stale file is replaced, reused or removed at the next worktree open with the setting on (WWN-D6, *`src/extension.ts`*) | vscode-project-manager |
| WWN-R15 | limitation | S4 | In a Codespace, Save Project in a generated workspace suggests the worktree's plain path, not the `vscode-remote://codespaces+…` path a folder window there gets, since the new branch of `getProjectDetails` returns before the Codespaces branch (*`src/utils/suggestion.ts`*) | vscode-project-manager |

## Review 1 — what changed (2026-10-22)

Reviewed by Fable 5.1 (`claude-fable-5-1`) in a fresh session, as a
`/plan-sweep` subagent. Every cited line in `src/`, `package.json`, the
`package.nls*.json` and `l10n/` files and the test files was re-read at
`091cb48` and matched the plan; the host facts of WWN-F9 were re-read on
2026-10-22 and hold; the quoted 1.143.0 workbench code, nls message ids
28156, 23030 and 27734, the git extension's `activeRepositoryName` in both
server builds, Claude Code 2.1.307's `kk($)` and `panelTabSessions`, and
`explorer.expandSingleFolderWorkspaces`'s default were all found as quoted.
`plan_links.py --check` and the sweep's anchor check passed before and
after the edits. No question was undecidable from the repo.

- **Added WWN-F12**: the fork runs in the server's extension host, whose
  URI transformer gives a remote window's workspace file, folders and
  storage URI the `file` scheme and sends `Uri.file(…)` back as
  `vscode-remote://…`. This is what WWN-D7's `file`-scheme test and
  `buildOpenUri` rely on in Matt's windows; the plan had carried it as an
  assumption. The *Assumed, not verified* entry now says only the open
  itself was not run.
- **WWN-D3** now says the repository name is read from the favorite's
  common git folder, which is what `getRepositoryName(projectPath)` does;
  the text had said "the tree's".
- **WWN-D6** records that nothing is pruned while the setting is off;
  **WWN-R14** carries that, the non-atomic write and the file written before
  the switch confirmation, which the body stated but *Residue* did not.
- **`src/utils/suggestion.ts`** notes that the new branch does not take the
  Codespaces path, carried as **WWN-R15**.
- **Tests**: the `buildOpenUri` suite's `setup` is stated not to create
  `globalStorage`, and B5 to write a regular file there, so that the
  `ENOTDIR` path is unambiguous.
- **Hand-over check 8** notes that `/srv/projects/worktrees/` does not
  exist today and git creates it, and what to do with the empty folder
  after.
- The note on the catch variable's type was corrected: it is `any`, and
  the point is that no `any` is written for the lint to flag.
- Header, Status and Summary brought to the reviewed state.

Not changed, checked and kept: the mechanism (WWN-D1), the storage place
(WWN-D5), the three readers rerouted by WWN-D7 and the unchanged fourth
(`Locators.removeRootPath`, which filters by `workspace.rootPath`), the
test counts 158 → 164 → 165 → 194 → 198, the translation files' line
endings and anchors, and the Gate's state.

## Implementation (2026-10-22)

Implemented on `master` at `3502b18`, which differs from the snapshot
`091cb48` only under `plans/`, by Opus 5.5, in the order of *Order of work*.
Step 0 was not needed: `vscode-whats-new/` and `node_modules/` were
populated. Nothing is committed (WF-D13).

**Run, and how it came out:**
- Baseline, before any change: lint 0 errors and 52 warnings; `npm test`,
  outside Claude's sandbox, 158 passing.
- `npm test` at each step, outside the sandbox: 164, 165, 194 and 198
  passing, as each step expected, with no failure at any step.
- *Verification* 1-6: lint 0 errors and 52 warnings, in the same nine files
  as before, `MockMemento.ts`'s two still at `:10` and `:16`; `npm run build`
  compiled; 198 passing; the diff touches only *Files*, the two new files
  are the only untracked ones outside `plans/`, and the `plans/` changes
  are this plan's and two left by another session; the VSIX printed
  `mattlightspeed 13.1.1 True`, `0` and `0` (110 files, 2.14 MB);
  `plan_links.py --check` passed.
- The test log's `DEP0169` deprecation line comes from VS Code's own agent
  host, and was in the baseline run too.

**Where the implementation chose what the text left open:**
- N11 and N12 follow N5, and S21 follows the profile test.
- WW2's `<root>/elsewhere/feat-x` is not created, since writing a file for
  it does not read it. B6's second tree is `<root>/worktrees/repo/gone`, and
  P3's subfolders are `key0` to `key3` and `empty`.
- SG1 names its view of the module `worktreeWorkspaceApi`, as
  `decoration.test.ts` names `windowApi`, rather than `module`, which shadows
  Node's.
- The translations are the implementer's, in each file's existing words:
  `pt-br` keeps `workspace` and `diretório`, `zh-tw` `文件夾` and `窗口`, and
  `fr` puts a space before the colon (WWN-R12).
- WWN-R7 is FU-2026-10-005's item, which the plan keeps as it stands, so it
  is recorded on that entry after `; also`, with no entry of its own.

**Not checked:**
- That each new test fails before its step: no test was run against the
  tree as it stood before its step. Each fails to compile there, except M7,
  M5, M6 and S21, which assert what the step adds.
- Anything in *Assumed, not verified*, and the hand-over's manual checks,
  which need Matt's editor.

## Tests to remove after implementation

None. Every test this plan adds stays, and no existing test becomes
redundant.
