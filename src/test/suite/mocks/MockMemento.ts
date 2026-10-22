import * as path from "path";
import * as vscode from "vscode";

export class MockMemento implements vscode.Memento {

    keys(): readonly string[] {
        throw new Error("Method not implemented.");
    }

    private store = new Map<string, any>();

    get<T>(key: string, defaultValue?: T): T | undefined {
        return this.store.has(key) ? this.store.get(key) : defaultValue;
    }

    update(key: string, value: any): Thenable<void> {
        if (value === undefined) {
            this.store.delete(key);
        } else {
            this.store.set(key, value);
        }
        return Promise.resolve();
    }
}

export function createMockContext(globalStoragePath?: string): vscode.ExtensionContext {
    const globalState = new MockMemento();
    return {
        globalState,
        extensionUri: vscode.Uri.file(path.resolve(__dirname, "..", "..", "..", "..", "..")),
        globalStorageUri: globalStoragePath === undefined ? undefined : vscode.Uri.file(globalStoragePath)
    } as unknown as vscode.ExtensionContext;
}

