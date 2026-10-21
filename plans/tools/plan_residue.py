"""Record which implemented plans have had their residue processed, and gate the register.

A plan is implemented when the trailing run of -e/-i segments in its filename includes
-i. plans/followups/ledger.txt holds one line per implemented plan whose residue is in
the follow-up register, whether or not it left an entry:

    <stem> <YYYY-MM-DD> <backfill|implement> <entries>

The register is the trunk's month files, plans/followups/<YYYY-MM>.md, and the register
of every other branch, plans/followups/branches/<segment>/<YYYY-MM>.md, whose ids carry
the segment. The trunk is the branch named main, or master where there is no main.
entries counts the lines in this repo's month files that name the plan as their source:
entries whose Source path starts plans/, and pointers to entries written into other
repos. `check` fails while an implemented plan under plans/archive/ has no line, a line
names no implemented plan, a count disagrees with the month files, a ledger line is
malformed or out of order, a month file breaks plans/followups/README.md's schema, or a
folder under plans/followups/branches/ names no segment. `next-id` prints the month file
and the next id for the branch a repo has checked out.

The same file is vendored unchanged beside plan_links.py in every repo with a register,
so it holds no per-repo configuration. The /plan-extract-followups and
/plan-review-followups skills import it from the repo they run in, and may use only these
names: FOLLOWUPS, BRANCHES, LEDGER, MONTH_FILE, SEGMENT, ID, STATUSES, FLAVOURS,
SEVERITY_HEADINGS, BIRTH_STATUS, ENTRY_FIELDS, NEW_THIS_MONTH, PREAMBLE, LedgerLine,
MonthFile, Register, today, repo_root, implemented_plans, archived_plans, read_ledger,
format_ledger, write_ledger, parse_month_text, parse_month_file, month_files,
register_counts, fid, preamble, segment_of, register_for, ledger_or_refuse, relative,
iso_date.

    python3 plans/tools/plan_residue.py check [--only=format|coverage|counts|register]
    python3 plans/tools/plan_residue.py record STEM... --how=backfill|implement [--date=D] [--none-registered]
    python3 plans/tools/plan_residue.py recount STEM...
    python3 plans/tools/plan_residue.py validate [PATH...]
    python3 plans/tools/plan_residue.py next-id [--month=YYYY-MM] [--repo=PATH]
    python3 plans/tools/plan_residue.py selftest
"""

import argparse
import contextlib
import datetime
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

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_links import plan_files, stem  # noqa: E402

FOLLOWUPS = Path('plans') / 'followups'
BRANCHES = FOLLOWUPS / 'branches'
LEDGER = FOLLOWUPS / 'ledger.txt'
MONTH_FILE = re.compile(r'^(\d{4}-\d{2})\.md$')
YEAR_MONTH = re.compile(r'\d{4}-(?:0[1-9]|1[0-2])')
SEGMENT = r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*'
ID = r'FU-\d{4}-\d{2}-(?:' + SEGMENT + r'-)?\d{3}'
STATUSES = ('open', 'done', 'superseded', 'accepted-limitation', 'handed-over', 'non-goal')
FLAVOURS = ('non-goal', 'deferred', 'owned-elsewhere', 'ordering', 'limitation', 'open-question', 'handover')
SEVERITY_HEADINGS = {
    'S1': 'S1 — security · privacy · data-integrity · compliance',
    'S2': 'S2 — correctness',
    'S3': 'S3 — UX',
    'S4': 'S4 — cleanliness',
}
BIRTH_STATUS = {'non-goal': 'non-goal', 'limitation': 'accepted-limitation'}
HOWS = ('backfill', 'implement')
CHECK_CLASSES = ('format', 'coverage', 'counts', 'register')
ENTRY_FIELDS = ('Status', 'Severity', 'Flavour', 'Owner', 'Source', 'Summary', 'Quote')

HEADING = re.compile(r'^### FU-(\d{4}-\d{2})-(?:(' + SEGMENT + r')-)?(\d{3}) · (.*)$')
FIELD = re.compile(r'^- \*\*(\w+)\*\*: ?(.*)$')
SOURCE = re.compile(r'^`([^`]+)` .*?(?<![\w/.-])((?:\w[\w.-]*/)?plans/[^\s`]*?\.md):(\d+)(?!\w)')
POINTER = re.compile(r'^- `([^`]+)` .* → \*\*([^*]+)\*\* (' + ID + r') \((S[1-4]), ([a-z-]+)\)$')
POINTER_LIKE = re.compile(r'^- `[^`]+` .*→ \*\*')
CONFLICT_MARKER = re.compile(r'^(?:<{7}|\|{7}|={7}|>{7})(?: |$)')
OWNER = re.compile(r'-|[\w.-]+')
RESIDUE_HEADING = re.compile(r'^##\s+(?:[\d.]+\s*·\s*)?Residue\s*$')
TABLE_SEPARATOR = re.compile(r'^\|(?:\s*:?-+:?\s*\|)+\s*$')
LIST_ITEM = re.compile(r'^(?:[-*+]|\d+[.)])\s')
FENCE_MARKERS = ('```', '~~~')
NEW_THIS_MONTH = '## New this month'

PREAMBLE = """# Follow-ups — {month}

Entries are appended by `/plan-implement`. An entry is closed by editing its
own **Status** line in place, never by adding a note in a later month.
Open items: `grep -rn '^- \\*\\*Status\\*\\*: open' plans/followups/`

Schema, severity tiers and flavours: `plans/followups/README.md`.

---
"""

LEDGER_HEADER = """# Residue ledger: one line per implemented plan whose residue has been processed into
# this repo's follow-up register, sorted by stem.
#   <stem> <YYYY-MM-DD processed> <backfill|implement> <entries>
# entries counts month-file lines naming the plan as source; a plan merged into an
# earlier plan's entry after "; also" counts 0. Add lines with plan_residue.py record.
"""

USAGE = ' | '.join(line.strip() for line in __doc__.splitlines() if line.startswith('    python3 '))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def is_implemented(name: str) -> bool:
    if not name.endswith('.md') or name == 'README.md':
        return False
    base = name[:-len('.md')]
    implemented = False
    while base.endswith(('-e', '-i')):
        implemented = implemented or base.endswith('-i')
        base = base[:-len('-i')]
    return implemented


def implemented_plans(root: Path) -> dict[str, list[Path]]:
    plans: dict[str, list[Path]] = {}
    for path in plan_files(root / 'plans'):
        if is_implemented(path.name):
            plans.setdefault(stem(path.name), []).append(path)
    return plans


def archived_plans(root: Path) -> dict[str, list[Path]]:
    archive = root / 'plans' / 'archive'
    narrowed = {name: [path for path in paths if archive in path.parents]
                for name, paths in implemented_plans(root).items()}
    return {name: paths for name, paths in narrowed.items() if paths}


@dataclass
class LedgerLine:
    stem: str
    date: str
    how: str
    entries: int
    line_no: int


def read_ledger(root: Path) -> tuple[list[LedgerLine], list[str]]:
    path = root / LEDGER
    if not path.is_file():
        return [], []
    lines: list[LedgerLine] = []
    findings: list[str] = []
    first_at: dict[str, int] = {}
    for line_no, text in enumerate(path.read_text(encoding='utf-8').split('\n'), start=1):
        if not text.strip() or text.lstrip().startswith('#'):
            continue
        where = f'{LEDGER.as_posix()}:{line_no}: '
        fields = text.split()
        if len(fields) != 4:
            findings.append(f'{where}expected 4 fields, got {len(fields)}')
            continue
        name, date, how, entries = fields
        problems = []
        if name.endswith('.md') or '/' in name or stem(name + '.md') != name:
            problems.append(f'bad stem: {name}')
        if not _is_date(date):
            problems.append(f'bad date: {date}')
        if how not in HOWS:
            problems.append(f'bad how: {how}')
        if not re.fullmatch(r'\d+', entries):
            problems.append(f'bad entries: {entries}')
        findings.extend(where + problem for problem in problems)
        if problems:
            continue
        if name in first_at:
            findings.append(f'{where}duplicate stem: {name} (first at line {first_at[name]})')
            continue
        first_at[name] = line_no
        if lines and name < lines[-1].stem:
            findings.append(f'{where}out of order: {name} after {lines[-1].stem}')
        lines.append(LedgerLine(name, date, how, int(entries), line_no))
    return lines, findings


