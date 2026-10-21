# Follow-up register

A plan's **residue** is everything it leaves behind: deliberate non-goals,
deferrals, follow-ups owned by another repo or a later plan, ordering
dependencies, accepted limitations, open questions and hand-overs. Every plan
lists its residue under a `## Residue` heading. When the plan is implemented,
each item still live becomes an entry in this directory, so it outlives the
conversation that implemented the plan.

This README defines the convention. It is the same in every repo.

## Month files

There is one file per month, `plans/followups/<YYYY-MM>.md`, created by whoever
appends to it first. `/plan-implement` appends to the file for the month the
plan is implemented in, under `## New this month`:

~~~markdown
# Follow-ups — 2026-10

Entries are appended by `/plan-implement`. An entry is closed by editing its
own **Status** line in place, never by adding a note in a later month.
Open items: `grep -rn '^- \*\*Status\*\*: open' plans/followups/`

Schema, severity tiers and flavours: `plans/followups/README.md`.

---

## New this month
~~~

On a branch other than the repo's trunk, the month file is that branch's own,
under `plans/followups/branches/`, as *Branches* describes.

`2026-09.md` also holds a one-off `## Backfill` section from passwave-core's
audit of every plan it implemented before the register existed, grouped by
severity tier; passwave-core's copy also lists, under `### Routed elsewhere`,
the entries it wrote into other repos. A later `/plan-extract-followups` run in
any repo adds one such section to the month file of the month it runs in, above
`## New this month`: in its own register, and in each register it routes to.

## An entry

The example is indented so that the open-items grep never counts it as an
entry. Real entries start at the left margin.

~~~markdown
    ### FU-2026-10-001 · passwave-web notice plan gates core's deploy

    - **Status**: open
    - **Severity**: S1
    - **Flavour**: ordering
    - **Owner**: passwave-web
    - **Source**: `document-collision-review` §8 step 2 — `plans/archive/document-collision-review-e-i.md:1014`
    - **Summary**: Core's own deploy is gated on passwave-web's notice plan being deployed; nothing outside that ordering list records it.
    - **Quote**:
      > `passwave-web`'s notice plan is revised for this end state, reviewed,
      > implemented and **deployed**.
~~~

Every field, in this order:

| Field | Rule |
|---|---|
| Heading | `### FU-<YYYY-MM>-<NNN> · <title>`, or `### FU-<YYYY-MM>-<segment>-<NNN> · <title>` in a branch's register (*Branches*). `<YYYY-MM>` is the month of the file the entry lives in, and `<segment>` the branch whose register the file is. `<NNN>` is three digits, zero-padded, allocated in sequence through the whole file whichever section the entry sits in, with no gap between the file's lowest id and its highest. An id is never renumbered and never reused, but for the one case in *Ids written before branches had registers*. The title is one line with no trailing period. |
| Status | One of the six statuses below. `- **Status**: ` is a fixed line prefix that the open-items grep depends on: never reword it, indent it, or merge it with another field. |
| Severity | `S1` to `S4`, below. |
| Flavour | One of the seven flavours below. |
| Owner | The repo that must act, or `-` for an item that belongs to no repo (a process or documentation item). |
| Source | The plan's stem in backticks, then the section, then `path:line`, written as plain text and never as a Markdown link. The stem is the durable key. `path:line` is a snapshot taken when the entry was written, and nothing keeps it fresh; if it has gone stale, `find plans -name '<stem>*.md'` finds the plan. When several plans name the same item, the earliest is the source and the later ones follow after `; also`. An entry whose plan lives in another repo prefixes the path with that repo's name. |
| Summary | One sentence in the writer's own words, stating the consequence rather than restating the quote. |
| Quote | The plan's words, verbatim, as a block quote: wrapped, never reworded. It is the evidence a reader checks the summary against. A Markdown link to a `.md` file inside the quote is written with `]\(` in place of `](`, so it renders as the same text and the plan-link gate never reads the register as a source of links. |

Entries are separated by one blank line and never by `---`, which breaks
`grep -A`. Another repo's entry is cited as `<repo> <id>`, for example
`passwave-web FU-2026-09-004`, or `passwave-web FU-2026-10-paddle-092` for one
in a branch's register.

## Statuses

