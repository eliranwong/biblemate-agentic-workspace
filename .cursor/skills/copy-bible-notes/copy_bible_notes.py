#!/usr/bin/env python3
"""Copy Notes table and inline <sup> note links from one .bible SQLite file to another."""

import argparse
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

SUP_RE = re.compile(r"<sup><ref\b[^>]*onclick=['\"]bn\((\d+),\s*(\d+),\s*(\d+),\s*[\"']([^\"']+)[\"']\)['\"][^>]*>.*?</ref></sup>")
VID_RE = re.compile(r'<vid id="v(\d+)\.(\d+)\.(\d+)"[^>]*>')
WORD_ID_RE = re.compile(r'<(zh|en|w)\s+id="(wh?\d+)">[^<]*</\1>')
ANY_WORD_TAG_RE = re.compile(r'<(?:zh|en|w)(?:\s+[^>]*)?>[^<]*</(?:zh|en|w)>')
TAG_RE = re.compile(r'<[^>]+>')
HEAD_RE = re.compile(r'^<b>([^<]+)</b>')


def plain_to_raw_offset(html_text: str, target_plain: int) -> int:
    """Map a plain-text character offset onto a raw HTML offset outside tags."""
    if target_plain <= 0:
        return 0
    seen = 0
    i = 0
    n = len(html_text)
    while i < n:
        if html_text[i] == '<':
            j = html_text.find('>', i)
            if j != -1:
                i = j + 1
                continue
        seen += 1
        if seen >= target_plain:
            return i + 1
        i += 1
    return n