def format_ledger(lines) -> str:
    body = ''.join(f'{line.stem} {line.date} {line.how} {line.entries}\n'
                   for line in sorted(lines, key=lambda line: line.stem))
    return LEDGER_HEADER + body


def write_ledger(root: Path, lines) -> None:
    (root / FOLLOWUPS).mkdir(parents=True, exist_ok=True)
    (root / LEDGER).write_bytes(format_ledger(lines).encode('utf-8'))


@dataclass
class Entry:
    number: int
    month: str
    title: str
    fields: dict[str, str]
    line_no: int
    source_stem: str | None
    source_local: bool
    segment: str | None = None


@dataclass
class MonthFile:
    label: str
    month: str
    entries: list[Entry]
    pointers: list[tuple[int, str]]
    errors: list[str]
    segment: str | None = None


def parse_month_text(text: str, month: str, label: str, segment: str | None = None) -> MonthFile:
    lines = text.split('\n')
    parsed = MonthFile(label, month, [], [], [], segment)
    errors: list[tuple[int, str]] = [(number, 'merge conflict marker')
                                     for number, line in enumerate(lines, start=1) if CONFLICT_MARKER.match(line)]
    inside: set[int] = set()
    for start, line in enumerate(lines):
        if line.startswith('### FU-'):
            end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('#')), len(lines))
            inside.update(range(start, end))
            _parse_entry(lines, start, end, month, parsed, errors)

    for index, line in enumerate(lines):
        if index in inside:
            continue
        if line.startswith('- **Status**: '):
            errors.append((index + 1, 'status line outside an entry'))
        pointer = POINTER.match(line)
        if pointer:
            parsed.pointers.append((index + 1, pointer.group(1)))
        elif POINTER_LIKE.match(line):
            errors.append((index + 1, f'malformed pointer: {line}'))

    seen: dict[int, int] = {}
    for entry in parsed.entries:
        if entry.segment != segment:
            continue
        if entry.number in seen:
            errors.append((entry.line_no, f'duplicate id {fid(entry.month, entry.number, entry.segment)}'))
        seen.setdefault(entry.number, entry.line_no)
    missing = [n for n in range(min(seen, default=1), max(seen, default=0) + 1) if n not in seen]
    if missing:
        where = min(line_no for number, line_no in seen.items() if number > missing[0])
        errors.append((where, 'ids not gapless: missing ' + ', '.join(f'{n:03d}' for n in missing[:5])))

    parsed.errors = [f'{label}:{line_no}: {message}' for line_no, message in sorted(errors, key=lambda e: e[0])]
    return parsed


def fid(month: str, number: int, segment: str | None = None) -> str:
    return f'FU-{month}-{segment}-{number:03d}' if segment else f'FU-{month}-{number:03d}'


def preamble(month: str, segment: str | None = None) -> str:
    return PREAMBLE.format(month=f'{month} · {segment}' if segment else month)


def _parse_entry(lines, start, end, month, parsed: MonthFile, errors) -> None:
    heading = HEADING.match(lines[start])
    if not heading or not heading.group(4).strip():
        errors.append((start + 1, f'bad entry heading: {lines[start]}'))
        return
    entry = Entry(int(heading.group(3)), heading.group(1), heading.group(4), {}, start + 1, None, False,
                  heading.group(2))
    parsed.entries.append(entry)
    entry_id = fid(entry.month, entry.number, entry.segment)
    if entry.month != month:
        errors.append((start + 1, f'id month {entry.month} does not match file month {month}'))
    if entry.segment != parsed.segment:
        errors.append((start + 1, f'id segment {entry.segment or "(trunk)"} does not match file segment '
                                  f'{parsed.segment or "(trunk)"}'))
    if entry.title.endswith('.'):
        errors.append((start + 1, f'title ends with a period: {entry_id}'))

    found = [(i + 1, match) for i in range(start + 1, end) if (match := FIELD.match(lines[i]))]
    names = [match.group(1) for _, match in found]
    if tuple(names) != ENTRY_FIELDS:
        errors.append((start + 1, f'fields out of order or missing in {entry_id}: [{", ".join(names)}]'))
        return
    entry.fields = {match.group(1): match.group(2) for _, match in found}
    at = {match.group(1): line_no for line_no, match in found}

    valid = {
        'Status': entry.fields['Status'] in STATUSES,
        'Severity': entry.fields['Severity'] in SEVERITY_HEADINGS,
        'Flavour': entry.fields['Flavour'] in FLAVOURS,
        'Owner': bool(OWNER.fullmatch(entry.fields['Owner'])),
        'Summary': bool(entry.fields['Summary'].strip()),
    }
    for name, ok in valid.items():
        if not ok:
            errors.append((at[name], f'bad {name} in {entry_id}: {entry.fields[name]}'))

    source = SOURCE.match(entry.fields['Source'])
    if source:
        entry.source_stem = source.group(1)
        entry.source_local = source.group(2).startswith('plans/')
    else:
        errors.append((at['Source'], f'unparseable Source in {entry_id}'))

    if not any(line.startswith('  > ') for line in lines[at['Quote']:end]):
        errors.append((at['Quote'], f'empty quote in {entry_id}'))


def parse_month_file(path: Path, label: str) -> MonthFile:
    return parse_month_text(path.read_text(encoding='utf-8'), MONTH_FILE.match(path.name).group(1), label,
                            _segment_of_path(path))


def _segment_of_path(path: Path) -> str | None:
    return path.parent.name if path.parent.parent.name == BRANCHES.name else None


def _is_register_file(root: Path, path: Path) -> bool:
    if not MONTH_FILE.match(path.name):
        return False
    return path.parent == root / FOLLOWUPS or (
        path.parent.parent == root / BRANCHES and re.fullmatch(SEGMENT, path.parent.name) is not None)


def month_files(root: Path) -> list[Path]:
    folder = root / FOLLOWUPS
    if not folder.is_dir():
        return []
    candidates = list(folder.iterdir())
    if (root / BRANCHES).is_dir():
        candidates += [path for register in (root / BRANCHES).iterdir() if register.is_dir()
                       for path in register.iterdir()]
    return sorted(path for path in candidates if path.is_file() and _is_register_file(root, path))


def _folder_errors(root: Path) -> list[str]:
    branches = root / BRANCHES
    if not branches.is_dir():
        return []
    return [f'{relative(root, path)}: not a branch register: a segment is lowercase letters, digits and single '
            'hyphens, starting with a letter'
            for path in sorted(branches.iterdir())
            if path.is_dir() and not path.name.startswith('.') and not re.fullmatch(SEGMENT, path.name)]


def _parse_register(root: Path, overrides: dict[Path, str] | None = None) -> list[MonthFile]:
    overrides = {path: text for path, text in (overrides or {}).items() if _is_register_file(root, path)}
    parsed = []
    for path in sorted(set(month_files(root)) | set(overrides)):
        label = path.relative_to(root).as_posix()
        if path in overrides:
            parsed.append(parse_month_text(overrides[path], MONTH_FILE.match(path.name).group(1), label,
                                           _segment_of_path(path)))
        else:
            parsed.append(parse_month_file(path, label))
    return parsed


def _count(parsed: list[MonthFile]) -> tuple[Counter, dict[str, str]]:
    counts: Counter = Counter()
    first: dict[str, str] = {}
    for month in parsed:
        named = [(entry.line_no, entry.source_stem) for entry in month.entries if entry.source_local]
        for line_no, name in sorted(named + month.pointers):
            counts[name] += 1
            first.setdefault(name, f'{month.label}:{line_no}')
    return counts, first


