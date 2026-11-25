#!/usr/bin/env python3
"""
tag_bible.py — Reusable Bible word-ID tagger & tagged_translations.sqlite mapper.

Supports:
  - English (--lang en), Chinese (--lang zh), or generic (--lang other) Bibles.
  - Optional helping materials (*x.bible SQLite) for initial phrase boundaries
    and Stage 3 validated Strong's refinement.
  - Standalone mode (no helper) seeded by tagged_translations.sqlite's existing columns
    (NET, KJV, LEB, BSB, Translation, Interlinear, Gloss for English; CUV + PMI for Chinese).
  - Tags `Verses` table first, updates `tagged_translations.sqlite` by `rowid`, then tags `Bible` table.
"""

import argparse
import difflib
import glob
import math
import os
import re
import shutil
import sqlite3
import time
from collections import Counter, defaultdict

STRONG_RE = re.compile(r"\b([HG]\d+)\b")
SUP_REF_RE = re.compile(r"<sup>\s*<ref[^>]*>\s*([HG]\d+)\s*</ref>\s*</sup>")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_TOKEN_RE = re.compile(r"(<mbn>.*?</mbn>|<[^>]+>|&[a-zA-Z0-9#]+;|\s+)", flags=re.S)
ZH_NOTE_RE = re.compile(r"(〔註：[^〕]*〕)")
ZH_BRACKET_NOTE_RE = re.compile(r"(〔[^〕]*〕)")
ZH_CHAR_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
ZH_NOISY_CHARS = set("那這的得了着在和與於為是之也而以")
ZH_VAR_NORM = str.maketrans({"裡": "裏", "著": "着", "為": "爲", "眾": "衆", "才": "纔", "床": "牀"})
ZH_PUNCT_RE = re.compile(r"(〔[^〕]*〕|[，。、；：「」『』（）〔〕？！：·—…　 ,.;:?!()\[\]\"'\s]+)")
PUNCT_ONLY_RE = re.compile(r"^[，。、；：「」『』（）〔〕？！：·—…　 ,.;:?!()\[\]\"'\s]+$")

STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "in", "is", "are", "was", "were", "be",
    "been", "being", "that", "which", "who", "whom", "this", "these", "those",
    "for", "with", "on", "at", "by", "from", "as", "it", "its", "he", "his",
    "him", "she", "her", "they", "their", "them", "we", "our", "us", "you", "your",
}

FUNC_WORDS = {
    "and", "then", "the", "a", "an", "in", "into", "to", "unto", "of", "for",
    "from", "on", "upon", "at", "by", "with", "as", "like", "but", "or", "so",
    "that", "if", "not", "no", "nor", "yet", "over", "under", "before", "after",
    "between", "among", "against", "through", "about", "now", "when", "will",
    "thou", "thee", "ye", "shalt", "shall", "hast", "hath", "doth", "did",
}

STRONG_FUNC_MAP = {
    "H9001": {"to", "for", "unto", "at", "in", "as", "of"},
    "H9002": {"and", "then", "but", "so", "now", "or"},
    "H9003": {"in", "into", "with", "by", "on", "at", "among", "when"},
    "H9004": {"like", "as", "according"},
    "H9005": {"then", "and", "so", "but", "now"},
    "H9009": {"the"},
    "G3588": {"the"},
    "G2532": {"and", "also", "even", "then"},
    "G1161": {"then", "but", "now", "and", "so"},
    "G1722": {"in", "into", "on", "at", "by", "with", "among"},
    "G1519": {"into", "to", "for", "in", "unto"},
    "G1537": {"from", "out"},
    "G575": {"from", "away"},
    "G4314": {"to", "toward", "with"},
    "G1223": {"through", "because", "by"},
}


def stem_en(w: str) -> str:
    w = w.lower().strip(".,;:?!\"'()[]—–- ")
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def en_tokens(text: str) -> set:
    words = re.findall(r"[A-Za-z]+", (text or "").lower())
    stems = {stem_en(w) for w in words if w not in STOPWORDS and len(w) > 1}
    return stems or {stem_en(w) for w in words if len(w) > 1}


def norm_archaic_en(w: str) -> str:
    wl = w.lower()
    if wl in ("jehovah", "lord"):
        return "yahweh"
    if wl in ("thou", "thee", "ye"):
        return "you"
    if wl in ("thy", "thine"):
        return "your"
    if wl == "hath":
        return "has"
    if wl == "doth":
        return "does"
    if wl == "shalt":
        return "shall"
    if wl == "wilt":
        return "will"
    if len(wl) > 4 and wl.endswith("eth"):
        return wl[:-3] + "s"
    if len(wl) > 4 and wl.endswith("est"):
        return wl[:-3]
    return wl


def norm_strong(s: str) -> str:
    m = re.match(r"^([HG])0*(\d+)", s)
    return f"{m.group(1)}{m.group(2)}" if m else s


def allowed_func_tokens(key: str, il: str, tr: str, gl: str) -> set:
    allowed = set(STRONG_FUNC_MAP.get(key, set()))
    for col in (il, tr, gl):
        for w in re.findall(r"[A-Za-z]+", (col or "").lower()):
            if w in FUNC_WORDS:
                allowed.add(w)
    return allowed


def row_word_set(key: str, il: str, tr: str, gl: str, extra: str):
    exact, stems = set(), set()
    for col in (tr, il, gl, extra):
        for w in re.findall(r"[A-Za-z]+", (col or "").lower()):
            exact.add(w)
            stems.add(stem_en(w))
    for w in STRONG_FUNC_MAP.get(key, ()):
        exact.add(w)
        stems.add(stem_en(w))
    return exact, stems


def match_score(word: str, exact: set, stems: set) -> float:
    wl = word.lower()
    if wl in exact:
        return 2.0
    if stem_en(wl) in stems:
        return 1.2
    return 0.0


def parse_x_bible_segments(text: str):
    if "<sup>" in text and "<ref" in text:
        parts = SUP_REF_RE.split(text)
    else:
        parts = STRONG_RE.split(text)
    segs, i = [], 0
    while i < len(parts):
        txt = HTML_TAG_RE.sub("", parts[i])
        tag = parts[i + 1] if i + 1 < len(parts) else None
        if txt:
            segs.append((txt, tag))
        i += 2
    return segs


