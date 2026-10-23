"""Keep the plan name register, check that plans refer to each other by name,
and find the tree for another repo's branch.

A plan's name is its filename without `.md` and without any trailing run of
`-s`/`-e`/`-i` lifecycle segments. plans/tools/names.md, the name register,
lists every name this repo's plans have had; a name is never removed or
reused. A plan refers to another as [[name]], [[name#section]], [[name|label]]
or [[repo:name]], never by path, so a rename or a move breaks no reference.

`--check` fails while a Markdown link or a backticked path points at a plan,
a link to anything else is dead and not listed in plans/tools/dead-links.txt,
an entry there matches nothing, a [[name]] is not registered, a plan's name is
not registered, the register is malformed or sits at its old path,
plans/names.md, two plans share a name, or plans/tools/branch-pairs.txt is
malformed.
`--convert` rewrites path links and paths to plans as name references.

A reference into a sibling repo is reported but never fails the check. It is
checked against the branch of the sibling that this repo's branch writes for:
the one plans/tools/branch-pairs.txt pairs with it, a line of
`<branch here> <repo> <branch there>`, or, from this repo's trunk (main, or
master where there is no main), the sibling's trunk. That branch is read from
the worktree that has it checked out, or from git where none has. Where no
branch is chosen, the sibling's checked-out tree answers. A linked worktree is
its main repo, named by its main checkout's folder, and is never a sibling.
Siblings are the repos beside the main checkout, so a tree run from anywhere
finds the same ones, and a link that leaves the tree is followed from the main
checkout's place.
plans/followups/ is never read.

`--tree REPO` prints the working tree of REPO that has that branch, or the one
`--branch` names, checked out, for writing plans and register entries there.
REPO is a path, or the name of a repo beside this tree's main checkout. A tree
outside the worktree layout is printed with a note. Where none has the branch,
it names the worktree it would create at the branch's place in the layout,
`<parent of the main checkout>/worktrees/<its folder>/<slug>`, and exits 3;
`--create` makes it and any folder of the layout it lacks, each with the mode
and group of the folder holding it, runs no hook, marks it plan-only in its
git directory, and prints the `safe.directory` line another account needs
before using it. `--worktrees REPO...` lists plan-only worktrees, marking those
outside the layout, with the command for each that can go. Neither fetches,
commits or removes anything.

The same file is vendored unchanged into every repo with a plans/ tree, so it
holds no per-repo configuration.

    python3 plans/tools/plan_links.py --check [--only=stems|names|allowlist|links|refs|pairs]
    python3 plans/tools/plan_links.py --convert
    python3 plans/tools/plan_links.py --register
    python3 plans/tools/plan_links.py --claim NAME...
    python3 plans/tools/plan_links.py --resolve REF...
    python3 plans/tools/plan_links.py --tree REPO [--branch=BRANCH] [--create]
    python3 plans/tools/plan_links.py --worktrees REPO...
    python3 plans/tools/plan_links.py --report [--emit-allowlist]
    python3 plans/tools/plan_links.py --selftest
"""

import argparse
import contextlib
import datetime
import functools
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

LINK = re.compile(r'\[([^\]]*)\]\(([^)\s]+?\.md)(#[^)\s]*)?\)')
FENCE_MARKERS = ('```', '~~~')
REPO_RENAMES = {
    'sonata-passwave-app': 'passwave-app',
    'sonata-passwave-web': 'passwave-web',
    'sonata-passwave-api': 'passwave-api',
    'sonata-passwave-core': 'passwave-core',
}
ALLOWLIST = Path('plans') / 'tools' / 'dead-links.txt'
NAMES = Path('plans') / 'tools' / 'names.md'
OLD_NAMES = Path('plans') / 'names.md'
REGISTER_PARTS = (NAMES.parts[1:], OLD_NAMES.parts[1:])
NAME =r'[A-Za-z0-9][\w.-]*'
REFERENCE = re.compile(rf'\[\[(?:({NAME}):)?({NAME})(#[^\]|\\\s]+)?(?:\\?\|([^\]\n]+))?\]\]')
CODE_SPAN = re.compile(r'(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)')
LINES = r':\d+(?:[-–,]\d+)*'
PATH_CITE = re.compile(rf'(/?(?:[\w.-]+/)*[\w.-]+\.md)({LINES})?')
LABEL_CITE = re.compile(rf'((?:[\w.-]+/)*[\w.-]+)({LINES})?(\s+§.*)?')
USAGE = ('plan_links.py (--check [--only=stems|names|allowlist|links|refs|pairs] | --convert | --register'
         ' | --claim NAME... | --resolve REF... | --tree REPO [--branch=BRANCH] [--create] | --worktrees REPO...'
         ' | --report [--emit-allowlist] | --selftest)')
NAMES_PREAMBLE = (
    '# Plan names\n'
    '\n'
    'The name register: every name a plan in this repo has had. A name is never\n'
    'removed and never reused, and a plan refers to another by name alone, as\n'
    '`[[name]]`. Claim a new plan\'s name before creating its file:\n'
    '\n'
    '    python3 plans/tools/plan_links.py --claim <name>\n'
    '\n'
)

OK = 'ok'
DEAD_LISTED = 'dead_listed'
DEAD_UNLISTED = 'dead_unlisted'
PLAN_PATH = 'plan_path'
CROSS_REPO_PATH = 'cross_repo_path'
LINK_VERDICTS = (OK, DEAD_LISTED, DEAD_UNLISTED, PLAN_PATH, CROSS_REPO_PATH)
GATING = (DEAD_UNLISTED, PLAN_PATH, CROSS_REPO_PATH)

KNOWN = 'known'
UNKNOWN_NAME = 'unknown_name'
CROSS_REPO_REF = 'cross_repo_ref'
CROSS_REPO_REF_UNRESOLVED = 'cross_repo_ref_unresolved'
REF_VERDICTS = (KNOWN, UNKNOWN_NAME, CROSS_REPO_REF, CROSS_REPO_REF_UNRESOLVED)

PAIRS = Path('plans') / 'tools' / 'branch-pairs.txt'
MARKER = 'plan-only'
WOULD_CREATE = 3
WORKTREES = 'worktrees'
CHECK_CLASSES = ('stems', 'names', 'allowlist', 'links', 'refs', 'pairs')
DEAD_GROUPS = (
    'Claude-memory paths',
    'Paths in this repo that no longer exist',
    'Non-plan paths in other repos',
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)


@functools.lru_cache(maxsize=None)
def main_worktree(root: Path) -> Path:
    # Read from the .git file rather than asked of git, so it answers for any user and in fixtures.
    try:
        dot_git = root / '.git'
        if not dot_git.is_file():
            return root
        text = _read(dot_git)
        if not text.startswith('gitdir: '):
            return root
        gitdir = Path(text[len('gitdir: '):].strip())
        if not gitdir.is_absolute():
            gitdir = root / gitdir
        if gitdir.parent.name != 'worktrees':
            return root
        common = Path(os.path.normpath(gitdir / _read(gitdir / 'commondir').strip()))
    except OSError:
        return root
    return common.parent if common.name == '.git' else root


def repo_name(root: Path) -> str:
    return main_worktree(root).name


def is_linked_worktree(path: Path) -> bool:
    return main_worktree(path) != path


def sibling_dir(root: Path) -> Path:
    return main_worktree(root).parent


def folder_repo(folder: Path) -> str:
    if is_linked_worktree(folder):
        return repo_name(folder)
    if not folder.exists() and folder.parent.parent.name == WORKTREES:
        return folder.parent.name
    return folder.name


