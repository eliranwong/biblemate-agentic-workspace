---
name: tag-bible
description: Tag a SQLite .bible file (Verses table first, then Bible table) with word IDs (wh.../w...) aligned to data/morphology.sqlite, and always add/populate a corresponding column in morphology.sqlite (defaulting to the Bible filename without the .bible extension). Supports optional helping materials (*x.bible, .tsv, .csv) or standalone tagging using existing morphology.sqlite columns (NET, KJV, LEB, BSB, CUV, Translation, Interlinear, Gloss). Use when the user runs /tag-bible or asks to tag a Bible file.
---

# Tag Bible Skill

## Overview
This skill tags a `.bible` SQLite database (`Verses` table first, then `Bible` table) with word-level IDs matching `data/OHGB.bible` (`id="wh{WordID}"` for OT `Book <= 39`, `id="w{WordID}"` for NT `Book >= 40`), and **always** adds and populates a corresponding column in the `morphology` table of `~/biblemate/data/morphology.sqlite` (defaulting to the Bible filename without the `.bible` extension, e.g. `ASV`, `WEB`, `CUVs`, `原文編號逐字中譯`, or overridden with `--col`).

Helper script: `.agents/skills/tag-bible/tag_bible.py`

---

## Tagging & Schema Conventions
1. **Morphology database & backup**:
   - Resolve `morphology.sqlite` in priority order:
     1. `~/biblemate/data_custom/morphology.sqlite` (if it exists), else
     2. `~/biblemate/data/morphology.sqlite`.
   - Every time before starting to tag a Bible, create a fresh backup copy `<morphology_path>.bak` alongside it, replacing any existing backup copy.
2. **Output directory**:
   - Save the tagged `.bible` file automatically in `biblemate_tagged_bibles/` at the repository root (creating `biblemate_tagged_bibles/` if it does not exist).
3. **Element tags**:
   - **English Bibles**: `<en id="wh{WordID}">...</en>` (OT) / `<en id="w{WordID}">...</en>` (NT); spaces and punctuation stay untagged outside `<en>`.
   - **Chinese Bibles**: `<zh id="wh{WordID}">...</zh>` (OT) / `<zh id="w{WordID}">...</zh>` (NT); untagged text, punctuation, and `〔註：...〕` notes stay in `<zh>...</zh>`.
   - **Other languages**: `<w id="wh{WordID}">...</w>` / `<w id="w{WordID}">...</w>` (or configurable via `--tag`).
4. **Execution order**:
   1. Back up `~/biblemate/data/morphology.sqlite` to `~/biblemate/data/morphology.sqlite.bak` (overwriting any old backup) and copy the input `.bible` to `biblemate_tagged_bibles/<name>.bible`.
   2. Tag the **`Verses` table first** and verify `0` text mismatches when stripping tags.
   3. Always update `~/biblemate/data/morphology.sqlite` (using `--col` if provided, otherwise the Bible filename without `.bible`, double-quoted safely for Unicode/special characters) **strictly by `rowid`**—never run unindexed `UPDATE morphology SET ... WHERE Book ... AND WordID = ?` (which causes 2+ hour full-table scans on 564,594 rows).
   4. Tag the **`Bible` table last** by projecting the `Verses` tags onto each `<verse>` body while preserving all headings, `<vid>`, `<ref>`, `<br>`, `&emsp;`, and inline HTML tags (`<span class="smcaps">`, `<i>`, etc.) without creating crossed tags.

---

## Pipeline Architecture

### Case A: Helping Materials Provided (`*x.bible`, `.tsv`, `.csv`)
- **Stage 1 (Phrase Boundaries Only)**: Extract **only** the word/phrase boundaries from the helping material (ignoring its `H...`/`G...`/`E...`/`WordID` numbers in the base stage) and align them losslessly onto the clean `Verses` text.
- **Stage 2 (Clean Base Alignment)**:
  - Run `6` iterations of symmetric Dirichlet-smoothed EM (`alpha = 2.0`, 3 IBM Model 1 + 3 mild position-prior iterations) between `eStrongContextSpecific` and the target segments.
  - For English Bibles, combine EM `sqrt(P(t|s) * P(s|t))` with English lexical stem similarity against `morphology.Translation`, `Interlinear`, and `Gloss`.
  - Decode via confidence-gated 1-to-1 bipartite matching with function-word/article suppression (`H853`, `H9009`, `G3588`) and Psalm `Verse = 1` superscription trimming when omitted in the target Bible.