def parse_usfm_dir(usfm_dir: str) -> dict:
    """Parse USFM 3.0 alignment files into {(b, c, v): [(phrase, strong_or_None)]}."""
    verses = {}
    tok_re = re.compile(r'(\\zaln-s\s+\|([^\\]*?)\\\*|\\zaln-e\\\*|\\w\s+([^|\\]+)\|[^\\]*?\\w\*)')
    for path in sorted(glob.glob(os.path.join(usfm_dir, "*.usfm"))):
        prefix_s = os.path.basename(path).split("-", 1)[0]
        if not prefix_s.isdigit():
            continue
        num = int(prefix_s)
        if num < 1 or num > 67 or num == 40:
            continue
        book = num if num <= 39 else num - 1
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        chap_splits = re.split(r"(?m)^\\c\s+(\d+)\b", raw)
        for ci in range(1, len(chap_splits), 2):
            chap = int(chap_splits[ci])
            v_splits = re.split(r"(?:^|\s)\\v\s+(\d+(?:-\d+)?)\s+", chap_splits[ci + 1])
            for vi in range(1, len(v_splits), 2):
                v_num = int(v_splits[vi].split("-")[0])
                v_body = re.sub(r"\\f\s.*?\\f\*", "", v_splits[vi + 1], flags=re.S)
                v_body = re.split(r"(?m)^\\(?:s\d*|sr|r|d|sp|ms\d*|ts)\b", v_body)[0]
                stack, segs, pos, cur_phrase, cur_strongs = [], [], 0, [], []

                def flush_p():
                    if cur_phrase:
                        txt = "".join(cur_phrase).strip()
                        if txt:
                            segs.append((txt, cur_strongs[-1] if cur_strongs else None))
                        cur_phrase.clear()
                        cur_strongs.clear()

                for m in tok_re.finditer(v_body):
                    if m.start() > pos:
                        between = re.sub(r"\\[a-z]+\d*\*?", "", v_body[pos:m.start()])
                        if between.strip():
                            cur_phrase.append(between)
                    tok = m.group(1)
                    if tok.startswith("\\zaln-s"):
                        flush_p()
                        sm = re.search(r'x-strong="([^"]+)"', m.group(2))
                        st_list = [norm_strong(p) for p in sm.group(1).split(":") if re.match(r"^[HG]\d+", p)] if sm else []
                        stack.append(st_list)
                    elif tok.startswith("\\zaln-e"):
                        flush_p()
                        if stack:
                            stack.pop()
                    elif tok.startswith("\\w "):
                        active = [s for lst in stack for s in lst]
                        if cur_phrase and active != cur_strongs:
                            flush_p()
                        if not cur_strongs and active:
                            cur_strongs.extend(active)
                        if cur_phrase:
                            cur_phrase.append(" ")
                        cur_phrase.append(m.group(3))
                    pos = m.end()
                if pos < len(v_body):
                    tail = re.sub(r"\\[a-z]+\d*\*?", "", v_body[pos:])
                    if tail.strip():
                        cur_phrase.append(tail)
                flush_p()
                if segs:
                    verses[(book, chap, v_num)] = segs
    return verses


def load_helper_verses(helper_path: str, helper_table: str = "Verses") -> dict:
    if os.path.isdir(helper_path):
        return parse_usfm_dir(helper_path)
    hx_conn = sqlite3.connect(f"file:{helper_path}?mode=ro", uri=True)
    if helper_table == "Bible":
        hx_verses = {}
        for _, _, chap_html in hx_conn.execute("SELECT Book, Chapter, Scripture FROM Bible WHERE Book > 0").fetchall():
            for vm in re.finditer(r"<verse>(.*?)</verse>", chap_html, flags=re.S):
                inner = vm.group(1)
                m_vid = re.search(r'<vid id="v(\d+)\.(\d+)\.(\d+)"[^>]*>.*?</vid>', inner, flags=re.S)
                if m_vid:
                    bcv = (int(m_vid.group(1)), int(m_vid.group(2)), int(m_vid.group(3)))
                    hx_verses[bcv] = inner[m_vid.end():]
    else:
        hx_verses = {
            (b, c, v): s
            for b, c, v, s in hx_conn.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
        }
    hx_conn.close()
    return hx_verses


def align_en_segments(segs, target_text: str):
    seg_chars, seg_idx_map = [], []
    for s_idx, (txt, _) in enumerate(segs):
        for ch in txt:
            if not ch.isspace():
                seg_chars.append(ch.lower())
                seg_idx_map.append(s_idx)
    seg_norm = "".join(seg_chars)

    tgt_chars, tgt_orig = [], []
    for idx, ch in enumerate(target_text):
        if not ch.isspace():
            tgt_chars.append(ch.lower())
            tgt_orig.append(idx)
    tgt_norm = "".join(tgt_chars)

    if not seg_norm or not tgt_norm:
        return [(target_text, None)]

    sm = difflib.SequenceMatcher(None, seg_norm, tgt_norm, autojunk=False)
    char_to_seg = [None] * len(tgt_norm)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                char_to_seg[j1 + k] = seg_idx_map[i1 + k]
        elif tag == "replace":
            span = set(seg_idx_map[i1:i2])
            if len(span) == 1:
                only = next(iter(span))
                for j in range(j1, j2):
                    char_to_seg[j] = only

    orig_to_seg = [None] * len(target_text)
    for j, s_idx in enumerate(char_to_seg):
        if s_idx is not None:
            orig_to_seg[tgt_orig[j]] = s_idx

    for idx in range(1, len(target_text) - 1):
        if target_text[idx].isspace() and orig_to_seg[idx - 1] is not None and orig_to_seg[idx - 1] == orig_to_seg[idx + 1]:
            orig_to_seg[idx] = orig_to_seg[idx - 1]

    out, cur_start, cur_seg = [], 0, orig_to_seg[0]
    for idx in range(1, len(target_text)):
        if orig_to_seg[idx] != cur_seg:
            out.append((target_text[cur_start:idx], segs[cur_seg][1] if cur_seg is not None else None))
            cur_start, cur_seg = idx, orig_to_seg[idx]
    out.append((target_text[cur_start:], segs[cur_seg][1] if cur_seg is not None else None))
    return out


def split_punct_en(aligned_pieces):
    out = []
    for piece, tag in aligned_pieces:
        if not piece:
            continue
        if not re.search(r"[A-Za-z0-9]", piece):
            out.append((piece, False, None))
            continue
        m = re.match(r"^([^A-Za-z0-9]*)(.*?)([^A-Za-z0-9]*)$", piece, re.S)
        lead, core, trail = m.group(1), m.group(2), m.group(3)
        if lead:
            out.append((lead, False, None))
        if core:
            out.append((core, True, tag))
        if trail:
            out.append((trail, False, None))
    return out


def split_punct_zh(aligned_pieces):
    out = []
    for piece, tag in aligned_pieces:
        if not piece:
            continue
        for part in ZH_PUNCT_RE.split(piece):
            if not part:
                continue
            if ZH_PUNCT_RE.fullmatch(part):
                out.append((part, False, None))
            else:
                out.append((part, True, tag))
    return out


def build_en_phrase_lexicon(m_cur, existing_cols):
    """Build known multi-word English phrases from tagged_translations.sqlite existing columns."""
    cols = [c for c in ("NET", "KJV", "LEB", "BSB", "Translation", "Interlinear", "Gloss") if c in existing_cols]
    phrases = set()
    if not cols:
        return phrases
    sql = f"SELECT {', '.join(cols)} FROM morphology"
    for row in m_cur.execute(sql).fetchall():
        for val in row:
            if not val:
                continue
            for part in val.split(" / "):
                clean = re.sub(r"[\[\]]", "", part).strip(" .,;:?!\"'()")
                words = clean.lower().split()
                if 2 <= len(words) <= 4:
                    phrases.add(tuple(words))
    return phrases