def register_counts(root: Path, overrides: dict[Path, str] | None = None) -> tuple[Counter, dict[str, str]]:
    return _count(_parse_register(root, overrides))


def residue_items(path: Path) -> int | None:
    visible = []
    in_fence = False
    for line in path.read_text(encoding='utf-8').split('\n'):
        if line.lstrip().startswith(FENCE_MARKERS):
            in_fence = not in_fence
            continue
        if not in_fence:
            visible.append(line)

    start = next((i for i, line in enumerate(visible) if RESIDUE_HEADING.match(line)), None)
    if start is None:
        return None
    section = []
    for line in visible[start + 1:]:
        if line.startswith(('# ', '## ')):
            break
        section.append(line)

    items = 0
    for i, line in enumerate(section):
        header_row = i + 1 < len(section) and TABLE_SEPARATOR.match(section[i + 1])
        if LIST_ITEM.match(line) or (line.startswith('|') and not TABLE_SEPARATOR.match(line) and not header_row):
            items += 1
    return items


def _is_date(text: str) -> bool:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        return False
    try:
        datetime.date.fromisoformat(text)
    except ValueError:
        return False
    return True


def iso_date(text: str) -> str:
    if not _is_date(text):
        raise argparse.ArgumentTypeError(f'not a YYYY-MM-DD date: {text}')
    return text


def ledger_or_refuse(root: Path) -> list[LedgerLine] | None:
    ledger, findings = read_ledger(root)
    if findings:
        for finding in findings:
            print(finding)
        print(f'refused: fix {LEDGER.as_posix()} first')
        return None
    return ledger


def check(root: Path, only: str | None = None) -> int:
    selected = (only,) if only else CHECK_CLASSES
    ledger, format_findings = read_ledger(root)
    plans = implemented_plans(root)
    archived = archived_plans(root)
    recorded = {line.stem: line for line in ledger}
    parsed = _parse_register(root)
    counts, first = _count(parsed)

    missing = [(name, f'missing from ledger: {name} ({relative(root, paths[0])}) — run: '
                      f'python3 plans/tools/plan_residue.py record {name} --how=implement')
               for name, paths in archived.items() if name not in recorded]
    stray = [(line.stem, f'not an implemented plan: {line.stem} ({LEDGER.as_posix()}:{line.line_no}) — '
                         'delete the line, or restore the plan')
             for line in ledger if line.stem not in plans]
    mismatched = [(line.stem, f'entries mismatch: {line.stem}: ledger says {line.entries}, register holds '
                              f'{counts[line.stem]} — run: python3 plans/tools/plan_residue.py recount {line.stem}')
                  for line in ledger if line.entries != counts[line.stem]]
    unrecorded = [(name, f'register cites unrecorded plan: {name} ({first[name]})')
                  for name in counts if name not in recorded]
    register_errors = _folder_errors(root) + [error for month in parsed for error in month.errors]

    findings = {
        'format': format_findings,
        'coverage': [text for _, text in sorted(missing + stray)],
        'counts': [text for _, text in sorted(mismatched + unrecorded)],
        'register': register_errors,
    }
    for name in CHECK_CLASSES:
        if name in selected:
            for finding in findings[name]:
                print(finding)

    print(f'plan_residue: {len(archived)} archived, {len(plans)} implemented, {len(ledger)} recorded, '
          f'{len(missing)} missing, {len(stray)} not-implemented, {len(format_findings)} format, '
          f'{len(mismatched)} count-mismatch, {len(unrecorded)} unrecorded-sources, '
          f'{len(register_errors)} register-errors')
    return 1 if any(findings[name] for name in selected) else 0


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def record(root: Path, stems, how: str, date: str, none_registered: bool = False) -> int:
    ledger = ledger_or_refuse(root)
    if ledger is None:
        return 1
    plans = implemented_plans(root)
    counts, _first = register_counts(root)
    recorded = {line.stem: line for line in ledger}

    refused = False
    added = []
    for name in dict.fromkeys(stems):
        if name not in plans:
            print(f'refused: {name}: no implemented plan with this stem')
            refused = True
            continue
        if name in recorded:
            print(f'refused: {name}: already recorded on {recorded[name].date} ({recorded[name].how})')
            refused = True
            continue
        if how == 'implement':
            items = residue_items(plans[name][0])
            if items is None:
                print(f"note: {name}: no ## Residue section; recorded from the plan's other sections")
            elif items and not counts[name] and not none_registered:
                print(f'refused: {name}: its ## Residue lists {items} items but no register entry names it as '
                      'source; write the register entries first, or pass --none-registered if implementation '
                      'closed every item or each was merged into an existing entry after "; also"')
                refused = True
                continue
        added.append(LedgerLine(name, date, how, counts[name], 0))
    if refused:
        return 1

    write_ledger(root, ledger + added)
    for line in added:
        print(f'recorded: {line.stem} {line.date} {line.how} {line.entries}')
    return 0


def recount(root: Path, stems) -> int:
    ledger = ledger_or_refuse(root)
    if ledger is None:
        return 1
    recorded = {line.stem: line for line in ledger}
    unknown = [name for name in dict.fromkeys(stems) if name not in recorded]
    for name in unknown:
        print(f'refused: {name}: not recorded')
    if unknown:
        return 1

    counts, _first = register_counts(root)
    changes = []
    for name in dict.fromkeys(stems):
        line = recorded[name]
        changes.append((name, line.entries, counts[name]))
        line.entries = counts[name]
    write_ledger(root, ledger)
    for name, old, new in changes:
        print(f'recounted: {name} {old} -> {new}')
    return 0


def validate(root: Path, paths) -> int:
    targets = [(Path(path), path) for path in paths] or [(path, relative(root, path)) for path in month_files(root)]
    failed = False
    for path, label in targets:
        if not path.is_file():
            print(f'{label}: no such file')
            failed = True
            continue
        if not MONTH_FILE.match(path.name):
            print(f'{label}: not a month file')
            failed = True
            continue
        parsed = parse_month_file(path, label)
        statuses = Counter(entry.fields['Status'] for entry in parsed.entries if entry.fields)
        summary = ', '.join(f'{status}: {n}' for status, n in statuses.items())
        print(f'{label}: {len(parsed.entries)} entries, statuses {{{summary}}}, {len(parsed.errors)} errors')
        for error in parsed.errors:
            print(error)
        failed = failed or bool(parsed.errors)
    return 1 if failed else 0


@dataclass
class Register:
    branch: str | None
    segment: str | None
    path: Path
    next: int


def segment_of(branch: str) -> str | None:
    words = re.sub(r'[^a-z0-9]+', '-', branch.lower()).strip('-')
    if not words:
        return None
    return words if words[0].isalpha() else f'b-{words}'


def register_for(root: Path, month: str) -> tuple[Register | None, str]:
    if not (root / 'plans').is_dir():
        return None, f'refused: {root} has no plans/ directory'
    trunk_file = root / FOLLOWUPS / f'{month}.md'
    trunk_next = max(_numbers(trunk_file), default=0) + 1
    if not (root / '.git').exists():
        return Register(None, None, trunk_file, trunk_next), ''
    result = _git(root, 'branch', '--show-current')
    if result.returncode != 0:
        reason = (result.stderr.strip().splitlines() or ['no message'])[0]
        return None, f'refused: git cannot read the branch at {root}: {reason}'
    branch = result.stdout.strip()
    if not branch:
        return None, f'refused: {root} has a detached HEAD; an entry is written on a branch'
    if branch == 'main' or (branch == 'master'
                            and _git(root, 'rev-parse', '--verify', '--quiet', 'refs/heads/main').returncode != 0):
        return Register(branch, None, trunk_file, trunk_next), ''
    segment = segment_of(branch)
    if segment is None:
        return None, f'refused: branch {branch} gives no register segment; rename it'
    names = _git(root, 'for-each-ref', '--format=%(refname:short)', 'refs/heads').stdout.split()
    shared = [name for name in names if name != branch and segment_of(name) == segment]
    if shared:
        return None, f'refused: branches {branch} and {shared[0]} share the register segment {segment}; rename one'
    path = root / BRANCHES / segment / f'{month}.md'
    own = _numbers(path)
    return Register(branch, segment, path, max(own) + 1 if own else trunk_next), ''


