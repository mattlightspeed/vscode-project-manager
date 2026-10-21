/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import path = require("path");
import * as vscode from "vscode";
import { Container } from "../core/container";
import { ProjectStorage } from "../storage/storage";
import { PathUtils } from "../utils/path";
import { isRemotePath } from "../utils/remote";
import { sortProjects } from "../utils/sorter";
import { getGitBranch } from "../utils/git";
import { getGitCommonDir, getLinkedWorktrees } from "../utils/worktrees";
import { NO_TAGS_DEFINED } from "./constants";
import { NoTagNode, ProjectNode, TagNode, WorktreeNode } from "./nodes";
import { WorktreeWatcher } from "./worktreeWatcher";

interface ProjectInQuickPick {
    label: string;
    description: string;
    profile: string;
}

// eslint-disable-next-line @typescript-eslint/no-empty-interface
interface ProjectInQuickPickList extends Array<ProjectInQuickPick> { }

export class StorageProvider implements vscode.TreeDataProvider<ProjectNode | TagNode>, vscode.Disposable {

    public readonly onDidChangeTreeData: vscode.Event<ProjectNode | TagNode | void>;

    private projectSource: ProjectStorage;
    private internalOnDidChangeTreeData: vscode.EventEmitter<ProjectNode | TagNode | void> = new vscode.EventEmitter<ProjectNode | void>();
    private static readonly TAGS_EXPANSION_STATE_KEY = "projectsExplorerFavorites.tagsExpansionState";
    private static readonly WORKTREES_EXPANSION_STATE_KEY = "projectsExplorerFavorites.worktreesExpansionState";
    private readonly worktreeWatcher = new WorktreeWatcher(() => this.refresh());

    constructor(projectSource: ProjectStorage) {
        this.projectSource = projectSource;
        this.onDidChangeTreeData = this.internalOnDidChangeTreeData.event;
    }

    private static getExpansionState(stateKey: string): Record<string, boolean> {
        return Container.context.globalState.get<Record<string, boolean>>(stateKey, {});
    }

    private static getCollapsibleState(stateKey: string, id: string, behavior: string): vscode.TreeItemCollapsibleState {
        switch (behavior) {
            case "alwaysExpanded":
                return vscode.TreeItemCollapsibleState.Expanded;
            case "alwaysCollapsed":
                return vscode.TreeItemCollapsibleState.Collapsed;
            case "startExpanded":
            case "startCollapsed": {
                const expansionState = StorageProvider.getExpansionState(stateKey);
                const isExpanded = expansionState[ id ];
                if (isExpanded === undefined) {
                    return behavior === "startExpanded" ? vscode.TreeItemCollapsibleState.Expanded : vscode.TreeItemCollapsibleState.Collapsed;
                }
                return isExpanded ? vscode.TreeItemCollapsibleState.Expanded : vscode.TreeItemCollapsibleState.Collapsed;
            }
            default:
                return vscode.TreeItemCollapsibleState.Expanded;
        }
    }

    private static async setExpanded(stateKey: string, id: string, expanded: boolean): Promise<void> {
        const expansionState = StorageProvider.getExpansionState(stateKey);
        const newExpansionState = { ...expansionState, [ id ]: expanded };
        await Container.context.globalState.update(stateKey, newExpansionState);
    }

    public static async resetTagExpansionState(): Promise<void> {
        await Container.context.globalState.update(StorageProvider.TAGS_EXPANSION_STATE_KEY, {});
    }

    public static getTagCollapsibleState(tagId: string, behavior: string): vscode.TreeItemCollapsibleState {
        return StorageProvider.getCollapsibleState(StorageProvider.TAGS_EXPANSION_STATE_KEY, tagId, behavior);
    }

    public static async setTagExpanded(tagId: string, expanded: boolean): Promise<void> {
        await StorageProvider.setExpanded(StorageProvider.TAGS_EXPANSION_STATE_KEY, tagId, expanded);
    }