Exactly these six, lowercase. An entry is born `open` unless its source plan
itself records one of the three other birth statuses marked below.

| Status | Meaning | Closed |
|---|---|---|
| `open` | Nothing has settled it. The default. | no |
| `done` | The work has been done. Never a birth status: an item a plan records as completed is not residue. | yes |
| `superseded` | Overtaken by a later decision or plan. | yes |
| `accepted-limitation` | A limitation the plan accepted (birth status). | no: it is due for re-confirmation whenever the register is verified |
| `handed-over` | A step needing root, credentials or an outside party, whose commands or request the plan records as given to its owner (birth status). | no: the step itself is still to be done |
| `non-goal` | Decided against, and still correct (birth status). Recorded so it is not proposed again. | yes |

## Flavours

| Flavour | What it is | Born as |
|---|---|---|
| `non-goal` | A deliberate non-goal: decided against, still correct. | `non-goal` |
| `deferred` | Deferred with intent: meant to happen later. The flavour most likely to be lost. | `open` |
| `owned-elsewhere` | A named follow-up owned by another repo, a design round or a future plan. | `open`, in the owning repo |
| `ordering` | An ordering dependency, "X must land first". Often `S1`, because a missed one ships half a change. | `open` |
| `limitation` | An accepted limitation. Someone must re-confirm that it is still acceptable. | `accepted-limitation` |
| `open-question` | An unresolved open question. | `open` |
| `handover` | A step needing root, credentials or an outside party. | `handed-over` if the plan records the hand-over as given, else `open` |

## Severity

| Tier | Covers |
|---|---|
| `S1` | Security, privacy, data integrity, compliance and legal. Anything touching identity data, notices, automated decisions or retention is `S1`. |
| `S2` | Correctness. |
| `S3` | UX. |
| `S4` | Cleanliness. |

## Closing an entry

Edit the entry's own `Status` line where it sits. Never close an entry by
appending a note to a later month's file. What is still open is then one grep:

    grep -rn '^- \*\*Status\*\*: open' plans/followups/

An entry is closed on a branch whose tree holds it, and a session never
switches the checked-out branch to do so. When the work that settles an entry
lands on a branch that does not hold it, the plan doing the work lists the
closure in its residue as `deferred`, naming the entry's id, so that the
closure is registered where the work is and made once the two branches meet.

## Items owned by another repo

An item whose owner is another repo is written as a full entry into **that
repo's** `plans/followups/<YYYY-MM>.md`, creating the directory, a copy of this
README and the month file if they are absent. It goes on the branch the item
is for, in the working tree that has that branch checked out, as
`/home/claude/.claude/CLAUDE.md`, *Writing for another repo's branch*, says;
`python3 /home/claude/plan-tooling/plans/tools/plan_links.py --tree <repo>`
prints that tree. Never switch a repo's branch to suit the register. On a
branch other than that repo's trunk, the entry goes into the branch's
register, as *Branches* describes. This repo keeps a one-line pointer under a
`### Routed elsewhere` heading:

~~~markdown
- `document-collision-review` §8 step 2 → **passwave-web** FU-2026-09-004 (S1, ordering)
~~~

Another repo still gets a plan or a register entry, never a direct code edit.

## Branches

A repo's **trunk** is its branch named `main`, or `master` where it has no
branch named `main`. Entries written on the trunk go into the month files
above. Every other branch keeps a register of its own,
`plans/followups/branches/<segment>/<YYYY-MM>.md`: month files of the same
shape, titled with the segment (`# Follow-ups — 2026-10 · paddle`). An entry
written on that branch goes there, and its id carries the segment, as in
`FU-2026-10-paddle-092`. No two branches can then give one id to different
entries, and no id changes when they merge.

The segment is the branch's name in lowercase, with each run of characters
other than letters and digits made one hyphen, any hyphen at either end
dropped, and `b-` in front if it does not then start with a letter:
`update-v1` stays `update-v1`, `dev-v1.1` becomes `dev-v1-1` and
`bench/throughput` becomes `bench-throughput`. The first entry in a branch's
register for a month takes the number after the highest id in that month's
trunk file as the branch's tree holds it, or `001` where there is none; later
entries follow in sequence through the branch's file. So a branch's numbers
stay clear of every unsegmented id it held when its register began, which is
what lets *Ids written before branches had registers* keep numbers.