def folder_slug(branch: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', branch.lower()).strip('-')


def layout_path(main: Path, branch: str) -> Path | None:
    slug = folder_slug(branch)
    return main.parent / WORKTREES / main.name / slug if slug else None


def current_branch(repo: Path) -> str | None:
    result = _git(repo, 'branch', '--show-current')
    return (result.stdout.strip() or None) if result.returncode == 0 else None


def _verifies(repo: Path, ref: str) -> bool:
    return _git(repo, 'rev-parse', '--verify', '--quiet', ref).returncode == 0


def trunk(repo: Path) -> str | None:
    return next((name for name in ('main', 'master') if has_branch(repo, name)), None)


def has_branch(repo: Path, branch: str) -> bool:
    return _verifies(repo, f'refs/heads/{branch}')


def remote_branches(repo: Path, branch: str) -> list[str]:
    return [f'{remote}/{branch}' for remote in _git(repo, 'remote').stdout.split()
            if _verifies(repo, f'refs/remotes/{remote}/{branch}')]


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str | None      # None: detached HEAD
    admin: Path | None      # the worktree's own git directory; None for the main worktree
    prunable: bool


def outside_layout(main: Path, worktree: Worktree) -> bool:
    here = os.path.realpath(worktree.path)
    if here == os.path.realpath(main):
        return False
    expected = layout_path(main, worktree.branch) if worktree.branch else None
    if expected is not None:
        return here != os.path.realpath(expected)
    # With no path of its own, a tree may sit anywhere directly in the clone's folder of the layout.
    return os.path.dirname(here) != os.path.realpath(main.parent / WORKTREES / main.name)


def _is_toplevel(repo: Path) -> bool:
    # git -C answers for an enclosing repo too, so a subdirectory or a fixture inside a repo must be told apart.
    result = _git(repo, 'rev-parse', '--show-toplevel')
    return result.returncode == 0 and os.path.realpath(result.stdout.strip()) == os.path.realpath(repo)


def worktrees(repo: Path) -> list[Worktree] | None:
    if not _is_toplevel(repo):
        return None
    listed = _git(repo, 'worktree', 'list', '--porcelain', '-z')
    if listed.returncode != 0:
        return None
    admins: dict[str, Path] = {}
    common = _git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if common.returncode == 0:
        try:
            for admin in sorted((Path(common.stdout.strip()) / 'worktrees').iterdir()):
                with contextlib.suppress(OSError):
                    admins.setdefault(os.path.realpath(_read(admin / 'gitdir').strip()), admin)
        except OSError:
            pass

    found: list[Worktree] = []
    for record in (record for record in listed.stdout.split('\0\0') if record):
        fields = dict(field.partition(' ')[::2] for field in record.split('\0'))
        if not found and 'bare' in fields:
            return None
        path = Path(fields['worktree'])
        branch = fields['branch'].removeprefix('refs/heads/') if 'branch' in fields else None
        admin = admins.get(os.path.realpath(path / '.git')) if found else None
        found.append(Worktree(path, branch, admin, 'prunable' in fields))
    return found


def read_pairs(root: Path) -> tuple[dict[tuple[str, str], str], list[str]]:
    path = root / PAIRS
    if not path.is_file():
        return {}, []
    pairs: dict[tuple[str, str], str] = {}
    problems: list[str] = []
    for number, line in enumerate(_read(path).split('\n'), start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        fields = line.split()
        if len(fields) != 3:
            problems.append(f'line {number}: expected 3 fields, got {len(fields)}')
        elif not re.fullmatch(NAME, fields[1]):
            problems.append(f'line {number}: not a repo name: {fields[1]}')
        elif fields[1] == repo_name(root):
            problems.append(f'line {number}: {fields[1]} is this repo')
        elif (fields[0], fields[1]) in pairs:
            problems.append(f'line {number}: duplicate: {fields[0]} {fields[1]}')
        else:
            pairs[(fields[0], fields[1])] = fields[2]
    return pairs, problems


def chosen_branch(here: Path, other: Path) -> tuple[str | None, str]:
    name = REPO_RENAMES.get(other.name, other.name)
    if not _is_toplevel(here):
        return None, (f'{here} is not the root of a git work tree: run from the root of the repo you work in, '
                      'or name the branch with --branch')
    current = current_branch(here)
    if current is None:
        return None, f'{here} is not on a branch: name the branch with --branch'
    pairs, problems = read_pairs(here)
    if problems:
        return None, f'{PAIRS.as_posix()}: {problems[0]}; fix it first'
    if (current, name) in pairs:
        return pairs[(current, name)], ''
    if current == trunk(here):
        other_trunk = trunk(other)
        if other_trunk is not None:
            return other_trunk, ''
        return None, (f'{name} has neither main nor master: ask which branch, and add the line '
                      f'"{current} {name} <branch>" to {PAIRS.as_posix()}')
    return None, (f'{repo_name(here)} is on {current}, which pairs with no branch of {name} in {PAIRS.as_posix()}: '
                  f'ask which branch, and add the line "{current} {name} <branch>"')


def stem(name: str) -> str:
    if name.endswith('.md'):
        name = name[:-len('.md')]
    while name.endswith(('-s', '-e', '-i')):
        name = name[:-len('-e')]
    return name


def plan_files(plans: Path) -> list[Path]:
    return sorted(
        path for path in plans.rglob('*.md')
        if path.is_file()
        and not any(part.startswith('.') for part in path.relative_to(plans).parts)
    )


def index_by_stem(files) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in files:
        if path.name != 'README.md':
            index.setdefault(stem(path.name), []).append(path)
    return index


def sibling_index(root: Path) -> dict[tuple[str, str], list[Path]]:
    index: dict[tuple[str, str], list[Path]] = {}
    for repo in sorted(sibling_dir(root).iterdir()):
        try:
            if repo.name == repo_name(root) or is_linked_worktree(repo) or not (repo / 'plans').is_dir():
                continue
            files = plan_files(repo / 'plans')
        except OSError:
            continue
        for name, paths in index_by_stem(files).items():
            index[(repo.name, name)] = paths
    return index


def read_allowlist(root: Path) -> list[str]:
    path = root / ALLOWLIST
    if not path.is_file():
        return []
    entries = (line.strip() for line in _read(path).split('\n'))
    return list(dict.fromkeys(e for e in entries if e and not e.startswith('#')))


def link_sources(plans: Path) -> list[Path]:
    return [
        path for path in plan_files(plans)
        if path.relative_to(plans).parts[0] != 'followups' and path.relative_to(plans).parts not in REGISTER_PARTS
    ]


def _is_named_plan(parts: tuple[str, ...]) -> bool:
    return (parts[-1].endswith('.md') and parts[-1] != 'README.md'
            and not any(part.startswith('.') for part in parts)
            and parts[0] != 'followups' and parts not in REGISTER_PARTS)


def named_plan_files(plans: Path) -> list[Path]:
    return [path for path in plan_files(plans) if _is_named_plan(path.relative_to(plans).parts)]


def branch_plans(repo: Path, branch: str) -> tuple[list[str], str | None] | None:
    listed = _git(repo, 'ls-tree', '-r', '-z', '--name-only', f'refs/heads/{branch}', '--', 'plans')
    if listed.returncode != 0:
        return None
    paths = [path for path in listed.stdout.split('\0') if path]
    plans = [path for path in paths if path.startswith('plans/') and _is_named_plan(tuple(path.split('/')[1:]))]
    names_text = None
    if NAMES.as_posix() in paths:
        shown = _git(repo, 'show', f'refs/heads/{branch}:{NAMES.as_posix()}')
        if shown.returncode == 0:
            names_text = shown.stdout
    return plans, names_text


def branch_names(repo: Path, branch: str) -> set[str] | None:
    found = branch_plans(repo, branch)
    if found is None:
        return None
    paths, text = found
    if text is not None:
        return set(parse_names(text)[0])
    return {stem(path.rsplit('/', 1)[-1]) for path in paths}


def is_name(text: str) -> bool:
    return bool(re.fullmatch(NAME, text)) and not text.endswith('.md') and stem(text + '.md') == text


def read_names(root: Path) -> tuple[list[str] | None, list[str]]:
    problems: list[str] = []
    if (root / OLD_NAMES).is_file():
        problems.append(f"{OLD_NAMES.as_posix()} is the name register's old path: "
                        f'git mv {OLD_NAMES.as_posix()} {NAMES.as_posix()}')
    path = root / NAMES
    if not path.is_file():
        return None, problems
    names, found = parse_names(_read(path))
    return names, problems + found


def parse_names(text: str) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    lines = text.split('\n')
    if lines[-1] == '':
        lines.pop()
    first_entry = next((i for i, line in enumerate(lines) if line.startswith('-')), len(lines))

    names: list[str] = []
    for number, line in enumerate(lines[first_entry:], start=first_entry + 1):
        if not line.startswith('- '):
            problems.append(f'line {number}: not an entry: {line}')
            continue
        name = line[len('- '):]
        if not is_name(name):
            problems.append(f'line {number}: not a name: {name}')
            continue
        if name in names:
            problems.append(f'line {number}: duplicate: {name}')
        elif names and name < names[-1]:
            problems.append(f'line {number}: out of order: {name}')
        names.append(name)
    return names, problems


def write_names(root: Path, names: Iterable[str]) -> None:
    path = root / NAMES
    if path.is_file():
        text = _read(path)
        first_entry = re.search(r'^-', text, re.MULTILINE)
        preamble = text[:first_entry.start()] if first_entry else text
        if preamble and not preamble.endswith('\n'):
            preamble += '\n'
    else:
        preamble = NAMES_PREAMBLE
    entries = ''.join(f'- {name}\n' for name in sorted(set(names)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((preamble + entries).encode('utf-8', 'surrogateescape'))


@dataclass(frozen=True)
class SiblingNames:
    names: frozenset[str]
    tree: Path | None             # the tree the names came from; None when read from git or missing
    branch: str | None = None     # None: the sibling's checked-out tree answered
    missing: bool = False         # the chosen branch is not in the sibling

    def scope(self) -> str:
        if self.branch is None:
            return ''
        return f' on {self.branch}' + (' (no such branch)' if self.missing else '')


class Siblings:
    def __init__(self, root: Path):
        self.root = root
        self._found: dict[str, SiblingNames | None] = {}

    def names(self, repo: str) -> SiblingNames | None:
        name = REPO_RENAMES.get(repo, repo)
        if name not in self._found:
            self._found[name] = self._look_up(name)
        return self._found[name]

    def _look_up(self, name: str) -> SiblingNames | None:
        path = sibling_dir(self.root) / name
        try:
            if not path.is_dir() or is_linked_worktree(path) or name == repo_name(self.root):
                return None
            branch, _reason = chosen_branch(self.root, path)
            if branch is not None and (found := worktrees(path)) is not None:
                holder = next((worktree for worktree in found if worktree.branch == branch and not worktree.prunable),
                              None)
                if holder is not None:
                    return SiblingNames(frozenset(_tree_names(holder.path)), holder.path, branch)
                if not has_branch(path, branch):
                    return SiblingNames(frozenset(), None, branch, missing=True)
                names = branch_names(path, branch)
                if names is not None:
                    return SiblingNames(frozenset(names), None, branch)
            if not (path / 'plans').is_dir():
                return None
            return SiblingNames(frozenset(_tree_names(path)), path)
        except OSError:
            return None


def _tree_names(tree: Path) -> list[str]:
    if not (tree / 'plans').is_dir():
        return []
    names = read_names(tree)[0]
    if names is None:
        names = list(index_by_stem(named_plan_files(tree / 'plans')))
    return names


def _line_parts(lines: list[str]) -> Iterator[tuple[int, str, list[tuple[int, int]], list[re.Match]]]:
    in_fence = False
    for line_no, line in enumerate(lines, start=1):
        if line.lstrip().startswith(FENCE_MARKERS):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        code = [match.span() for match in CODE_SPAN.finditer(line)]
        links = [
            match for match in LINK.finditer(line)
            if not match.group(2).startswith(('http://', 'https://')) and not _inside(match.start(), code)
        ]
        yield line_no, line, code, links


def iter_links(path: Path) -> Iterator[tuple[int, str, str, str]]:
    for line_no, _line, _code, links in _line_parts(_read(path).split('\n')):
        for match in links:
            yield line_no, match.group(1), match.group(2), match.group(3) or ''


def iter_cites(path: Path) -> Iterator[tuple[int, str, str]]:
    for line_no, line, _code, _links in _line_parts(_read(path).split('\n')):
        guarded = _guarded_spans(line)
        for match in CODE_SPAN.finditer(line):
            if not _inside(match.start(), guarded) and PATH_CITE.fullmatch(match.group(2).strip()):
                yield line_no, match.group(0), match.group(2)


def iter_references(path: Path) -> Iterator[tuple[int, re.Match]]:
    for line_no, line, code, _links in _line_parts(_read(path).split('\n')):
        for match in REFERENCE.finditer(line):
            if not _inside(match.start(), code):
                yield line_no, match


def link_path(root: Path, src: Path, target: str) -> Path:
    # A link that leaves the repo assumes it sits beside its neighbours, as only the main checkout does.
    path = Path(os.path.normpath(src.parent / target))
    main = main_worktree(root)
    if main == root or path == root or root in path.parents:
        return path
    if not os.path.isabs(target):
        path = Path(os.path.normpath(main / os.path.relpath(path, root)))
    if path == main or main in path.parents:
        return root / path.relative_to(main)
    return path


def cross_repo_plan(root: Path, src: Path, target: str) -> tuple[str, str] | None:
    path = link_path(root, src, target)
    if path == root or root in path.parents:
        return None
    parts = path.parts
    if 'plans' not in parts[:-1]:
        return None
    i = len(parts) - 2 - parts[:-1][::-1].index('plans')
    if i == 0:
        return None
    rest = parts[i + 1:]
    if ((len(rest) > 1 and rest[0] == 'followups') or rest[-1] == 'README.md' or rest in REGISTER_PARTS
            or any(part.startswith('.') for part in rest)):
        return None
    name = folder_repo(Path(*parts[:i]))
    repo = REPO_RENAMES.get(name, name)
    if repo == repo_name(root):
        return None
    return repo, stem(rest[-1])


def classify_link(root: Path, src: Path, target: str, index, named, dead) -> tuple[str, tuple[str | None, str] | None]:
    cross = cross_repo_plan(root, src, target)
    if cross is not None:
        return CROSS_REPO_PATH, cross
    path = link_path(root, src, target)
    if path.exists():
        return (PLAN_PATH, (None, stem(path.name))) if path in named else (OK, None)
    if target in dead:
        return DEAD_LISTED, None
    target_stem = stem(os.path.basename(target))
    if target_stem in index:
        return PLAN_PATH, (None, target_stem)
    return DEAD_UNLISTED, None


def classify_cite(root: Path, content: str, index) -> tuple[str, tuple[str | None, str], str] | None:
    match = PATH_CITE.fullmatch(content.strip())
    if match is None:
        return None
    path_text, lines = match.group(1), match.group(2) or ''
    parts = [part for part in path_text.split('/') if part not in ('', '.', '..')]
    file, dirs = parts[-1], parts[:-1]
    absolute = path_text.startswith('/')

    if file == 'README.md' or any(part.startswith('.') for part in dirs):
        return None
    if not absolute and dirs and dirs[0] != 'plans' and (root / dirs[0]).exists():
        return None
    if 'plans' in dirs:
        i = len(dirs) - 1 - dirs[::-1].index('plans')
        rest = dirs[i + 1:]
        if rest[:1] == ['followups'] or (*rest, file) in REGISTER_PARTS:
            return None
        if i > 0:
            name = folder_repo(Path('/', *dirs[:i])) if absolute else dirs[i - 1]
            repo = REPO_RENAMES.get(name, name)
            if repo != repo_name(root):
                if absolute:
                    exists = Path('/', *dirs[:i]).is_dir()
                else:
                    exists = (sibling_dir(root) / repo / 'plans').is_dir()
                return (CROSS_REPO_PATH, (repo, stem(file)), lines) if exists else None
    if stem(file) in index:
        return PLAN_PATH, (None, stem(file)), lines
    return None


def classify_reference(root: Path, repo: str | None, name: str, names: set[str], siblings: Siblings) -> str:
    if repo is None or REPO_RENAMES.get(repo, repo) == repo_name(root):
        return KNOWN if name in names else UNKNOWN_NAME
    found = siblings.names(repo)
    if found is not None and name in found.names:
        return CROSS_REPO_REF
    return CROSS_REPO_REF_UNRESOLVED


def render_reference(repo: str | None, name: str, fragment: str, label: str, in_table: bool) -> str:
    target = (f'{repo}:' if repo else '') + name + fragment
    core = _unwrap(label)
    if not core:
        return f'[[{target}]]'
    cite = LABEL_CITE.fullmatch(core)
    if cite and stem(os.path.basename(cite.group(1))) == name:
        return f'[[{target}]]' + (cite.group(2) or '') + (cite.group(3) or '')
    separator = '\\|' if in_table else '|'
    return f'[[{target}{separator}{label.strip()}]]'


def _unwrap(label: str) -> str:
    text = label.strip()
    while True:
        for mark in ('**', '`', '*', '_'):
            if len(text) > 2 * len(mark) and text.startswith(mark) and text.endswith(mark):
                text = text[len(mark):-len(mark)].strip()
                break
        else:
            return text


def _corpus(root: Path):
    plans = root / 'plans'
    named = named_plan_files(plans)
    return (link_sources(plans), index_by_stem(named), set(named), read_allowlist(root),
            read_names(root), Siblings(root), read_pairs(root))


@dataclass
class Link:
    src: Path
    line: int
    target: str
    fragment: str
    verdict: str
    kind: str
    resolved: tuple[str | None, str] | None


@dataclass
class Reference:
    src: Path
    line: int
    text: str
    repo: str | None
    name: str
    verdict: str
    scope: str = ''


@dataclass
class Scan:
    links: list[Link]
    references: list[Reference]
    collisions: dict[str, list[Path]]
    unused_allowlist: list[str]
    names: set[str]
    name_problems: list[str]
    unregistered: dict[str, list[Path]]
    pair_problems: list[str]

    def count(self, verdict: str, kind: str | None = None) -> int:
        return sum(1 for link in self.links if link.verdict == verdict and kind in (None, link.kind))

    def count_kind(self, kind: str) -> int:
        return sum(1 for link in self.links if link.kind == kind)

    def ref_count(self, verdict: str) -> int:
        return sum(1 for reference in self.references if reference.verdict == verdict)

    def summary(self) -> str:
        return (
            f'plan_links: {self.count_kind("link")} links, {self.count_kind("cite")} cites, '
            f'{self.count(PLAN_PATH)} plan-paths, {self.count(CROSS_REPO_PATH)} cross-repo-paths, '
            f'{self.count(DEAD_UNLISTED)} dead-unlisted, {len(self.unused_allowlist)} unused-allowlist, '
            f'{len(self.references)} references, {self.ref_count(UNKNOWN_NAME)} unknown-names, '
            f'{self.ref_count(CROSS_REPO_REF_UNRESOLVED)} cross-repo-unresolved, {len(self.collisions)} collided-names, '
            f'{len(self.unregistered)} unregistered, {len(self.name_problems)} register-problems, '
            f'{len(self.pair_problems)} pair-problems'
        )


def _scan(root: Path) -> Scan:
    sources, index, named, allowlist, (registered, problems), siblings, (_pairs, pair_problems) = _corpus(root)
    dead = set(allowlist)
    names = set(registered or ())
    links: list[Link] = []
    references: list[Reference] = []
    for src in sources:
        for line_no, _label, target, fragment in iter_links(src):
            verdict, resolved = classify_link(root, src, target, index, named, dead)
            links.append(Link(src, line_no, target, fragment, verdict, 'link', resolved))
        for line_no, span, content in iter_cites(src):
            cite = classify_cite(root, content, index)
            if cite is not None:
                verdict, resolved, _lines = cite
                links.append(Link(src, line_no, span, '', verdict, 'cite', resolved))
        for line_no, match in iter_references(src):
            repo, name = match.group(1), match.group(2)
            verdict = classify_reference(root, repo, name, names, siblings)
            found = siblings.names(repo) if verdict in (CROSS_REPO_REF, CROSS_REPO_REF_UNRESOLVED) else None
            scope = found.scope() if found is not None else ''
            references.append(Reference(src, line_no, match.group(0), repo, name, verdict, scope))

    used = {link.target for link in links if link.verdict == DEAD_LISTED}
    collisions = {name: paths for name, paths in index.items() if len(paths) > 1}
    missing = [f'{NAMES.as_posix()} is missing; run --register'] if registered is None and not problems else []
    unregistered = {name: paths for name, paths in index.items() if name not in names}
    return Scan(links, references, collisions, [entry for entry in allowlist if entry not in used],
                names, missing + problems, unregistered, pair_problems)


def check(root: Path, only: str | None = None) -> int:
    scan = _scan(root)
    selected = (only,) if only else CHECK_CLASSES
    violations = 0

    if 'links' in selected:
        for link in scan.links:
            if link.verdict in GATING:
                print(f'{_relative(root, link.src)}:{link.line}: {link.verdict}: {link.target}')
                violations += 1
    if 'refs' in selected:
        for reference in scan.references:
            if reference.verdict in (UNKNOWN_NAME, CROSS_REPO_REF_UNRESOLVED):
                print(f'{_relative(root, reference.src)}:{reference.line}: {reference.verdict}: '
                      f'{reference.text}{reference.scope}')
                violations += reference.verdict == UNKNOWN_NAME
    if 'stems' in selected:
        for name, paths in scan.collisions.items():
            print(f'collided name: {name}: {_joined(root, paths)}')
        violations += len(scan.collisions)
    if 'names' in selected:
        for problem in scan.name_problems:
            print(f'names: {problem}')
        for name, paths in scan.unregistered.items():
            print(f'unregistered: {name}: {_joined(root, paths)}')
        violations += len(scan.name_problems) + len(scan.unregistered)
    if 'allowlist' in selected:
        for entry in scan.unused_allowlist:
            print(f'allowlist entry unused: {entry}')
        violations += len(scan.unused_allowlist)
    if 'pairs' in selected:
        for problem in scan.pair_problems:
            print(f'pairs: {problem}')
        violations += len(scan.pair_problems)

    print(scan.summary())
    return 1 if violations else 0


def convert(root: Path) -> int:
    converted = _convert(root)
    for src, count in converted.items():
        print(f'{_relative(root, src)}: {count} converted')
    print(f'plan_links: {sum(converted.values())} converted in {len(converted)} files')
    return 0


def _convert(root: Path) -> dict[Path, int]:
    sources, index, named, allowlist, _names, _siblings, _pairs = _corpus(root)
    dead = set(allowlist)
    converted = {}
    for src in sources:
        lines = _read(src).split('\n')
        count = 0
        for line_no, line, _code, links in list(_line_parts(lines)):
            in_table = line.lstrip().startswith('|')
            # Right to left, so a replacement never shifts a span not yet replaced.
            for match in reversed(links):
                verdict, resolved = classify_link(root, src, match.group(2), index, named, dead)
                if verdict in (PLAN_PATH, CROSS_REPO_PATH):
                    repo, name = resolved
                    reference = render_reference(repo, name, match.group(3) or '', match.group(1), in_table)
                    line = line[:match.start()] + reference + line[match.end():]
                    count += 1
            guarded = _guarded_spans(line)
            for span in reversed(list(CODE_SPAN.finditer(line))):
                if _inside(span.start(), guarded):
                    continue
                cite = classify_cite(root, span.group(2), index)
                if cite is not None:
                    _verdict, (repo, name), cited_lines = cite
                    reference = f'[[{repo}:{name}]]' if repo else f'[[{name}]]'
                    line = line[:span.start()] + reference + cited_lines + line[span.end():]
                    count += 1
            lines[line_no - 1] = line
        if count:
            src.write_bytes('\n'.join(lines).encode('utf-8', 'surrogateescape'))
            converted[src] = count
    return converted


def register(root: Path) -> int:
    registered, problems = read_names(root)
    if problems:
        return _refuse_malformed(problems)
    known = set(registered or ())
    index = index_by_stem(named_plan_files(root / 'plans'))
    new = sorted(name for name in index if name not in known)
    invalid = [name for name in new if not is_name(name)]
    for name in invalid:
        print(f'refused: {name}: not a name ({_joined(root, index[name])})')
    if invalid:
        return 1

    for name in new:
        print(f'registered: {name}')
    if new or registered is None:
        write_names(root, known | set(new))
    print(f'plan_links: {len(new)} registered, {len(known) + len(new)} names')
    return 0


def claim(root: Path, requested: list[str]) -> int:
    registered, problems = read_names(root)
    if problems:
        return _refuse_malformed(problems)
    known = set(registered or ())
    wanted = list(dict.fromkeys(requested))
    refused = False
    for name in wanted:
        if not is_name(name):
            print(f'refused: {name}: not a name')
            refused = True
        elif name in known:
            print(f'refused: {name}: already registered')
            refused = True
    if refused:
        return 1

    write_names(root, known | set(wanted))
    for name in wanted:
        print(f'claimed: {name}')
    return 0


def resolve(root: Path, refs: list[str]) -> int:
    all_found = True
    siblings = Siblings(root)
    for text in refs:
        match = REFERENCE.fullmatch(text if text.startswith('[[') else f'[[{text}]]')
        if match is None:
            print(f'{text}: not a reference')
            all_found = False
            continue
        repo, name, fragment = match.group(1), match.group(2), match.group(3) or ''
        if repo is not None and REPO_RENAMES.get(repo, repo) != repo_name(root):
            found = siblings.names(repo)
            if found is None:
                print(f'{text}: no repo {repo} beside this one')
                all_found = False
                continue
            if found.tree is None:
                print(_resolved_on_branch(root, text, repo, name, found))
                all_found = False
                continue
            repo_dir = found.tree
        else:
            repo_dir = root

        paths = index_by_stem(named_plan_files(repo_dir / 'plans')).get(name, [])
        shown = [_relative(root, path) if repo_dir == root else str(path) for path in paths]
        if len(shown) == 1:
            print(shown[0] + fragment)
            continue
        all_found = False
        if shown:
            print(f'{text}: {len(shown)} files: ' + ', '.join(shown))
        elif name in (read_names(repo_dir)[0] or ()):
            print(f'{text}: registered, no plan file')
        else:
            print(f'{text}: unknown name')
    return 0 if all_found else 1


def _resolved_on_branch(root: Path, text: str, repo: str, name: str, found: SiblingNames) -> str:
    if found.missing:
        return f'{text}: {repo} has no branch {found.branch}'
    listed = branch_plans(sibling_dir(root) / REPO_RENAMES.get(repo, repo), found.branch)
    paths = [path for path in (listed[0] if listed else []) if stem(path.rsplit('/', 1)[-1]) == name]
    if paths:
        return f'{text}: on {found.branch}, which no tree of {repo} has checked out: ' + ', '.join(paths)
    if name in found.names:
        return f'{text}: registered on {found.branch}, no plan file'
    return f'{text}: unknown name on {found.branch}'


def tree(here: Path, repo: Path, branch: str | None, create: bool) -> int:
    found = worktrees(repo)
    if found is None:
        print(f'refused: {repo} is not the root of a git work tree')
        return 1
    main = found[0].path
    if branch is None:
        branch, reason = chosen_branch(here, main)
        if branch is None:
            print(f'refused: {reason}')
            return 1

    holder = next((worktree for worktree in found if worktree.branch == branch), None)
    if holder is not None and holder.prunable:
        print(f'refused: {branch} is held by {holder.path}, a worktree whose folder is missing: '
              f'git -C {main} worktree prune')
        return 1
    if holder is not None:
        print(holder.path)
        if outside_layout(main, holder):
            print(_outside_note(main, holder))
        _print_removable(main, found, holder.path)
        return 0

    target = layout_path(main, branch)
    if target is None:
        print(f'refused: branch {branch} gives no folder name')
        return 1
    layout = target.parent.parent
    if (layout / '.git').exists():
        print(f'refused: the layout puts {branch} at {target}, inside the git work tree {layout}')
        return 1
    if target.exists() or target.is_symlink():
        print(f'refused: {target} exists and does not have {branch} checked out')
        return 1
    remote_ref = None
    if not has_branch(main, branch):
        remotes = remote_branches(main, branch)
        if not remotes:
            print(f'refused: {branch} is no branch of {main}, local or remote-tracking')
            return 1
        if len(remotes) > 1:
            print(f'refused: {branch} is on more than one remote of {main} ({", ".join(remotes)}): '
                  'create the local branch first')
            return 1
        remote_ref = remotes[0]

    if not create:
        tracking = f', a new local branch tracking {remote_ref} as of the last fetch' if remote_ref else ''
        print(f'would create: {target} on {branch}{tracking}. Ask, then run again with --create.')
        return WOULD_CREATE

    made: list[Path] = []
    try:
        for folder in (layout, target.parent):
            if not folder.is_dir():
                containing = folder.parent.stat()
                folder.mkdir()
                made.append(folder)
                with contextlib.suppress(PermissionError):
                    os.chown(folder, -1, containing.st_gid)
                folder.chmod(containing.st_mode & 0o7777)
    except OSError as exc:
        _remove_folders(made)
        print(f'refused: {exc.filename} could not be created: {exc.strerror}')
        return 1

    if remote_ref is None:
        add = ('worktree', 'add', '--quiet', str(target), branch)
    else:
        add = ('worktree', 'add', '--quiet', '--track', '-b', branch, str(target), remote_ref)
    added = _git(main, '-c', 'core.hooksPath=/dev/null', *add)
    if added.returncode != 0:
        _remove_folders(made)
        reason = next((line for line in reversed(added.stderr.splitlines()) if line.strip()), 'no message')
        print(f'refused: git worktree add failed: {reason}')
        return 1
    try:
        git_dir = _git(target, 'rev-parse', '--absolute-git-dir')
        if git_dir.returncode != 0:
            raise OSError(git_dir.stderr.strip() or 'git rev-parse --absolute-git-dir failed')
        line = f'plan-only worktree made by plan_links.py --tree on {datetime.date.today().isoformat()} from {here}\n'
        (Path(git_dir.stdout.strip()) / MARKER).write_bytes(line.encode('utf-8', 'surrogateescape'))
    except OSError as exc:
        print(f'refused: {target} was created, but its plan-only marker could not be written: {exc}')
        return 1

    print(target)
    print(f'created: plan-only worktree of {main} on {branch}; commit there. While it holds {branch}, '
          f'git checks {branch} out nowhere else: git -C {main} worktree remove {target}')
    print('trust: git run by another account refuses this tree, which this account owns, unless that account '
          f'trusts it: git config --global --add safe.directory {target}')
    _print_removable(main, found, target)
    return 0


def _outside_note(main: Path, worktree: Worktree) -> str:
    expected = layout_path(main, worktree.branch)
    where = f'which puts {worktree.branch} at {expected}' if expected else f'which has no folder for {worktree.branch}'
    return f'note: {worktree.path} is outside the worktree layout, {where}'


def _remove_folders(made: list[Path]) -> None:
    for folder in reversed(made):
        with contextlib.suppress(OSError):
            folder.rmdir()


def _plan_only(worktree: Worktree) -> bool:
    return worktree.admin is not None and (worktree.admin / MARKER).is_file()


def _state(main: Path, worktree: Worktree, trunk_name: str | None) -> tuple[str, str | None, str | None]:
    if worktree.prunable:
        return 'folder missing', 'prune', f'git -C {main} worktree prune'
    # --no-optional-locks: a report never writes another tree's index.
    status = _git(worktree.path, '--no-optional-locks', 'status', '--porcelain', '--untracked-files=normal')
    uncommitted = len(status.stdout.splitlines())
    if uncommitted:
        return f'{uncommitted} uncommitted', None, None
    remove = f'git -C {main} worktree remove {worktree.path}'
    if worktree.branch is None:
        return 'clean, on no branch', 'remove', remove
    ref = f'refs/heads/{worktree.branch}'
    if trunk_name and _git(main, 'merge-base', '--is-ancestor', ref, f'refs/heads/{trunk_name}').returncode == 0:
        return f'clean, merged into {trunk_name}', 'remove', remove
    if _git(main, 'for-each-ref', '--format=%(upstream:track)', ref).stdout.strip() == '[gone]':
        return 'clean, upstream gone', 'remove', remove
    return 'clean', None, None


def _plan_only_worktrees(found: list[Worktree]) -> list[Worktree]:
    return sorted((worktree for worktree in found if _plan_only(worktree)), key=lambda worktree: worktree.path)


def _print_removable(main: Path, found: list[Worktree], printed: Path) -> None:
    others = [worktree for worktree in _plan_only_worktrees(found) if worktree.path != printed]
    trunk_name = trunk(main) if others else None
    for worktree in others:
        state, _verb, command = _state(main, worktree, trunk_name)
        if command:
            print(f'removable: {worktree.path} ({worktree.branch or "no branch"}): {state}; {command}')


def report_worktrees(repos: list[Path]) -> int:
    code = 0
    listed = total = removable = outside = 0
    for repo in repos:
        found = worktrees(repo)
        if found is None:
            print(f'refused: {repo} is not the root of a git work tree')
            code = 1
            continue
        main = found[0].path
        plan_only = _plan_only_worktrees(found)
        trunk_name = trunk(main) if plan_only else None
        print(f'{main}: {len(plan_only)} plan-only worktrees')
        for worktree in plan_only:
            state, verb, command = _state(main, worktree, trunk_name)
            elsewhere = outside_layout(main, worktree)
            print(f'  {worktree.path} ({worktree.branch or "no branch"}): {state}'
                  + ('; outside the layout' if elsewhere else '')
                  + (f'; {verb}: {command}' if command else ''))
            removable += command is not None
            outside += elsewhere
        listed += 1
        total += len(plan_only)
    print(f'plan_links: {listed} repos, {total} plan-only worktrees, {removable} removable, '
          f'{outside} outside the layout')
    return code


def report(root: Path, emit_allowlist: bool = False) -> int:
    scan = _scan(root)
    if emit_allowlist:
        print(_allowlist_text(root, scan), end='')
        return 0

    print(f'plan_links report: {root}')
    print()
    print(f'{"kind":<6}{"verdict":<24}{"occurrences":>12}{"distinct targets":>18}')
    rows = [('link', verdict) for verdict in LINK_VERDICTS] + [('cite', PLAN_PATH), ('cite', CROSS_REPO_PATH)]
    for kind, verdict in rows:
        links = [link for link in scan.links if link.kind == kind and link.verdict == verdict]
        print(f'{kind:<6}{verdict:<24}{len(links):>12}{len({link.target for link in links}):>18}')
    print(f'{"total":<30}{len(scan.links):>12}{len({link.target for link in scan.links}):>18}')
    print()

    anchored = sum(1 for link in scan.links if link.fragment)
    by_repo = Counter(link.resolved[0] for link in scan.links if link.verdict == CROSS_REPO_PATH)
    print('references: ' + ', '.join(f'{scan.ref_count(verdict)} {verdict}' for verdict in REF_VERDICTS))
    print(f'links carrying an #anchor: {anchored}')
    print('cross-repo paths by repo: ' + (', '.join(f'{r} {n}' for r, n in by_repo.most_common()) or 'none'))
    print(f'names: {len(scan.names)} registered, {len(scan.unregistered)} unregistered, '
          f'{len(scan.name_problems)} problems')
    print(f'collided names: {len(scan.collisions)}')
    for name, paths in scan.collisions.items():
        print(f'  {name}: {_joined(root, paths)}')
    print(f'unused allowlist entries: {len(scan.unused_allowlist)}')
    return 0


def _dead_group(root: Path, link: Link) -> int:
    parts = link.target.split('/')
    if '.claude' in parts or 'memory' in parts:
        return 0
    first = next((part for part in parts if part not in ('.', '..')), '')
    if first in REPO_RENAMES or (first != repo_name(root) and (sibling_dir(root) / first).is_dir()):
        return 2
    return 1


def _allowlist_text(root: Path, scan: Scan) -> str:
    groups: list[dict[str, int]] = [{} for _ in DEAD_GROUPS]
    for link in scan.links:
        if link.verdict == DEAD_UNLISTED:
            targets = groups[_dead_group(root, link)]
            targets[link.target] = targets.get(link.target, 0) + 1

    out = ['# Dead link targets, left as written in the prose. One literal target per line.']
    for label, targets in zip(DEAD_GROUPS, groups):
        if targets:
            out.append(f'# {label}, {len(targets)} targets / {sum(targets.values())} occurrences')
            out.extend(sorted(targets))
    return '\n'.join(out) + '\n'


def selftest() -> int:
    return _run_cases(SELFTEST_CASES)


def _run_cases(cases) -> int:
    failed = 0
    for number, case in enumerate(cases, start=1):
        tmp = Path(tempfile.mkdtemp(prefix='plan_links-')).resolve()
        try:
            case(tmp)
            print(f'case {number}: ok')
        except Exception as exc:
            failed += 1
            print(f'case {number}: FAIL {case.__name__}: {type(exc).__name__}: {exc}')
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f'selftest: {len(cases) - failed} passed, {failed} failed')
    return 1 if failed else 0


def _read(path: Path) -> str:
    return path.read_bytes().decode('utf-8', 'surrogateescape')


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _joined(root: Path, paths: list[Path]) -> str:
    return ', '.join(_relative(root, path) for path in paths)


def _inside(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _guarded_spans(line: str) -> list[tuple[int, int]]:
    return [match.span() for match in LINK.finditer(line)] + [match.span() for match in REFERENCE.finditer(line)]


def _refuse_malformed(problems: list[str]) -> int:
    for problem in problems:
        print(f'names: {problem}')
    print('refused: fix the name register first')
    return 1


# ─── Self-test fixtures ─────────────────────────────────────────────────────
#
# Each case receives an empty directory and builds a fake repo at `root/` with
# fake sibling repos beside it. A case passes by returning.

def _fixture(tmp: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8'))
    (tmp / 'root' / 'plans').mkdir(parents=True, exist_ok=True)
    return tmp / 'root'


def _classify_in(root: Path, src: str, target: str):
    _sources, index, named, allowlist, _names, _siblings, _pairs = _corpus(root)
    return classify_link(root, root / src, target, index, named, set(allowlist))


def _captured(function, *args) -> tuple[int, list[str]]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = function(*args)
    return code, buffer.getvalue().splitlines()


def _same(actual, expected, what: str) -> None:
    if actual != expected:
        raise AssertionError(f'{what}: expected {expected!r}, got {actual!r}')


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


_GIT_ISOLATED = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}


def _sh(path: Path, *args: str) -> None:
    subprocess.run(['git', '-C', str(path), *args], check=True, capture_output=True,
                   env={**os.environ, **_GIT_ISOLATED})


def _git_repo(path: Path, branch: str, files: dict[str, str] | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _sh(path, 'init', '-q', '-b', branch)
    for rel, text in (files or {}).items():
        _write(path / rel, text)
    _commit(path)
    return path


def _commit(path: Path, message: str = 'selftest') -> None:
    _sh(path, 'add', '-A')
    _sh(path, '-c', 'user.name=selftest', '-c', 'user.email=selftest@localhost', 'commit', '-q', '--allow-empty',
        '-m', message)


def _add_worktree(repo: Path, path: Path, *args: str) -> Path:
    _sh(repo, '-c', 'core.hooksPath=/dev/null', 'worktree', 'add', '-q', str(path), *args)
    return path


def _case_stem_strips_only_a_trailing_run_of_segments(tmp: Path) -> None:
    table = {
        'foo.md': 'foo', 'foo-e.md': 'foo', 'foo-i.md': 'foo', 'foo-e-i.md': 'foo',
        'foo-i-e.md': 'foo', 'foo-e-e.md': 'foo', 'foo-ei.md': 'foo-ei',
        'foo-e-x.md': 'foo-e-x', 'e.md': 'e',
        'foo-s.md': 'foo', 'foo-s-e.md': 'foo', 'foo-e-s.md': 'foo',
        'foo-ss.md': 'foo-ss', 'foo-s-x.md': 'foo-s-x', 's.md': 's',
    }
    _same({name: stem(name) for name in table}, table, 'stem table')


def _case_named_plans_exclude_readmes_the_register_and_followups(tmp: Path) -> None:
    files = ('a.md', 'README.md', 'names.md', 'tools/names.md', 'archive/b-i.md', 'archive/README.md',
             'followups/2026-09.md', 'followups/README.md', '.extract/c.md', 'sub/names.md', 'sub/tools/names.md')
    root = _fixture(tmp, {f'root/plans/{rel}': '' for rel in files})
    plans = root / 'plans'

    def under_plans(paths):
        return [path.relative_to(plans).as_posix() for path in paths]

    _same(under_plans(link_sources(plans)),
          ['README.md', 'a.md', 'archive/README.md', 'archive/b-i.md', 'sub/names.md', 'sub/tools/names.md'],
          'link sources')
    _same(under_plans(named_plan_files(plans)), ['a.md', 'archive/b-i.md', 'sub/names.md', 'sub/tools/names.md'],
          'named plan files')
    _same(len(plan_files(plans)), 10, 'plan files')


def _case_code_and_fences_hide_links_cites_and_references(tmp: Path) -> None:
    lines = [
        "[l1](x.md) `[l2](y.md)` ``[[foo]] `z.md` `` [[bar]]",
        "```fence",
        "[l3](w.md) [[baz]] `v.md`",
        "```",
        "[`u.md`](t.md) [[qux|`s.md`]] `r.md`",
        "",
    ]
    root = _fixture(tmp, {'root/plans/a.md': '\n'.join(lines)})
    path = root / 'plans/a.md'
    _same(list(iter_links(path)), [(1, 'l1', 'x.md', ''), (5, '`u.md`', 't.md', '')], 'links')
    _same([(line, match.group(2)) for line, match in iter_references(path)], [(1, 'bar'), (5, 'qux')], 'references')
    _same(list(iter_cites(path)), [(5, '`r.md`', 'r.md')], 'cites')


def _case_link_to_an_existing_file(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/foo.md': '',
        'root/plans/followups/2026-09.md': '',
        'root/plans/README.md': '',
        'root/docs/foo.md': '',
        'root/plans/a.md': '',
    })
    for target in ('foo.md', str(root / 'plans/foo.md')):
        _same(_classify_in(root, 'plans/a.md', target), (PLAN_PATH, (None, 'foo')), target)
    for target in ('../docs/foo.md', 'followups/2026-09.md', 'README.md'):
        _same(_classify_in(root, 'plans/a.md', target), (OK, None), target)


def _case_broken_link_with_a_plan_name_is_a_plan_path(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/foo-e-i.md': '',
        'root/plans/dup.md': '',
        'root/plans/archive/dup-i.md': '',
        'root/plans/a.md': '',
    })
    for target in ('foo.md', 'sub/foo-e.md', 'foo-s.md'):
        _same(_classify_in(root, 'plans/a.md', target), (PLAN_PATH, (None, 'foo')), target)
    _same(_classify_in(root, 'plans/a.md', 'gone/dup-e.md'), (PLAN_PATH, (None, 'dup')), 'gone/dup-e.md')


def _case_unknown_target_fails_closed(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a.md': '[bar](bar.md)\n'})
    _same(_classify_in(root, 'plans/a.md', 'bar.md'), (DEAD_UNLISTED, None), 'verdict')


def _case_allowlisted_target_is_dead_listed(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/foo-i.md': '',
        'root/plans/tools/dead-links.txt': '# c\n\n../docs/foo.md\n',
    })
    _same(_classify_in(root, 'plans/a.md', '../docs/foo.md'), (DEAD_LISTED, None), 'verdict')


def _case_cross_repo_plan_paths(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/x.md': '',
        'root/plans/a.md': '',
        'sibling/plans/archive/x-i.md': '',
        'sibling/plans/README.md': '',
        'sibling/plans/names.md': '',
        'sibling/plans/tools/names.md': '',
    })
    expected = [
        ('../../sibling/plans/x.md', (CROSS_REPO_PATH, ('sibling', 'x'))),
        ('../../sonata-passwave-web/plans/archive/y-e-i.md', (CROSS_REPO_PATH, ('passwave-web', 'y'))),
        (str(tmp / 'group/other/plans/z-e.md'), (CROSS_REPO_PATH, ('other', 'z'))),
        ('../../root/plans/x.md', (PLAN_PATH, (None, 'x'))),
        ('../../group/other/plans/sub/z.md', (CROSS_REPO_PATH, ('other', 'z'))),
        ('../../sibling/plans/README.md', (OK, None)),
        ('../../sibling/plans/names.md', (OK, None)),
        ('../../sibling/plans/tools/names.md', (OK, None)),
        ('../../sibling/plans/followups/2026-09.md', (DEAD_UNLISTED, None)),
        ('../../sibling/plans/.hidden/q.md', (DEAD_UNLISTED, None)),
    ]
    for target, verdict in expected:
        _same(_classify_in(root, 'plans/a.md', target), verdict, target)

    _fixture(tmp, {'passwave-web/plans/x.md': '', 'passwave-web/plans/a.md': ''})
    _same(_classify_in(tmp / 'passwave-web', 'plans/a.md', '../../sonata-passwave-web/plans/x.md'),
          (PLAN_PATH, (None, 'x')), 'a path through this repo\'s old name')


def _case_cites_classified_by_path_shape(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/foo-e.md': ''})
    for rel in ('root/docs', 'sibling/plans', 'passwave-web/plans', 'group/other/plans'):
        (tmp / rel).mkdir(parents=True, exist_ok=True)
    index = index_by_stem(named_plan_files(root / 'plans'))
    expected = [
        ('plans/foo-e.md', (PLAN_PATH, (None, 'foo'), '')),
        (' foo.md:12-20 ', (PLAN_PATH, (None, 'foo'), ':12-20')),
        ('archive/foo-e-i.md:3', (PLAN_PATH, (None, 'foo'), ':3')),
        ('defer/foo.md', (PLAN_PATH, (None, 'foo'), '')),
        ('root/plans/foo.md', (PLAN_PATH, (None, 'foo'), '')),
        (str(root / 'plans/foo-i.md'), (PLAN_PATH, (None, 'foo'), '')),
        ('sibling/plans/bar-e.md:4', (CROSS_REPO_PATH, ('sibling', 'bar'), ':4')),
        ('../sonata-passwave-web/plans/archive/bar.md:57–58', (CROSS_REPO_PATH, ('passwave-web', 'bar'), ':57–58')),
        (str(tmp / 'group/other/plans/bar.md'), (CROSS_REPO_PATH, ('other', 'bar'), '')),
        ('ghost/plans/foo.md', None),
        ('/x/y/other/plans/bar.md', None),
        ('docs/foo.md', None),
        ('../docs/foo.md', None),
        ('plans/followups/2026-09.md', None),
        ('sibling/plans/followups/x.md', None),
        ('plans/README.md', None),
        ('plans/names.md', None),
        ('sibling/plans/names.md', None),
        ('plans/tools/names.md', None),
        ('sibling/plans/tools/names.md', None),
        ('plans/.extract/foo.md', None),
        ('unknown.md', None),
        ('foo.md and more', None),
        ('foo.py', None),
    ]
    for content, verdict in expected:
        _same(classify_cite(root, content, index), verdict, repr(content))

    _fixture(tmp, {'passwave-web/plans/x.md': ''})
    web_index = {'x': [tmp / 'passwave-web/plans/x.md']}
    content = '../sonata-passwave-web/plans/x.md'
    _same(classify_cite(tmp / 'passwave-web', content, web_index), (PLAN_PATH, (None, 'x'), ''),
          'a path through this repo\'s old name')
    _same(classify_cite(root, content, web_index), (CROSS_REPO_PATH, ('passwave-web', 'x'), ''), 'from root')


def _case_references_parse_every_form(tmp: Path) -> None:
    expected = [
        ('[[foo]]', (None, 'foo', None, None)),
        ('[[foo#sec-2]]', (None, 'foo', '#sec-2', None)),
        ('[[foo|the plan]]', (None, 'foo', None, 'the plan')),
        ('[[foo\\|in a table]]', (None, 'foo', None, 'in a table')),
        ('[[r:foo#s|l]]', ('r', 'foo', '#s', 'l')),
        ('[[v0.5-build-plan]]', (None, 'v0.5-build-plan', None, None)),
        ('[[EXPORT_SYSTEM_PLAN]]', (None, 'EXPORT_SYSTEM_PLAN', None, None)),
    ]
    for text, groups in expected:
        match = REFERENCE.fullmatch(text)
        _same(match.groups() if match else None, groups, text)
    for text in ['[[ -n $x ]]', '[["b" * 64]]', '[[x, y]]', '[[]]', '[[a b]]', '[[#sec]]', '[[:foo]]']:
        _same(REFERENCE.search(text), None, text)


def _case_reference_verdicts(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/foo.md': '',
        'root/plans/tools/names.md': NAMES_PREAMBLE + '- foo\n- gone\n',
        'sibling/plans/x.md': '',
        'sibling/plans/y.md': '',
        'sibling/plans/tools/names.md': NAMES_PREAMBLE + '- x\n',
        'other/plans/z-e.md': '',
        'passwave-web/plans/w.md': '',
    })
    siblings = Siblings(root)
    _same({r: siblings.names(r).names for r in ('sibling', 'other', 'passwave-web')},
          {'sibling': frozenset({'x'}), 'other': frozenset({'z'}), 'passwave-web': frozenset({'w'})}, 'sibling names')
    _same(siblings.names('missing'), None, 'a missing sibling')
    names = set(read_names(root)[0])
    expected = {
        KNOWN: [(None, 'foo'), (None, 'gone'), ('root', 'foo')],
        UNKNOWN_NAME: [(None, 'nope'), ('root', 'nope')],
        CROSS_REPO_REF: [('sibling', 'x'), ('other', 'z'), ('sonata-passwave-web', 'w')],
        CROSS_REPO_REF_UNRESOLVED: [('sibling', 'y'), ('missing', 'q')],
    }
    for verdict, references in expected.items():
        for repo, name in references:
            _same(classify_reference(root, repo, name, names, siblings), verdict, f'{repo}:{name}')


def _case_names_file_parsing(tmp: Path) -> None:
    root = _fixture(tmp, {})
    _same(read_names(root), (None, []), 'no file')
    cases = [
        (NAMES_PREAMBLE + '- a\n- b-c\n- v0.5\n', (['a', 'b-c', 'v0.5'], [])),
        ('# Mine\n\ntext\n\n- a\n', (['a'], [])),
        ('# t\n\n- b\n- a\n- a\n- bad name\n- foo-e\n- x.md\n-c\n- d \n\ntext\n', (['b', 'a', 'a'], [
            'line 4: out of order: a',
            'line 5: duplicate: a',
            'line 6: not a name: bad name',
            'line 7: not a name: foo-e',
            'line 8: not a name: x.md',
            'line 9: not an entry: -c',
            'line 10: not a name: d ',
            'line 11: not an entry: ',
            'line 12: not an entry: text',
        ])),
    ]
    for text, expected in cases:
        _write(root / NAMES, text)
        _same(read_names(root), expected, repr(text))


def _case_register(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/b.md': '',
        'root/plans/a-e.md': '',
        'root/plans/README.md': '',
        'root/plans/followups/2026-09.md': '',
        'root/plans/archive/c-i.md': '',
    })
    names = root / NAMES
    _same(_captured(register, root),
          (0, ['registered: a', 'registered: b', 'registered: c', 'plan_links: 3 registered, 3 names']), 'first run')
    _same(names.read_bytes(), (NAMES_PREAMBLE + '- a\n- b\n- c\n').encode(), 'first register')
    _same(_captured(register, root), (0, ['plan_links: 0 registered, 3 names']), 'second run')
    _same(names.read_bytes(), (NAMES_PREAMBLE + '- a\n- b\n- c\n').encode(), 'second register')

    (root / 'plans/b.md').unlink()
    _write(root / 'plans/d.md', '')
    _write(names, '# Mine\n\nkept\n\n- a\n- b\n- c\n')
    _same(_captured(register, root), (0, ['registered: d', 'plan_links: 1 registered, 4 names']), 'kept preamble')
    _same(names.read_bytes(), b'# Mine\n\nkept\n\n- a\n- b\n- c\n- d\n', 'register keeps b')

    _write(names, '- z\n- y\n')
    _same(_captured(register, root),
          (1, ['names: line 2: out of order: y', 'refused: fix the name register first']), 'malformed')
    _same(names.read_bytes(), b'- z\n- y\n', 'malformed register unchanged')

    bad = _fixture(tmp / 'bad', {'root/plans/bad name.md': ''})
    _same(_captured(register, bad), (1, ['refused: bad name: not a name (plans/bad name.md)']), 'invalid name')
    _same((bad / NAMES).exists(), False, 'nothing written')

    empty = _fixture(tmp / 'empty', {})
    _same(_captured(register, empty), (0, ['plan_links: 0 registered, 0 names']), 'empty plans')
    _same((empty / NAMES).read_bytes(), NAMES_PREAMBLE.encode(), 'empty register')


def _case_claim(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/tools/names.md': NAMES_PREAMBLE + '- b\n'})
    names = root / NAMES
    _same(_captured(claim, root, ['c', 'a', 'c']), (0, ['claimed: c', 'claimed: a']), 'claim')
    _same(names.read_bytes(), (NAMES_PREAMBLE + '- a\n- b\n- c\n').encode(), 'claimed register')

    _same(_captured(claim, root, ['b', 'new']), (1, ['refused: b: already registered']), 'already registered')
    _same(names.read_bytes(), (NAMES_PREAMBLE + '- a\n- b\n- c\n').encode(), 'unchanged register')

    invalid = ['bad name', 'foo-e', 'x.md', 'a/b', '-x']
    _same(_captured(claim, root, invalid), (1, [f'refused: {name}: not a name' for name in invalid]), 'invalid')

    fresh = _fixture(tmp / 'fresh', {})
    _same(_captured(claim, fresh, ['x']), (0, ['claimed: x']), 'no register yet')
    _same((fresh / NAMES).read_bytes(), (NAMES_PREAMBLE + '- x\n').encode(), 'new register')

    _write(names, '- z\n- y\n')
    _same(_captured(claim, root, ['q']),
          (1, ['names: line 2: out of order: y', 'refused: fix the name register first']), 'malformed')


def _case_render_reference_labels(tmp: Path) -> None:
    expected = [
        ((None, 'foo', '', '', False), '[[foo]]'),
        ((None, 'foo', '', 'foo', False), '[[foo]]'),
        ((None, 'foo', '', '`foo-e.md`', False), '[[foo]]'),
        ((None, 'foo', '', '**foo**', False), '[[foo]]'),
        ((None, 'foo', '', 'archive/foo-e-i.md:210-220', False), '[[foo]]:210-220'),
        ((None, 'foo', '', '`archive/foo-e-i.md:210-220`', False), '[[foo]]:210-220'),
        ((None, 'foo', '', 'foo-e.md §4', False), '[[foo]] §4'),
        ((None, 'foo', '', 'foo §1 "DH-GM steps 3–4"', False), '[[foo]] §1 "DH-GM steps 3–4"'),
        ((None, 'foo', '#sec', 'foo.md', False), '[[foo#sec]]'),
        ((None, 'foo', '', 'ks-01', False), '[[foo|ks-01]]'),
        ((None, 'foo', '', 'ks-01', True), '[[foo\\|ks-01]]'),
        ((None, 'foo', '#sec', ' WS16 ', False), '[[foo#sec|WS16]]'),
        ((None, 'foo', '', 'foo-bar', False), '[[foo|foo-bar]]'),
        (('r', 'foo', '', 'r/plans/foo-e.md', False), '[[r:foo]]'),
        (('r', 'foo', '', 'ws3', False), '[[r:foo|ws3]]'),
        ((None, 'foo', '', '`x`', False), '[[foo|`x`]]'),
    ]
    for arguments, rendered in expected:
        _same(render_reference(*arguments), rendered, repr(arguments))


def _case_convert_rewrites_in_place_and_only_once(tmp: Path) -> None:
    before = [
        '# Title',
        'See [foo](foo.md), [two *b*](bar.md#sec-2), [guide](../docs/guide.md), [gone](gone.md) and '
        '[s](../../sibling/plans/s-e.md) here.',
        '| R1 | [unit 05](foo-e.md) | `plans/archive/bar-e.md:12` |',
        'Cite `foo-e-i.md:3-4`, `../docs/guide.md`, `[q](foo.md)` and [`foo-e.md`](https://example.com/foo.md).',
        '~~~',
        '[foo](foo.md) `foo.md`',
        '~~~',
        'last [not a link](nowhere',
    ]
    after = before[:1] + [
        'See [[foo]], [[bar#sec-2|two *b*]], [guide](../docs/guide.md), [gone](gone.md) and [[sibling:s]] here.',
        '| R1 | [[foo\\|unit 05]] | [[bar]]:12 |',
        'Cite [[foo]]:3-4, `../docs/guide.md`, `[q](foo.md)` and [`foo-e.md`](https://example.com/foo.md).',
    ] + before[4:]
    root = _fixture(tmp, {
        'root/plans/foo-e-i.md': '',
        'root/plans/archive/bar-e.md': '',
        'root/docs/guide.md': '',
        'root/plans/tools/dead-links.txt': 'gone.md\n',
        'sibling/plans/s-e.md': '[foo](foo.md)\n',
        'root/plans/a.md': '\r\n'.join(before),
    })
    _same(_convert(root), {root / 'plans/a.md': 6}, 'first conversion')
    _same((root / 'plans/a.md').read_bytes(), '\r\n'.join(after).encode('utf-8'), 'file bytes')
    _same(_convert(root), {}, 'second conversion')
    _same((tmp / 'sibling/plans/s-e.md').read_bytes(), b'[foo](foo.md)\n', 'sibling untouched')


def _case_convert_and_check_skip_followups_and_the_register(tmp: Path) -> None:
    files = {
        'root/plans/foo.md': '',
        'root/plans/tools/names.md': '# Plan names\n\n[x](foo.md) `plans/foo.md`\n\n- foo\n',
        'root/plans/followups/2026-09.md': '- **Source**: [foo](foo.md) `plans/foo.md:1` [[nope]]\n',
    }
    root = _fixture(tmp, files)
    _same(_convert(root), {}, 'conversion')
    for rel, content in files.items():
        _same((tmp / rel).read_bytes(), content.encode('utf-8'), rel)
    _same(_captured(check, root), (0, [
        'plan_links: 0 links, 0 cites, 0 plan-paths, 0 cross-repo-paths, 0 dead-unlisted, 0 unused-allowlist, '
        '0 references, 0 unknown-names, 0 cross-repo-unresolved, 0 collided-names, 0 unregistered, '
        '0 register-problems, 0 pair-problems',
    ]), 'check')


def _case_check_scopes_each_violation_class(tmp: Path) -> None:
    names_text = NAMES_PREAMBLE + '- a\n- dup\n- foo\n- dup\n'
    root = _fixture(tmp, {
        'root/plans/dup.md': '',
        'root/plans/archive/dup-i.md': '',
        'root/plans/foo-i.md': '',
        'root/plans/new.md': '',
        'root/plans/a.md': '[foo](foo.md) [[nope]] `plans/foo-i.md`\n',
        'root/plans/tools/names.md': names_text,
        'root/plans/tools/dead-links.txt': 'never-used.md\n',
        'root/plans/tools/branch-pairs.txt': 'a b\n',
    })
    second_dup = names_text.count('\n')
    links = ['plans/a.md:1: plan_path: foo.md', 'plans/a.md:1: plan_path: `plans/foo-i.md`']
    refs = ['plans/a.md:1: unknown_name: [[nope]]']
    stems = ['collided name: dup: plans/archive/dup-i.md, plans/dup.md']
    names = [f'names: line {second_dup}: duplicate: dup', 'unregistered: new: plans/new.md']
    allowlist = ['allowlist entry unused: never-used.md']
    pairs = ['pairs: line 1: expected 3 fields, got 2']
    expected = {'links': links, 'refs': refs, 'stems': stems, 'names': names, 'allowlist': allowlist, 'pairs': pairs,
                None: links + refs + stems + names + allowlist + pairs}
    for only, findings in expected.items():
        code, lines = _captured(check, root, only)
        _same((code, lines[:-1]), (1, findings), f'--only={only}')
        _same(lines[-1].startswith('plan_links: '), True, f'--only={only} summary line')

    (root / 'plans/archive/dup-i.md').unlink()
    _write(root / NAMES, NAMES_PREAMBLE + '- a\n- dup\n- foo\n- new\n')
    _write(root / ALLOWLIST, '')
    _write(root / PAIRS, '')
    _write(root / 'plans/a.md', '[[foo]] [[foo]]:3\n')
    for only in expected:
        code, lines = _captured(check, root, only)
        _same((code, lines[:-1]), (0, []), f'--only={only} once fixed')


def _case_cross_repo_references_never_gate_and_readmes_never_collide(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/a.md': '[[sibling:y]] and [[sibling:nowhere]]\n',
        'root/plans/README.md': '',
        'root/plans/sub/README.md': '',
        'root/plans/tools/names.md': NAMES_PREAMBLE + '- a\n',
        'sibling/plans/y-e.md': '',
    })
    code, lines = _captured(check, root)
    _same((code, lines[:-1]), (0, ['plans/a.md:1: cross_repo_ref_unresolved: [[sibling:nowhere]]']), 'check')


def _case_check_without_a_register(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a.md': '[[a]]\n'})
    code, lines = _captured(check, root, 'names')
    _same((code, lines[:-1]),
          (1, ['names: plans/tools/names.md is missing; run --register', 'unregistered: a: plans/a.md']), 'names')
    code, lines = _captured(check, root, 'refs')
    _same((code, lines[:-1]), (1, ['plans/a.md:1: unknown_name: [[a]]']), 'refs')


def _case_a_register_at_its_old_path_is_refused(tmp: Path) -> None:
    text = NAMES_PREAMBLE + '- a\n- gone\n'
    root = _fixture(tmp, {
        'root/plans/a.md': '[[a]] [[gone]]\n',
        'root/plans/names.md': text,
        'sibling/plans/x.md': '',
        'sibling/plans/names.md': NAMES_PREAMBLE + '- old\n- x\n',
    })
    moved = "plans/names.md is the name register's old path: git mv plans/names.md plans/tools/names.md"
    _same(read_names(root), (None, [moved]), 'read')
    code, lines = _captured(check, root, 'names')
    _same((code, lines[:-1]), (1, [f'names: {moved}', 'unregistered: a: plans/a.md']), 'check')
    _same(_captured(register, root), (1, [f'names: {moved}', 'refused: fix the name register first']), 'register')
    _same(_captured(claim, root, ['b']), (1, [f'names: {moved}', 'refused: fix the name register first']), 'claim')
    _same((root / NAMES).exists(), False, 'nothing written')
    _same((root / OLD_NAMES).read_bytes(), text.encode(), 'old register unchanged')
    _same(_captured(resolve, root, ['a', 'gone']), (1, ['plans/a.md', 'gone: unknown name']), 'resolve')
    _same(Siblings(root).names('sibling').names, frozenset({'x'}), 'a sibling at the old path')

    _write(root / NAMES, '- z\n- y\n')
    _same(read_names(root), (['z', 'y'], [moved, 'line 2: out of order: y']), 'both paths, the move first')
    _write(root / NAMES, text)
    (root / OLD_NAMES).unlink()
    _same(_captured(check, root)[0], 0, 'moved')


def _case_resolve(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/archive/foo-e-i.md': '',
        'root/plans/dup.md': '',
        'root/plans/archive/dup-i.md': '',
        'root/plans/tools/names.md': NAMES_PREAMBLE + '- dup\n- foo\n- gone\n',
        'sibling/plans/x-e.md': '',
        'sibling/plans/tools/names.md': NAMES_PREAMBLE + '- old\n- x\n',
    })
    refs = ['foo', '[[foo#sec|label]]', 'root:foo', 'gone', 'nope', 'dup',
            'sibling:x', 'sibling:old', 'sibling:nope', 'missing:x', 'a b']
    out = [
        'plans/archive/foo-e-i.md',
        'plans/archive/foo-e-i.md#sec',
        'plans/archive/foo-e-i.md',
        'gone: registered, no plan file',
        'nope: unknown name',
        'dup: 2 files: plans/archive/dup-i.md, plans/dup.md',
        str(tmp / 'sibling/plans/x-e.md'),
        'sibling:old: registered, no plan file',
        'sibling:nope: unknown name',
        'missing:x: no repo missing beside this one',
        'a b: not a reference',
    ]
    _same(_captured(resolve, root, refs), (1, out), 'resolve')
    _same(_captured(resolve, root, ['foo']), (0, ['plans/archive/foo-e-i.md']), 'resolve one')


def _case_report_and_emit_allowlist(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/foo-i.md': '',
        'root/plans/tools/names.md': NAMES_PREAMBLE + '- a\n- foo\n',
        'root/plans/tools/dead-links.txt': 'listed.md\n',
        'root/plans/a.md': '[f](foo.md#x) [g](gone.md) [m](../../.claude/memory/m.md) [s](../../sibling/missing.md) '
                           '[d](missing/doc.md) [l](listed.md) [[foo]] [[nope]] [[sibling:y]] `plans/foo-i.md`\n',
    })
    (tmp / 'sibling/plans').mkdir(parents=True)

    def row(kind, verdict, occurrences, distinct):
        return f'{kind:<6}{verdict:<24}{occurrences:>12}{distinct:>18}'

    code, lines = _captured(report, root)
    _same(code, 0, 'report exit')
    for line in [
        row('link', 'dead_listed', 1, 1),
        row('link', 'dead_unlisted', 4, 4),
        row('link', 'plan_path', 1, 1),
        row('cite', 'plan_path', 1, 1),
        f'{"total":<30}{7:>12}{7:>18}',
        'references: 1 known, 1 unknown_name, 0 cross_repo_ref, 1 cross_repo_ref_unresolved',
        'links carrying an #anchor: 1',
        'cross-repo paths by repo: none',
        'names: 2 registered, 0 unregistered, 0 problems',
    ]:
        _same(line in lines, True, f'report line {line!r} in {lines!r}')

    _same(_captured(report, root, True), (0, [
        '# Dead link targets, left as written in the prose. One literal target per line.',
        '# Claude-memory paths, 1 targets / 1 occurrences',
        '../../.claude/memory/m.md',
        '# Paths in this repo that no longer exist, 2 targets / 2 occurrences',
        'gone.md',
        'missing/doc.md',
        '# Non-plan paths in other repos, 1 targets / 1 occurrences',
        '../../sibling/missing.md',
    ]), 'emit allowlist')


