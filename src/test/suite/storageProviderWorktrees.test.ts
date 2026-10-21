/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import path = require("path");
import * as vscode from "vscode";
import { Container } from "../../core/container";
import { ProjectNode, TagNode, WorktreeNode } from "../../sidebar/nodes";
import { StorageProvider } from "../../sidebar/storageProvider";
import { ProjectStorage } from "../../storage/storage";
import { createMockContext } from "./mocks/MockMemento";
import { addLinkedWorktree, makeMainCheckout, makeTempDir, removeTempDir, sleep, waitFor } from "./mocks/worktreeFixtures";

const RESET_SETTINGS = [ "worktrees.showInFavorites", "worktrees.collapseItems", "git.showBranchName" ];

async function setSetting(key: string, value: unknown): Promise<void> {
    await vscode.workspace.getConfiguration("projectManager").update(key, value, vscode.ConfigurationTarget.Global);
}

async function resetSettings(): Promise<void> {
    for (const key of RESET_SETTINGS) {
        await setSetting(key, undefined);
    }
}

suite("StorageProvider worktrees", function () {
    this.timeout(5000);

    let root: string;
    let storage: ProjectStorage;
    let provider: StorageProvider;

    function makeRepoWithWorktrees(...branches: string[]): string {
        const repo = makeMainCheckout(root, "repo");
        for (const branch of branches) {
            addLinkedWorktree(path.join(repo, ".git"), branch, path.join(root, "worktrees", "repo", branch), { branch });
        }
        return repo;
    }

    async function rootNodes(): Promise<ProjectNode[]> {
        return await provider.getChildren() as ProjectNode[];
    }

    async function rootNode(name: string): Promise<ProjectNode> {
        return (await rootNodes()).find(node => node.label === name);
    }

    async function children(element: ProjectNode | TagNode): Promise<ProjectNode[]> {
        return await provider.getChildren(element) as ProjectNode[];
    }

    suiteSetup(async () => {
        Container.initialize(createMockContext());
        await resetSettings();
    });

    setup(() => {
        root = makeTempDir("storage-provider-worktrees-");
        storage = new ProjectStorage(path.join(root, "projects.json"));
        provider = new StorageProvider(storage);
    });

    teardown(async () => {
        provider.dispose();
        await resetSettings();
        await Container.context.globalState.update("viewAsList", undefined);
        await StorageProvider.resetWorktreesExpansionState();
        await StorageProvider.resetTagExpansionState();
        removeTempDir(root);
    });

    test("a favorite with linked worktrees starts collapsed", async () => {
        storage.push("repo", makeRepoWithWorktrees("feat"));

        assert.strictEqual((await rootNode("repo")).collapsibleState, vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("a favorite with no linked worktrees, or not a repository, is not collapsible", async () => {
        storage.push("repo", makeMainCheckout(root, "repo"));
        storage.push("plain", root);

        assert.strictEqual((await rootNode("repo")).collapsibleState, vscode.TreeItemCollapsibleState.None);
        assert.strictEqual((await rootNode("plain")).collapsibleState, vscode.TreeItemCollapsibleState.None);
    });

    test("a remote favorite is not collapsible and has no children", async () => {
        storage.push("remote", "vscode-remote://ssh-remote+host/srv/x");

        const node = await rootNode("remote");
        assert.strictEqual(node.collapsibleState, vscode.TreeItemCollapsibleState.None);
        assert.deepStrictEqual(await children(node), []);
    });

    test("expanding a favorite lists its worktrees as WorktreeNodes sorted by label", async () => {
        storage.push("repo", makeRepoWithWorktrees("gamma10", "Beta", "gamma9", "alpha"));

        const worktreeNodes = await children(await rootNode("repo"));
        assert.deepStrictEqual(worktreeNodes.map(node => node.label), [ "alpha", "Beta", "gamma9", "gamma10" ]);
        assert.ok(worktreeNodes.every(node => node instanceof WorktreeNode));
    });

    test("worktree children carry the favorite's profile", async () => {
        storage.push("repo", makeRepoWithWorktrees("feat", "fix"), [], "work");

        const worktreeNodes = await children(await rootNode("repo"));
        assert.strictEqual(worktreeNodes.length, 2);
        assert.ok(worktreeNodes.every(node => node.command.arguments[ 2 ] === "work"));
    });

    test("in tag view, a favorite under its tag is collapsible and expands to its worktrees", async () => {
        await Container.context.globalState.update("viewAsList", false);
        storage.push("repo", makeRepoWithWorktrees("feat"), [ "Work" ]);

        const [ tagNode ] = await provider.getChildren() as TagNode[];
        assert.ok(tagNode instanceof TagNode);
        assert.strictEqual(tagNode.label, "Work");

        const [ repoNode ] = await children(tagNode);
        assert.strictEqual(repoNode.label, "repo");
        assert.strictEqual(repoNode.collapsibleState, vscode.TreeItemCollapsibleState.Collapsed);

        const worktreeNodes = await children(repoNode);
        assert.strictEqual(worktreeNodes.length, 1);
        assert.ok(worktreeNodes[ 0 ] instanceof WorktreeNode);
    });

    test("with worktrees.showInFavorites off, a favorite with worktrees is not collapsible", async () => {
        await setSetting("worktrees.showInFavorites", false);
        storage.push("repo", makeRepoWithWorktrees("feat"));

        assert.strictEqual((await rootNode("repo")).collapsibleState, vscode.TreeItemCollapsibleState.None);
    });

    test("with worktrees.showInFavorites off, expanding a favorite gives no children", async () => {
        await setSetting("worktrees.showInFavorites", false);
        storage.push("repo", makeRepoWithWorktrees("feat"));

        assert.deepStrictEqual(await children(await rootNode("repo")), []);
    });

    test("a WorktreeNode has no children", async () => {
        storage.push("repo", makeRepoWithWorktrees("feat"));

        const [ worktreeNode ] = await children(await rootNode("repo"));
        assert.deepStrictEqual(await children(worktreeNode), []);
    });

    test("alwaysExpanded starts a favorite with worktrees expanded", async () => {
        await setSetting("worktrees.collapseItems", "alwaysExpanded");
        storage.push("repo", makeRepoWithWorktrees("feat"));

        assert.strictEqual((await rootNode("repo")).collapsibleState, vscode.TreeItemCollapsibleState.Expanded);
    });

    test("alwaysCollapsed ignores a remembered expansion", async () => {
        const repo = makeRepoWithWorktrees("feat");
        await StorageProvider.rememberWorktreesExpansion(repo, true);
        await setSetting("worktrees.collapseItems", "alwaysCollapsed");

        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("startCollapsed and startExpanded honour a remembered state", async () => {
        const repo = makeRepoWithWorktrees("feat");

        await setSetting("worktrees.collapseItems", "startCollapsed");
        await StorageProvider.rememberWorktreesExpansion(repo, true);
        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Expanded);

        await setSetting("worktrees.collapseItems", "startExpanded");
        await StorageProvider.rememberWorktreesExpansion(repo, false);
        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("rememberWorktreesExpansion stores the state only for startExpanded and startCollapsed", async () => {
        const repo = makeRepoWithWorktrees("feat");

        await setSetting("worktrees.collapseItems", "alwaysExpanded");
        await StorageProvider.rememberWorktreesExpansion(repo, false);
        await setSetting("worktrees.collapseItems", "startExpanded");
        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Expanded);

        await StorageProvider.rememberWorktreesExpansion(repo, false);
        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("resetWorktreesExpansionState forgets remembered states", async () => {
        const repo = makeRepoWithWorktrees("feat");
        await StorageProvider.rememberWorktreesExpansion(repo, true);

        await StorageProvider.resetWorktreesExpansionState();

        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("worktree and tag expansion states are stored apart", async () => {
        const repo = makeRepoWithWorktrees("feat");

        await StorageProvider.rememberWorktreesExpansion(repo, true);
        assert.strictEqual(StorageProvider.getTagCollapsibleState(repo, "startCollapsed"), vscode.TreeItemCollapsibleState.Collapsed);

        await StorageProvider.resetWorktreesExpansionState();
        await StorageProvider.setTagExpanded(repo, true);
        assert.strictEqual(StorageProvider.getWorktreesCollapsibleState(repo), vscode.TreeItemCollapsibleState.Collapsed);
    });

    test("refreshesOnWindowFocus follows git.showBranchName and worktrees.showInFavorites", async () => {
        const cases: [ string, boolean, boolean ][] = [
            [ "never", false, false ],
            [ "never", true, true ],
            [ "onlyInSideBar", false, true ],
            [ "always", false, true ],
            [ "onlyInCommandPalette", false, false ]
        ];
        for (const [ showBranchName, showInFavorites, expected ] of cases) {
            await setSetting("git.showBranchName", showBranchName);
            await setSetting("worktrees.showInFavorites", showInFavorites);
            assert.strictEqual(StorageProvider.refreshesOnWindowFocus(), expected, `${showBranchName}, ${showInFavorites}`);
        }
    });

    test("a new worktree record refreshes the tree", async () => {
        const repo = makeMainCheckout(root, "repo");
        storage.push("repo", repo);
        let count = 0;
        const subscription = provider.onDidChangeTreeData(() => count++);
        try {
            await provider.getChildren();

            addLinkedWorktree(path.join(repo, ".git"), "feat", path.join(root, "worktrees", "repo", "feat"));

            await waitFor(() => count >= 1);
        } finally {
            subscription.dispose();
        }
    });

    test("with worktrees.showInFavorites off, a new worktree record does not refresh the tree", async () => {
        await setSetting("worktrees.showInFavorites", false);
        const repo = makeMainCheckout(root, "repo");
        storage.push("repo", repo);
        let count = 0;
        const subscription = provider.onDidChangeTreeData(() => count++);
        try {
            await provider.getChildren();

            addLinkedWorktree(path.join(repo, ".git"), "feat", path.join(root, "worktrees", "repo", "feat"));

            await sleep(800);
            assert.strictEqual(count, 0);
        } finally {
            subscription.dispose();
        }
    });

    test("git.showBranchName still describes a favorite by its branch", async () => {
        await setSetting("git.showBranchName", "always");
        storage.push("repo", makeMainCheckout(root, "repo", "develop"));

        assert.strictEqual((await rootNode("repo")).description, "develop");
    });

    test("worktrees with the same label are ordered by path", async () => {
        const repo = makeMainCheckout(root, "repo");
        addLinkedWorktree(path.join(repo, ".git"), "b", path.join(root, "b", "x"), { detached: true });
        addLinkedWorktree(path.join(repo, ".git"), "a", path.join(root, "a", "x"), { detached: true });
        storage.push("repo", repo);

        const worktreeNodes = await children(await rootNode("repo"));
        assert.deepStrictEqual(worktreeNodes.map(node => node.label), [ "x", "x" ]);
        assert.strictEqual(worktreeNodes[ 0 ].preview.path, path.join(root, "a", "x"));
    });
});