def copy_bible_notes(
    src_path: str,
    dst_path: str,
    out_path: str | None = None,
    backup: bool = True,
    replace_links: bool = False,
    dry_run: bool = False,
) -> dict:
    t0 = time.time()
    src = Path(src_path)
    dst = Path(dst_path)
    target = Path(out_path) if out_path else dst

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")
    if not dst.exists():
        raise FileNotFoundError(f"Target not found: {dst}")

    if not dry_run:
        if out_path:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, target)
        elif backup:
            bak = Path(f"{dst}.bak")
            shutil.copy2(dst, bak)
            print(f"Backed up {dst} -> {bak}")

    src_conn = sqlite3.connect(str(src))
    dst_conn = sqlite3.connect(str(dst if dry_run else target))

    # Check Notes table in source
    src_tables = {r[0] for r in src_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "Notes" not in src_tables:
        raise RuntimeError(f"Source {src} has no Notes table.")

    notes_schema = src_conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Notes'").fetchone()[0]
    notes_rows = src_conn.execute("SELECT Book, Chapter, Verse, ID, Note FROM Notes").fetchall()

    head_map = {}
    for b, c, v, nid, note in notes_rows:
        if note:
            hm = HEAD_RE.match(note.strip())
            if hm:
                head_map[(b, c, v, nid)] = hm.group(1).strip(" .…")

    stats = {
        "exact_word_id": 0,
        "headword": 0,
        "nearby_word_id": 0,
        "nearest_wid": 0,
        "rel_pos": 0,
        "verse_end": 0,
        "unplaced_verse": 0,
    }
    updates = []
    orig_chapters = {}
    src_sup_total = 0

    dst_chapters = dst_conn.execute("SELECT Book, Chapter, Scripture FROM Bible").fetchall()
    for b, ch, dst_scr in dst_chapters:
        if replace_links:
            dst_scr = SUP_RE.sub("", dst_scr)
        elif SUP_RE.search(dst_scr):
            raise RuntimeError(
                f"Target {target} already contains bn() <sup> links (e.g. {b}:{ch}). "
                "Pass --replace-links to replace them."
            )
        orig_chapters[(b, ch)] = dst_scr

        row = src_conn.execute("SELECT Scripture FROM Bible WHERE Book=? AND Chapter=?", (b, ch)).fetchone()
        if not row:
            continue
        src_scr = row[0]
        matches = list(SUP_RE.finditer(src_scr))
        if not matches:
            continue
        src_sup_total += len(matches)

        src_vids = list(VID_RE.finditer(src_scr))
        src_v_bounds = {}
        for idx, vm in enumerate(src_vids):
            key = (int(vm.group(1)), int(vm.group(2)), int(vm.group(3)))
            s_end = src_vids[idx + 1].start() if idx + 1 < len(src_vids) else len(src_scr)
            src_v_bounds[key] = (vm.start(), s_end)

        by_verse = {}
        for m in matches:
            nb, nc, nv, nid = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
            prefix = src_scr[max(0, m.start() - 160):m.start()]
            prefix_clean = SUP_RE.sub("", prefix)

            vb = src_v_bounds.get((nb, nc, nv))
            rel_ratio = None
            if vb:
                src_v_plain = TAG_RE.sub("", SUP_RE.sub("", src_scr[vb[0]:vb[1]]))
                src_pre_plain = TAG_RE.sub("", SUP_RE.sub("", src_scr[vb[0]:m.start()]))
                if len(src_v_plain) > 0:
                    rel_ratio = len(src_pre_plain) / len(src_v_plain)

            by_verse.setdefault((nb, nc, nv), []).append((m.group(0), nid, prefix_clean, rel_ratio))

        dst_vids = list(VID_RE.finditer(dst_scr))
        verse_slices = []
        for idx, vm in enumerate(dst_vids):
            vb, vc, vv = int(vm.group(1)), int(vm.group(2)), int(vm.group(3))
            s_end = dst_vids[idx + 1].start() if idx + 1 < len(dst_vids) else len(dst_scr)
            verse_slices.append((vb, vc, vv, vm.start(), s_end))

        placed_keys = set()
        new_parts = []
        last_pos = 0

        for vb, vc, vv, s_start, s_end in verse_slices:
            new_parts.append(dst_scr[last_pos:s_start])
            v_text = dst_scr[s_start:s_end]
            notes_list = by_verse.get((vb, vc, vv))
            if notes_list:
                placed_keys.add((vb, vc, vv))
                insertions = {}
                dst_wids_all = list(WORD_ID_RE.finditer(v_text))

                for sup_tag, nid, prefix_clean, rel_ratio in notes_list:
                    pos = None

                    # Tier 1: Exact immediately preceding <zh|en|w id="...">
                    zm_exact = re.search(
                        r'<(zh|en|w)\s+id="(wh?\d+)">[^<]*</\1>(?:[，、；：。！？「」『』（）,.;:!?\'"\s]*)$',
                        prefix_clean,
                    )
                    if zm_exact:
                        aid = zm_exact.group(2)
                        am = re.search(rf'<(?:zh|en|w)\s+id="{aid}">[^<]*</(?:zh|en|w)>', v_text)
                        if am:
                            pos = am.end()
                            stats["exact_word_id"] += 1

                    # Tier 2: Headword match from <b>...</b>
                    if pos is None:
                        hw = head_map.get((vb, vc, vv, nid), "")
                        if hw:
                            cands = [hw]
                            if "神" in hw:
                                cands.append(hw.replace("神", "上帝"))
                            if "上帝" in hw:
                                cands.append(hw.replace("上帝", "神"))
                            for cand in cands:
                                if len(cand) >= 1:
                                    hm = re.search(
                                        rf'<(?:zh|en|w)[^>]*>[^<]*{re.escape(cand)}[^<]*</(?:zh|en|w)>',
                                        v_text,
                                        flags=re.IGNORECASE,
                                    )
                                    if hm:
                                        pos = hm.end()
                                        stats["headword"] += 1
                                        break
                                    # Fallback plain text search outside tags for untagged Bibles
                                    pm = re.search(rf'(?<![A-Za-z0-9_]){re.escape(cand)}(?![A-Za-z0-9_])', v_text, flags=re.IGNORECASE)
                                    if pm and '<' not in v_text[max(0, pm.start() - 20):pm.start()] or (pm and '>' in v_text[max(0, pm.start() - 20):pm.start()]):
                                        pos = pm.end()
                                        stats["headword"] += 1
                                        break

                    # Tier 3: Nearby <zh|en|w id="..."> within 15 plain chars in source
                    all_z = list(WORD_ID_RE.finditer(prefix_clean))
                    if pos is None and all_z:
                        last_z = all_z[-1]
                        tail_plain = TAG_RE.sub("", prefix_clean[last_z.end():])
                        aid = last_z.group(2)
                        if len(tail_plain) <= 15:
                            am = re.search(rf'<(?:zh|en|w)\s+id="{aid}">[^<]*</(?:zh|en|w)>', v_text)
                            if am:
                                pos = am.end()
                                stats["nearby_word_id"] += 1

                    # Tier 4: Nearest numeric wh.../w... WordID in target verse (+-15)
                    if pos is None and all_z:
                        aid = all_z[-1].group(2)
                        ptype = "wh" if aid.startswith("wh") else "w"
                        anum = int(aid[len(ptype):])
                        cands = [m2 for m2 in dst_wids_all if m2.group(2).startswith(ptype)]
                        if cands:
                            best_m = min(cands, key=lambda m2: abs(int(m2.group(2)[len(ptype):]) - anum))
                            if abs(int(best_m.group(2)[len(ptype):]) - anum) <= 15:
                                pos = best_m.end()
                                stats["nearest_wid"] += 1

                    # Tier 5: Relative character position snapped to nearest word tag end
                    if pos is None and rel_ratio is not None:
                        plain_len = len(TAG_RE.sub("", v_text))
                        target_plain = int(round(rel_ratio * plain_len))
                        raw_target = plain_to_raw_offset(v_text, target_plain)
                        word_ends = [m2.end() for m2 in ANY_WORD_TAG_RE.finditer(v_text)]
                        if word_ends:
                            pos = min(word_ends, key=lambda p: abs(p - raw_target))
                        else:
                            pos = raw_target
                        stats["rel_pos"] += 1

                    # Tier 6: Verse end fallback
                    if pos is None:
                        vend = v_text.rfind("</verse>")
                        pos = vend if vend != -1 else len(v_text)
                        stats["verse_end"] += 1

                    insertions.setdefault(pos, []).append(sup_tag)

                out_v = []
                vp = 0
                for pos in sorted(insertions):
                    out_v.append(v_text[vp:pos])
                    out_v.extend(insertions[pos])
                    vp = pos
                out_v.append(v_text[vp:])
                v_text = "".join(out_v)

            new_parts.append(v_text)
            last_pos = s_end

        new_parts.append(dst_scr[last_pos:])
        new_scr = "".join(new_parts)

        for k, nl in by_verse.items():
            if k not in placed_keys:
                stats["unplaced_verse"] += len(nl)
                new_scr += "".join(x[0] for x in nl)

        updates.append((new_scr, b, ch))

    if not dry_run:
        dst_conn.execute("DROP TABLE IF EXISTS Notes")
        dst_conn.execute(notes_schema)
        dst_conn.executemany("INSERT INTO Notes (Book, Chapter, Verse, ID, Note) VALUES (?, ?, ?, ?, ?)", notes_rows)
        dst_conn.executemany("UPDATE Bible SET Scripture = ? WHERE Book = ? AND Chapter = ?", updates)
        dst_conn.commit()

        # Verify
        mismatches = 0
        dst_sup_total = 0
        for b, ch, scr in dst_conn.execute("SELECT Book, Chapter, Scripture FROM Bible"):
            dst_sup_total += len(SUP_RE.findall(scr))
            if SUP_RE.sub("", scr) != orig_chapters[(b, ch)]:
                mismatches += 1
        dst_notes_cnt = dst_conn.execute("SELECT COUNT(*) FROM Notes").fetchone()[0]
        print(f"Copied Notes={dst_notes_cnt}/{len(notes_rows)}, Bible links={dst_sup_total}/{src_sup_total}, text mismatches={mismatches}")
    else:
        print(f"[DRY RUN] Notes={len(notes_rows)}, Bible links={src_sup_total}")

    print(f"Placement stats: {stats}")
    print(f"Elapsed: {time.time() - t0:.2f}s")

    src_conn.close()
    dst_conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Copy Notes table and inline <sup> note links between .bible SQLite files.")
    parser.add_argument("source", help="Source .bible file containing Notes and Bible note links")
    parser.add_argument("target", help="Target .bible file to receive Notes and Bible note links")
    parser.add_argument("--out", help="Optional output .bible path (writes a new copy instead of editing target in-place)")
    parser.add_argument("--no-backup", action="store_true", help="Do not create <target>.bak when editing in-place")
    parser.add_argument("--replace-links", action="store_true", help="Strip existing bn() <sup> links in target before inserting")
    parser.add_argument("--dry-run", action="store_true", help="Compute placement stats without modifying any file")
    args = parser.parse_args()

    copy_bible_notes(
        src_path=args.source,
        dst_path=args.target,
        out_path=args.out,
        backup=not args.no_backup,
        replace_links=args.replace_links,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

