/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import fs = require("fs");
import path = require("path");
import { ConfigurationTarget, Uri, window, workspace, WorkspaceFolder } from "vscode";
import { Container } from "../../core/container";
import {
    buildOpenUri, currentProjectUri, currentWorktreeWorkspaceFolder, findWorktreeWorkspaceFolder, opensWorktreesAsWorkspaces,
    projectUriOf, pruneWorktreeWorkspaces, workspaceFileName, worktreeWindowName, worktreeWorkspacesFolder, writeWorktreeWorkspace
} from "../../utils/worktreeWorkspace";
import { createMockContext } from "./mocks/MockMemento";
import { makeTempDir, removeTempDir } from "./mocks/worktreeFixtures";

function readJson(file: string): unknown {
    return JSON.parse(fs.readFileSync(file, "utf8"));
}

function keyFolders(storage: string): string[] {
    return fs.existsSync(storage) ? fs.readdirSync(storage) : [];
}

function workspaceFolder(uri: Uri, name: string): WorkspaceFolder {
    return { uri, name, index: 0 };
}

async function setOpenAsWorkspace(value: boolean | undefined): Promise<void> {
    await workspace.getConfiguration("projectManager").update("worktrees.openAsWorkspace", value, ConfigurationTarget.Global);
}

suite("Worktree window names", () => {

    test("worktreeWindowName joins the repository and the label", () => {
        assert.strictEqual(worktreeWindowName("passwave-core", "feature/login"), "passwave-core · feature/login");
    });

    test("workspaceFileName keeps a name that every platform allows", () => {
        assert.strictEqual(workspaceFileName("passwave-core · update-v1"), "passwave-core · update-v1.code-workspace");
    });

    test("workspaceFileName replaces each character that a file name cannot hold", () => {
        assert.strictEqual(workspaceFileName("repo · feature/login"), "repo · feature-login.code-workspace");
        assert.strictEqual(workspaceFileName("a<b>c:d\"e\\f|g?h*i"), "a-b-c-d-e-f-g-h-i.code-workspace");
        assert.strictEqual(workspaceFileName("a\u0001b\tc"), "a-b-c.code-workspace");
    });

    test("workspaceFileName drops trailing dots and spaces, and names an empty result", () => {
        assert.strictEqual(workspaceFileName("repo · x. ."), "repo · x.code-workspace");
        assert.strictEqual(workspaceFileName("..."), "worktree.code-workspace");
    });
});

