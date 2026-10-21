/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

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