def tokenize_en_standalone(text: str, phrase_lex: set):
    """Greedy longest-phrase tokenization for English without a helper Bible."""
    parts = re.split(r"([A-Za-z0-9']+)", text)
    # Collapse simple "word space word" sequences when in phrase_lex
    out = []
    i = 0
    while i < len(parts):
        p = parts[i]
        if not p:
            i += 1
            continue
        if re.fullmatch(r"[A-Za-z0-9']+", p):
            # Try 4, 3, 2 word lookahead
            matched = False
            for k in (4, 3, 2):
                end_i = i + 2 * (k - 1)
                if end_i < len(parts):
                    ok = True
                    w_list = []
                    for step in range(i, end_i + 1, 2):
                        if not re.fullmatch(r"[A-Za-z0-9']+", parts[step]):
                            ok = False
                            break
                        w_list.append(parts[step].lower())
                    for sp in range(i + 1, end_i, 2):
                        if parts[sp] != " ":
                            ok = False
                            break
                    if ok and tuple(w_list) in phrase_lex:
                        out.append(("".join(parts[i : end_i + 1]), True, None))
                        i = end_i + 1
                        matched = True
                        break
            if not matched:
                out.append((p, True, None))
                i += 1
        else:
            out.append((p, False, None))
            i += 1
    return out


def build_zh_vocab(verses: dict, m_cur, has_cuv: bool):
    unigram = Counter()
    ngram = Counter()
    total_chars = 0
    for text in verses.values():
        for chunk in ZH_PUNCT_RE.split(text):
            if not chunk or ZH_PUNCT_RE.fullmatch(chunk):
                continue
            for run in re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]+", chunk):
                n = len(run)
                total_chars += n
                for ch in run:
                    unigram[ch] += 1
                for L in range(2, 6):
                    if n >= L:
                        for idx in range(n - L + 1):
                            ngram[run[idx : idx + L]] += 1

    log_total = math.log(max(1, total_chars))
    vocab_score = {ch: math.log(cnt) - log_total for ch, cnt in unigram.items()}
    for w, cnt in ngram.items():
        if cnt < 4:
            continue
        L = len(w)
        log_pw = math.log(cnt) - log_total
        min_pmi = 1e9
        for k in range(1, L):
            left, right = w[:k], w[k:]
            cl = unigram[left] if len(left) == 1 else ngram.get(left, 0)
            cr = unigram[right] if len(right) == 1 else ngram.get(right, 0)
            if cl == 0 or cr == 0:
                min_pmi = -1e9
                break
            pmi = log_pw - (math.log(cl) - log_total) - (math.log(cr) - log_total)
            if pmi < min_pmi:
                min_pmi = pmi
        thresh = 3.0 if L == 2 else (4.2 if L == 3 else 5.5)
        if min_pmi >= thresh:
            vocab_score[w] = log_pw + 0.6 * (L - 1)

    if has_cuv:
        for (val,) in m_cur.execute('SELECT DISTINCT CUV FROM morphology WHERE CUV != ""').fetchall():
            for part in val.split(" / "):
                w = part.strip()
                if 2 <= len(w) <= 6 and re.fullmatch(r"[\u4e00-\u9fff\u3400-\u4dbf]+", w):
                    vocab_score[w] = max(vocab_score.get(w, -10.0), -6.0 + 0.5 * (len(w) - 1))
    return vocab_score


def tokenize_zh_standalone(text: str, vocab_score: dict):
    out = []
    for chunk in ZH_PUNCT_RE.split(text):
        if not chunk:
            continue
        if ZH_PUNCT_RE.fullmatch(chunk):
            out.append((chunk, False, None))
            continue
        pos = 0
        for m in re.finditer(r"[\u4e00-\u9fff\u3400-\u4dbf]+", chunk):
            if m.start() > pos:
                out.append((chunk[pos:m.start()], False, None))
            run = m.group(0)
            n = len(run)
            dp = [(-1e18, 0)] * (n + 1)
            dp[0] = (0.0, 0)
            for i in range(1, n + 1):
                for L in range(1, min(6, i + 1)):
                    w = run[i - L : i]
                    sc = vocab_score.get(w)
                    if sc is not None and dp[i - L][0] + sc > dp[i][0]:
                        dp[i] = (dp[i - L][0] + sc, i - L)
                if dp[i][0] < -1e17:
                    dp[i] = (dp[i - 1][0] - 20.0, i - 1)
            toks, idx = [], n
            while idx > 0:
                prev = dp[idx][1]
                toks.append(run[prev:idx])
                idx = prev
            for tok in reversed(toks):
                out.append((tok, True, None))
            pos = m.end()
        if pos < len(chunk):
            out.append((chunk[pos:], False, None))
    return out


def tag_bible_table(bible_db: str, tag_name: str):
    t0 = time.time()
    tag_re = re.compile(rf'<{tag_name}\s+id="([^"]+)">([^<]*)</{tag_name}>')
    strip_re = re.compile(rf"</?{tag_name}[^>]*>")

    conn = sqlite3.connect(bible_db)
    cur = conn.cursor()
    verses = {
        (b, c, v): s
        for b, c, v, s in cur.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
    }
    chapters = cur.execute("SELECT rowid, Book, Chapter, Scripture FROM Bible").fetchall()
    updates, mismatches = [], 0

    for rowid, b, c, chap_html in chapters:
        clean_chap = strip_re.sub("", chap_html)

        def repl_verse(vm):
            v_inner = vm.group(1)
            m_vid = re.search(r'<vid id="v(\d+)\.(\d+)\.(\d+)"[^>]*>.*?</vid>', v_inner, flags=re.S)
            if not m_vid:
                return vm.group(0)
            vb, vc, vv = int(m_vid.group(1)), int(m_vid.group(2)), int(m_vid.group(3))
            tagged_v = verses.get((vb, vc, vv))
            if not tagged_v:
                return vm.group(0)
            prefix_html = v_inner[:m_vid.end()]
            body_html = v_inner[m_vid.end():]

            # Parse tagged_v chars -> tid
            t_chars, t_ids = [], []
            pos = 0
            for m in tag_re.finditer(tagged_v):
                for ch in tagged_v[pos:m.start()]:
                    if not ch.isspace():
                        t_chars.append(ch)
                        t_ids.append(None)
                for ch in m.group(2):
                    if not ch.isspace():
                        t_chars.append(ch)
                        t_ids.append(m.group(1))
                pos = m.end()
            for ch in tagged_v[pos:]:
                if not ch.isspace():
                    t_chars.append(ch)
                    t_ids.append(None)

            t_idx, n_t = 0, len(t_chars)
            raw_items = []
            for part in HTML_TOKEN_RE.split(body_html):
                if not part:
                    continue
                if HTML_TOKEN_RE.fullmatch(part):
                    if part.startswith("<mbn>"):
                        ntxt = re.sub(r"<[^>]+>", "", part)
                        for ch in ntxt:
                            if not ch.isspace() and t_idx < n_t and t_chars[t_idx] == ch:
                                t_idx += 1
                    raw_items.append((part, True, None))
                    continue
                for ch in part:
                    tid = None
                    if t_idx < n_t and t_chars[t_idx] == ch:
                        tid = t_ids[t_idx]
                        t_idx += 1
                    else:
                        for k in range(t_idx, min(n_t, t_idx + 12)):
                            if t_chars[k] == ch:
                                tid = t_ids[k]
                                t_idx = k + 1
                                break
                    raw_items.append((ch, False, tid))

            n = len(raw_items)
            for i in range(n):
                txt, is_hw, _ = raw_items[i]
                if is_hw and txt.isspace():
                    p = i - 1
                    while p >= 0 and raw_items[p][1] and raw_items[p][0].isspace():
                        p -= 1
                    q = i + 1
                    while q < n and raw_items[q][1] and raw_items[q][0].isspace():
                        q += 1
                    if p >= 0 and q < n and not raw_items[p][1] and not raw_items[q][1]:
                        if raw_items[p][2] is not None and raw_items[p][2] == raw_items[q][2]:
                            raw_items[i] = (txt, True, raw_items[p][2])

            out, buf, cur_tid = [], [], None
            for txt, _, tid in raw_items:
                if tid != cur_tid:
                    if buf:
                        s = "".join(buf)
                        out.append(f'<{tag_name} id="{cur_tid}">{s}</{tag_name}>' if cur_tid else s)
                        buf = []
                    cur_tid = tid
                buf.append(txt)
            if buf:
                s = "".join(buf)
                out.append(f'<{tag_name} id="{cur_tid}">{s}</{tag_name}>' if cur_tid else s)
            return f"<verse>{prefix_html}{''.join(out)}</verse>"

        new_chap = re.sub(r"<verse>(.*?)</verse>", repl_verse, clean_chap, flags=re.S)
        if strip_re.sub("", new_chap) != clean_chap:
            mismatches += 1
        updates.append((new_chap, rowid))

    cur.executemany("UPDATE Bible SET Scripture = ? WHERE rowid = ?", updates)
    conn.commit()
    conn.close()
    print(f"Tagged {len(updates)} chapters in Bible table in {time.time() - t0:.2f}s (mismatches={mismatches}).")


