/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import { execFileSync } from "child_process";
import fs = require("fs");
import path = require("path");
import { getGitCommonDir, getLinkedWorktrees } from "../../utils/worktrees";
import { addLinkedWorktree, makeMainCheckout, makeTempDir, removeTempDir, toGitPath } from "./mocks/worktreeFixtures";

suite("getGitCommonDir", function () {
    this.timeout(5000);

    let root: string;

    setup(() => {
        root = makeTempDir("worktrees-");
    });

    teardown(() => {
        removeTempDir(root);
    });

    test("returns undefined for a folder without .git", () => {
        const workspaceFile = path.join(root, "x.code-workspace");
        fs.writeFileSync(workspaceFile, "{}");

        assert.strictEqual(getGitCommonDir(root), undefined);
        assert.strictEqual(getGitCommonDir(workspaceFile), undefined);
    });

    test("returns the .git folder of a main checkout", () => {
        const repo = makeMainCheckout(root, "repo");

        assert.strictEqual(getGitCommonDir(repo), path.join(repo, ".git"));
    });

    test("follows a linked worktree's .git file and commondir to the clone's .git folder", () => {
        const repo = makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        addLinkedWorktree(path.join(repo, ".git"), "feat", tree);

        assert.strictEqual(getGitCommonDir(tree), path.join(repo, ".git"));
    });

    test("resolves a relative gitdir line against the project folder", () => {
        const repo = makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        addLinkedWorktree(path.join(repo, ".git"), "feat", tree);
        fs.writeFileSync(path.join(tree, ".git"), "gitdir: ../../../repo/.git/worktrees/feat\n");

        assert.strictEqual(getGitCommonDir(tree), path.join(repo, ".git"));
    });

    test("returns the folder a .git file names when it has no commondir", () => {
        const moduleDir = path.join(root, "modules", "sub");
        fs.mkdirSync(moduleDir, { recursive: true });
        const sub = path.join(root, "sub");
        fs.mkdirSync(sub);
        fs.writeFileSync(path.join(sub, ".git"), `gitdir: ${toGitPath(moduleDir)}\n`);

        assert.strictEqual(getGitCommonDir(sub), moduleDir);
    });

    test("returns undefined for a .git file without a gitdir line", () => {
        const project = path.join(root, "project");
        fs.mkdirSync(project);
        fs.writeFileSync(path.join(project, ".git"), "not a gitdir\n");

        assert.strictEqual(getGitCommonDir(project), undefined);
    });

    test("returns undefined when commondir cannot be read", () => {
        const repo = makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        const recordDir = addLinkedWorktree(path.join(repo, ".git"), "feat", tree);
        fs.unlinkSync(path.join(recordDir, "commondir"));
        fs.mkdirSync(path.join(recordDir, "commondir"));

        assert.strictEqual(getGitCommonDir(tree), undefined);
    });
});