def _numbers(path: Path) -> list[int]:
    if not path.is_file():
        return []
    parsed = parse_month_file(path, path.name)
    return [entry.number for entry in parsed.entries if entry.segment == parsed.segment]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)


def next_id(root: Path, month: str) -> int:
    register, refusal = register_for(root, month)
    if register is None:
        print(refusal)
        return 1
    new = '' if register.path.exists() else ' (new file)'
    print(f'{relative(root, register.path)} {fid(month, register.next, register.segment)}{new}')
    return 0


def year_month(text: str) -> str:
    if not YEAR_MONTH.fullmatch(text):
        raise argparse.ArgumentTypeError(f'not a YYYY-MM month: {text}')
    return text


def selftest() -> int:
    return _run_cases(SELFTEST_CASES)


def _run_cases(cases) -> int:
    failed = 0
    for number, case in enumerate(cases, start=1):
        tmp = Path(tempfile.mkdtemp(prefix='plan_residue-')).resolve()
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


# ─── Self-test fixtures ─────────────────────────────────────────────────────
#
# Each case receives an empty directory and builds a fake repo at `root/`, with
# fake sibling repos beside it where a case needs them. A case passes by returning.

def _fixture(tmp: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8'))
    (tmp / 'root' / 'plans').mkdir(parents=True, exist_ok=True)
    return tmp / 'root'


def _captured(function, *args) -> tuple[int, list[str], list[str]]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = function(*args)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue().splitlines(), err.getvalue().splitlines()


def _same(actual, expected, what: str) -> None:
    if actual != expected:
        raise AssertionError(f'{what}: expected {expected!r}, got {actual!r}')


def _source(name: str, path: str | None = None, line: int = 1) -> str:
    return f"`{name}` §1 — `{path or f'plans/{name}-i.md'}:{line}`"


def _entry_text(number: int, source: str, month: str = '2026-09', segment: str | None = None, **fields) -> str:
    values = {'Status': 'open', 'Severity': 'S2', 'Flavour': 'deferred', 'Owner': '-', 'Source': source,
              'Summary': 'A consequence.', **fields}
    lines = [f'### {fid(month, number, segment)} · An item', '']
    lines += [f'- **{name}**: {values[name]}' for name in ENTRY_FIELDS[:-1]]
    lines += ['- **Quote**:', '  > quoted words', '']
    return '\n'.join(lines) + '\n'


def _month_text(body: str, month: str = '2026-09') -> str:
    return PREAMBLE.format(month=month) + '\n' + body


def _line_of(text: str, prefix: str, occurrence: int = 1) -> int:
    matches = [n for n, line in enumerate(text.split('\n'), start=1) if line.startswith(prefix)]
    return matches[occurrence - 1]


def _ledger(root: Path, *lines: str) -> None:
    (root / FOLLOWUPS).mkdir(parents=True, exist_ok=True)
    (root / LEDGER).write_bytes(''.join(line + '\n' for line in lines).encode('utf-8'))


_GIT_ISOLATED = {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}


def _sh(path: Path, *args: str) -> None:
    subprocess.run(['git', '-C', str(path), *args], check=True, capture_output=True,
                   env={**os.environ, **_GIT_ISOLATED})


def _git_repo(path: Path, branch: str, commit: bool = False) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _sh(path, 'init', '-q', '-b', branch)
    if commit:
        _sh(path, '-c', 'user.name=selftest', '-c', 'user.email=selftest@localhost', 'commit', '-q',
            '--allow-empty', '-m', 'selftest')
    return path


def _case_is_implemented_table(tmp: Path) -> None:
    table = {'foo-i.md': True, 'foo-e-i.md': True, 'foo-i-e.md': True, 'foo-e.md': False, 'foo.md': False,
             'foo-ei.md': False, 'foo-i.txt': False, 'README.md': False, '2026-09.md': False}
    _same({name: is_implemented(name) for name in table}, table, 'is_implemented table')


def _case_implemented_plans(tmp: Path) -> None:
    root = _fixture(tmp, {f'root/{path}': '' for path in (
        'plans/a-i.md', 'plans/archive/b-e-i.md', 'plans/sub/c-i-e.md', 'plans/d-e.md', 'plans/.claude/e-i.md',
        'plans/followups/2026-09.md', 'plans/followups/README.md')})
    _same(implemented_plans(root), {
        'a': [root / 'plans/a-i.md'], 'b': [root / 'plans/archive/b-e-i.md'], 'c': [root / 'plans/sub/c-i-e.md'],
    }, 'implemented plans')
    _same(archived_plans(root), {'b': [root / 'plans/archive/b-e-i.md']}, 'archived plans')


def _case_read_ledger_valid_and_absent(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/followups/ledger.txt': LEDGER_HEADER + '\na 2026-09-12 backfill 0\nb 2026-09-13 implement 3\n',
    })
    _same(read_ledger(root), ([LedgerLine('a', '2026-09-12', 'backfill', 0, 7),
                               LedgerLine('b', '2026-09-13', 'implement', 3, 8)], []), 'valid ledger')
    (root / LEDGER).unlink()
    _same(read_ledger(root), ([], []), 'absent ledger')


def _case_read_ledger_findings(tmp: Path) -> None:
    root = _fixture(tmp, {})
    _ledger(root, 'x 2026-09-12 backfill', 'y 2026-09-12 backfill 1 extra', 'a 2026-13-01 backfill 0',
            'b 2026-9-1 backfill 0', 'c 2026-09-12 implemented 0', 'd 2026-09-12 backfill -1',
            'e 2026-09-12 backfill x', 'f-i 2026-09-12 backfill 0', 'g.md 2026-09-12 backfill 0',
            'h 2026-09-12 backfill 0', 'h 2026-09-12 backfill 0', 'aa 2026-09-12 backfill 0')
    lines, findings = read_ledger(root)
    at = 'plans/followups/ledger.txt:'
    _same(findings, [
        f'{at}1: expected 4 fields, got 3', f'{at}2: expected 4 fields, got 5', f'{at}3: bad date: 2026-13-01',
        f'{at}4: bad date: 2026-9-1', f'{at}5: bad how: implemented', f'{at}6: bad entries: -1',
        f'{at}7: bad entries: x', f'{at}8: bad stem: f-i', f'{at}9: bad stem: g.md',
        f'{at}11: duplicate stem: h (first at line 10)', f'{at}12: out of order: aa after h',
    ], 'findings')
    _same([line.stem for line in lines], ['h', 'aa'], 'returned lines')


def _case_parse_month_text_valid(tmp: Path) -> None:
    pointer = '- `a` §1 → **alpha** FU-2026-09-001 (S2, deferred)'
    text = _month_text(
        '## Backfill — x\n\n### Routed elsewhere\n\n' + pointer + '\n\n### S2 — correctness\n\n'
        + _entry_text(1, _source('a', line=3)) + '\n'
        + _entry_text(3, _source('z', 'passwave-core/plans/z-i.md', 9)) + '\n'
        + NEW_THIS_MONTH + '\n\n' + _entry_text(2, _source('b')) + '\n'
        + _entry_text(4, '`c` §2 — plans/c-i.md:7; also plans/c-i.md:9'))
    parsed = parse_month_text(text, '2026-09', 'm.md')
    _same(parsed.errors, [], 'errors')
    _same([entry.number for entry in parsed.entries], [1, 3, 2, 4], 'numbers in file order')
    _same([entry.source_local for entry in parsed.entries], [True, False, True, True], 'source_local')
    _same(parsed.entries[3].source_stem, 'c', 'bare-path source stem')
    _same(parsed.pointers, [(_line_of(text, pointer), 'a')], 'pointers')