def _case_folder_slug_table(tmp: Path) -> None:
    table = {'update-v1': 'update-v1', 'bench/throughput': 'bench-throughput', 'dev-v1.1': 'dev-v1-1',
             'Feature/Login_2': 'feature-login-2', '--x--': 'x', '_': '', '1.2': '1-2', 'a//b': 'a-b', 'é': ''}
    _same({branch: folder_slug(branch) for branch in table}, table, 'folder slug table')


def _case_layout_path_vectors(tmp: Path) -> None:
    # sonata-server-automation's tests/unit/classes/test_worktree_layout.py holds the same rows, and checks them
    # against its copy of this file: change both together.
    vectors = [
        ('/usr/share/nginx/sites/passwave/passwave-core', 'update-v1',
         '/usr/share/nginx/sites/passwave/worktrees/passwave-core/update-v1'),
        ('/usr/share/nginx/sites/passwave/passwave-web', 'main',
         '/usr/share/nginx/sites/passwave/worktrees/passwave-web/main'),
        ('/srv/projects/sonata-server-automation', 'master',
         '/srv/projects/worktrees/sonata-server-automation/master'),
        ('/srv/projects/sonata-server-automation/', 'feat/x',
         '/srv/projects/worktrees/sonata-server-automation/feat-x'),
        ('/usr/share/nginx/sites/lightspeed-digital', 'WS22.release_readiness',
         '/usr/share/nginx/sites/worktrees/lightspeed-digital/ws22-release-readiness'),
        ('/srv/sites/Acme_Shop', 'Feat__X--', '/srv/sites/worktrees/Acme_Shop/feat-x'),
        ('/srv/sites/shop', 'dev-v1.1', '/srv/sites/worktrees/shop/dev-v1-1'),
        ('/srv/sites/shop', 'ü-x', '/srv/sites/worktrees/shop/x'),
        ('/srv/sites/shop', 'a' * 70 + '/b', '/srv/sites/worktrees/shop/' + 'a' * 70 + '-b'),
    ]
    no_slug = ['_', '__', '+']
    _same([str(layout_path(Path(main), branch)) for main, branch, _place in vectors],
          [place for _main, _branch, place in vectors], 'layout vectors')
    _same([(folder_slug(name), layout_path(Path('/srv/sites/shop'), name)) for name in no_slug],
          [('', None)] * len(no_slug), 'no slug')