suite("getLinkedWorktrees", function () {
    this.timeout(5000);

    let root: string;
    let repo: string;
    let commonDir: string;

    setup(() => {
        root = makeTempDir("worktrees-");
        repo = path.join(root, "repo");
        commonDir = path.join(repo, ".git");
    });

    teardown(() => {
        removeTempDir(root);
    });

    test("returns [] for a folder that is not a git repository", () => {
        assert.deepStrictEqual(getLinkedWorktrees(root), []);
    });

    test("returns [] when the clone has no worktrees folder", () => {
        makeMainCheckout(root, "repo");

        assert.deepStrictEqual(getLinkedWorktrees(repo), []);
    });

    test("returns [] for an empty worktrees folder", () => {
        makeMainCheckout(root, "repo");
        fs.mkdirSync(path.join(commonDir, "worktrees"));

        assert.deepStrictEqual(getLinkedWorktrees(repo), []);
    });

    test("lists each linked worktree with its path and branch, sorted by path", () => {
        makeMainCheckout(root, "repo");
        const zeta = path.join(root, "worktrees", "repo", "zeta");
        const alpha = path.join(root, "worktrees", "repo", "alpha");
        addLinkedWorktree(commonDir, "b", zeta, { branch: "zeta" });
        addLinkedWorktree(commonDir, "a", alpha, { branch: "feature/alpha" });

        assert.deepStrictEqual(getLinkedWorktrees(repo), [
            { path: alpha, branch: "feature/alpha", missing: false },
            { path: zeta, branch: "zeta", missing: false }
        ]);
    });

    test("marks a record whose folder is gone as missing, with no branch", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "gone");
        addLinkedWorktree(commonDir, "gone", tree, { createTree: false });

        assert.deepStrictEqual(getLinkedWorktrees(repo), [ { path: tree, branch: undefined, missing: true } ]);
    });

    test("marks a folder whose .git file was removed as missing", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        addLinkedWorktree(commonDir, "feat", tree, { branch: "feat" });
        fs.unlinkSync(path.join(tree, ".git"));

        const [ worktree ] = getLinkedWorktrees(repo);
        assert.strictEqual(worktree.missing, true);
        assert.strictEqual(worktree.branch, undefined);
    });

    test("gives no branch for a detached HEAD", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "detached");
        addLinkedWorktree(commonDir, "detached", tree, { detached: true });

        const [ worktree ] = getLinkedWorktrees(repo);
        assert.strictEqual(worktree.missing, false);
        assert.strictEqual(worktree.branch, undefined);
    });

    test("resolves a relative gitdir record against its own folder", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        addLinkedWorktree(commonDir, "feat", tree, { relativeGitdir: true });

        const [ worktree ] = getLinkedWorktrees(repo);
        assert.strictEqual(worktree.path, tree);
    });

    test("drops trailing whitespace and the /.git suffix, as git does", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        const recordDir = addLinkedWorktree(commonDir, "feat", tree);
        fs.writeFileSync(path.join(recordDir, "gitdir"), `${toGitPath(tree)}/.git \n\t\n`);

        const [ worktree ] = getLinkedWorktrees(repo);
        assert.strictEqual(worktree.path, tree);
    });

    test("takes a gitdir with no /.git suffix as the folder itself", () => {
        makeMainCheckout(root, "repo");
        const tree = path.join(root, "worktrees", "repo", "feat");
        const recordDir = addLinkedWorktree(commonDir, "feat", tree);
        fs.writeFileSync(path.join(recordDir, "gitdir"), `${toGitPath(tree)}\n`);

        const [ worktree ] = getLinkedWorktrees(repo);
        assert.strictEqual(worktree.path, tree);
    });

    test("skips a record with no gitdir file", () => {
        makeMainCheckout(root, "repo");
        const recordDir = path.join(commonDir, "worktrees", "orphan");
        fs.mkdirSync(recordDir, { recursive: true });
        fs.writeFileSync(path.join(recordDir, "HEAD"), "ref: refs/heads/orphan\n");

        assert.strictEqual(getLinkedWorktrees(repo).length, 0);
    });

    test("skips a record whose gitdir file is empty or only whitespace", () => {
        makeMainCheckout(root, "repo");
        const recordDir = addLinkedWorktree(commonDir, "feat", path.join(root, "worktrees", "repo", "feat"));

        fs.writeFileSync(path.join(recordDir, "gitdir"), "");
        assert.strictEqual(getLinkedWorktrees(repo).length, 0);

        fs.writeFileSync(path.join(recordDir, "gitdir"), " \n");
        assert.strictEqual(getLinkedWorktrees(repo).length, 0);
    });

    test("ignores entries of the worktrees folder that are not folders", () => {
        makeMainCheckout(root, "repo");
        addLinkedWorktree(commonDir, "feat", path.join(root, "worktrees", "repo", "feat"));
        fs.writeFileSync(path.join(commonDir, "worktrees", "stray"), "");

        assert.strictEqual(getLinkedWorktrees(repo).length, 1);
    });

    test("from a linked worktree, lists the clone's other linked worktrees but not itself", () => {
        makeMainCheckout(root, "repo");
        const treeA = path.join(root, "worktrees", "repo", "a");
        const treeB = path.join(root, "worktrees", "repo", "b");
        addLinkedWorktree(commonDir, "a", treeA, { branch: "a" });
        addLinkedWorktree(commonDir, "b", treeB, { branch: "b" });

        assert.deepStrictEqual(getLinkedWorktrees(treeA).map(worktree => worktree.path), [ treeB ]);
    });

    test("recognises the favorite itself through a symlink", () => {
        makeMainCheckout(root, "repo");
        const treeA = path.join(root, "worktrees", "repo", "a");
        const treeB = path.join(root, "worktrees", "repo", "b");
        addLinkedWorktree(commonDir, "a", treeA, { branch: "a" });
        addLinkedWorktree(commonDir, "b", treeB, { branch: "b" });
        const link = path.join(root, "link-a");
        fs.symlinkSync(treeA, link, "junction");

        assert.deepStrictEqual(getLinkedWorktrees(link).map(worktree => worktree.path), [ treeB ]);
    });

    test("lists the worktrees of a clone whose .git file has no commondir", () => {
        const moduleDir = path.join(root, "modules", "sub");
        fs.mkdirSync(moduleDir, { recursive: true });
        const sub = path.join(root, "sub");
        fs.mkdirSync(sub);
        fs.writeFileSync(path.join(sub, ".git"), `gitdir: ${toGitPath(moduleDir)}\n`);
        addLinkedWorktree(moduleDir, "x", path.join(root, "x"));

        assert.strictEqual(getLinkedWorktrees(sub).length, 1);
    });

    test("agrees with git worktree list --porcelain", function () {
        try {
            execFileSync("git", [ "--version" ]);
        } catch {
            this.skip();
        }

        const globalConfig = path.join(root, "gitconfig");
        fs.writeFileSync(globalConfig, "");
        const env: NodeJS.ProcessEnv = {
            ...Object.fromEntries(Object.entries(process.env).filter(([ name ]) => !name.startsWith("GIT_"))),
            GIT_CONFIG_NOSYSTEM: "1",
            GIT_CONFIG_GLOBAL: globalConfig
        };
        const git = (...args: string[]): string => execFileSync("git",
            [ "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main", ...args ],
            { env, encoding: "utf8" });

        git("init", repo);
        git("-C", repo, "commit", "--allow-empty", "-m", "init");
        git("-C", repo, "worktree", "add", "-b", "feat-a", path.join(root, "worktrees", "repo", "feat-a"));
        git("-C", repo, "worktree", "add", "-b", "feat-b", path.join(root, "elsewhere"));
        fs.rmSync(path.join(root, "elsewhere"), { recursive: true, force: true });

        const stanzas = git("-C", repo, "worktree", "list", "--porcelain")
            .split(/\n\n/)
            .map(stanza => stanza.split("\n").filter(line => line !== ""))
            .filter(lines => lines.length > 0)
            .slice(1);
        const fromGit = new Map(stanzas.map(lines => {
            const worktreePath = path.resolve(lines.find(line => line.startsWith("worktree ")).substring("worktree ".length));
            return [ worktreePath, lines ];
        }));

        const worktrees = getLinkedWorktrees(repo);
        assert.deepStrictEqual(new Set(worktrees.map(worktree => path.resolve(worktree.path))), new Set(fromGit.keys()));
        for (const worktree of worktrees) {
            const lines = fromGit.get(path.resolve(worktree.path));
            if (!worktree.missing) {
                const branchLine = lines.find(line => line.startsWith("branch refs/heads/"));
                assert.strictEqual(worktree.branch, branchLine.substring("branch refs/heads/".length));
            }
            assert.strictEqual(lines.some(line => line.startsWith("prunable")), worktree.missing);
        }
    });
});
