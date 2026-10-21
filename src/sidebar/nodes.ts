/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import path = require("path");
import { Command, IconPath, l10n, MarkdownString, ThemeColor, ThemeIcon, TreeItem, TreeItemCollapsibleState, Uri } from "vscode";
import { ThemeIcons } from "vscode-ext-codicons";
import { currentIconThemeHasFolderIcon, getProjectIcon, getIconDetailsFromProjectPath } from "../utils/icons";
import { REMOTE_PREFIX, VIRTUAL_WORKSPACE_PREFIX } from "../utils/remote";
import { LinkedWorktree } from "../utils/worktrees";

export interface ProjectPreview {
    name: string;
    path: string;
    detail?: string;
}

export class ProjectNode extends TreeItem {

    constructor(
        public readonly label: string,
        public readonly collapsibleState: TreeItemCollapsibleState,
        public readonly icon: string | undefined,
        public readonly preview: ProjectPreview,
        public readonly command?: Command
    ) {
        super(label, collapsibleState);

        if (icon) {
            this.iconPath = this.getIconPath(icon, preview.path);
            this.contextValue = "ProjectNodeKind";
        } else {
            this.contextValue = "ConfigNodeKind";
        }

        this.resourceUri = Uri.from({
            scheme: 'projectManager-view',
            path: preview.path
        });

        const tooltipIcon = getIconDetailsFromProjectPath(preview.path);
        this.tooltip = new MarkdownString(
            `${label}\n\n_${preview.path}_\n\n${tooltipIcon.icon} ${tooltipIcon.title}`, true);
        this.description = preview.detail;
    }

    private getIconPath(icon: string, projectPath: string): string | IconPath {
        if (currentIconThemeHasFolderIcon()) {
            return getProjectIcon(icon, projectPath);
        } else {
            // if icon is a string that matches the pattern $(icon-name), returns corresponding ThemeIcon
            if (/^\$\([a-z-]+\)$/.test(icon)) {
                return new ThemeIcon(icon.substring(2, icon.length - 1));
            }
            switch (icon) {
                case "Git":
                case "Mercurial":
                    return ThemeIcons.git_merge;

                case "SVN":
                    return ThemeIcons.zap;

                case "VSCode":
                    return ThemeIcons.file_code;

                case "Any":
                    return ThemeIcons.folder;

                case "favorites":
                    return ThemeIcons.folder;

                case "favorites-workspace":
                    return ThemeIcons.root_folder;

                case "favorites-remote":
                    if (projectPath.startsWith(`${REMOTE_PREFIX}://codespaces`)) {
                        return ThemeIcons.github;
                    }
                    if (projectPath.startsWith(`${REMOTE_PREFIX}://dev-container`)) {
                        return new ThemeIcon('symbol-method', new ThemeColor("icon.foreground"));
                    }
                    if (projectPath.startsWith(`${REMOTE_PREFIX}://ssh`)) {
                        return ThemeIcons.terminal;
                    }
                    if (projectPath.startsWith(`${REMOTE_PREFIX}://wsl`)) {
                        return ThemeIcons.terminal_linux;
                    }
                    if (projectPath.startsWith(`${VIRTUAL_WORKSPACE_PREFIX}://`)) {
                        return ThemeIcons.remote;
                    }
                    return ThemeIcons.remote_explorer;

                default:
                    return getProjectIcon(icon, projectPath);
            }
        }
    }

}


export class TagNode extends TreeItem {

    constructor(
        public readonly label: string,
        public readonly collapsibleState: TreeItemCollapsibleState,
    ) {
        super(label, collapsibleState);
        this.iconPath = ThemeIcons.tag;
    }
}

export class NoTagNode extends TagNode {

    constructor(
        label: string,
        public readonly collapsibleState: TreeItemCollapsibleState,
    ) {
        super("", collapsibleState);
        this.description = label;
    }
}

export class WorktreeNode extends ProjectNode {

    public readonly worktree: LinkedWorktree;

    constructor(worktree: LinkedWorktree, projectPath: string, profile: string | undefined) {
        const label = worktree.branch ?? path.basename(worktree.path);
        super(label, TreeItemCollapsibleState.None, undefined, {
            name: label,
            path: worktree.path,
            detail: describeWorktree(worktree, projectPath)
        }, worktree.missing ? undefined : {
            command: "_projectManager.open",
            title: "",
            arguments: [ worktree.path, label, profile ]
        });

        this.worktree = worktree;
        this.iconPath = worktree.missing ? ThemeIcons.warning : ThemeIcons.git_branch;
        this.contextValue = worktree.missing ? "WorktreeMissingNodeKind" : "WorktreeNodeKind";
        if (worktree.missing) {
            const explanation = l10n.t("The folder of this worktree no longer exists. `git worktree prune` removes its record, unless the worktree is locked.");
            this.tooltip = new MarkdownString(`${explanation}\n\n_${worktree.path}_`);
        }
    }
}

function describeWorktree(worktree: LinkedWorktree, projectPath: string): string {
    const relativePath = path.relative(path.dirname(projectPath), worktree.path);
    const climbsOut = relativePath === ".." || relativePath.startsWith(`..${path.sep}`);
    const location = climbsOut ? worktree.path : relativePath;
    if (worktree.missing) {
        return l10n.t("{0} (missing)", location);
    }
    if (!worktree.branch) {
        return l10n.t("{0} (detached)", location);
    }
    return location;
}