def _case_parse_month_text_errors(tmp: Path) -> None:
    base = _month_text(NEW_THIS_MONTH + '\n\n' + _entry_text(1, _source('a')))
    heading = '### FU-2026-09-001 · An item'
    fid = 'FU-2026-09-001'

    def at(text: str, prefix: str, occurrence: int = 1) -> str:
        return f'm.md:{_line_of(text, prefix, occurrence)}: '

    swapped = base.replace('- **Status**: open\n- **Severity**: S2', '- **Severity**: S2\n- **Status**: open')
    two = base + '\n' + _entry_text(1, _source('a'))
    gap = base + '\n' + _entry_text(3, _source('a'))
    stray = base.replace('---\n', '---\n- **Status**: open\n')
    bad_pointer = '- `x` → **web** FU-2026-09-1 (S1, ordering)'
    malformed = base.replace(NEW_THIS_MONTH, bad_pointer + '\n\n' + NEW_THIS_MONTH)
    cases = [
        (base.replace(heading, '### FU-2026-09-1 · x'), '### FU-2026-09-1', 'bad entry heading: ### FU-2026-09-1 · x'),
        (base.replace(heading, '### FU-2026-10-001 · An item'), '### FU-', 'id month 2026-10 does not match file month 2026-09'),
        (base.replace('- **Summary**: A consequence.\n', ''), '### FU-',
         f'fields out of order or missing in {fid}: [Status, Severity, Flavour, Owner, Source, Quote]'),
        (swapped, '### FU-', f'fields out of order or missing in {fid}: [Severity, Status, Flavour, Owner, Source, Summary, Quote]'),
        (base.replace('**Status**: open', '**Status**: closed'), '- **Status**', f'bad Status in {fid}: closed'),
        (base.replace('**Severity**: S2', '**Severity**: S5'), '- **Severity**', f'bad Severity in {fid}: S5'),
        (base.replace('**Flavour**: deferred', '**Flavour**: bogus'), '- **Flavour**', f'bad Flavour in {fid}: bogus'),
        (base.replace('**Owner**: -', '**Owner**:'), '- **Owner**', f'bad Owner in {fid}: '),
        (base.replace(_source('a'), '`a` §1 — nothing here'), '- **Source**', f'unparseable Source in {fid}'),
        (base.replace(_source('a'), '`a` §1 — `../plans/a.md:1`'), '- **Source**', f'unparseable Source in {fid}'),
        (base.replace('**Summary**: A consequence.', '**Summary**: '), '- **Summary**', f'bad Summary in {fid}: '),
        (base.replace('  > quoted words\n', ''), '- **Quote**', f'empty quote in {fid}'),
        (base.replace(heading, '### FU-2026-09-001 · Done.'), '### FU-', f'title ends with a period: {fid}'),
        (two, ('### FU-', 2), f'duplicate id {fid}'),
        (gap, '### FU-2026-09-003', 'ids not gapless: missing 002'),
        (stray, '- **Status**', 'status line outside an entry'),
        (malformed, bad_pointer, f'malformed pointer: {bad_pointer}'),
    ]
    _same(len(cases), 17, 'defect count')
    for text, where, message in cases:
        prefix, occurrence = where if isinstance(where, tuple) else (where, 1)
        _same(parse_month_text(text, '2026-09', 'm.md').errors, [at(text, prefix, occurrence) + message], message)


def _case_register_counts(tmp: Path) -> None:
    pointer = '- `a` §1 → **alpha** FU-2026-09-001 (S2, deferred)'
    september = _month_text(
        '## Backfill — x\n\n### Routed elsewhere\n\n' + pointer + '\n\n### S2 — correctness\n\n'
        + _entry_text(1, _source('a')) + '\n' + _entry_text(2, _source('z', 'passwave-core/plans/z-i.md')) + '\n'
        + _entry_text(3, '`b` §1 — plans/b-i.md:4') + '\n' + NEW_THIS_MONTH + '\n')
    root = _fixture(tmp, {
        'root/plans/followups/2026-09.md': september,
        'root/plans/followups/2026-10.md': _month_text(NEW_THIS_MONTH + '\n\n' + _entry_text(1, _source('b'), '2026-10'), '2026-10'),
        'root/plans/followups/README.md': pointer + '\n\n    ' + _entry_text(1, _source('r')).replace('\n', '\n    '),
        'root/plans/followups/notes.md': '- **Source**: ' + _source('q') + '\n',
    })
    label = 'plans/followups/2026-09.md'
    _same(register_counts(root), (Counter({'a': 2, 'b': 2}), {
        'a': f'{label}:{_line_of(september, pointer)}', 'b': f'{label}:{_line_of(september, "### FU-2026-09-003")}',
    }), 'counts and first locations')
    november = root / FOLLOWUPS / '2026-11.md'
    counts, _first = register_counts(root, {november: _month_text(NEW_THIS_MONTH + '\n\n' + _entry_text(1, _source('c'), '2026-11'), '2026-11')})
    _same(counts, Counter({'a': 2, 'b': 2, 'c': 1}), 'counts with an override')


def _case_residue_items(tmp: Path) -> None:
    root = _fixture(tmp, {
        'root/plans/table.md': '## 13 · Residue\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n| 5 | 6 |\n\n'
                               '## 14 · Next\n\n| x |\n| y |\n',
        'root/plans/list.md': '## Residue\n\n- a\n  - nested\n1) b\n* c\n\n```\n- d\n```\n',
        'root/plans/fenced.md': 'intro\n```\n## Residue\n- x\n```\n',
        'root/plans/prose.md': '## Residue\n\nNothing.\n',
    })
    _same([residue_items(root / 'plans' / name) for name in ('table.md', 'list.md', 'fenced.md', 'prose.md')],
          [3, 3, None, 0], 'residue items')


def _register(*sources: str, month: str = '2026-09', segment: str | None = None, first: int = 1) -> str:
    entries = '\n'.join(_entry_text(number, source, month, segment)
                        for number, source in enumerate(sources, start=first))
    return preamble(month, segment) + '\n' + NEW_THIS_MONTH + '\n\n' + entries


def _case_check_coverage(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/archive/a-i.md': '', 'root/plans/archive/b-i.md': '',
                          'root/plans/c-i.md': '', 'root/plans/d-i.md': ''})
    _ledger(root, 'a 2026-09-12 backfill 0', 'd 2026-09-12 implement 0', 'zz 2026-09-12 backfill 0')
    code, out, _err = _captured(main, ['check', '--only=coverage'], root)
    _same((code, out[:-1]), (1, [
        'missing from ledger: b (plans/archive/b-i.md) — run: python3 plans/tools/plan_residue.py record b --how=implement',
        'not an implemented plan: zz (plans/followups/ledger.txt:3) — delete the line, or restore the plan',
    ]), 'coverage findings')
    _same(out[-1].startswith('plan_residue: 2 archived, 4 implemented, 3 recorded, 1 missing, 1 not-implemented'),
          True, out[-1])


def _case_check_counts(tmp: Path) -> None:
    month = _register(_source('a'), _source('a'), _source('c'))
    root = _fixture(tmp, {'root/plans/a-i.md': '', 'root/plans/c-i.md': '', 'root/plans/followups/2026-09.md': month})
    _ledger(root, 'a 2026-09-12 backfill 1')
    code, out, _err = _captured(main, ['check', '--only=counts'], root)
    _same((code, out[:-1]), (1, [
        'entries mismatch: a: ledger says 1, register holds 2 — run: python3 plans/tools/plan_residue.py recount a',
        f'register cites unrecorded plan: c (plans/followups/2026-09.md:{_line_of(month, "### FU-2026-09-003")})',
    ]), 'counts findings')