- **Stage 3 (Validated Strong's Refinement)**: Validate the helping material's `H...`/`G...` tags against `morphology.sqlite` (`eStrongContextSpecific`, `eStrong`, `LexicalEntry`) in the same verse to fill unclaimed gaps and correct conflicts only when `>= 2x` global `(eStrongContextSpecific, word)` support exists.

### Case B: No Helping Materials Provided (Standalone Mode)
- **English Bibles**: Build a phrase dictionary from `morphology.sqlite`'s already-mapped `NET`, `KJV`, `LEB`, `BSB`, `Translation`, `Interlinear`, and `Gloss` columns (longest-match tokenization per verse), then run Stage 2 EM + English lexical similarity + 1-to-1 decoding.
- **Chinese Bibles**: Seed a Chinese word vocabulary from `morphology.CUV` combined with unsupervised PMI n-gram discovery across the target Bible, segment via Viterbi DP (isolating `〔註：...〕` notes), then run Stage 2 EM + 1-to-1 decoding.
- **Other Languages**: Unsupervised PMI / whitespace tokenization + Stage 2 EM + 1-to-1 decoding.

### Case C: Sibling / Revised Edition Transfer (`--transfer-from <tagged.bible>`)
- **English revisions (e.g., `KJV → ASV`, `ASV → WEB` with `--norm-archaic`, `NASB1995 → NASB2020`)**:
  - Transfers exact-match `wh...`/`w...` word IDs onto unchanged spans via `SequenceMatcher` (with `--norm-archaic` normalizing `Jehovah`/`LORD` ↔ `Yahweh`, `-eth`/`-est`, `thou`/`ye` ↔ `you` for `ASV → WEB`), automatically masks inline `[c:v ...]` footnotes (e.g., in `WEB.bible`), and runs EM + Stages 4–5 on changed/untagged spans.
- **Chinese revisions (e.g., `CUV → RCUV`)**: Projects `CUV` character/token boundaries onto the revised Bible (normalizing `上帝 ↔ 神`, Traditional Chinese variants, and optional `--names-tsv` `cu1995t → rcuv2011t` proper-name pairs), isolates `<mbn>...</mbn>` footnotes, and runs EM on changed/reordered spans.

### Post-Processing (All Cases)
- **Stage 4 (`v ± 1` Sliding-Window Recovery)**: Match remaining untagged tokens against unmapped, non-suppressed `WordID`s in adjacent verses (`v - 1`, `v + 1`, including chapter boundaries) for low-coverage/shifted verses.
- **Stage 5 (Refinement)**:
  - **English (`--lang en`)**: Peel leading function words (`in`, `the`, `and`, `then`, `of`, `to`, `for`, `from`, `not`, etc.) and split/reassign multi-word phrases and single-word leftovers across empty `WordID`s in the same verse using core lexical columns (`Translation`, `Interlinear`, `Gloss`) and existing mapped columns (`NET`, `KJV`, `LEB`, `BSB`, `UST`, `ULT`, `NASB1995`, `NASB2020`).
  - **Chinese (`--lang zh`)**: Guarded `LCT` refinement fills remaining untagged `<zh>` spans using `morphology.LCT` while blocking suppressed particles (`H853`, `H9009`, `G3588`) and noisy single-char particles (`那`, `這`, `的`, `得`, etc.).

---

## Usage

```bash
# Tag an English Bible with no helping materials, adding column ASV to morphology.sqlite
python3 .agents/skills/tag-bible/tag_bible.py --bible data/ASV.bible --col ASV --lang en

# Tag an English Bible using an *x.bible helper (Verses first, then Bible table)
python3 .agents/skills/tag-bible/tag_bible.py --bible data/NET.bible --helper data/NETx.bible --col NET --lang en

# Tag a Chinese Bible with no helping materials (seeded by morphology.CUV + PMI)
python3 .agents/skills/tag-bible/tag_bible.py --bible data/CUVs.bible --col CUVs --lang zh

# Tag a revised English Bible from a tagged sibling (e.g., KJV -> ASV, ASV -> WEB)
python3 .agents/skills/tag-bible/tag_bible.py --bible ~/biblemate/data/bibles/ASV.bible --transfer-from biblemate_tagged_bibles/KJV.bible --col ASV --lang en
python3 .agents/skills/tag-bible/tag_bible.py --bible ~/biblemate/data/bibles/WEB.bible --transfer-from biblemate_tagged_bibles/ASV.bible --norm-archaic --col WEB --lang en

# Tag only the Verses table first, then run --only-bible-table later
python3 .agents/skills/tag-bible/tag_bible.py --bible data/WEB.bible --col WEB --lang en --skip-bible-table
python3 .agents/skills/tag-bible/tag_bible.py --bible data/WEB.bible --lang en --only-bible-table
```

## Verification Checklist
- Confirm `0` text mismatches on `Verses` when stripping tags.
- Confirm `0` text mismatches on `Bible` when stripping `<en>`/`<zh>` tags.
- Inspect sample verses (`Gen 1:1`, `Gen 1:2`, `Ps 23:1`, `Mat 1:1`, `John 3:16`) in `morphology.sqlite` and both tables of the `.bible` file before reporting completion.

