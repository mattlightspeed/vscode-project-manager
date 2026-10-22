/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

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