To find the file and the next id for the branch a repo has checked out:

    python3 plans/tools/plan_residue.py next-id [--month=YYYY-MM] [--repo=PATH]

It refuses on a detached HEAD, which has no branch to write on, and when two
of the repo's branches give the same segment. For a repo whose copy of the
tool is older, or which has none, run the reference copy with `--repo`:
`python3 /home/claude/plan-tooling/plans/tools/plan_residue.py next-id --repo=<repo>`.

An entry lives on the branches whose tree holds it. The open-items grep, the
checks and both follow-up skills read the tree that is checked out, and an
entry is verified against that tree's code. To find an id on another branch:

    git grep -n '<id>' $(git for-each-ref --format='%(refname:short)' refs/heads) -- plans/followups/

To write in another branch's register, use the tree that has that branch
checked out, which `plan_links.py --tree . --branch=<branch>` prints.

### At a merge

A branch's register comes with it when it merges, and is part of the
receiving branch's register from then on: nothing moves and no id changes. The
merge is the person's. Afterwards:

1. Resolve any conflict under `plans/followups/` so that each entry, pointer
   and ledger line appears once, and the ledger stays sorted by stem. Only a
   file both sides changed can conflict: the ledger, where both added lines at
   the same place; a trunk month file, where both edited one entry; or a
   branch's register that a cherry-pick put on both sides.
2. Run `python3 plans/tools/plan_residue.py check`, which the repo's residue
   gate also runs. It fails on a conflict marker left in a month file, a
   duplicate id, an id in a file that is not its own, and a ledger count the
   merge changed, which `python3 plans/tools/plan_residue.py recount <stem>`
   puts right.

A branch that never merges back, and only gives or takes cherry-picks, keeps
its register to itself. A pick that carries a register file or entry brings
it with its ids, which collide with nothing. A pick that edits an entry the
destination does not hold leaves that file out.

### Ids written before branches had registers

Before a repo took up this section, each of its branches allocated
unsegmented ids in one sequence, so two branches can hold one id for
different entries. Where, in some month, they do, the repo reconciles that
month once, under the register entry that asks for it, before the branches
merge:

- An entry the trunk holds, under the same heading, keeps its id.
- On every other branch, each unsegmented entry of that month that the trunk
  does not hold takes the branch's segment, keeps its number, and moves into
  the branch's register for that month, with the pointers and backfill
  sections beside it that the trunk does not hold: `FU-2026-10-050` on
  `paddle` becomes `FU-2026-10-paddle-050`. A trunk month file left with no
  entry on that branch is deleted there.
- Every reference to a changed id that the session can reach changes with
  it: this repo's plans and month files, and the pointers in other repos'
  registers on the branches they have checked out. Each one it cannot reach
  is listed in the entry that asked for the reconciliation.
- If an entry's branch of origin is unclear, or a month does not divide this
  way, stop and ask.

This is the only case in which an id changes.

## What a status is not

An entry's status is not evidence about the current code. The register records
what a plan said. An `open` entry may have been done since without anyone
editing it; only a verification pass that checks the code can say so, and it
records what it finds by editing `Status`.

`/plan-review-followups` is that pass. It takes the open entries of the repo it runs
in, three at a time, highest severity first, and closes an entry only as `done` or
`superseded`.

## The ledger

A repo that vendors `plans/tools/plan_residue.py` also keeps
`plans/followups/ledger.txt`: one line per implemented plan whose residue has been
processed into the register, whether or not it left an entry.

    <stem> <YYYY-MM-DD> <backfill|implement> <entries>

`entries` counts the lines in this repo's month files, branch registers included, that
name the plan as their source: its own entries, and its pointers to entries written into
other repos. A plan
whose items were all merged into an earlier plan's entry, after `; also`, counts 0.
Lines are sorted by stem and are added by the tool, after the plan's entries are
written:

    python3 plans/tools/plan_residue.py record <stem> --how=implement

A plan is implemented when the trailing `-e`/`-i` segments of its filename include
`-i`. `python3 plans/tools/plan_residue.py check` fails while an implemented plan under
`plans/archive/` has no line, a line names no implemented plan, a count disagrees with
the month files, or a month file breaks the schema above. Archived plans that no line
names yet are processed in bulk with `/plan-extract-followups`.