def _case_read_pairs(tmp: Path) -> None:
    root = _fixture(tmp, {})
    _same(read_pairs(root), ({}, []), 'no file')
    _write(root / PAIRS, '# which branch\n\nupdate-v1 passwave-web paddle\nupdate-v1 passwave-scan-app update-v1\n'
                         '  main other x  \n')
    _same(read_pairs(root), ({('update-v1', 'passwave-web'): 'paddle', ('update-v1', 'passwave-scan-app'): 'update-v1',
                              ('main', 'other'): 'x'}, []), 'valid')
    _write(root / PAIRS, 'a b\nupdate-v1 passwave-web paddle\nupdate-v1 passwave-web main\nx root y\nx bad/name y\n'
                         'p q r s\n')
    _same(read_pairs(root), ({('update-v1', 'passwave-web'): 'paddle'}, [
        'line 1: expected 3 fields, got 2',
        'line 3: duplicate: update-v1 passwave-web',
        'line 4: root is this repo',
        'line 5: not a repo name: bad/name',
        'line 6: expected 3 fields, got 4',
    ]), 'problems')


def _case_a_linked_worktree_names_its_main_repo(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': '', 'plans/tools/names.md': NAMES_PREAMBLE + '- one\n'})
    _sh(b, 'branch', 'x')
    b_x = _add_worktree(b, tmp / 'B-x', 'x')
    _git_repo(tmp / 'C', 'main', {'plans/c.md': ''})
    for name, dot_git in (('S', 'gitdir: ../B/.git/modules/S\n'), ('G', 'not a gitdir\n'),
                          ('R', 'gitdir: ../B/.git/worktrees/B-x\n')):
        (tmp / name / 'plans').mkdir(parents=True)
        _write(tmp / name / '.git', dot_git)
    plain = tmp / 'plain'
    plain.mkdir()

    _same([main_worktree(path) for path in (b_x, tmp / 'R', b)], [b, b, b], 'main worktrees')
    _same(repo_name(b_x), 'B', 'repo name')
    _same({path.name: is_linked_worktree(path) for path in (b_x, b, tmp / 'S', tmp / 'G', plain)},
          {'B-x': True, 'B': False, 'S': False, 'G': False, 'plain': False}, 'linked worktrees')
    for root in (b_x, b):
        _same({repo for repo, _name in sibling_index(root)}, {'C'}, f'sibling index of {root.name}')
    _same(Siblings(b).names('B-x'), None, 'a worktree is no sibling')
    _same(Siblings(b_x).names('B'), None, 'the main checkout is no sibling')

    _write(b_x / 'plans/a.md', '[[B:one]]\n')
    _same(classify_reference(b_x, 'B', 'one', {'one'}, Siblings(b_x)), KNOWN, 'verdict')
    code, lines = _captured(check, b_x, 'refs')
    _same((code, len(lines), lines[-1].startswith('plan_links: ')), (0, 1, True), 'check in the worktree')


def _case_a_tree_in_the_layout_finds_the_repos_beside_its_main_checkout(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': '', 'plans/tools/names.md': NAMES_PREAMBLE + '- one\n'})
    _sh(b, 'branch', 'x')
    b_x = _add_worktree(b, tmp / WORKTREES / 'B' / 'x', 'x')
    c = _git_repo(tmp / 'C', 'main', {'plans/c.md': ''})
    _sh(c, 'branch', 'feature')

    _same([sibling_dir(b_x), sibling_dir(b)], [tmp, tmp], 'sibling dirs')
    _same({repo for repo, _name in sibling_index(b_x)}, {'C'}, 'sibling index')
    _same(Siblings(b_x).names('C').names, frozenset({'c'}), 'sibling names')
    _write(b_x / 'plans/a.md', '[[C:c]] [[B:one]]\n')
    code, lines = _captured(check, b_x, 'refs')
    _same((code, lines[:-1]), (0, []), 'check in the tree')
    _same(_captured(resolve, b_x, ['C:c']), (0, [str(c / 'plans/c.md')]), 'resolve')
    index = index_by_stem(named_plan_files(b_x / 'plans'))
    _same(classify_cite(b_x, 'C/plans/c.md', index), (CROSS_REPO_PATH, ('C', 'c'), ''), 'cite')
    dead = Link(b_x / 'plans/a.md', 1, '../../C/missing.md', '', DEAD_UNLISTED, 'link', None)
    _same(_dead_group(b_x, dead), 2, 'a dead link into a sibling')

    _write(b_x / PAIRS, 'x C feature\n')
    _same(_captured(resolve, b_x, ['C:c']),
          (1, ['C:c: on feature, which no tree of C has checked out: plans/c.md']), 'resolve on the paired branch')

    _same(_captured(main, ['--tree', 'C', '--branch=main'], b_x), (0, [str(c)]), '--tree by name')
    _same(_captured(main, ['--tree', '.', '--branch=x'], b_x), (0, [str(b_x)]), '--tree of this tree')
    _same(_captured(main, ['--worktrees', 'C'], b_x), (0, [
        f'{c}: 0 plan-only worktrees',
        'plan_links: 1 repos, 0 plan-only worktrees, 0 removable, 0 outside the layout',
    ]), '--worktrees by name')
    _same(_captured(main, ['--tree', 'nowhere', '--branch=main'], b_x),
          (1, [f'refused: {tmp}/nowhere is not the root of a git work tree']), 'a name no repo has')


def _case_links_from_a_tree_are_followed_from_its_main_checkout(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': '', 'plans/a.md': ''})
    _sh(b, 'branch', 'x')
    b_x = _add_worktree(b, tmp / WORKTREES / 'B' / 'x', 'x')
    for rel in ('C/docs/guide.md', 'C/plans/c.md'):
        _write(tmp / rel, '')
    expected = [
        ('../../C/docs/guide.md', (OK, None)),
        (str(tmp / 'C/docs/guide.md'), (OK, None)),
        ('../../C/docs/missing.md', (DEAD_UNLISTED, None)),
        ('../../C/plans/c.md', (CROSS_REPO_PATH, ('C', 'c'))),
        ('../../B/plans/one.md', (PLAN_PATH, (None, 'one'))),
        (str(b / 'plans/one.md'), (PLAN_PATH, (None, 'one'))),
        ('one.md', (PLAN_PATH, (None, 'one'))),
    ]
    for root in (b, b_x):
        for target, verdict in expected:
            _same(_classify_in(root, 'plans/a.md', target), verdict, f'from {root}: {target}')
    _same([link_path(b_x, b_x / 'plans/a.md', target)
           for target in ('../../C/docs/guide.md', str(b / 'plans/one.md'), 'one.md')],
          [tmp / 'C/docs/guide.md', b_x / 'plans/one.md', b_x / 'plans/one.md'], 'paths from the tree')
    _same(link_path(b, b / 'plans/a.md', '../../C/x.md'), tmp / 'C/x.md', 'paths from the main checkout')


def _case_a_path_into_a_worktree_names_its_repo(tmp: Path) -> None:
    c = _git_repo(tmp / 'C', 'main', {'plans/c.md': ''})
    for name in ('x', 'y'):
        _sh(c, 'branch', name)
    c_x = _add_worktree(c, tmp / WORKTREES / 'C' / 'x', 'x')
    c_y = _add_worktree(c, tmp / 'C-y', 'y')
    gone = tmp / WORKTREES / 'C' / 'gone'
    root = _fixture(tmp, {'root/plans/a.md': ''})
    index = index_by_stem(named_plan_files(root / 'plans'))

    _same([folder_repo(path) for path in (c_x, c_y, c, gone, tmp / 'gone', tmp / WORKTREES)],
          ['C', 'C', 'C', 'C', 'gone', WORKTREES], 'folder repos')
    for folder in (c_x, c_y, gone):
        _same(cross_repo_plan(root, root / 'plans/a.md', str(folder / 'plans/c-e.md')), ('C', 'c'),
              f'a link into {folder}')
    for folder in (c_x, c_y):
        _same(classify_cite(root, str(folder / 'plans/c.md'), index), (CROSS_REPO_PATH, ('C', 'c'), ''),
              f'a cite into {folder}')
    _same(classify_cite(root, str(gone / 'plans/c.md'), index), None, 'a cite into a missing tree')
    own = index_by_stem(named_plan_files(c / 'plans'))
    _same(classify_cite(c, str(c_x / 'plans/c.md'), own), (PLAN_PATH, (None, 'c'), ''), 'a cite into its own worktree')


def _case_worktrees_and_trunks(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main')
    _sh(b, 'branch', 'x')
    _sh(b, 'branch', 'g')
    _add_worktree(b, tmp / 'B-x', 'x')
    _add_worktree(b, tmp / 'B-d', '--detach')
    shutil.rmtree(_add_worktree(b, tmp / 'B-g', 'g'))
    admin = b / '.git' / 'worktrees'

    found = worktrees(b)
    _same(found[0], Worktree(b, 'main', None, False), 'main worktree')
    _same(set(found[1:]), {Worktree(tmp / 'B-x', 'x', admin / 'B-x', False),
                           Worktree(tmp / 'B-d', None, admin / 'B-d', False),
                           Worktree(tmp / 'B-g', 'g', admin / 'B-g', True)}, 'linked worktrees')
    _same(worktrees(tmp / 'B-x'), found, 'from a linked worktree')
    plain = tmp / 'plain'
    plain.mkdir()
    _sh(tmp, 'init', '-q', '--bare', 'bare.git')
    _same([worktrees(plain), worktrees(tmp / 'bare.git')], [None, None], 'not work trees')

    both = _git_repo(tmp / 'both', 'master')
    _sh(both, 'branch', 'main')
    unborn = tmp / 'unborn'
    unborn.mkdir()
    _sh(unborn, 'init', '-q', '-b', 'main')
    repos = {'main': _git_repo(tmp / 'only-main', 'main'), 'master': _git_repo(tmp / 'only-master', 'master'),
             'both': both, 'dev': _git_repo(tmp / 'only-dev', 'dev'), 'unborn': unborn}
    _same({label: trunk(repo) for label, repo in repos.items()},
          {'main': 'main', 'master': 'master', 'both': 'main', 'dev': None, 'unborn': None}, 'trunks')
    _same([current_branch(b), current_branch(tmp / 'B-d'), current_branch(plain)], ['main', None, None],
          'current branches')


def _case_branch_names(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': '', 'plans/tools/names.md': NAMES_PREAMBLE + '- one\n- two\n'})
    _sh(b, 'branch', 'nonames')
    other = _add_worktree(b, tmp / 'B-nonames', 'nonames')
    (other / NAMES).unlink()
    for rel in ('plans/archive/three-e-i.md', 'plans/README.md', 'plans/followups/2026-10.md', 'plans/.hidden/q.md',
                'plans/names.md'):
        _write(other / rel, '')
    _commit(other)
    plain = tmp / 'plain'
    plain.mkdir()

    _same(branch_names(b, 'main'), {'one', 'two'}, 'from the register')
    _same(branch_names(b, 'nonames'), {'one', 'three'}, 'from the files')
    _same([branch_names(b, 'nope'), branch_names(plain, 'main')], [None, None], 'no branch, no repo')
    named = {('a.md',): True, ('archive', 'b-i.md'): True, ('README.md',): False, ('followups', 'x.md'): False,
             ('names.md',): False, ('tools', 'names.md'): False, ('.x', 'a.md'): False, ('tools', 'x.txt'): False}
    _same({parts: _is_named_plan(parts) for parts in named}, named, 'named plan table')


def _case_tree_finds_the_tree_holding_the_branch(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    b = _git_repo(tmp / 'B', 'main')
    for name in ('x', 'y', '_'):
        _sh(b, 'branch', name)
    b_x = _add_worktree(b, tmp / 'B-x', 'x')
    b_y = _add_worktree(b, tmp / WORKTREES / 'B' / 'y', 'y')
    b_u = _add_worktree(b, tmp / 'B-u', '_')
    note = f'note: {b_x} is outside the worktree layout, which puts x at {tmp}/{WORKTREES}/B/x'

    _same(_captured(tree, a, b, 'main', False), (0, [str(b)]), 'the main checkout')
    _same(_captured(tree, a, b, 'x', False), (0, [str(b_x), note]), 'a worktree outside the layout')
    _same(_captured(tree, a, b, 'y', False), (0, [str(b_y)]), 'a worktree in the layout')
    _same(_captured(tree, a, b, '_', False),
          (0, [str(b_u), f'note: {b_u} is outside the worktree layout, which has no folder for _']), 'no folder')
    _same(_captured(tree, a, b_x, 'main', False), (0, [str(b)]), 'named by its worktree')
    _same(_captured(tree, a, b, 'x', True), (0, [str(b_x), note]), 'nothing to create')
    _sh(b, 'checkout', '-q', '-b', 'q')
    _same(_captured(tree, a, b, 'q', False), (0, [str(b)]), 'a branch in place in the main checkout')

    folder = tmp / WORKTREES / 'B'
    (tmp / 'link').symlink_to(folder / 'y')
    cases = {
        'at its place': (folder / 'y', 'y', False),
        'through a symlink': (tmp / 'link', 'y', False),
        'beside the clone': (tmp / 'B-y', 'y', True),
        "at another branch's place": (folder / 'y', 'x', True),
        'detached in the folder': (folder / 'anything', None, False),
        'detached elsewhere': (tmp / 'elsewhere', None, True),
        'detached deeper in the folder': (folder / 'a' / 'b', None, True),
        'no slug in the folder': (folder / 'x', '_', False),
        'no slug elsewhere': (tmp / 'x', '_', True),
        'the main checkout': (b, 'q', False),
    }
    _same({label: outside_layout(b, Worktree(path, branch, None, False)) for label, (path, branch, _) in cases.items()},
          {label: outside for label, (_path, _branch, outside) in cases.items()}, 'outside the layout')


def _case_tree_creates_a_plan_only_worktree_when_asked(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    b = _git_repo(tmp / 'B', 'main')
    for name in ('y', 'w', 'feat/One_2'):
        _sh(b, 'branch', name)
    hook = b / '.git' / 'hooks' / 'post-checkout'
    _write(hook, '#!/bin/sh\ntouch "$PWD/HOOK-RAN"\n')
    hook.chmod(0o755)
    layout = tmp / WORKTREES / 'B'
    b_y = layout / 'y'

    _same(_captured(tree, a, b, 'y', False),
          (3, [f'would create: {b_y} on y. Ask, then run again with --create.']), 'would create')
    _same(((tmp / WORKTREES).exists(), len(worktrees(b))), (False, 1), 'nothing created')
    _same(_captured(tree, a, b, 'y', True), (0, [
        str(b_y),
        f'created: plan-only worktree of {b} on y; commit there. While it holds y, git checks y out nowhere else: '
        f'git -C {b} worktree remove {b_y}',
        'trust: git run by another account refuses this tree, which this account owns, unless that account '
        f'trusts it: git config --global --add safe.directory {b_y}',
    ]), 'create')
    _same(current_branch(b_y), 'y', 'branch of the new worktree')
    marker = b / '.git' / 'worktrees' / 'y' / 'plan-only'
    _same(marker.is_file() and marker.read_text(encoding='utf-8').startswith(
        'plan-only worktree made by plan_links.py --tree on '), True, 'marker')
    _same((b_y / 'HOOK-RAN').exists(), False, 'no hook ran')
    _same(_captured(tree, a, b, 'y', False), (0, [str(b_y)]), 'found once made')
    _same(_captured(tree, a, b, 'feat/One_2', False),
          (3, [f'would create: {layout}/feat-one-2 on feat/One_2. Ask, then run again with --create.']), 'slug')

    marker_name = globals()['MARKER']
    globals()['MARKER'] = 'missing/plan-only'
    try:
        code, lines = _captured(tree, a, b, 'w', True)
    finally:
        globals()['MARKER'] = marker_name
    _same((code, len(lines),
           lines[0].startswith(f'refused: {layout}/w was created, but its plan-only marker could not be written: ')),
          (1, 1, True), f'marker fails: {lines}')
    _same(_captured(tree, a, b, 'w', False), (0, [
        f'{layout}/w',
        f'removable: {b_y} (y): clean, merged into main; git -C {b} worktree remove {b_y}',
    ]), 'a worktree without its marker')
    _same(_captured(report_worktrees, [b])[1][0], f'{b}: 1 plan-only worktrees', 'only the marked one')


def _case_tree_creates_the_layout_folders(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    proj = tmp / 'proj'
    b = _git_repo(proj / 'B', 'main')
    for name in ('y', 'z'):
        _sh(b, 'branch', name)
    proj.chmod(0o2750)
    folders = [proj / WORKTREES, proj / WORKTREES / 'B']
    real_chown = os.chown
    calls = []

    def recorded(path, uid, gid):
        calls.append((Path(path), uid, gid))
        real_chown(path, uid, gid)

    os.chown = recorded
    try:
        code = _captured(tree, a, b, 'y', True)[0]
    finally:
        os.chown = real_chown
    _same(code, 0, 'create')
    _same([folder.stat().st_mode & 0o7777 for folder in folders], [0o2750, 0o2750], 'the containing mode')
    _same(calls, [(folder, -1, proj.stat().st_gid) for folder in folders], 'the containing group')
    folders[1].chmod(0o700)
    _same(_captured(tree, a, b, 'z', True)[0], 0, 'create beside')
    _same(folders[1].stat().st_mode & 0o7777, 0o700, 'a folder already there keeps its mode')

    c = _git_repo(tmp / 'C', 'main')
    _sh(c, 'branch', 'u')
    admin = c / '.git' / 'worktrees'
    admin.mkdir()
    admin.chmod(0o500)
    try:
        result = _captured(tree, a, c, 'u', True)
    finally:
        admin.chmod(0o700)
    _same(result, (1, ["refused: git worktree add failed: fatal: could not create directory of "
                       "'.git/worktrees/u': Permission denied"]), 'git fails')
    _same((tmp / WORKTREES).exists(), False, 'the folders it made are removed')

    d = _git_repo(tmp / 'locked' / 'D', 'main')
    _sh(d, 'branch', 'v')
    (tmp / 'locked').chmod(0o500)
    try:
        result = _captured(tree, a, d, 'v', True)
    finally:
        (tmp / 'locked').chmod(0o700)
    _same(result, (1, [f'refused: {tmp}/locked/{WORKTREES} could not be created: Permission denied']), 'no folder')

    half = tmp / 'half'
    e = _git_repo(half / 'E', 'main')
    _sh(e, 'branch', 'v')

    def refused(path, uid, gid):
        if Path(path).name == 'E':
            raise PermissionError(1, 'Operation not permitted', str(path))
        real_chown(path, uid, gid)

    os.chown = refused
    try:
        code = _captured(tree, a, e, 'v', True)[0]
    finally:
        os.chown = real_chown
    _same((code, (half / WORKTREES / 'E' / 'v').is_dir(), (half / WORKTREES / 'E').stat().st_mode & 0o7777),
          (0, True, half.stat().st_mode & 0o7777), 'a refused chown keeps the folder, with the mode')

    full = tmp / 'full'
    _write(full / 'kept.txt', '')
    _remove_folders([full, tmp / 'absent'])
    _same(full.is_dir(), True, 'a folder that cannot go is left')

    f = _git_repo(tmp / 'filed' / 'F', 'main')
    _sh(f, 'branch', 'v')
    _write(tmp / 'filed' / WORKTREES, '')
    _same(_captured(tree, a, f, 'v', True),
          (1, [f'refused: {tmp}/filed/{WORKTREES} could not be created: File exists']), 'a file in the way')


def _case_tree_tracks_a_remote_only_branch(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    origin = _git_repo(tmp / 'origin', 'main')
    _sh(origin, 'branch', 'r')
    _sh(origin, 'branch', 's')
    o2 = _git_repo(tmp / 'O2', 's')
    b = tmp / 'B'
    _sh(tmp, 'clone', '-q', str(origin), str(b))
    _sh(b, 'remote', 'add', 'other', str(o2))
    _sh(b, 'fetch', '-q', 'other')

    _same(_captured(tree, a, b, 'r', False), (3, [
        f'would create: {tmp}/{WORKTREES}/B/r on r, a new local branch tracking origin/r as of the last fetch. '
        'Ask, then run again with --create.',
    ]), 'would create')
    _same(_captured(tree, a, b, 'r', True)[0], 0, 'create')
    _same(_git(b, 'rev-parse', '--abbrev-ref', 'r@{upstream}').stdout.strip(), 'origin/r', 'upstream')
    _same(_captured(tree, a, b, 's', True),
          (1, [f'refused: s is on more than one remote of {b} (origin/s, other/s): create the local branch first']),
          'two remotes')
    _same(_captured(tree, a, b, 'nope', True), (1, [f'refused: nope is no branch of {b}, local or remote-tracking']),
          'no branch')
    _same([(tmp / WORKTREES / 'B' / 's').exists(), (tmp / WORKTREES / 'B' / 'nope').exists()], [False, False],
          'nothing created')


def _case_tree_refusals(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': ''})
    for name in ('_', 'p', 'q', 'z', 'w'):
        _sh(b, 'branch', name)
    plain = tmp / 'plain'
    plain.mkdir()
    _sh(tmp, 'init', '-q', '--bare', 'bare.git')

    for repo in (plain, tmp / 'bare.git', b / 'plans'):
        _same(_captured(tree, a, repo, 'main', False), (1, [f'refused: {repo} is not the root of a git work tree']),
              repo.name)
    _same(_captured(tree, a, b, '_', False), (1, ['refused: branch _ gives no folder name']), 'empty slug')
    (tmp / WORKTREES / 'B' / 'p').mkdir(parents=True)
    _same(_captured(tree, a, b, 'p', False),
          (1, [f'refused: {tmp}/{WORKTREES}/B/p exists and does not have p checked out']), 'a plain folder')
    _add_worktree(b, tmp / WORKTREES / 'B' / 'q', 'z')
    _same(_captured(tree, a, b, 'q', False),
          (1, [f'refused: {tmp}/{WORKTREES}/B/q exists and does not have q checked out']),
          'a worktree on another branch')
    shutil.rmtree(_add_worktree(b, tmp / 'elsewhere' / 'w', 'w'))
    _same(_captured(tree, a, b, 'w', False), (1, [
        f'refused: w is held by {tmp}/elsewhere/w, a worktree whose folder is missing: git -C {b} worktree prune',
    ]), 'a missing folder')
    inner = _git_repo(tmp / 'nest' / WORKTREES, 'main')
    _sh(inner, 'branch', 'p')
    _same(_captured(tree, a, inner, 'p', False),
          (1, [f'refused: the layout puts p at {inner}/{WORKTREES}/p, inside the git work tree {inner}']),
          'a main checkout named worktrees')
    beside = _git_repo(tmp / 'side' / 'S', 'main')
    _sh(beside, 'branch', 'p')
    other = _git_repo(tmp / 'side' / WORKTREES, 'main')
    _same(_captured(tree, a, beside, 'p', False),
          (1, [f'refused: the layout puts p at {other}/S/p, inside the git work tree {other}']),
          'a repo named worktrees beside it')
    _same(len(worktrees(b)), 3, 'nothing created')


def _case_tree_follows_the_pairing(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main')
    _sh(b, 'branch', 'x')
    b_x = _add_worktree(b, tmp / WORKTREES / 'B' / 'x', 'x')
    a = _git_repo(tmp / 'A', 'main', {'plans/a.md': ''})
    _sh(a, 'branch', 'a1')
    _sh(a, 'branch', 'a2')
    _write(a / PAIRS, 'a1 B x\n')
    d = _git_repo(tmp / 'D', 'dev')

    _sh(a, 'checkout', '-q', 'a1')
    _same(_captured(tree, a, b, None, False), (0, [str(b_x)]), 'paired')
    _sh(a, 'checkout', '-q', 'main')
    _same(_captured(tree, a, b, None, False), (0, [str(b)]), 'trunk to trunk')
    _sh(a, 'checkout', '-q', 'a2')
    _same(_captured(tree, a, b, None, False), (1, [
        'refused: A is on a2, which pairs with no branch of B in plans/tools/branch-pairs.txt: ask which branch, '
        'and add the line "a2 B <branch>"',
    ]), 'unpaired')
    _sh(a, 'checkout', '-q', '--detach')
    _same(_captured(tree, a, b, None, False),
          (1, [f'refused: {a} is not on a branch: name the branch with --branch']), 'detached')
    _same(_captured(tree, a / 'plans', b, None, False), (1, [
        f'refused: {a}/plans is not the root of a git work tree: run from the root of the repo you work in, '
        'or name the branch with --branch',
    ]), 'a subdirectory')
    _sh(a, 'checkout', '-q', 'main')
    _same(_captured(tree, a, d, None, False), (1, [
        'refused: D has neither main nor master: ask which branch, and add the line "main D <branch>" to '
        'plans/tools/branch-pairs.txt',
    ]), 'no trunk')
    _write(a / PAIRS, 'a1 B\n')
    _same(_captured(tree, a, b, None, False),
          (1, ['refused: plans/tools/branch-pairs.txt: line 1: expected 3 fields, got 2; fix it first']), 'malformed')
    _same(_captured(tree, a, b, 'main', False), (0, [str(b)]), 'named despite the malformed file')


def _case_worktrees_report(tmp: Path) -> None:
    a = _git_repo(tmp / 'A', 'main')
    origin = _git_repo(tmp / 'origin', 'main')
    _sh(origin, 'branch', 'u')
    b = tmp / 'B'
    _sh(tmp, 'clone', '-q', str(origin), str(b))
    for name in ('m', 'd', 'c', 'k', 'e', 'n'):
        _sh(b, 'branch', name)
    for name in ('m', 'd', 'c', 'k', 'e', 'u'):
        _same(_captured(tree, a, b, name, True)[0], 0, f'create {name}')
    layout = tmp / WORKTREES / 'B'
    _write(layout / 'd' / 'new.txt', '')
    _write(layout / 'c' / 'c.txt', 'c')
    _commit(layout / 'c')
    _write(layout / 'u' / 'u.txt', 'u')
    _commit(layout / 'u')
    _sh(origin, 'branch', '-D', 'u')
    _sh(b, 'fetch', '-q', '--prune')
    shutil.rmtree(layout / 'k')
    _sh(layout / 'e', 'checkout', '-q', '--detach')
    _sh(b, 'worktree', 'move', str(layout / 'c'), str(tmp / 'B-c'))
    _add_worktree(b, tmp / 'B-n', 'n')
    plain = tmp / 'plain'
    plain.mkdir()

    _same(_captured(report_worktrees, [b, plain]), (1, [
        f'{b}: 6 plan-only worktrees',
        f'  {tmp}/B-c (c): clean; outside the layout',
        f'  {layout}/d (d): 1 uncommitted',
        f'  {layout}/e (no branch): clean, on no branch; remove: git -C {b} worktree remove {layout}/e',
        f'  {layout}/k (k): folder missing; prune: git -C {b} worktree prune',
        f'  {layout}/m (m): clean, merged into main; remove: git -C {b} worktree remove {layout}/m',
        f'  {layout}/u (u): clean, upstream gone; remove: git -C {b} worktree remove {layout}/u',
        f'refused: {plain} is not the root of a git work tree',
        'plan_links: 1 repos, 6 plan-only worktrees, 4 removable, 1 outside the layout',
    ]), 'report')
    _same(_captured(tree, a, b, 'main', False), (0, [
        str(b),
        f'removable: {layout}/e (no branch): clean, on no branch; git -C {b} worktree remove {layout}/e',
        f'removable: {layout}/k (k): folder missing; git -C {b} worktree prune',
        f'removable: {layout}/m (m): clean, merged into main; git -C {b} worktree remove {layout}/m',
        f'removable: {layout}/u (u): clean, upstream gone; git -C {b} worktree remove {layout}/u',
    ]), 'tree repeats the removable ones')


def _case_cross_repo_references_follow_the_paired_branch(tmp: Path) -> None:
    b = _git_repo(tmp / 'B', 'main', {'plans/one.md': '', 'plans/tools/names.md': NAMES_PREAMBLE + '- one\n'})
    _sh(b, 'checkout', '-q', '-b', 'x')
    _write(b / 'plans/two.md', '')
    _write(b / NAMES, NAMES_PREAMBLE + '- lost\n- one\n- two\n')
    _commit(b)
    _sh(b, 'checkout', '-q', '-b', 'y', 'main')
    _write(b / NAMES, NAMES_PREAMBLE + '- one\n- why\n')
    _commit(b)
    a = _git_repo(tmp / 'A', 'main', {'plans/a.md': '[[B:one]] [[B:two]] [[B:why]] [[B:four]]\n',
                                      'plans/tools/names.md': NAMES_PREAMBLE + '- a\n'})
    _sh(a, 'branch', 'a1')
    _sh(a, 'branch', 'a2')

    def refs(row: str, names: list[str], scope: str) -> None:
        code, lines = _captured(check, a, 'refs')
        expected = [f'plans/a.md:1: cross_repo_ref_unresolved: [[B:{name}]]{scope}' for name in names]
        _same((code, lines[:-1]), (0, expected), row)

    refs('trunk to trunk', ['two', 'why', 'four'], ' on main')
    _sh(a, 'checkout', '-q', 'a1')
    _write(a / PAIRS, 'a1 B x\n')
    refs('paired, from git', ['why', 'four'], ' on x')
    _same(_captured(resolve, a, ['B:two', 'B:lost', 'B:why']), (1, [
        'B:two: on x, which no tree of B has checked out: plans/two.md',
        'B:lost: registered on x, no plan file',
        'B:why: unknown name on x',
    ]), 'resolve from git')
    b_x = _add_worktree(b, tmp / 'B-x', 'x')
    _write(b_x / NAMES, NAMES_PREAMBLE + '- four\n- lost\n- one\n- two\n')
    refs('paired, from the worktree', ['why'], ' on x')
    _same(_captured(resolve, a, ['B:two']), (0, [f'{b_x}/plans/two.md']), 'resolve in the worktree')
    _write(a / PAIRS, 'a1 B gone\n')
    refs('paired with a missing branch', ['one', 'two', 'why', 'four'], ' on gone (no such branch)')
    _same(_captured(resolve, a, ['B:one']), (1, ['B:one: B has no branch gone']), 'resolve a missing branch')
    _sh(a, 'checkout', '-q', 'a2')
    _write(a / PAIRS, 'a1 B x\n')
    refs('unpaired', ['two', 'four'], '')


def _case_cli_dispatch_and_usage_errors(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/a.md': '[a](a.md)\n',
        'root/plans/tools/names.md': NAMES_PREAMBLE + '- a\n',
    })
    _same(_captured(main, ['--convert'], root), (0, ['plans/a.md: 1 converted', 'plan_links: 1 converted in 1 files']),
          '--convert')
    for argv, code in [
        (['--check'], 0),
        (['--check', '--only=names'], 0),
        (['--register'], 0),
        (['--claim', 'z'], 0),
        (['--resolve', 'z'], 1),
        (['--report'], 0),
        (['--report', '--emit-allowlist'], 0),
        (['--tree', str(root / 'nogit')], 1),
        (['--tree', str(root), '--branch=main'], 1),
        (['--worktrees', str(root)], 1),
    ]:
        _same(_captured(main, argv, root)[0], code, ' '.join(argv))

    for argv in ([], ['--only=links'], ['--check', '--emit-allowlist'], ['--report', '--only=links'],
                 ['--claim'], ['--check', '--convert'], ['--branch=x', '--check'], ['--create', '--check'],
                 ['--tree'], ['--worktrees'], ['--check', '--tree', 'x']):
        errors = io.StringIO()
        try:
            with contextlib.redirect_stderr(errors), contextlib.redirect_stdout(io.StringIO()):
                main(argv, root)
        except SystemExit as exc:
            _same(exc.code, 2, f'{argv} exit code')
            _same('usage:' in errors.getvalue(), True, f'{argv} usage')
        else:
            raise AssertionError(f'{argv}: no usage error')


def _case_runner_and_repo_root(tmp: Path) -> None:
    def ok(_tmp: Path) -> None:
        return None

    def boom(_tmp: Path) -> None:
        raise AssertionError('boom')

    _same(_captured(_run_cases, (ok, boom)),
          (1, ['case 1: ok', 'case 2: FAIL boom: AssertionError: boom', 'selftest: 1 passed, 1 failed']), 'runner')
    _same(repo_root(), Path(__file__).resolve().parents[2], 'repo root')


SELFTEST_CASES = (
    _case_stem_strips_only_a_trailing_run_of_segments,
    _case_named_plans_exclude_readmes_the_register_and_followups,
    _case_code_and_fences_hide_links_cites_and_references,
    _case_link_to_an_existing_file,
    _case_broken_link_with_a_plan_name_is_a_plan_path,
    _case_unknown_target_fails_closed,
    _case_allowlisted_target_is_dead_listed,
    _case_cross_repo_plan_paths,
    _case_cites_classified_by_path_shape,
    _case_references_parse_every_form,
    _case_reference_verdicts,
    _case_names_file_parsing,
    _case_register,
    _case_claim,
    _case_render_reference_labels,
    _case_convert_rewrites_in_place_and_only_once,
    _case_convert_and_check_skip_followups_and_the_register,
    _case_check_scopes_each_violation_class,
    _case_cross_repo_references_never_gate_and_readmes_never_collide,
    _case_check_without_a_register,
    _case_a_register_at_its_old_path_is_refused,
    _case_resolve,
    _case_report_and_emit_allowlist,
    _case_folder_slug_table,
    _case_layout_path_vectors,
    _case_read_pairs,
    _case_a_linked_worktree_names_its_main_repo,
    _case_a_tree_in_the_layout_finds_the_repos_beside_its_main_checkout,
    _case_links_from_a_tree_are_followed_from_its_main_checkout,
    _case_a_path_into_a_worktree_names_its_repo,
    _case_worktrees_and_trunks,
    _case_branch_names,
    _case_tree_finds_the_tree_holding_the_branch,
    _case_tree_creates_a_plan_only_worktree_when_asked,
    _case_tree_creates_the_layout_folders,
    _case_tree_tracks_a_remote_only_branch,
    _case_tree_refusals,
    _case_tree_follows_the_pairing,
    _case_worktrees_report,
    _case_cross_repo_references_follow_the_paired_branch,
    _case_cli_dispatch_and_usage_errors,
    _case_runner_and_repo_root,
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        self.exit(2, f'plan_links.py: {message}; usage: {USAGE}\n')


def repo_argument(here: Path, text: str) -> Path:
    path = (here / text).resolve()
    if '/' in text or path.is_dir():
        return path
    return (sibling_dir(here) / text).resolve()


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = _Parser(prog='plan_links.py', usage=USAGE, description=__doc__.split('\n\n')[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='exit 1 on any gating violation')
    mode.add_argument('--convert', action='store_true', help='rewrite path references to plans as names')
    mode.add_argument('--register', action='store_true',
                      help=f'add every unregistered plan name to {NAMES.as_posix()}')
    mode.add_argument('--claim', nargs='+', metavar='NAME', help='register new names before their files exist')
    mode.add_argument('--resolve', nargs='+', metavar='REF', help="print each reference's current file")
    mode.add_argument('--tree', metavar='REPO', help="print the tree to write in for REPO's branch")
    mode.add_argument('--worktrees', nargs='+', metavar='REPO', help='list plan-only worktrees and which can go')
    mode.add_argument('--report', action='store_true', help='print a summary table; always exit 0')
    mode.add_argument('--selftest', action='store_true', help='run the built-in fixtures')
    parser.add_argument('--only', choices=CHECK_CLASSES, help='with --check: one violation class')
    parser.add_argument('--emit-allowlist', action='store_true',
                        help='with --report: print the dead-links.txt content')
    parser.add_argument('--branch', help='with --tree: this branch, not the paired one')
    parser.add_argument('--create', action='store_true',
                        help='with --tree: create the worktree when no tree has the branch')
    args = parser.parse_args(argv)
    if args.only and not args.check:
        parser.error('--only is accepted only with --check')
    if args.emit_allowlist and not args.report:
        parser.error('--emit-allowlist is accepted only with --report')
    if args.branch is not None and not args.tree:
        parser.error('--branch is accepted only with --tree')
    if args.create and not args.tree:
        parser.error('--create is accepted only with --tree')

    if args.selftest:
        return selftest()
    if args.tree or args.worktrees:
        here = (root or Path.cwd()).resolve()
        if args.tree:
            return tree(here, repo_argument(here, args.tree), args.branch, args.create)
        return report_worktrees([repo_argument(here, text) for text in args.worktrees])
    root = root or repo_root()
    if args.check:
        return check(root, args.only)
    if args.convert:
        return convert(root)
    if args.register:
        return register(root)
    if args.claim:
        return claim(root, args.claim)
    if args.resolve:
        return resolve(root, args.resolve)
    return report(root, args.emit_allowlist)


if __name__ == '__main__':
    sys.exit(main())