def _case_check_scopes_each_class(tmp: Path) -> None:
    month = _register(_source('a'))
    root = _fixture(tmp, {
        'root/plans/a-i.md': '', 'root/plans/b-i.md': '', 'root/plans/archive/c-i.md': '',
        'root/plans/followups/2026-09.md': month.replace('**Status**: open', '**Status**: closed'),
    })
    _ledger(root, 'b 2026-09-12 backfill 5', 'a 2026-09-12 backfill 1')
    status_line = _line_of(month, '- **Status**')
    findings = {
        'format': 'plans/followups/ledger.txt:2: out of order: a after b',
        'coverage': 'missing from ledger: c (plans/archive/c-i.md) — run: python3 plans/tools/plan_residue.py record c --how=implement',
        'counts': 'entries mismatch: b: ledger says 5, register holds 0 — run: python3 plans/tools/plan_residue.py recount b',
        'register': f'plans/followups/2026-09.md:{status_line}: bad Status in FU-2026-09-001: closed',
    }
    runs = {None: list(findings.values()), **{name: [finding] for name, finding in findings.items()}}
    for only, expected in runs.items():
        code, out, _err = _captured(main, ['check'] + ([f'--only={only}'] if only else []), root)
        _same((code, out[:-1]), (1, expected), f'--only={only}')
        _same(out[-1].startswith('plan_residue: '), True, f'--only={only} summary line')

    (root / FOLLOWUPS / '2026-09.md').write_bytes(month.encode('utf-8'))
    _ledger(root, 'a 2026-09-12 backfill 1', 'b 2026-09-12 backfill 0', 'c 2026-09-12 backfill 0')
    for only in runs:
        code, out, _err = _captured(main, ['check'] + ([f'--only={only}'] if only else []), root)
        _same((code, len(out)), (0, 1), f'--only={only} once fixed')


def _case_check_empty_tree(tmp: Path) -> None:
    root = _fixture(tmp, {})
    _same(_captured(main, ['check'], root), (0, [
        'plan_residue: 0 archived, 0 implemented, 0 recorded, 0 missing, 0 not-implemented, 0 format, 0 count-mismatch, '
        '0 unrecorded-sources, 0 register-errors'], []), 'empty tree')


def _case_record_writes_sorted(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a-i.md': '', 'root/plans/b-i.md': '', 'root/plans/c-i.md': '',
                          'root/plans/followups/2026-09.md': _register(_source('c'), _source('c'))})
    _same(_captured(main, ['record', 'c', 'b', '--how=backfill', '--date=2026-10-02'], root),
          (0, ['recorded: c 2026-10-02 backfill 2', 'recorded: b 2026-10-02 backfill 0'], []), 'record c b')
    _same((root / LEDGER).read_text(), LEDGER_HEADER + 'b 2026-10-02 backfill 0\nc 2026-10-02 backfill 2\n', 'ledger')
    _same(_captured(main, ['record', 'a', '--how=backfill', '--date=2026-10-02'], root)[0], 0, 'record a')
    _same((root / LEDGER).read_text().split('\n')[5], 'a 2026-10-02 backfill 0', 'a sorts first')


