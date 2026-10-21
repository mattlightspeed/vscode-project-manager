/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import { MarkdownString, ThemeIcon, TreeItemCollapsibleState } from "vscode";
import { Container } from "../../core/container";
import { WorktreeNode } from "../../sidebar/nodes";
import { createMockContext } from "./mocks/MockMemento";

suite("WorktreeNode", () => {

    const projectPath = "/sites/passwave/passwave-web";
    const treePath = "/sites/passwave/worktrees/passwave-web/feat-x";

    suiteSetup(() => {
        Container.initialize(createMockContext());
    });

    test("labels a tree by its branch", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, undefined);

        assert.strictEqual(node.label, "feat/x");
    });

    test("labels a detached tree by its folder name and says so", () => {
        const node = new WorktreeNode({ path: treePath, branch: undefined, missing: false }, projectPath, undefined);

        assert.strictEqual(node.label, "feat-x");
        assert.strictEqual(node.description, "worktrees/passwave-web/feat-x (detached)");
    });

    test("describes a tree by its path relative to the favorite's parent folder", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, undefined);

        assert.strictEqual(node.description, "worktrees/passwave-web/feat-x");
    });

    test("describes a tree outside the favorite's parent folder by its absolute path", () => {
        const outside = new WorktreeNode({ path: "/tmp/wt-check", branch: "wt-check", missing: false }, projectPath, undefined);
        const above = new WorktreeNode({ path: "/sites", branch: "main", missing: false }, projectPath, undefined);

        assert.strictEqual(outside.description, "/tmp/wt-check");
        assert.strictEqual(above.description, "/sites");
    });

    test("opens through _projectManager.open with the tree's path, its label and the favorite's profile", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, "work");

        assert.strictEqual(node.command.command, "_projectManager.open");
        assert.deepStrictEqual(node.command.arguments, [ treePath, "feat/x", "work" ]);
    });

    test("is a WorktreeNodeKind with a git-branch icon", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, undefined);

        assert.strictEqual(node.contextValue, "WorktreeNodeKind");
        assert.strictEqual((node.iconPath as ThemeIcon).id, "git-branch");
    });

    test("a missing tree has no command, is a WorktreeMissingNodeKind with a warning icon, and says so", () => {
        const node = new WorktreeNode({ path: treePath, branch: undefined, missing: true }, projectPath, "work");

        assert.strictEqual(node.command, undefined);
        assert.strictEqual(node.contextValue, "WorktreeMissingNodeKind");
        assert.strictEqual((node.iconPath as ThemeIcon).id, "warning");
        assert.strictEqual(node.description, "worktrees/passwave-web/feat-x (missing)");
        const tooltip = (node.tooltip as MarkdownString).value;
        assert.ok(tooltip.includes("git worktree prune"));
        assert.ok(tooltip.includes(treePath));
    });

    test("is never collapsible", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, undefined);

        assert.strictEqual(node.collapsibleState, TreeItemCollapsibleState.None);
    });

    test("carries the tree's path in its resourceUri", () => {
        const node = new WorktreeNode({ path: treePath, branch: "feat/x", missing: false }, projectPath, undefined);

        assert.strictEqual(node.resourceUri.scheme, "projectManager-view");
        assert.strictEqual(node.resourceUri.path, treePath);
    });

    test("describes a tree in a folder whose name starts with .. by its relative path", () => {
        const node = new WorktreeNode({ path: "/sites/passwave/..wt/feat", branch: "feat", missing: false }, projectPath, undefined);

        assert.strictEqual(node.description, "..wt/feat");
    });
});
