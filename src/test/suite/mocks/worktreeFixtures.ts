/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import fs = require("fs");
import os = require("os");
import path = require("path");

export interface LinkedWorktreeOptions {
    branch?: string;
    detached?: boolean;
    createTree?: boolean;
    relativeGitdir?: boolean;
}

export function makeTempDir(prefix: string): string {
    return fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), prefix)));
}

export function removeTempDir(dir: string): void {
    fs.rmSync(dir, { recursive: true, force: true });
}

export function makeMainCheckout(parent: string, name: string, branch = "main"): string {
    const repo = path.join(parent, name);
    fs.mkdirSync(path.join(repo, ".git"), { recursive: true });
    fs.writeFileSync(path.join(repo, ".git", "HEAD"), `ref: refs/heads/${branch}\n`);
    return repo;
}

// Git writes paths with "/" on every platform.
export function toGitPath(fsPath: string): string {
    return fsPath.split(path.sep).join("/");
}

export function addLinkedWorktree(commonDir: string, id: string, worktreePath: string, options: LinkedWorktreeOptions = {}): string {
    const recordDir = path.join(commonDir, "worktrees", id);
    fs.mkdirSync(recordDir, { recursive: true });

    const treeGitFile = path.join(worktreePath, ".git");
    const gitdir = options.relativeGitdir ? path.relative(recordDir, treeGitFile) : treeGitFile;
    fs.writeFileSync(path.join(recordDir, "gitdir"), `${toGitPath(gitdir)}\n`);
    fs.writeFileSync(path.join(recordDir, "commondir"), "../..\n");
    const head = options.detached ? "0123456789abcdef0123456789abcdef01234567" : `ref: refs/heads/${options.branch ?? "main"}`;
    fs.writeFileSync(path.join(recordDir, "HEAD"), `${head}\n`);

    if (options.createTree !== false) {
        fs.mkdirSync(worktreePath, { recursive: true });
        fs.writeFileSync(treeGitFile, `gitdir: ${toGitPath(recordDir)}\n`);
    }
    return recordDir;
}

export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export async function waitFor(predicate: () => boolean, timeoutMs = 2000): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (!predicate()) {
        if (Date.now() >= deadline) {
            throw new Error("timed out");
        }
        await sleep(25);
    }
}
