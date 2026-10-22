/*---------------------------------------------------------------------------------------------
*  Copyright (c) Alessandro Fragnani. All rights reserved.
*  Licensed under the GPLv3 License. See License.md in the project root for license information.
*--------------------------------------------------------------------------------------------*/

import * as assert from "assert";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

const NEW_SETTING_KEYS = [
    "projectManager.configuration.worktrees.showInFavorites.description",
    "projectManager.configuration.worktrees.collapseItems.description",
    "projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysExpanded",
    "projectManager.configuration.worktrees.collapseItems.enumDescriptions.alwaysCollapsed",
    "projectManager.configuration.worktrees.collapseItems.enumDescriptions.startExpanded",
    "projectManager.configuration.worktrees.collapseItems.enumDescriptions.startCollapsed",
    "projectManager.configuration.worktrees.openAsWorkspace.description"
];

const NEW_RUNTIME_KEYS = [
    "{0} (missing)",
    "{0} (detached)",
    "The folder of this worktree no longer exists. `git worktree prune` removes its record, unless the worktree is locked.",
    "Could not write a workspace for this worktree, so it opens as a folder: {0}"
];

const LANGS = [ "az", "cs", "fr", "pt-br", "ru", "uk", "zh-cn", "zh-tw" ];

interface MenuEntry {
    command: string;
    group?: string;
    when?: string;
}

interface SettingContribution {
    type: string;
    default: unknown;
    enum?: string[];
}

interface PackageJSON {
    contributes: {
        menus: Record<string, MenuEntry[]>;
        configuration: { properties: Record<string, SettingContribution> }[];
    };
}

suite("Manifest", () => {

    let extension: vscode.Extension<unknown>;
    let packageJSON: PackageJSON;

    function setting(key: string): SettingContribution {
        return packageJSON.contributes.configuration.map(section => section.properties[ key ]).find(property => property);
    }

    suiteSetup(() => {
        extension = vscode.extensions.all.find(e => e.extensionPath === path.resolve(__dirname, "..", "..", "..", ".."));
        packageJSON = extension.packageJSON;
    });

    test("contributes projectManager.worktrees.showInFavorites, on by default", () => {
        const showInFavorites = setting("projectManager.worktrees.showInFavorites");

        assert.strictEqual(showInFavorites.type, "boolean");
        assert.strictEqual(showInFavorites.default, true);
        assert.strictEqual(vscode.workspace.getConfiguration("projectManager").inspect("worktrees.showInFavorites").defaultValue, true);
    });

    test("contributes projectManager.worktrees.collapseItems with the tags' modes, startCollapsed by default", () => {
        const collapseItems = setting("projectManager.worktrees.collapseItems");

        assert.deepStrictEqual(collapseItems.enum, setting("projectManager.tags.collapseItems").enum);
        assert.strictEqual(collapseItems.default, "startCollapsed");
    });

    test("contributes projectManager.worktrees.openAsWorkspace, on by default", () => {
        const openAsWorkspace = setting("projectManager.worktrees.openAsWorkspace");

        assert.strictEqual(openAsWorkspace.type, "boolean");
        assert.strictEqual(openAsWorkspace.default, true);
        assert.strictEqual(vscode.workspace.getConfiguration("projectManager").inspect("worktrees.openAsWorkspace").defaultValue, true);
    });

    test("gives worktree nodes only the open-in-new-window, reveal and add-to-workspace menus", () => {
        const itemMenus = packageJSON.contributes.menus[ "view/item/context" ];
        const worktreeMenus = itemMenus.filter(entry => entry.when?.includes("viewItem == WorktreeNodeKind"));

        assert.strictEqual(worktreeMenus.length, 6);
        assert.deepStrictEqual(new Set(worktreeMenus.map(entry => `${entry.command}|${entry.group}`)), new Set([
            "_projectManager.openInNewWindow|inline",
            "_projectManager.openInNewWindow|navigation",
            "_projectManager.revealInFinder#sideBar|navigation@2",
            "_projectManager.revealInExplorer#sideBar|navigation@2",
            "_projectManager.revealInFileManager#sideBar|navigation@2",
            "projectManager.addToWorkspace#sideBar|workspace"
        ]));
        assert.ok(!itemMenus.some(entry => entry.when?.includes("WorktreeMissingNodeKind")));
        assert.ok(worktreeMenus.every(entry => entry.when.startsWith("view == projectsExplorerFavorites")));
    });

    test("the What's New extension menu names the extension's own id", () => {
        const entry = packageJSON.contributes.menus[ "extension/context" ].find(e => e.command === "_projectManager.whatsNewContextMenu");
        assert.ok(entry);
        assert.ok(entry.when.includes(`extension == ${extension.id}`));
    });

    test("every new setting string is in each package.nls file", () => {
        for (const fileName of [ "package.nls.json", ...LANGS.map(lang => `package.nls.${lang}.json`) ]) {
            assertHasStrings(path.join(extension.extensionPath, fileName), NEW_SETTING_KEYS);
        }
    });

    test("every new runtime string is in each l10n bundle", () => {
        for (const fileName of [ "bundle.l10n.json", ...LANGS.map(lang => `bundle.l10n.${lang}.json`) ]) {
            assertHasStrings(path.join(extension.extensionPath, "l10n", fileName), NEW_RUNTIME_KEYS);
        }
    });
});

function assertHasStrings(file: string, keys: string[]): void {
    const strings: Record<string, unknown> = JSON.parse(fs.readFileSync(file, "utf8"));
    for (const key of keys) {
        const value = strings[ key ];
        assert.ok(typeof value === "string" && value !== "", `${path.basename(file)} lacks "${key}"`);
    }
}
