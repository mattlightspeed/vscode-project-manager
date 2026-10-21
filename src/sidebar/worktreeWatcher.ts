/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

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