    public static showsWorktrees(): boolean {
        return vscode.workspace.getConfiguration("projectManager").get<boolean>("worktrees.showInFavorites", true);
    }

    public static refreshesOnWindowFocus(): boolean {
        const showGitBranch = vscode.workspace.getConfiguration("projectManager").get<string>("git.showBranchName", "never");
        return showGitBranch === "onlyInSideBar" || showGitBranch === "always" || StorageProvider.showsWorktrees();
    }

    public static async resetWorktreesExpansionState(): Promise<void> {
        await Container.context.globalState.update(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, {});
    }

    public static getWorktreesCollapsibleState(projectPath: string): vscode.TreeItemCollapsibleState {
        if (!StorageProvider.showsWorktrees() || isRemotePath(projectPath) || getLinkedWorktrees(projectPath).length === 0) {
            return vscode.TreeItemCollapsibleState.None;
        }
        const behavior = vscode.workspace.getConfiguration("projectManager").get<string>("worktrees.collapseItems", "startCollapsed");
        return StorageProvider.getCollapsibleState(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, projectPath, behavior);
    }

    public static async rememberWorktreesExpansion(projectPath: string, expanded: boolean): Promise<void> {
        const behavior = vscode.workspace.getConfiguration("projectManager").get<string>("worktrees.collapseItems", "startCollapsed");
        if (behavior === "startExpanded" || behavior === "startCollapsed") {
            await StorageProvider.setExpanded(StorageProvider.WORKTREES_EXPANSION_STATE_KEY, projectPath, expanded);
        }
    }

    public refresh(): void {
        this.internalOnDidChangeTreeData.fire();
    }

    public getTreeItem(element: ProjectNode | TagNode): vscode.TreeItem {
        return element;
    }