suite("writeWorktreeWorkspace", function () {
    this.timeout(5000);

    let root: string;
    let storage: string;
    let tree: string;

    setup(() => {
        root = makeTempDir("worktree-workspace-");
        storage = path.join(root, "storage");
        tree = path.join(root, "worktrees", "repo", "feat-x");
        fs.mkdirSync(tree, { recursive: true });
    });

    teardown(() => {
        removeTempDir(root);
    });

    test("writes a workspace whose one folder is the worktree, named as its window", () => {
        const file = writeWorktreeWorkspace(storage, tree, "repo · feat/x");

        assert.strictEqual(path.basename(file), "repo · feat-x.code-workspace");
        assert.strictEqual(path.dirname(path.dirname(file)), storage);
        assert.match(path.basename(path.dirname(file)), /^[0-9a-f]{16}$/);
        assert.strictEqual(fs.readFileSync(file, "utf8"),
            JSON.stringify({ folders: [ { name: "repo · feat/x", path: tree } ] }, null, "\t") + "\n");
    });

    test("gives each worktree one folder of its own, the same every time", () => {
        const first = writeWorktreeWorkspace(storage, tree, "repo · feat-x");
        const second = writeWorktreeWorkspace(storage, tree, "repo · feat-x");
        const elsewhere = writeWorktreeWorkspace(storage, path.join(root, "elsewhere", "feat-x"), "repo · feat-x");

        assert.strictEqual(second, first);
        assert.notStrictEqual(path.dirname(elsewhere), path.dirname(first));
        assert.strictEqual(path.basename(elsewhere), path.basename(first));
    });

    test("leaves an up-to-date file untouched, with its other keys", () => {
        const file = writeWorktreeWorkspace(storage, tree, "repo · feat-x");
        const content = JSON.stringify({ folders: [ { name: "repo · feat-x", path: tree } ], settings: { "editor.tabSize": 2 } });
        fs.writeFileSync(file, content);
        const aMinuteAgo = new Date(Date.now() - 60000);
        fs.utimesSync(file, aMinuteAgo, aMinuteAgo);
        const modified = fs.statSync(file).mtimeMs;

        writeWorktreeWorkspace(storage, tree, "repo · feat-x");

        assert.strictEqual(fs.readFileSync(file, "utf8"), content);
        assert.strictEqual(fs.statSync(file).mtimeMs, modified);
    });

    test("replaces the folders of an outdated file and keeps its other keys", () => {
        const file = writeWorktreeWorkspace(storage, tree, "repo · feat-x");
        const settings = { "editor.tabSize": 2 };
        fs.writeFileSync(file, JSON.stringify({ folders: [ { path: "/somewhere/else" } ], settings }));

        writeWorktreeWorkspace(storage, tree, "repo · feat-x");

        assert.deepStrictEqual(readJson(file), { folders: [ { name: "repo · feat-x", path: tree } ], settings });
    });

    test("replaces a file that is not a JSON object", () => {
        const file = writeWorktreeWorkspace(storage, tree, "repo · feat-x");
        for (const content of [ "// edited\n{ \"folders\": [] }", "[]", "null" ]) {
            fs.writeFileSync(file, content);

            writeWorktreeWorkspace(storage, tree, "repo · feat-x");

            assert.deepStrictEqual(readJson(file), { folders: [ { name: "repo · feat-x", path: tree } ] }, content);
        }
    });

    test("moves the other keys of the worktree's previous file to its new name, and removes the previous file", () => {
        const previous = writeWorktreeWorkspace(storage, tree, "repo · a");
        const settings = { "editor.tabSize": 2 };
        fs.writeFileSync(previous, JSON.stringify({ ...(readJson(previous) as object), settings }));

        const file = writeWorktreeWorkspace(storage, tree, "repo · b");

        assert.strictEqual(path.dirname(file), path.dirname(previous));
        assert.ok(!fs.existsSync(previous));
        assert.deepStrictEqual(readJson(file), { folders: [ { name: "repo · b", path: tree } ], settings });
    });

    test("starts afresh when the previous file is not a JSON object, and removes it", () => {
        const previous = writeWorktreeWorkspace(storage, tree, "repo · a");
        fs.writeFileSync(previous, "not json");

        const file = writeWorktreeWorkspace(storage, tree, "repo · b");

        assert.ok(!fs.existsSync(previous));
        assert.deepStrictEqual(readJson(file), { folders: [ { name: "repo · b", path: tree } ] });
    });

    test("throws when its folder cannot be made", () => {
        const blocked = path.join(root, "blocked");
        fs.writeFileSync(blocked, "");

        assert.throws(() => writeWorktreeWorkspace(path.join(blocked, "storage"), tree, "repo · feat-x"));
    });
});