def _case_record_refusals_write_nothing(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a-i.md': '', 'root/plans/b-i.md': ''})
    _captured(main, ['record', 'b', '--how=backfill', '--date=2026-10-02'], root)
    before = (root / LEDGER).read_bytes()
    _same(_captured(main, ['record', 'a', 'nope', '--how=backfill'], root),
          (1, ['refused: nope: no implemented plan with this stem'], []), 'unknown stem')
    _same(_captured(main, ['record', 'b', '--how=backfill'], root),
          (1, ['refused: b: already recorded on 2026-10-02 (backfill)'], []), 'recorded stem')
    _same((root / LEDGER).read_bytes(), before, 'ledger after refusals')
    (root / LEDGER).write_bytes(before + b'broken line\n')
    _same(_captured(main, ['record', 'a', '--how=backfill'], root), (1, [
        'plans/followups/ledger.txt:7: expected 4 fields, got 2', 'refused: fix plans/followups/ledger.txt first',
    ], []), 'malformed ledger')


def _case_record_implement_guard(tmp: Path) -> None:
    table = '## Residue\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n'
    root = _fixture(tmp, {
        'root/plans/r-i.md': table, 'root/plans/r2-i.md': table, 'root/plans/n-i.md': '# N\n',
        'root/plans/e-i.md': '## Residue\n\n- one item\n',
        'root/plans/followups/2026-09.md': _register(_source('e')),
    })
    date = '--date=2026-10-02'
    code, out, _err = _captured(main, ['record', 'r', '--how=implement', date], root)
    _same((code, out), (1, [
        'refused: r: its ## Residue lists 2 items but no register entry names it as source; write the register '
        'entries first, or pass --none-registered if implementation closed every item or each was merged into an '
        'existing entry after "; also"']), 'guard')
    _same(_captured(main, ['record', 'r', '--how=implement', '--none-registered', date], root),
          (0, ['recorded: r 2026-10-02 implement 0'], []), '--none-registered')
    _same(_captured(main, ['record', 'n', '--how=implement', date], root), (0, [
        "note: n: no ## Residue section; recorded from the plan's other sections",
        'recorded: n 2026-10-02 implement 0'], []), 'no Residue section')
    _same(_captured(main, ['record', 'e', '--how=implement', date], root),
          (0, ['recorded: e 2026-10-02 implement 1'], []), 'registered residue')
    _same(_captured(main, ['record', 'r2', '--how=backfill', date], root),
          (0, ['recorded: r2 2026-10-02 backfill 0'], []), 'backfill never refuses')


def _case_record_default_date(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a-i.md': ''})
    before = today()
    _captured(main, ['record', 'a', '--how=backfill'], root)
    after = today()
    [line], _findings = read_ledger(root)
    _same(line.date in (before, after), True, f'default date {line.date}')


def _case_recount(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/a-i.md': '',
                          'root/plans/followups/2026-09.md': _register(_source('a'), _source('a'), _source('a'))})
    _ledger(root, 'a 2026-09-12 backfill 1')
    _same(_captured(main, ['recount', 'a'], root), (0, ['recounted: a 1 -> 3'], []), 'recount a')
    _same((root / LEDGER).read_text(), LEDGER_HEADER + 'a 2026-09-12 backfill 3\n', 'recounted ledger')
    before = (root / LEDGER).read_bytes()
    _same(_captured(main, ['recount', 'q'], root), (1, ['refused: q: not recorded'], []), 'recount q')
    _same((root / LEDGER).read_bytes(), before, 'ledger after refusal')
    _ledger(root, 'a 2026-09-12 backfill')
    _same(_captured(main, ['recount', 'a'], root), (1, [
        'plans/followups/ledger.txt:1: expected 4 fields, got 3', 'refused: fix plans/followups/ledger.txt first',
    ], []), 'malformed ledger')


def _case_validate(tmp: Path) -> None:
    october = _register(_source('a'), month='2026-10').replace('open', 'closed')
    root = _fixture(tmp, {
        'root/plans/followups/2026-09.md': _register(_source('a')),
        'root/plans/followups/2026-10.md': october,
        'root/plans/followups/notes.md': '',
    })
    _same(_captured(main, ['validate'], root), (1, [
        'plans/followups/2026-09.md: 1 entries, statuses {open: 1}, 0 errors',
        'plans/followups/2026-10.md: 1 entries, statuses {closed: 1}, 1 errors',
        f'plans/followups/2026-10.md:{_line_of(october, "- **Status**")}: bad Status in FU-2026-10-001: closed',
    ], []), 'no paths')
    valid = str(root / FOLLOWUPS / '2026-09.md')
    _same(_captured(main, ['validate', valid], root), (0, [f'{valid}: 1 entries, statuses {{open: 1}}, 0 errors'], []), 'valid path')
    notes = str(root / FOLLOWUPS / 'notes.md')
    _same(_captured(main, ['validate', notes], root), (1, [f'{notes}: not a month file'], []), 'notes.md')
    gone = str(root / FOLLOWUPS / '2026-11.md')
    _same(_captured(main, ['validate', gone], root), (1, [f'{gone}: no such file'], []), 'missing path')


def _case_segment_of_and_ids(tmp: Path) -> None:
    table = {'paddle': 'paddle', 'update-v1': 'update-v1', 'dev-v1.1': 'dev-v1-1',
             'bench/throughput': 'bench-throughput', 'Feature__X': 'feature-x', '-x-': 'x',
             '2027-rework': 'b-2027-rework', 'café': 'caf', '_': None, '': None}
    _same({branch: segment_of(branch) for branch in table}, table, 'segment_of table')
    _same([segment for segment in table.values() if segment and not re.fullmatch(SEGMENT, segment)], [],
          'segments that SEGMENT rejects')
    _same((fid('2026-10', 92, 'paddle'), fid('2026-10', 92)), ('FU-2026-10-paddle-092', 'FU-2026-10-092'), 'fid')
    _same(preamble('2026-10'), PREAMBLE.format(month='2026-10'), 'trunk preamble')
    _same(preamble('2026-10', 'paddle').split('\n')[0], '# Follow-ups — 2026-10 · paddle', 'branch preamble')
    ids = {'FU-2026-10-001': True, 'FU-2026-10-paddle-092': True, 'FU-2026-10-update-v1-001': True,
           'FU-2026-10-b-2027-001': True, 'FU-2026-10-1x-001': False, 'FU-2026-10-paddle-92': False,
           'FU-2026-10-Paddle-001': False}
    _same({text: re.fullmatch(ID, text) is not None for text in ids}, ids, 'ID')


def _case_branch_register_text(tmp: Path) -> None:
    def month(file_segment, *ids) -> str:
        entries = '\n'.join(_entry_text(number, _source('a'), '2026-10', segment) for segment, number in ids)
        return preamble('2026-10', file_segment) + '\n' + NEW_THIS_MONTH + '\n\n' + entries

    pointer = '- `a` §1 → **alpha** FU-2026-10-blog-001 (S2, deferred)'
    text = month('paddle', ('paddle', 35), ('paddle', 36)) + '\n### Routed elsewhere\n\n' + pointer + '\n'
    parsed = parse_month_text(text, '2026-10', 'b.md', 'paddle')
    _same(parsed.errors, [], 'errors')
    _same([(entry.segment, entry.number) for entry in parsed.entries], [('paddle', 35), ('paddle', 36)], 'entries')
    _same(parsed.pointers, [(_line_of(text, pointer), 'a')], 'pointers')
    _same(parse_month_text(month(None, (None, 35), (None, 36)), '2026-10', 't.md').errors, [], 'trunk file from 035')

    bad_heading = _entry_text(1, _source('a'), '2026-10').replace('### FU-2026-10-001 · An item',
                                                                  '### FU-2026-10-1x-001 · A')
    cases = [
        ('paddle', month('paddle', ('paddle', 35), ('paddle', 36), (None, 37)), '### FU-2026-10-037',
         'id segment (trunk) does not match file segment paddle'),
        ('paddle', month('paddle', ('paddle', 35), ('paddle', 36), ('blog', 37)), '### FU-2026-10-blog-037',
         'id segment blog does not match file segment paddle'),
        (None, month(None, (None, 35), (None, 36), ('paddle', 37)), '### FU-2026-10-paddle-037',
         'id segment paddle does not match file segment (trunk)'),
        ('paddle', month('paddle', ('paddle', 35), ('paddle', 37)), '### FU-2026-10-paddle-037',
         'ids not gapless: missing 036'),
        ('paddle', month('paddle', ('paddle', 35), ('paddle', 35)), ('### FU-2026-10-paddle-035', 2),
         'duplicate id FU-2026-10-paddle-035'),
        ('paddle', month('paddle', ('paddle', 35), ('paddle', 36)) + '\n' + bad_heading, '### FU-2026-10-1x-001',
         'bad entry heading: ### FU-2026-10-1x-001 · A'),
    ]
    for segment, defective, where, message in cases:
        prefix, occurrence = where if isinstance(where, tuple) else (where, 1)
        _same(parse_month_text(defective, '2026-10', 'b.md', segment).errors,
              [f'b.md:{_line_of(defective, prefix, occurrence)}: {message}'], message)


def _case_conflict_markers(tmp: Path) -> None:
    markers = ('<<<<<<< HEAD', '||||||| base', '=======', '>>>>>>> paddle')
    base = _month_text(NEW_THIS_MONTH + '\n\n' + _entry_text(1, _source('a')))
    text = base.replace('- **Severity**: S2\n', '<<<<<<< HEAD\n- **Severity**: S2\n||||||| base\n- **Severity**: S3\n'
                                                '=======\n- **Severity**: S1\n>>>>>>> paddle\n')
    text = text.replace(NEW_THIS_MONTH, '=======\n' + NEW_THIS_MONTH)
    at = [number for number, line in enumerate(text.split('\n'), start=1) if line in markers]
    _same(len(at), 5, 'marker lines in the fixture')
    errors = parse_month_text(text, '2026-09', 'm.md').errors
    _same([error for error in errors if error.endswith('merge conflict marker')],
          [f'm.md:{number}: merge conflict marker' for number in at], 'conflict markers')
    lookalikes = base.replace('  > quoted words\n', '  > quoted words\n  > =======\n')
    lookalikes = lookalikes.replace(NEW_THIS_MONTH, '========\n\n=======x\n\n' + NEW_THIS_MONTH)
    _same([error for error in parse_month_text(lookalikes, '2026-09', 'm.md').errors
           if error.endswith('merge conflict marker')], [], 'lines that are not markers')


def _case_branch_registers_in_the_tree(tmp: Path) -> None:
    pointer = '- `a` §1 → **alpha** FU-2026-10-003 (S2, deferred)'
    root = _fixture(tmp, {
        'root/plans/followups/2026-10.md': _register(_source('a'), month='2026-10'),
        'root/plans/followups/branches/paddle/2026-10.md':
            _register(_source('b'), month='2026-10', segment='paddle', first=2)
            + '\n### Routed elsewhere\n\n' + pointer + '\n',
        'root/plans/followups/branches/paddle/notes.md': '- **Source**: ' + _source('q') + '\n',
        'root/plans/followups/branches/Bad_Name/2026-10.md': _register(_source('q'), month='2026-10'),
        'root/plans/followups/branches/.scratch/2026-10.md': _register(_source('q'), month='2026-10'),
        'root/plans/followups/branches/stray.md': _register(_source('q'), month='2026-10'),
    })
    trunk, paddle = root / FOLLOWUPS / '2026-10.md', root / BRANCHES / 'paddle' / '2026-10.md'
    _same(month_files(root), [trunk, paddle], 'month files')
    _same(register_counts(root)[0], Counter({'a': 2, 'b': 1}), 'counts')
    blog = root / BRANCHES / 'blog' / '2026-11.md'
    counts, _first = register_counts(root, {blog: _register(_source('c'), month='2026-11', segment='blog')})
    _same(counts, Counter({'a': 2, 'b': 1, 'c': 1}), 'counts with an override')
    code, out, _err = _captured(main, ['check', '--only=register'], root)
    _same((code, out[:-1]), (1, [
        'plans/followups/branches/Bad_Name: not a branch register: a segment is lowercase letters, digits and single '
        'hyphens, starting with a letter']), 'check --only=register')
    _same(_captured(main, ['validate'], root), (0, [
        'plans/followups/2026-10.md: 1 entries, statuses {open: 1}, 0 errors',
        'plans/followups/branches/paddle/2026-10.md: 1 entries, statuses {open: 1}, 0 errors',
    ], []), 'validate')


def _case_register_for(tmp: Path) -> None:
    trunk = 'plans/followups/2026-10.md'

    def repo(name: str, plans: bool = True, month_file: bool = True) -> Path:
        root = tmp / name
        root.mkdir()
        if plans:
            (root / 'plans').mkdir()
        if month_file:
            (root / FOLLOWUPS).mkdir()
            held = _register(_source('a'), _source('a'), _source('a'), month='2026-10')
            (root / trunk).write_bytes(held.encode('utf-8'))
        return root

    def branch_file(root: Path, text: str) -> Path:
        path = root / BRANCHES / 'paddle' / '2026-10.md'
        path.parent.mkdir(parents=True)
        path.write_bytes(text.encode('utf-8'))
        return root

    def outcome(root: Path):
        register, refusal = register_for(root, '2026-10')
        return refusal if register is None else (register.branch, register.segment, relative(root, register.path),
                                                 register.next)

    master_and_main = _git_repo(repo('master-and-main'), 'master', commit=True)
    _sh(master_and_main, 'branch', 'main')
    detached = _git_repo(repo('detached'), 'main', commit=True)
    _sh(detached, 'checkout', '-q', '--detach')
    shared = _git_repo(repo('shared'), 'feature/x', commit=True)
    _sh(shared, 'branch', 'feature-x')
    broken = repo('broken')
    (broken / '.git').write_bytes(f'gitdir: {tmp}/nowhere\n'.encode('utf-8'))
    branch_register = 'plans/followups/branches/paddle/2026-10.md'
    rows = [
        (repo('bare', month_file=False), (None, None, trunk, 1)),
        (repo('plain'), (None, None, trunk, 4)),
        (_git_repo(repo('main'), 'main'), ('main', None, trunk, 4)),
        (_git_repo(repo('master'), 'master', commit=True), ('master', None, trunk, 4)),
        (master_and_main, ('master', 'master', 'plans/followups/branches/master/2026-10.md', 4)),
        (_git_repo(repo('paddle'), 'paddle'), ('paddle', 'paddle', branch_register, 4)),
        (branch_file(_git_repo(repo('paddle-empty'), 'paddle'), preamble('2026-10', 'paddle')),
         ('paddle', 'paddle', branch_register, 4)),
        (branch_file(_git_repo(repo('paddle-held'), 'paddle'),
                     _register(_source('a'), _source('a'), month='2026-10', segment='paddle', first=4)),
         ('paddle', 'paddle', branch_register, 6)),
        (repo('no-plans', plans=False, month_file=False), f'refused: {tmp}/no-plans has no plans/ directory'),
        (detached, f'refused: {detached} has a detached HEAD; an entry is written on a branch'),
        (shared, 'refused: branches feature/x and feature-x share the register segment feature-x; rename one'),
        (_git_repo(repo('underscore'), '_'), 'refused: branch _ gives no register segment; rename it'),
    ]
    for root, expected in rows:
        _same(outcome(root), expected, root.name)
    refusal = outcome(broken)
    _same(refusal.startswith(f'refused: git cannot read the branch at {broken}: fatal: not a git repository'), True,
          refusal)


def _case_next_id(tmp: Path) -> None:
    root = _fixture(tmp, {'root/plans/followups/2026-10.md': _register(_source('a'), _source('a'), month='2026-10')})
    _same(_captured(main, ['next-id', '--month=2026-10'], root),
          (0, ['plans/followups/2026-10.md FU-2026-10-003'], []), 'trunk file')
    _same(_captured(main, ['next-id', '--month=2026-11'], root),
          (0, ['plans/followups/2026-11.md FU-2026-11-001 (new file)'], []), 'new trunk file')
    _git_repo(root, 'paddle')
    _same(_captured(main, ['next-id', '--month=2026-10'], root),
          (0, ['plans/followups/branches/paddle/2026-10.md FU-2026-10-paddle-003 (new file)'], []), 'branch register')
    detached = _git_repo(tmp / 'detached', 'main', commit=True)
    (detached / 'plans').mkdir()
    _sh(detached, 'checkout', '-q', '--detach')
    _same(_captured(main, ['next-id', f'--repo={detached}'], root),
          (1, [f'refused: {detached} has a detached HEAD; an entry is written on a branch'], []), '--repo detached')
    plain = tmp / 'plain'
    (plain / 'plans').mkdir(parents=True)
    before = today()[:7]
    code, out, err = _captured(main, ['next-id'], plain)
    after = today()[:7]
    _same((code, err), (0, []), 'default month exit')
    _same(out in ([f'plans/followups/{m}.md FU-{m}-001 (new file)'] for m in (before, after)), True,
          f'default month {out}')


def _case_cli_usage_errors(tmp: Path) -> None:
    for argv in ([], ['check', '--only=bogus'], ['record', 'a'], ['record', 'a', '--how=backfill', '--none-registered'],
                 ['record', 'a', '--how=backfill', '--date=2026-02-30'], ['batches'], ['next-id', '--month=2026-13'],
                 ['next-id', '--month=2026-1'], ['next-id', 'extra']):
        code, _out, err = _captured(main, argv, tmp)
        _same((code, bool(err) and err[0].startswith('plan_residue.py: ')), (2, True), f'{argv}: {err}')


def _case_runner_and_repo_root(tmp: Path) -> None:
    def boom(_tmp: Path) -> None:
        raise AssertionError('boom')

    code, out, _err = _captured(_run_cases, (boom,))
    _same((code, out), (1, ['case 1: FAIL boom: AssertionError: boom', 'selftest: 0 passed, 1 failed']), 'runner')
    outcome = None
    try:
        _same(1, 2, 'mismatch')
    except AssertionError as exc:
        outcome = str(exc)
    _same(outcome, 'mismatch: expected 2, got 1', '_same on a mismatch')
    _same(repo_root(), Path(__file__).resolve().parents[2], 'repo_root')


SELFTEST_CASES = (
    _case_is_implemented_table,
    _case_implemented_plans,
    _case_read_ledger_valid_and_absent,
    _case_read_ledger_findings,
    _case_parse_month_text_valid,
    _case_parse_month_text_errors,
    _case_register_counts,
    _case_residue_items,
    _case_check_coverage,
    _case_check_counts,
    _case_check_scopes_each_class,
    _case_check_empty_tree,
    _case_record_writes_sorted,
    _case_record_refusals_write_nothing,
    _case_record_implement_guard,
    _case_record_default_date,
    _case_recount,
    _case_validate,
    _case_segment_of_and_ids,
    _case_branch_register_text,
    _case_conflict_markers,
    _case_branch_registers_in_the_tree,
    _case_register_for,
    _case_next_id,
    _case_cli_usage_errors,
    _case_runner_and_repo_root,
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        self.exit(2, f'plan_residue.py: {message}; usage: {USAGE}\n')


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = _Parser(prog='plan_residue.py', usage=USAGE, description=__doc__.split('\n\n')[0])
    commands = parser.add_subparsers(dest='command', required=True, parser_class=_Parser)

    command = commands.add_parser('check', help='exit 1 on any finding')
    command.add_argument('--only', choices=CHECK_CLASSES, help='one class of finding')

    command = commands.add_parser('record', help='add implemented plans to the ledger')
    command.add_argument('stems', nargs='+')
    command.add_argument('--how', required=True, choices=HOWS)
    command.add_argument('--date', type=iso_date, help='YYYY-MM-DD; default today, UTC')
    command.add_argument('--none-registered', action='store_true',
                         help='with --how=implement: record a plan whose Residue left no new register entry')

    command = commands.add_parser('recount', help="refresh ledger lines' entries from the month files")
    command.add_argument('stems', nargs='+')

    command = commands.add_parser('validate', help="check month files against the register's schema")
    command.add_argument('paths', nargs='*')

    command = commands.add_parser('next-id', help='print the month file and the next id for the branch checked out')
    command.add_argument('--month', type=year_month, help='YYYY-MM; default this month, UTC')
    command.add_argument('--repo', type=Path, help='the repo to write in; default the one holding this file')

    commands.add_parser('selftest', help='run the built-in fixtures')

    args = parser.parse_args(argv)
    if args.command == 'record' and args.none_registered and args.how == 'backfill':
        parser.error('--none-registered is accepted only with --how=implement')

    if args.command == 'selftest':
        return selftest()
    root = root or repo_root()
    date = getattr(args, 'date', None) or today()
    if args.command == 'check':
        return check(root, args.only)
    if args.command == 'record':
        return record(root, args.stems, args.how, date, args.none_registered)
    if args.command == 'recount':
        return recount(root, args.stems)
    if args.command == 'next-id':
        return next_id(args.repo or root, args.month or today()[:7])
    return validate(root, args.paths)


if __name__ == '__main__':
    sys.exit(main())