def create_verses_plain(bible_db: str):
    """Duplicate Verses into VersesPlain and strip all tags from Scripture."""
    t0 = time.time()
    conn = sqlite3.connect(bible_db)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS VersesPlain")
    cur.execute("CREATE TABLE VersesPlain AS SELECT * FROM Verses")
    rows = cur.execute("SELECT rowid, Scripture FROM VersesPlain").fetchall()
    updates = [(HTML_TAG_RE.sub("", s) if s else s, rowid) for rowid, s in rows]
    cur.executemany("UPDATE VersesPlain SET Scripture = ? WHERE rowid = ?", updates)
    conn.commit()
    conn.close()
    print(f"Created VersesPlain table with {len(updates)} tag-stripped rows in {time.time() - t0:.2f}s.")


def resolve_default_morph_path(morph_arg: str) -> str:
    if morph_arg:
        return os.path.expanduser(morph_arg)
    custom = os.path.expanduser("~/biblemate/data_custom/tagged_translations.sqlite")
    if os.path.exists(custom):
        return custom
    return os.path.expanduser("~/biblemate/data/tagged_translations.sqlite")


def main():
    parser = argparse.ArgumentParser(description="Tag a .bible file and optionally populate tagged_translations.sqlite.")
    parser.add_argument("--bible", required=True, help="Path to source .bible SQLite file")
    parser.add_argument("--morph", default="", help="Path to tagged_translations.sqlite (default: ~/biblemate/data_custom/tagged_translations.sqlite if exists, else ~/biblemate/data/tagged_translations.sqlite)")
    parser.add_argument("--out-dir", default="biblemate_tagged_bibles", help="Output directory for tagged .bible (default: biblemate_tagged_bibles)")
    parser.add_argument("--col", default="", help="Column name to add/update in morphology table (default: bible filename without .bible)")
    parser.add_argument("--lang", default="en", choices=["en", "zh", "other"], help="Bible language")
    parser.add_argument("--tag", default="", help="Override XML tag name (default: en for en, zh for zh, w for other)")
    parser.add_argument("--helper", default="", help="Optional *x.bible helper file or USFM directory")
    parser.add_argument("--helper-table", default="Verses", choices=["Verses", "Bible"], help="Table in helper file to read Strong's segments from (default: Verses)")
    parser.add_argument("--transfer-from", default="", help="Optional already-tagged sibling .bible file (e.g., NASB1995.bible, KJV.bible, ASV.bible, CUV.bible) for exact-span transfer before EM")
    parser.add_argument("--norm-archaic", action="store_true", help="Normalize archaic English (Jehovah/LORD->Yahweh, -eth, -est, thou/ye->you) during --transfer-from")
    parser.add_argument("--names-tsv", default="", help="Optional TSV with book/chapter/verse/cu1995t/rcuv2011t for sibling Chinese name mapping")
    parser.add_argument("--skip-bible-table", action="store_true", help="Only tag Verses table, do not tag Bible table")
    parser.add_argument("--only-bible-table", action="store_true", help="Only propagate Verses tags to Bible table")
    parser.add_argument("--refine-only", action="store_true", help="Run Stage 4 & 5 refinement directly on already-tagged Verses + morphology.<col>, then re-tag Bible table")
    args = parser.parse_args()

    tag_name = args.tag or ("en" if args.lang == "en" else ("zh" if args.lang == "zh" else "w"))
    os.makedirs(args.out_dir, exist_ok=True)
    out_bible = os.path.join(args.out_dir, os.path.basename(args.bible))
    if os.path.abspath(args.bible) != os.path.abspath(out_bible):
        if not args.only_bible_table or not os.path.exists(out_bible):
            shutil.copy2(args.bible, out_bible)
            print(f"Copied {args.bible} -> {out_bible}")

    if args.only_bible_table:
        tag_bible_table(out_bible, tag_name)
        create_verses_plain(out_bible)
        return

    t0 = time.time()
    morph_path = resolve_default_morph_path(args.morph)
    morph_bak = f"{morph_path}.bak"
    shutil.copy2(morph_path, morph_bak)
    print(f"Backed up {morph_path} -> {morph_bak}")

    b_conn = sqlite3.connect(out_bible)
    b_cur = b_conn.cursor()
    strip_re = re.compile(rf"</?{tag_name}[^>]*>")
    target_verses = {
        (b, c, v): strip_re.sub("", s)
        for b, c, v, s in b_cur.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
    }
    print(f"Loaded {len(target_verses)} verses from {out_bible}.")

    m_conn = sqlite3.connect(morph_path)
    m_cur = m_conn.cursor()
    existing_cols = [r[1] for r in m_cur.execute("PRAGMA table_info(morphology)").fetchall()]

    # Tokenize verses (skipped in --refine-only mode)
    tokenized = {}
    if not args.refine_only:
        if args.helper:
            hx_verses = load_helper_verses(args.helper, args.helper_table)
            zh_vocab = build_zh_vocab(target_verses, m_cur, "CUV" in existing_cols) if args.lang == "zh" else None
            for bcv, txt in target_verses.items():
                hx = hx_verses.get(bcv)
                if hx:
                    segs = hx if isinstance(hx, list) else parse_x_bible_segments(hx)
                    aligned = align_en_segments(segs, txt)
                    tokenized[bcv] = split_punct_zh(aligned) if args.lang == "zh" else split_punct_en(aligned)
                elif args.lang == "zh":
                    tokenized[bcv] = tokenize_zh_standalone(txt, zh_vocab)
                else:
                    parts = re.split(r"([A-Za-z0-9']+)", txt)
                    tokenized[bcv] = [(p, bool(re.fullmatch(r"[A-Za-z0-9']+", p)), None) for p in parts if p]
        elif args.lang == "en":
            phrase_lex = build_en_phrase_lexicon(m_cur, existing_cols)
            for bcv, txt in target_verses.items():
                tokenized[bcv] = tokenize_en_standalone(txt, phrase_lex)
        elif args.lang == "zh":
            zh_vocab = build_zh_vocab(target_verses, m_cur, "CUV" in existing_cols)
            for bcv, txt in target_verses.items():
                tokenized[bcv] = tokenize_zh_standalone(txt, zh_vocab)
        else:
            for bcv, txt in target_verses.items():
                parts = re.split(r"(\w+)", txt)
                tokenized[bcv] = [(p, bool(re.fullmatch(r"\w+", p)), None) for p in parts if p]

    # Load morphology rows (using all other mapped English columns as reference, excluding args.col)
    ref_en_cols = [
        c for c in ("NET", "KJV", "ASV", "WEB", "LEB", "BSB", "UST", "ULT", "NASB1995", "NASB2020", "NIV", "NLT2015", "ESV2016", "NRSV")
        if c in existing_cols and c != args.col
    ]
    extra_sel = (", " + ", ".join(ref_en_cols)) if ref_en_cols else ""
    col_sel = f", {args.col}" if (args.refine_only and args.col and args.col in existing_cols) else ""
    morph_by_verse = defaultdict(list)
    book_verses = defaultdict(list)
    seen_bcv = set()
    for row in m_cur.execute(
        f"SELECT rowid, Book, Chapter, Verse, WordID, eStrongContextSpecific, eStrong, LexicalEntry, Interlinear, Translation, Gloss{extra_sel}{col_sel} "
        "FROM morphology ORDER BY rowid"
    ).fetchall():
        rowid, b, c, v, wid, escs, es, le, il, tr, gl = row[:11]
        end_extra = 11 + len(ref_en_cols)
        extra_str = " ".join(x for x in row[11:end_extra] if x)
        existing_val = (row[end_extra] or "") if col_sel else ""
        key = (escs or "").split(",")[0].strip()
        is_suppressed = (tr == "" and il in ("[object marker]", "-", "")) or key in ("H853", "H9009", "G3588")
        valid_strongs = {norm_strong(tok) for src in (escs, es, le) for tok in re.findall(r"[HG]\d+", src or "")}
        eng_stems = en_tokens(f"{tr or ''} {il or ''} {gl or ''}") if args.lang == "en" else set()
        allowed_funcs = allowed_func_tokens(key, il, tr, gl) if args.lang == "en" else set()
        exact_all, stems_all = row_word_set(key, il, tr, gl, extra_str) if args.lang == "en" else (set(), set())
        is_obj_marker = (key == "H853" and il == "[object marker]")
        morph_by_verse[(b, c, v)].append([
            rowid, wid, key, is_suppressed, valid_strongs, eng_stems,
            allowed_funcs, exact_all, stems_all, is_obj_marker, existing_val
        ])
        if (b, c, v) not in seen_bcv:
            seen_bcv.add((b, c, v))
            book_verses[b].append((b, c, v))

    adj_verses = {}
    for b, v_list in book_verses.items():
        for i, bcv in enumerate(v_list):
            nbrs = []
            if i > 0:
                nbrs.append(v_list[i - 1])
            if i + 1 < len(v_list):
                nbrs.append(v_list[i + 1])
            adj_verses[bcv] = nbrs

    if args.refine_only:
        verse_scriptures = {
            (b, c, v): s
            for b, c, v, s in b_cur.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
        }
    else:
        # Build EM corpus
        corpus = []
        for bcv, pieces in tokenized.items():
            m_list = morph_by_verse.get(bcv)
            if not m_list:
                continue
            tgt_indices = [idx for idx, (_, is_w, _) in enumerate(pieces) if is_w]
            if not tgt_indices:
                continue
            tgt_tokens = [pieces[idx][0].lower() for idx in tgt_indices]
            src_keys = ["NULL"] + [m[2] for m in m_list]
            corpus.append((bcv, src_keys, tgt_tokens, m_list, tgt_indices))

        # 6 EM iterations
        cooc = defaultdict(set)
        for _, src_keys, tgt_tokens, _, _ in corpus:
            t_set = set(tgt_tokens)
            for s in set(src_keys):
                cooc[s].update(t_set)
        t_prob = {s: {t: 1.0 / len(t_set) for t in t_set} for s, t_set in cooc.items()}
        rev_prob = defaultdict(dict)

        for it in range(6):
            counts = defaultdict(lambda: defaultdict(float))
            totals = defaultdict(float)
            use_pos = (it >= 3)
            for _, src_keys, tgt_tokens, _, _ in corpus:
                L, M = len(src_keys) - 1, len(tgt_tokens)
                for j, t in enumerate(tgt_tokens):
                    weights, z = [], 0.0
                    pos_t = j / max(1, M - 1)
                    for i, s in enumerate(src_keys):
                        tp = t_prob[s].get(t, 1e-9)
                        w = tp * 0.15 if i == 0 else (tp * math.exp(-0.3 * (((i - 1) / max(1, L - 1)) - pos_t) ** 2) if use_pos else tp)
                        weights.append(w)
                        z += w
                    if z <= 0:
                        continue
                    inv_z = 1.0 / z
                    for i, s in enumerate(src_keys):
                        counts[s][t] += weights[i] * inv_z
                        totals[s] += weights[i] * inv_z
            tgt_totals = defaultdict(float)
            for s, td in counts.items():
                for t, val in td.items():
                    tgt_totals[t] += val
                if totals[s] > 0:
                    t_prob[s] = {t: val / (totals[s] + 2.0) for t, val in td.items()}
            rev_prob = defaultdict(dict)
            for s, td in counts.items():
                for t, val in td.items():
                    rev_prob[t][s] = val / (tgt_totals[t] + 2.0)
            print(f"  EM iter {it + 1}/6 done")

        # Decode base + Stage 3 helper validation
        base_maps, global_support = {}, Counter()
        for bcv, src_keys, tgt_tokens, m_list, tgt_indices in corpus:
            pieces = tokenized[bcv]
            L, M = len(m_list), len(tgt_tokens)
            edges = []
            for j, t_low in enumerate(tgt_tokens):
                t_stems = en_tokens(t_low) if args.lang == "en" else set()
                pos_t = j / max(1, M - 1)
                n_sc = max(math.sqrt(t_prob["NULL"].get(t_low, 1e-9) * rev_prob.get(t_low, {}).get("NULL", 1e-9)) * 0.20, 0.002)
                for i in range(1, L + 1):
                    s = src_keys[i]
                    pf, pr = t_prob[s].get(t_low, 0.0), rev_prob.get(t_low, {}).get(s, 0.0)
                    em_sc = math.sqrt(pf * pr) if (pf > 0 and pr > 0) else 0.0
                    lex_sim = 0.0
                    if args.lang == "en" and t_stems and m_list[i - 1][5]:
                        inter = len(t_stems & m_list[i - 1][5])
                        if inter > 0:
                            lex_sim = inter / math.sqrt(len(t_stems) * len(m_list[i - 1][5]))
                    combined = em_sc + 0.35 * lex_sim
                    if combined == 0.0:
                        continue
                    w = combined * math.exp(-0.15 * (((i - 1) / max(1, L - 1)) - pos_t) ** 2) * (0.05 if m_list[i - 1][3] else 1.0)
                    if w > n_sc:
                        edges.append((w, i - 1, j))
            edges.sort(reverse=True)
            used_m, used_j, j_to_m = set(), set(), {}
            for _, m_idx, j in edges:
                if m_idx not in used_m and j not in used_j:
                    j_to_m[j] = m_idx
                    used_m.add(m_idx)
                    used_j.add(j)
            p_map = {tgt_indices[j]: m_idx for j, m_idx in j_to_m.items()}
            base_maps[bcv] = p_map
            for p_idx, m_idx in p_map.items():
                global_support[(m_list[m_idx][2], pieces[p_idx][0].lower())] += 1

        verse_scriptures = {}
        for bcv, _, _, m_list, _ in corpus:
            b = bcv[0]
            pieces = tokenized[bcv]
            p_map = base_maps[bcv]
            used_m = set(p_map.values())
            L = len(m_list)
            # Sibling transfer override/seed if --transfer-from is provided
            if args.transfer_from and args.lang == "en":
                if not hasattr(main, "_sib_cache"):
                    sc = sqlite3.connect(f"file:{args.transfer_from}?mode=ro", uri=True)
                    main._sib_cache = {
                        (sb, sc_c, sv): ss
                        for sb, sc_c, sv, ss in sc.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
                    }
                    sc.close()
                sib_s = main._sib_cache.get(bcv)
                if sib_s:
                    norm_fn = norm_archaic_en if args.norm_archaic else (lambda x: x.lower())
                    en_re = re.compile(rf'(<{tag_name}\s+id="(wh?\d+)">([^<]*)</{tag_name}>)')
                    w_re = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
                    sib_toks, pos_s = [], 0
                    for sm_m in en_re.finditer(sib_s):
                        for wm in w_re.finditer(sib_s[pos_s:sm_m.start()]):
                            sib_toks.append((norm_fn(wm.group(0)), None))
                        fid = sm_m.group(2)
                        swid = int(fid[2:] if fid.startswith("wh") else fid[1:])
                        for wm in w_re.finditer(sm_m.group(3)):
                            sib_toks.append((norm_fn(wm.group(0)), swid))
                        pos_s = sm_m.end()
                    for wm in w_re.finditer(sib_s[pos_s:]):
                        sib_toks.append((norm_fn(wm.group(0)), None))
                    wid_to_mi = {m_list[mi][1]: mi for mi in range(L)}
                    tgt_pidxs = [idx for idx, (_, is_w, _) in enumerate(pieces) if is_w]
                    tgt_norm = [norm_fn(pieces[idx][0]) for idx in tgt_pidxs]
                    sm_tr = difflib.SequenceMatcher(None, [x[0] for x in sib_toks], tgt_norm, autojunk=False)
                    for tag_op, i1, i2, j1, j2 in sm_tr.get_opcodes():
                        if tag_op == "equal":
                            for k in range(i2 - i1):
                                swid = sib_toks[i1 + k][1]
                                if swid is not None and swid in wid_to_mi:
                                    mi = wid_to_mi[swid]
                                    if mi not in used_m:
                                        p_map[tgt_pidxs[j1 + k]] = mi
                                        used_m.add(mi)
            if args.helper:
                for p_idx, (text_piece, is_w, h_tag) in enumerate(pieces):
                    if not is_w or not h_tag:
                        continue
                    ht = norm_strong(h_tag)
                    cands = [mi for mi in range(L) if ht in m_list[mi][4] and not m_list[mi][3]]
                    if not cands:
                        continue
                    pos_p = p_idx / max(1, len(pieces) - 1)
                    cands.sort(key=lambda mi: abs((mi / max(1, L - 1)) - pos_p))
                    if p_idx not in p_map:
                        for mi in cands:
                            if mi not in used_m:
                                p_map[p_idx] = mi
                                used_m.add(mi)
                                break
                    else:
                        cur_mi = p_map[p_idx]
                        if ht not in m_list[cur_mi][4]:
                            for mi in cands:
                                if mi not in used_m:
                                    if global_support[(m_list[mi][2], text_piece.lower())] >= max(3, global_support[(m_list[cur_mi][2], text_piece.lower())] * 2):
                                        used_m.discard(cur_mi)
                                        p_map[p_idx] = mi
                                        used_m.add(mi)
                                    break
            prefix = "wh" if b <= 39 else "w"
            parts_out = []
            for idx, (text_piece, is_w, _) in enumerate(pieces):
                mi = p_map.get(idx) if is_w else None
                if mi is None:
                    parts_out.append(f"<{tag_name}>{text_piece}</{tag_name}>" if args.lang == "zh" else text_piece)
                else:
                    m_item = m_list[mi]
                    parts_out.append(f'<{tag_name} id="{prefix}{m_item[1]}">{text_piece}</{tag_name}>')
                    if text_piece not in m_item[10]:
                        m_item[10] = text_piece if not m_item[10] else f"{m_item[10]} / {text_piece}"
            verse_scriptures[bcv] = "".join(parts_out)

    # Stage 4: Strict v±1 sliding-window boundary recovery (low-coverage / shifted verses only)
    if args.lang == "en":
        col_support = Counter()
        for items in morph_by_verse.values():
            for m_item in items:
                if m_item[10]:
                    for part in m_item[10].split(" / "):
                        col_support[(m_item[2], part.strip().lower())] += 1
        en_split_re = re.compile(rf'(<{tag_name}\s+id="[^"]+">[^<]*</{tag_name}>)')
        sw_recovered = 0
        for bcv, scripture in list(verse_scriptures.items()):
            b = bcv[0]
            nbrs = adj_verses.get(bcv)
            if not nbrs:
                continue
            cand_m = []
            for nbcv in nbrs:
                n_items = morph_by_verse.get(nbcv, [])
                if not n_items:
                    continue
                filled_ratio = sum(1 for x in n_items if x[10]) / len(n_items)
                for m_item in n_items:
                    if not m_item[10] and not m_item[3]:
                        cand_m.append((m_item, filled_ratio < 0.40))
            if not cand_m:
                continue
            parts = en_split_re.split(scripture)
            untagged = []
            for p_idx, part in enumerate(parts):
                if not part or en_split_re.fullmatch(part):
                    continue
                for wm in re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)?", part):
                    wtxt = wm.group(0)
                    if wtxt.lower() not in STOPWORDS:
                        untagged.append((p_idx, wm.start(), wm.end(), wtxt))
            if not untagged:
                continue
            edges = []
            for u_idx, (_, _, _, wtxt) in enumerate(untagged):
                wlow, wstems = wtxt.lower(), en_tokens(wtxt)
                for m_idx, (m_item, is_low_cov) in enumerate(cand_m):
                    sup = col_support.get((m_item[2], wlow), 0)
                    lex = 0.0
                    if wstems and m_item[5]:
                        inter = len(wstems & m_item[5])
                        if inter > 0:
                            lex = inter / math.sqrt(len(wstems) * len(m_item[5]))
                    if (is_low_cov and (sup >= 3 or lex >= 0.7)) or (lex >= 0.7 and sup >= 1):
                        edges.append((sup + 10.0 * lex, u_idx, m_idx))
            if not edges:
                continue
            edges.sort(reverse=True)
            used_u, used_m, part_reps = set(), set(), defaultdict(list)
            prefix = "wh" if b <= 39 else "w"
            for _, u_idx, m_idx in edges:
                if u_idx in used_u or m_idx in used_m:
                    continue
                used_u.add(u_idx)
                used_m.add(m_idx)
                p_idx, s_pos, e_pos, wtxt = untagged[u_idx]
                m_item, _ = cand_m[m_idx]
                part_reps[p_idx].append((s_pos, e_pos, f"{prefix}{m_item[1]}", wtxt))
                m_item[10] = wtxt
                sw_recovered += 1
            if part_reps:
                for p_idx, reps in part_reps.items():
                    reps.sort()
                    orig_p, buf, cur_pos = parts[p_idx], [], 0
                    for s_pos, e_pos, full_id, wtxt in reps:
                        buf.append(orig_p[cur_pos:s_pos])
                        buf.append(f'<{tag_name} id="{full_id}">{wtxt}</{tag_name}>')
                        cur_pos = e_pos
                    buf.append(orig_p[cur_pos:])
                    parts[p_idx] = "".join(buf)
                verse_scriptures[bcv] = "".join(parts)
        print(f"Stage 4 v±1 sliding-window recovered: {sw_recovered} words.")

        # Stage 5a & 5b: Function-word peeling & multi-word splitting using morphology reference columns
        en_tag_re = re.compile(rf'(<{tag_name}\s+id="(wh?\d+)">([^<]*)</{tag_name}>)')
        peeled_count, splits_done, tokens_assigned = 0, 0, 0
        for bcv, scripture in list(verse_scriptures.items()):
            b = bcv[0]
            items = morph_by_verse.get(bcv, [])
            if not items:
                continue
            prefix = "wh" if b <= 39 else "w"
            wid_to_idx = {it[1]: idx for idx, it in enumerate(items)}

            for _pass in range(3):
                pass_changed = False
                parts, pos = [], 0
                for m in en_tag_re.finditer(scripture):
                    if m.start() > pos:
                        parts.append([scripture[pos:m.start()], None])
                    parts.append([m.group(3), m.group(2)])
                    pos = m.end()
                if pos < len(scripture):
                    parts.append([scripture[pos:], None])
                new_parts = []
                for p_txt, full_id in parts:
                    if not full_id:
                        new_parts.append((p_txt, None))
                        continue
                    wid = int(full_id[2:] if full_id.startswith("wh") else full_id[1:])
                    m_idx = wid_to_idx.get(wid)
                    m_split = re.match(r"^([A-Za-z]+)(\s+)(.+)$", p_txt) if m_idx is not None else None
                    if not m_split or m_split.group(1).lower() not in FUNC_WORDS:
                        new_parts.append((p_txt, full_id))
                        continue
                    first_w, sp, rest = m_split.group(1), m_split.group(2), m_split.group(3)
                    first_low = first_w.lower()
                    target_idx = None
                    for delta in (-1, -2, -3, -4, 1, 2):
                        ci = m_idx + delta
                        if 0 <= ci < len(items) and items[ci][10] == "" and first_low in items[ci][6]:
                            target_idx = ci
                            break
                    if target_idx is not None:
                        t_item = items[target_idx]
                        t_item[10] = first_w
                        items[m_idx][10] = rest if items[m_idx][10] == p_txt else items[m_idx][10].replace(p_txt, rest, 1)
                        new_parts.extend([(first_w, f"{prefix}{t_item[1]}"), (sp, None), (rest, full_id)])
                        peeled_count += 1
                        pass_changed = True
                    else:
                        new_parts.append((p_txt, full_id))
                if pass_changed:
                    scripture = "".join(f'<{tag_name} id="{fid}">{txt}</{tag_name}>' if fid else txt for txt, fid in new_parts)
                    verse_scriptures[bcv] = scripture
                else:
                    break

            parts, pos = [], 0
            for m in en_tag_re.finditer(scripture):
                if m.start() > pos:
                    parts.append([scripture[pos:m.start()], None])
                parts.append([m.group(3), m.group(2)])
                pos = m.end()
            if pos < len(scripture):
                parts.append([scripture[pos:], None])

            new_parts, verse_changed = [], False
            for p_txt, full_id in parts:
                if not full_id:
                    new_parts.append((p_txt, None))
                    continue
                wid = int(full_id[2:] if full_id.startswith("wh") else full_id[1:])
                m_idx = wid_to_idx.get(wid)
                wtoks = re.split(r"(\s+)", p_txt)
                word_positions = [i for i, wt in enumerate(wtoks) if wt and not wt.isspace() and re.fullmatch(r"[A-Za-z]+(?:'[A-Za-z]+)?", wt)]
                if m_idx is None or not word_positions:
                    new_parts.append((p_txt, full_id))
                    continue
                # Search empty non-object-marker WordIDs in the same verse, ordered by proximity
                cand_indices = [m_idx] + sorted(
                    [ci for ci in range(len(items)) if ci != m_idx and items[ci][10] == "" and not items[ci][9]],
                    key=lambda ci: abs(ci - m_idx),
                )
                if len(cand_indices) == 1:
                    new_parts.append((p_txt, full_id))
                    continue
                # Single-word reassignment if host has 0 match in core lexical columns AND host has another word in verse AND empty WordID has exact match >= 2.0
                if len(word_positions) == 1:
                    w = wtoks[word_positions[0]]
                    w_stem = stem_en(w)
                    host_core = (w.lower() in items[m_idx][5]) or (w_stem in items[m_idx][5])
                    if not host_core and len(items[m_idx][10].split()) > 1:
                        best_ci = None
                        for ci in cand_indices[1:]:
                            if match_score(w, items[ci][7], items[ci][8]) >= 2.0:
                                best_ci = ci
                                break
                        if best_ci is not None:
                            items[best_ci][10] = w
                            if " / " in items[m_idx][10]:
                                rem_parts = [x for x in items[m_idx][10].split(" / ") if x != p_txt.strip()]
                                items[m_idx][10] = " / ".join(rem_parts)
                            else:
                                items[m_idx][10] = re.sub(rf"(?<!\S){re.escape(p_txt.strip())}(?!\S)", "", items[m_idx][10]).strip()
                            new_parts.append((p_txt, f"{prefix}{items[best_ci][1]}"))
                            tokens_assigned += 1
                            splits_done += 1
                            verse_changed = True
                            continue
                    new_parts.append((p_txt, full_id))
                    continue
                if not any(match_score(wtoks[wp], items[m_idx][7], items[m_idx][8]) >= 1.2 for wp in word_positions):
                    new_parts.append((p_txt, full_id))
                    continue
                word_assign, used_neighbors = {}, set()
                for wp in word_positions:
                    w = wtoks[wp]
                    host_sc = match_score(w, items[m_idx][7], items[m_idx][8])
                    best_ci, best_sc = m_idx, host_sc
                    for ci in cand_indices[1:]:
                        if ci in used_neighbors:
                            continue
                        sc = match_score(w, items[ci][7], items[ci][8])
                        if sc >= 2.0 and (sc > host_sc or host_sc < 2.0 or sum(1 for wp2 in word_positions if wp2 != wp and match_score(wtoks[wp2], items[m_idx][7], items[m_idx][8]) >= 2.0) >= 1):
                            if sc > best_sc or (sc == best_sc and ci != m_idx and host_sc == 0.0):
                                best_sc, best_ci = sc, ci
                    if best_ci != m_idx and any(wp2 != wp and word_assign.get(wp2, m_idx) == m_idx for wp2 in word_positions):
                        word_assign[wp] = best_ci
                        used_neighbors.add(best_ci)
                    else:
                        word_assign[wp] = m_idx
                if not any(ci != m_idx for ci in word_assign.values()):
                    new_parts.append((p_txt, full_id))
                    continue
                tok_cis = [(wt, word_assign[i] if i in word_assign else None) for i, wt in enumerate(wtoks) if wt]
                for i in range(1, len(tok_cis) - 1):
                    if tok_cis[i][1] is None and tok_cis[i][0].isspace() and tok_cis[i - 1][1] is not None and tok_cis[i - 1][1] == tok_cis[i + 1][1]:
                        tok_cis[i] = (tok_cis[i][0], tok_cis[i - 1][1])
                grouped = []
                for wt, ci in tok_cis:
                    if grouped and grouped[-1][1] == ci:
                        grouped[-1][0] += wt
                    else:
                        grouped.append([wt, ci])
                ci_phrases = defaultdict(list)
                for grp_txt, ci in grouped:
                    if ci is not None:
                        ci_phrases[ci].append(grp_txt)
                        new_parts.append((grp_txt, f"{prefix}{items[ci][1]}"))
                    else:
                        new_parts.append((grp_txt, None))
                for ci, plist in ci_phrases.items():
                    phrase = " ".join(plist)
                    it = items[ci]
                    if ci == m_idx:
                        it[10] = phrase if it[10] == p_txt else it[10].replace(p_txt, phrase, 1)
                    else:
                        it[10] = phrase
                        tokens_assigned += 1
                splits_done += 1
                verse_changed = True
            if verse_changed:
                verse_scriptures[bcv] = "".join(f'<{tag_name} id="{fid}">{txt}</{tag_name}>' if fid else txt for txt, fid in new_parts)
        print(f"Stage 5a peeled {peeled_count} function words; Stage 5b split {splits_done} phrases (+{tokens_assigned} WordIDs).")

    elif args.lang == "zh" and "LCT" in existing_cols:
        # Guarded LCT refinement for Chinese Bibles (excludes suppressed particles & noisy single chars)
        lct_map = {
            rowid: (lct_v or "").replace("上帝", "神").translate(ZH_VAR_NORM).strip()
            for rowid, lct_v in m_cur.execute("SELECT rowid, LCT FROM morphology").fetchall()
        }
        zh_span_re = re.compile(rf'(<{tag_name}(?:\s+id="([^"]+)")?>([^<]*)</{tag_name}>)')
        lct_recovered = 0
        for bcv, scripture in list(verse_scriptures.items()):
            b = bcv[0]
            items = morph_by_verse.get(bcv, [])
            if not items or f"<{tag_name}>" not in scripture:
                continue
            cand_m = [it for it in items if not it[10] and not it[3] and lct_map.get(it[0])]
            if not cand_m:
                continue
            spans, pos = [], 0
            for m in zh_span_re.finditer(scripture):
                if m.start() > pos:
                    spans.append([scripture[pos:m.start()], None, False])
                spans.append([m.group(3), m.group(2), True])
                pos = m.end()
            if pos < len(scripture):
                spans.append([scripture[pos:], None, False])
            untagged_idx = [
                idx for idx, (txt, tid, is_z) in enumerate(spans)
                if is_z and tid is None and txt and not PUNCT_ONLY_RE.fullmatch(txt) and not txt.startswith("〔註：")
            ]
            if not untagged_idx:
                continue
            edges = []
            for s_idx in untagged_idx:
                nt = spans[s_idx][0].replace("上帝", "神").translate(ZH_VAR_NORM).strip()
                if not nt or not ZH_CHAR_RE.search(nt):
                    continue
                for m_idx, it in enumerate(cand_m):
                    nl = lct_map[it[0]]
                    sc = 0.0
                    if nt == nl:
                        if not (len(nt) == 1 and nt in ZH_NOISY_CHARS):
                            sc = 3.0 if len(nt) >= 2 else 1.5
                    elif len(nt) >= 2 and len(nl) >= 2 and (nt in nl or nl in nt):
                        sc = 2.0
                    if sc > 0:
                        edges.append((sc, s_idx, m_idx))
            if not edges:
                continue
            edges.sort(reverse=True)
            used_s, used_m, changed = set(), set(), False
            prefix = "wh" if b <= 39 else "w"
            for _, s_idx, m_idx in edges:
                if s_idx in used_s or m_idx in used_m:
                    continue
                used_s.add(s_idx)
                used_m.add(m_idx)
                it = cand_m[m_idx]
                txt = spans[s_idx][0]
                spans[s_idx][1] = f"{prefix}{it[1]}"
                it[10] = txt
                lct_recovered += 1
                changed = True
            if changed:
                verse_scriptures[bcv] = "".join(
                    (f'<{tag_name} id="{tid}">{txt}</{tag_name}>' if tid else (f"<{tag_name}>{txt}</{tag_name}>" if is_z else txt))
                    for txt, tid, is_z in spans
                )
        print(f"Stage 5 (zh) LCT-guided recovered: {lct_recovered} words.")

    # Update Verses table
    b_cur.executemany(
        "UPDATE Verses SET Scripture = ? WHERE Book = ? AND Chapter = ? AND Verse = ?",
        [(s, b, c, v) for (b, c, v), s in verse_scriptures.items()],
    )
    b_conn.commit()
    mismatches = sum(
        1 for b, c, v, s in b_cur.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0").fetchall()
        if strip_re.sub("", s) != target_verses[(b, c, v)]
    )
    b_conn.close()
    print(f"Verses updated & verified: {mismatches} mismatches out of {len(target_verses)} verses.")

    # Always update tagged_translations.sqlite column via rowid (default: bible filename without .bible)
    col_name = args.col or os.path.splitext(os.path.basename(args.bible))[0]
    q_col = '"' + col_name.replace('"', '""') + '"'
    if col_name not in existing_cols:
        m_cur.execute(f'ALTER TABLE morphology ADD COLUMN {q_col} TEXT DEFAULT ""')
    else:
        m_cur.execute(f'UPDATE morphology SET {q_col} = ""')
    m_conn.commit()
    updates = [(m_item[10], m_item[0]) for items in morph_by_verse.values() for m_item in items if m_item[10]]
    m_cur.executemany(f"UPDATE morphology SET {q_col} = ? WHERE rowid = ?", updates)
    m_conn.commit()
    print(f"Updated morphology.{col_name}: {len(updates)} rows filled.")
    m_conn.close()

    if not args.skip_bible_table:
        tag_bible_table(out_bible, tag_name)
    create_verses_plain(out_bible)
    print(f"Total elapsed: {time.time() - t0:.2f}s (output: {out_bible})")


if __name__ == "__main__":
    main()