suite("pruneWorktreeWorkspaces", function () {
    this.timeout(5000);

    let root: string;
    let storage: string;

    function makeTree(name: string): string {
        const tree = path.join(root, "worktrees", "repo", name);
        fs.mkdirSync(tree, { recursive: true });
        return tree;
    }

    setup(() => {
        root = makeTempDir("worktree-workspace-");
        storage = path.join(root, "storage");
    });

    teardown(() => {
        removeTempDir(root);
    });

    test("removes the folder of a worktree that no longer exists", () => {
        const tree = makeTree("gone");
        const file = writeWorktreeWorkspace(storage, tree, "repo · gone");
        fs.rmSync(tree, { recursive: true });

        pruneWorktreeWorkspaces(storage);

        assert.ok(!fs.existsSync(path.dirname(file)));
    });

    test("keeps the folder of a worktree that exists", () => {
        const file = writeWorktreeWorkspace(storage, makeTree("feat"), "repo · feat");

        pruneWorktreeWorkspaces(storage);

        assert.ok(fs.existsSync(file));
    });

    test("removes a folder whose files name no folder", () => {
        const contents = [ "not json", "{}", "{\"folders\":[]}", "{\"folders\":[{\"uri\":\"x\"}]}" ];
        contents.forEach((content, index) => {
            const keyFolder = path.join(storage, `key${index}`);
            fs.mkdirSync(keyFolder, { recursive: true });
            fs.writeFileSync(path.join(keyFolder, "x.code-workspace"), content);
        });
        fs.mkdirSync(path.join(storage, "empty"));

        pruneWorktreeWorkspaces(storage);

        assert.deepStrictEqual(keyFolders(storage), []);
    });

    test("ignores a file beside the folders, and a storage folder that does not exist", () => {
        fs.mkdirSync(storage, { recursive: true });
        fs.writeFileSync(path.join(storage, "stray"), "");

        pruneWorktreeWorkspaces(storage);

        assert.deepStrictEqual(keyFolders(storage), [ "stray" ]);
        assert.doesNotThrow(() => pruneWorktreeWorkspaces(path.join(root, "nowhere")));
    });
});

suite("Worktree workspace windows", () => {

    const storage = path.resolve("/storage/worktree-workspaces");
    const tree = Uri.file("/sites/worktrees/repo/feat");
    const treeFolder = workspaceFolder(tree, "repo · feat");
    const generated = Uri.file(path.join(storage, "0123456789abcdef", "repo · feat.code-workspace"));

    test("finds the folder of a generated worktree workspace", () => {
        assert.strictEqual(findWorktreeWorkspaceFolder(generated, [ treeFolder ], storage), treeFolder);
    });

    test("ignores a workspace file that is not one the extension writes", () => {
        const others = [
            "/home/user/mine.code-workspace",
            path.join(storage, "repo · feat.code-workspace"),
            path.join(storage, "0123456789abcdef", "deeper", "repo · feat.code-workspace"),
            path.join(storage, "0123456789abcdef", "repo · feat.json")
        ];
        for (const other of others) {
            assert.strictEqual(findWorktreeWorkspaceFolder(Uri.file(other), [ treeFolder ], storage), undefined, other);
        }
    });

    test("ignores a folder window, a remote workspace file and a workspace without folders", () => {
        const remote = generated.with({ scheme: "vscode-remote", authority: "ssh-remote+host" });

        assert.strictEqual(findWorktreeWorkspaceFolder(undefined, [ treeFolder ], storage), undefined);
        assert.strictEqual(findWorktreeWorkspaceFolder(remote, [ treeFolder ], storage), undefined);
        assert.strictEqual(findWorktreeWorkspaceFolder(generated, [], storage), undefined);
        assert.strictEqual(findWorktreeWorkspaceFolder(generated, undefined, storage), undefined);
    });

    test("projectUriOf takes a worktree workspace's folder, another workspace's file, or a folder window's folder", () => {
        const mine = Uri.file("/home/user/mine.code-workspace");

        assert.strictEqual(projectUriOf(generated, [ treeFolder ], storage), tree);
        assert.strictEqual(projectUriOf(mine, [ treeFolder ], storage), mine);
        assert.strictEqual(projectUriOf(undefined, [ treeFolder ], storage), tree);
        assert.strictEqual(projectUriOf(undefined, undefined, storage), undefined);
    });
});