    public getChildren(element?: ProjectNode | TagNode): Thenable<ProjectNode[] | TagNode[]> {

        if (element instanceof ProjectNode) {
            return Promise.resolve(this.getWorktreeNodes(element));
        }

        // loop !!!
        return new Promise(resolve => {

            if (element) {

                const nodes: ProjectNode[] = [];

                let projectsMapped = <ProjectInQuickPickList>this.projectSource.getProjectsByTag(element.label);

                if (projectsMapped.length === 0) {
                    resolve(nodes);
                }

                projectsMapped = sortProjects(projectsMapped);

                const showGitBranch = vscode.workspace.getConfiguration("projectManager").get<string>("git.showBranchName", "never");

                for (let index = 0; index < projectsMapped.length; index++) {
                    const prj: ProjectInQuickPick = projectsMapped[ index ];

                    let iconFavorites = "favorites";
                    if (path.extname(prj.description) === ".code-workspace") {
                        iconFavorites = "favorites-workspace";
                    } else if (isRemotePath(prj.description)) {
                        iconFavorites = "favorites-remote";
                    }

                    const projectPath = PathUtils.expandHomePath(prj.description);
                    const gitBranch = (showGitBranch === "always" || showGitBranch === "onlyInSideBar") ? getGitBranch(projectPath) : undefined;

                    nodes.push(new ProjectNode(prj.label, StorageProvider.getWorktreesCollapsibleState(projectPath),
                        iconFavorites, {
                            name: prj.label,
                            path: projectPath,
                            detail: gitBranch
                        }, {
                            command: "_projectManager.open",
                            title: "",
                            arguments: [ projectPath, prj.label, prj.profile ],
                        }));
                }

                resolve(nodes);

            } else { // ROOT

                this.watchFavoritesWorktrees();

                // no project saved yet, returns [] `empty`...
                if (this.projectSource.length() === 0) {
                    return resolve([]);
                }

                // choose the view
                const viewAsList = Container.context.globalState.get<boolean>("viewAsList", true);

                // viewAsTags - must have at least one tag otherwise, use `viewAsList`
                if (!viewAsList) {
                    let nodes: TagNode[] = [];

                    const tagsCollapseBehavior = vscode.workspace.getConfiguration("projectManager").get<string>("tags.collapseItems", "startExpanded");
                    const tags = this.projectSource.getAvailableTags().sort();
                    for (const tag of tags) {
                        nodes.push(new TagNode(tag, StorageProvider.getTagCollapsibleState(tag, tagsCollapseBehavior)));
                    }

                    // has any, then OK
                    if (nodes.length > 0) {
                        if (this.projectSource.getProjectsByTag('').length !== 0) {
                            nodes.push(new NoTagNode(NO_TAGS_DEFINED, StorageProvider.getTagCollapsibleState(NO_TAGS_DEFINED, tagsCollapseBehavior)));
                        }

                        // should filter ?
                        const filterByTags = Container.context.globalState.get<string[]>("filterByTags", []);
                        if (filterByTags.length > 0) {
                            nodes = nodes.filter(node => filterByTags.includes(node.label)
                                || (filterByTags.includes(NO_TAGS_DEFINED) && node.label === ""));
                        }

                        resolve(nodes);
                        return;
                    }
                }

                // viewAsList OR no Tags
                // raw list
                const nodes: ProjectNode[] = [];

                let projectsMapped: ProjectInQuickPickList;

                const filterByTags = Container.context.globalState.get<string[]>("filterByTags", []);
                if (filterByTags.length > 0) {
                    projectsMapped = <ProjectInQuickPickList>this.projectSource.getProjectsByTags(filterByTags);
                } else {
                    projectsMapped = <ProjectInQuickPickList>this.projectSource.map();
                }

                projectsMapped = sortProjects(projectsMapped);

                const showGitBranch = vscode.workspace.getConfiguration("projectManager").get<string>("git.showBranchName", "never");

                for (let index = 0; index < projectsMapped.length; index++) {
                    const prj: ProjectInQuickPick = projectsMapped[ index ];

                    let iconFavorites = "favorites";
                    if (path.extname(prj.description) === ".code-workspace") {
                        iconFavorites = "favorites-workspace";
                    } else if (isRemotePath(prj.description)) {
                        iconFavorites = "favorites-remote";
                    }

                    const projectPath = PathUtils.expandHomePath(prj.description);
                    const gitBranch = (showGitBranch === "always" || showGitBranch === "onlyInSideBar") ? getGitBranch(projectPath) : undefined;

                    nodes.push(new ProjectNode(prj.label, StorageProvider.getWorktreesCollapsibleState(projectPath),
                        iconFavorites, {
                            name: prj.label,
                            path: projectPath,
                            detail: gitBranch
                        },
                        {
                            command: "_projectManager.open",
                            title: "",
                            arguments: [ projectPath, prj.label, prj.profile ],
                        }));
                }

                resolve(nodes);
            }
        });
    }

    private getWorktreeNodes(element: ProjectNode): WorktreeNode[] {
        const projectPath = element.preview.path;
        if (element instanceof WorktreeNode || !StorageProvider.showsWorktrees() || isRemotePath(projectPath)) {
            return [];
        }
        const profile = element.command.arguments[ 2 ];
        return getLinkedWorktrees(projectPath)
            .map(worktree => new WorktreeNode(worktree, projectPath, profile))
            .sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base", numeric: true })
                || a.preview.path.localeCompare(b.preview.path));
    }

    private watchFavoritesWorktrees(): void {
        const commonDirs: string[] = [];
        if (StorageProvider.showsWorktrees()) {
            for (const project of <ProjectInQuickPickList>this.projectSource.map()) {
                const projectPath = PathUtils.expandHomePath(project.description);
                const commonDir = isRemotePath(projectPath) ? undefined : getGitCommonDir(projectPath);
                if (commonDir) {
                    commonDirs.push(commonDir);
                }
            }
        }
        this.worktreeWatcher.watch(commonDirs);
    }

    public dispose(): void {
        this.worktreeWatcher.dispose();
    }

}
