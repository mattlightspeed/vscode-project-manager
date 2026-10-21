/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import { EventEmitter } from "events";
import fs = require("fs");
import path = require("path");
import { WorktreeWatcher } from "../../sidebar/worktreeWatcher";
import { makeTempDir, removeTempDir, sleep, waitFor } from "./mocks/worktreeFixtures";

type WatchListener = (event: string, filename: string | null) => void;

interface WatcherInternals {
    watched: Map<string, { gitDirWatcher: fs.FSWatcher; worktreesWatcher: fs.FSWatcher | undefined }>;
    rewatchWorktrees(commonDir: string): void;
}

suite("WorktreeWatcher", function () {
    this.timeout(5000);

    let tmp: string;
    let commonDir: string;
    let calls: number;
    let watcher: WorktreeWatcher;

    function makeGitDir(name: string): string {
        const gitDir = path.join(tmp, name, ".git");
        fs.mkdirSync(gitDir, { recursive: true });
        return gitDir;
    }

    async function assertNoCall(): Promise<void> {
        const before = calls;
        await sleep(400);
        assert.strictEqual(calls, before);
    }

    setup(() => {
        tmp = makeTempDir("worktree-watcher-");
        commonDir = makeGitDir("repo");
        calls = 0;
        watcher = new WorktreeWatcher(() => calls++, 50);
    });

    teardown(() => {
        watcher.dispose();
        removeTempDir(tmp);
    });

    test("calls back once, after the delay, when worktree records are added", async () => {
        fs.mkdirSync(path.join(commonDir, "worktrees"));
        watcher.watch([ commonDir ]);

        fs.mkdirSync(path.join(commonDir, "worktrees", "a"));
        fs.mkdirSync(path.join(commonDir, "worktrees", "b"));

        await waitFor(() => calls === 1);
        await sleep(300);
        assert.strictEqual(calls, 1);
    });

    test("calls back when the worktrees folder is created, and keeps watching it", async () => {
        watcher.watch([ commonDir ]);

        fs.mkdirSync(path.join(commonDir, "worktrees"));
        await waitFor(() => calls === 1);

        fs.mkdirSync(path.join(commonDir, "worktrees", "a"));
        await waitFor(() => calls === 2);
    });

    test("calls back when the worktrees folder is removed, and again when it returns", async () => {
        fs.mkdirSync(path.join(commonDir, "worktrees", "a"), { recursive: true });
        watcher.watch([ commonDir ]);

        fs.rmSync(path.join(commonDir, "worktrees"), { recursive: true, force: true });
        await waitFor(() => calls >= 1);

        const callsAfterRemoval = calls;
        fs.mkdirSync(path.join(commonDir, "worktrees"));
        fs.mkdirSync(path.join(commonDir, "worktrees", "b"));
        await waitFor(() => calls > callsAfterRemoval);
    });

    test("ignores other changes in the git folder", async () => {
        watcher.watch([ commonDir ]);

        fs.writeFileSync(path.join(commonDir, "HEAD"), "ref: refs/heads/main\n");
        fs.writeFileSync(path.join(commonDir, "index.lock"), "");
        fs.mkdirSync(path.join(commonDir, "logs"));
        fs.writeFileSync(path.join(commonDir, "logs", "x"), "");

        await assertNoCall();
    });

    test("stops watching a folder dropped from the list", async () => {
        const first = makeGitDir("a");
        const second = makeGitDir("b");
        watcher.watch([ first, second ]);
        watcher.watch([ second ]);

        fs.mkdirSync(path.join(first, "worktrees"));
        await assertNoCall();

        fs.mkdirSync(path.join(second, "worktrees"));
        await waitFor(() => calls === 1);
    });

    test("watching the same folder twice calls back once per change", async () => {
        watcher.watch([ commonDir ]);
        watcher.watch([ commonDir ]);

        fs.mkdirSync(path.join(commonDir, "worktrees"));
        await sleep(400);
        assert.strictEqual(calls, 1);
    });

    test("skips a folder that does not exist", () => {
        assert.doesNotThrow(() => watcher.watch([ path.join(tmp, "nope", ".git") ]));
    });

    test("dispose stops every watcher and a pending call", async () => {
        watcher.watch([ commonDir ]);
        fs.mkdirSync(path.join(commonDir, "worktrees"));
        watcher.dispose();
        await assertNoCall();

        fs.mkdirSync(path.join(commonDir, "worktrees", "a"));
        await assertNoCall();
    });

    test("an error from a git-folder watcher stops watching that folder", async () => {
        watcher.watch([ commonDir ]);
        const internals = watcher as unknown as WatcherInternals;

        internals.watched.get(commonDir).gitDirWatcher.emit("error", new Error("x"));

        assert.strictEqual(internals.watched.has(commonDir), false);
        fs.mkdirSync(path.join(commonDir, "worktrees"));
        await assertNoCall();
    });

    test("an error from a worktrees-folder watcher closes it quietly", async () => {
        fs.mkdirSync(path.join(commonDir, "worktrees"));
        watcher.watch([ commonDir ]);
        const internals = watcher as unknown as WatcherInternals;

        assert.doesNotThrow(() => internals.watched.get(commonDir).worktreesWatcher.emit("error", new Error("x")));

        fs.rmSync(path.join(commonDir, "worktrees"), { recursive: true, force: true });
        await waitFor(() => calls >= 1);
    });

    test("rewatching a folder that is no longer watched does nothing", async () => {
        const internals = watcher as unknown as WatcherInternals;

        assert.doesNotThrow(() => internals.rewatchWorktrees(path.join(tmp, "nope", ".git")));
        await assertNoCall();
    });

    test("an event without a file name refreshes", async () => {
        const listeners = new Map<string, WatchListener>();
        const watchedPaths: string[] = [];
        const fakeWatch = (watchedPath: string, listener: WatchListener) => {
            watchedPaths.push(watchedPath);
            listeners.set(watchedPath, listener);
            return Object.assign(new EventEmitter(), { close: () => undefined });
        };
        const fsModule = fs as unknown as { watch: unknown };
        const realWatch = fsModule.watch;
        fsModule.watch = fakeWatch;
        try {
            watcher.watch([ commonDir ]);

            listeners.get(commonDir)("rename", null);

            await waitFor(() => calls === 1);
            const worktreesDir = path.join(commonDir, "worktrees");
            assert.strictEqual(watchedPaths.filter(watchedPath => watchedPath === worktreesDir).length, 2);
        } finally {
            fsModule.watch = realWatch;
        }
    });
});