suite("buildOpenUri", function () {
    this.timeout(5000);

    let root: string;
    let globalStorage: string;
    let generatedFolder: string;
    let tree: string;

    suiteSetup(async () => {
        await setOpenAsWorkspace(undefined);
    });

    setup(() => {
        root = makeTempDir("worktree-workspace-");
        globalStorage = path.join(root, "globalStorage");
        generatedFolder = path.join(globalStorage, "worktree-workspaces");
        tree = path.join(root, "worktrees", "repo", "feat");
        fs.mkdirSync(tree, { recursive: true });
        Container.initialize(createMockContext(globalStorage));
    });

    teardown(async () => {
        await setOpenAsWorkspace(undefined);
        removeTempDir(root);
    });

    test("opens a favorite as its folder, and writes nothing", () => {
        assert.strictEqual(buildOpenUri(tree).toString(), Uri.file(tree).toString());
        assert.ok(!fs.existsSync(generatedFolder));
    });

    test("opens a worktree through its generated workspace", () => {
        const uri = buildOpenUri(tree, "repo · feat");

        assert.strictEqual(uri.scheme, "file");
        assert.strictEqual(path.dirname(path.dirname(uri.fsPath)), generatedFolder);
        assert.strictEqual(path.basename(uri.fsPath), "repo · feat.code-workspace");
        assert.ok(fs.existsSync(uri.fsPath));
    });

    test("opens a worktree as its folder when worktrees.openAsWorkspace is off", async () => {
        await setOpenAsWorkspace(false);

        assert.strictEqual(buildOpenUri(tree, "repo · feat").toString(), Uri.file(tree).toString());
        assert.ok(!fs.existsSync(generatedFolder));
    });

    test("opens a remote path as it always has, and writes nothing", () => {
        const remotePath = "vscode-remote://ssh-remote+host/srv/repo";

        assert.strictEqual(buildOpenUri(remotePath, "repo · feat").toString(), Uri.parse(remotePath).toString());
        assert.ok(!fs.existsSync(generatedFolder));
    });

    test("opens the folder, with a warning, when the workspace cannot be written", () => {
        fs.writeFileSync(globalStorage, "");
        const windowApi = window as unknown as { showWarningMessage: (message: string) => Thenable<string | undefined> };
        const originalShowWarningMessage = windowApi.showWarningMessage;
        const warnings: string[] = [];
        windowApi.showWarningMessage = (message: string) => {
            warnings.push(message);
            return Promise.resolve(undefined);
        };

        try {
            assert.strictEqual(buildOpenUri(tree, "repo · feat").toString(), Uri.file(tree).toString());
        } finally {
            windowApi.showWarningMessage = originalShowWarningMessage;
        }

        assert.strictEqual(warnings.length, 1);
        assert.ok(warnings[ 0 ].startsWith("Could not write a workspace for this worktree, so it opens as a folder: "), warnings[ 0 ]);
    });

    test("removes the workspaces of worktrees that are gone", () => {
        const gone = path.join(root, "worktrees", "repo", "gone");
        fs.mkdirSync(gone, { recursive: true });
        const goneFile = buildOpenUri(gone, "repo · gone").fsPath;
        fs.rmSync(gone, { recursive: true });

        const treeFile = buildOpenUri(tree, "repo · feat").fsPath;

        assert.ok(!fs.existsSync(path.dirname(goneFile)));
        assert.deepStrictEqual(keyFolders(generatedFolder), [ path.basename(path.dirname(treeFile)) ]);
    });
});

suite("Worktree workspace settings and storage", function () {
    this.timeout(5000);

    let root: string;

    setup(() => {
        root = makeTempDir("worktree-workspace-");
        Container.initialize(createMockContext(root));
    });

    teardown(async () => {
        await setOpenAsWorkspace(undefined);
        removeTempDir(root);
    });

    test("worktreeWorkspacesFolder is under the extension's global storage", () => {
        assert.strictEqual(worktreeWorkspacesFolder(), path.join(root, "worktree-workspaces"));
    });

    test("outside a worktree workspace, the current project is what VS Code reports", () => {
        assert.strictEqual(currentWorktreeWorkspaceFolder(), undefined);
        assert.strictEqual(currentProjectUri()?.toString(), (workspace.workspaceFile ?? workspace.workspaceFolders?.[ 0 ]?.uri)?.toString());
    });

    test("opensWorktreesAsWorkspaces is on by default and follows its setting", async () => {
        assert.strictEqual(opensWorktreesAsWorkspaces(), true);

        await setOpenAsWorkspace(false);

        assert.strictEqual(opensWorktreesAsWorkspaces(), false);
    });
});
