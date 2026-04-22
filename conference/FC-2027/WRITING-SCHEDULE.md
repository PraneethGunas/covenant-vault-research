# FC 2027 Writing Schedule

**Target:** 15 pp LNCS paper ready to submit by **Sep 15, 2026**.
**Time budget:** ~4 months (post-defense May 1 through Sep 15, 2026).
**Draft cycles:** 3 (initial, advisor-reviewed, externally-reviewed).

This is a week-by-week plan. Adjust ±1 week for real-world slippage; watch the drop-dead dates.

---

## Phase 0 — Pre-defense preparation (before May 1, 2026)

**Time:** ≤1 hour of prep work; not a writing phase.

- [ ] Read `OUTLINE.md` once end-to-end
- [ ] Skim `../FRAMING-GUIDE.md` § "FC 2027 — Primary target"
- [ ] Verify skeleton compiles (see `paper/SETUP.md`)
- [ ] Do NOT start writing — focus on the defense

---

## Phase 1 — Port and preprint (May 1 – May 28, 2026, 4 weeks)

**Goal:** Get a full-length, non-anonymized preprint on IACR ePrint + arXiv. This serves double duty:
1. Establishes priority date
2. Forces a clean "port" of thesis content into paper-like structure

### Week 1 (May 1–7) — Thesis close-out + workspace setup

| Day | Action |
|---|---|
| Mon May 4 | Submit thesis to VT graduate school (PDF + metadata) |
| Tue May 5 | Verify `conference/FC-2027/paper/` skeleton compiles |
| Wed May 6 | Copy `Thesis/references.bib` → `conference/FC-2027/paper/references.bib`; cross-check entries |
| Thu May 7 | Install LNCS class (`sudo tlmgr install llncs`); run `pdflatex fc27-paper.tex` end-to-end |
| Fri May 8 | Commit initial workspace; tag `v0.1-skeleton` |

**Deliverable:** `paper/fc27-paper.pdf` compiles (skeleton with placeholder text).

### Week 2 (May 11–17) — Port §3 Impossibility Results (THE CORE)

**Priority:** Get the two theorems rendered correctly in LNCS format.

| Day | Action |
|---|---|
| Mon | Copy thesis `ch5_security.tex` § 5.1–5.2 into `paper/sections/03-impossibility.tex` |
| Tue | Adapt Definition 5.1 → Definition 3.1; Proposition 5.2 → Proposition 3.2 |
| Wed | Adapt Theorem 5.3 → Theorem 3.3; port proof |
| Thu | Port §5.3 two-dimensional tradeoff as § 3.3; verify TikZ compiles in LNCS two-column |
| Fri | Compile; read aloud to self; spot-check proof gaps |
| Sat | Trim: cut redundant sentences; ensure §3 fits 3pp |

**Deliverable:** Draft §3 Impossibility Results (3pp).

### Week 3 (May 18–24) — Intro + Background

| Day | Action |
|---|---|
| Mon | Draft §1 from scratch (don't port thesis Ch1 verbatim — it's too long and academic) |
| Tue | Draft §1.4 contribution summary paragraph; check alignment with §3 |
| Wed | Port thesis Ch2 → §2; reduce 13pp → 2pp; create consolidated 4-panel covenant mechanism figure |
| Thu | Port threat taxonomy table; point to Appendix B |
| Fri | End-to-end read: Abstract + §1 + §2 + §3 |
| Sat | Verify coherent narrative arc |

**Deliverable:** Drafts §1 (1.5pp), §2 (2pp), §3 (3pp). Running total: 6.5pp.

### Week 4 (May 25–31) — Preprint assembly and release

| Day | Action |
|---|---|
| Mon | Fill in §4, §5, §6, §7, §8 with *thesis-extracted* content (no compression yet — this is the preprint, full-length is OK) |
| Tue | Draft abstract (200 words) and keywords |
| Wed | Compile preprint version: `paper/fc27-preprint.tex` (non-anonymized, 40–60 pp with appendices) |
| Thu | **Upload to IACR ePrint** (https://eprint.iacr.org/submit) — target May 20 latest |
| Fri | **Upload to arXiv** (cs.CR primary) — target May 22 |
| Sat | Announce on bitcoin-dev mailing list, Delving Bitcoin forum, Twitter |

**Deliverable:** Public preprint with ePrint ID + arXiv ID. Community feedback starts flowing.

---

## Phase 2 — First anonymized draft (June 2026, 4 weeks)

**Goal:** Compress preprint → 15pp anonymized FC version. First full draft.

### Week 5 (Jun 1–7) — Compression pass

| Day | Action |
|---|---|
| Mon | Measure current page count against 15pp target (expect 20–25pp) |
| Tue | Compress §4 Empirical: keep 2 key tables, move 6 to appendix |
| Wed | Compress §2 Background: cut 0.5pp from taxonomy; consolidate mechanism figure further if needed |
| Thu | Compress §6 Related Work: 2pp → 1pp; keep lineage paragraph structure |
| Fri | Verify page count = 14–15pp body; refactor overflow to appendix |
| Sat | Rest |

**Deliverable:** 15pp body draft (non-anonymized).

### Week 6 (Jun 8–14) — Anonymization pass

| Day | Action |
|---|---|
| Mon | Replace author block with `\author{Anonymous Authors}` and `\institute{Anonymous Institution}` |
| Tue | Run `grep -rin "praneeth\|gunas\|virginia tech\|arlington\|blacksburg\|matsuo\|wenjing\|na meng" paper/` and scrub each hit |
| Wed | Anonymize GitHub repo URLs: `anonymized-repo` placeholders |
| Thu | Anonymize "we contributed upstream to simple-cat-csfs-vault" → "[anonymized contribution]" |
| Fri | Remove VT frontmatter (dedication, acks from thesis) if any leaked |
| Sat | Verify: anon PDF + diff against non-anon preprint |

**Deliverable:** `paper/fc27-paper.pdf` fully anonymized.

### Week 7 (Jun 15–21) — Advisor review round 1

| Day | Action |
|---|---|
| Mon | Send to Matsuo (chair) with 1-page cover note: goals, page count, specific asks |
| Tue | Send to Lou (co-chair) and Meng (committee) |
| Wed–Fri | Allow reviewers time (typical turnaround: 1 week) |
| Sat | Read any early feedback |

**Deliverable:** Advisor feedback gathered.

### Week 8 (Jun 22–28) — Advisor revisions

| Day | Action |
|---|---|
| Mon–Tue | Aggregate feedback; categorize (content / framing / polish) |
| Wed | Address content feedback: revise §3, §4 proofs/measurements |
| Thu | Address framing feedback: revise §1, abstract |
| Fri | Address polish feedback: typos, citations |
| Sat | Re-compile; re-verify page count |

**Deliverable:** Draft v2 (post-advisor).

---

## Phase 3 — External review + polish (July 2026, 4 weeks)

**Goal:** Get one more round of expert eyes before submission.

### Week 9 (Jun 29 – Jul 5) — External-review outreach

External reviewers to approach (all optional, but high-leverage):

- **Jeremy Rubin** — CTV author; best for §2 CTV accuracy, §3 theorem statement
- **Salvatore Ingala** — CCV + pymatt author; §2 CCV accuracy, §4 measurement validity
- **James O'Beirne** — OP_VAULT author; §2 OP_VAULT accuracy, §5 deployment guidance
- **Andrew Poelstra** — CAT+CSFS, Simplicity author; §2 CAT+CSFS accuracy, §6 related work
- **Russell O'Connor** — Simplicity author; §2 Simplicity section

| Day | Action |
|---|---|
| Mon | Email Rubin and Ingala (priority): "30 min read, pass for BIP-level accuracy" |
| Tue | Email O'Beirne and Poelstra |
| Wed | Email O'Connor |
| Thu–Sat | Patience window |

**Deliverable:** External-review requests sent.

### Week 10 (Jul 6–12) — External review window

| Day | Action |
|---|---|
| Mon | Follow up if no acknowledgment |
| Tue–Fri | Receive feedback rolling |
| Sat | Consolidate feedback |

**Deliverable:** External feedback gathered.

**Note:** If ACM DeFi @ CCS 2026 is a target (deadline ~Jul 10), this week is the submission deadline. Otherwise skip.

### Week 11 (Jul 13–19) — External revisions

| Day | Action |
|---|---|
| Mon | Categorize external feedback by severity |
| Tue–Wed | Address high-priority corrections (likely §2 BIP accuracy) |
| Thu | Re-cite anything reviewers pointed to |
| Fri | Check Pull Request-style: respond to each suggestion in writing |
| Sat | Re-compile; send redline to reviewers |

**Deliverable:** Draft v3 (post-external).

### Week 12 (Jul 20–26) — Polish pass 1

| Day | Action |
|---|---|
| Mon | Read full paper aloud; flag awkward sentences |
| Tue | Sentence-level rewrite pass |
| Wed | Figure captions pass — each caption self-contained |
| Thu | Table caption pass |
| Fri | Equation labeling consistency |
| Sat | Cross-reference pass (all `\ref{}` resolve) |

**Deliverable:** Draft v4 (linguistic polish).

---

## Phase 4 — Final preparation (August 2026, 4 weeks)

### Week 13 (Jul 27 – Aug 2) — Appendix finalization

| Day | Action |
|---|---|
| Mon–Tue | Appendix A Alloy: finalize; verify assertions compile in Alloy |
| Wed | Appendix B full threat matrix: 11×4 table |
| Thu | Appendix C per-experiment measurements: port from thesis Ch4 |
| Fri | Appendix page count check |
| Sat | References re-sort, verify all have DOI/URL |

**Deliverable:** Complete paper + appendices.

### Week 14 (Aug 3–9) — Reproducibility artifact

Even if FC doesn't require it, reviewers appreciate.

| Day | Action |
|---|---|
| Mon | Anonymized repo — `zenodo.org` deposit, DOI assigned |
| Tue | Docker image tag — push to anonymized Docker Hub |
| Wed | README with one-command experiment replay |
| Thu | Verify experiments reproduce on a clean machine |
| Fri | Update §4 to reference artifact |
| Sat | Rest |

**Deliverable:** Reproducibility artifact online.

### Week 15 (Aug 10–16) — Polish pass 2

| Day | Action |
|---|---|
| Mon | Color-blind safety check (viridis palette on plots) |
| Tue | Grayscale-print check (LNCS proceedings are B&W) |
| Wed | Bibliography consistency (all `splncs04.bst` format) |
| Thu | Spell check (aspell or LanguageTool) |
| Fri | Grammar pass |
| Sat | Anonymization re-verification |

**Deliverable:** Draft v5 (publication-ready).

### Week 16 (Aug 17–23) — Final read-through

| Day | Action |
|---|---|
| Mon | Print and read hard copy — catches things screen doesn't |
| Tue | Address last-minute catches |
| Wed | Friend-of-committee read (someone outside Bitcoin but in security) |
| Thu | Final compilation; verify PDF/A compliance |
| Fri | Checksum the submission PDF; backup to git tag |
| Sat | Rest + internal sanity check |

**Deliverable:** Submission-ready PDF.

---

## Phase 5 — Submission (early September 2026, 2 weeks)

### Week 17 (Aug 24–30) — Submission pre-flight

| Day | Action |
|---|---|
| Mon | Check FC'27 CFP (should be live by now) for any format updates |
| Tue | Verify HotCRP account |
| Wed | Final anonymization check |
| Thu | Supplementary material prep (artifact link, data archive) |
| Fri | Draft the submission-portal text (title, keywords, track selection) |
| Sat | **Submit a full dry run** — check every form field |

**Deliverable:** Submission account prepared.

### Week 18 (Aug 31 – Sep 6) — Submission buffer

| Day | Action |
|---|---|
| Mon | Last revision opportunity |
| Tue | Secondary read |
| Wed | Committee courtesy send — "I'm submitting on Sep 15; here's the final" |
| Thu | Polish |
| Fri | Rest |
| Sat | Prepare submission checklist |

### Week 19 (Sep 7–13) — Pre-deadline (final week)

| Day | Action |
|---|---|
| Mon | Do NOT make substantive changes this week |
| Tue | Verify all URLs in bibliography still resolve |
| Wed | Upload to HotCRP as draft (early submission = less stress) |
| Thu | Verify submission renders correctly in portal |
| Fri | **Submit** — target end of day Friday Sep 12 |
| Sat–Sun | Monitor for confirmation email |

### Deadline day

**Sep 15, 2026 (Tuesday):** ★★★ FC'27 submission deadline ★★★

Even though we aimed for Sep 12, submission portals have been known to lag, and FC sometimes allows a weekend buffer. Target submission by Sep 12 AoE (Anywhere-on-Earth) to have room for ~72h of platform troubleshooting.

---

## Phase 6 — Post-submission (mid-September onward)

### Week 20+ (Sep 16 – Nov 20)

- No author action required during review period
- Do NOT post the final version publicly until notification
- Keep an eye on bitcoin-dev for parallel work that might need response
- Monitor conference dates for registration/travel planning

### Nov 20–25 (expected) — Notification

- Accept: rebuttal if permitted (FC typically allows)
- Reject: read reviews, extract constructive feedback, cascade to CAAW (~Jan 2027)

### Jan 12, 2027 — Camera-ready (if accepted)

- Address reviewer comments
- Final non-anonymized version
- Copyright forms

### Mar 2–6, 2027 — FC 2027 conference

- Travel arrangements
- Prepare 20-minute presentation (slides + demo)
- Network with reviewers, BIP authors

---

## Risk management

### Schedule slippage scenarios

| Slippage | Symptom | Recovery |
|---|---|---|
| 1 week late | Week 17 (Aug 24) not reached | Skip external review round 2; submit on schedule |
| 2 weeks late | Preprint not posted by May 31 | Post preprint anyway; compress Phase 2 timeline |
| 1 month late | No draft by end of July | Aim for CAAW (Jan 2027) instead of FC main; restructure as empirical |
| >1 month late | No draft by end of August | Skip FC'27; retarget CAAW 2027 or ICBC 2028 SoK |

### Content risk

**Risk:** Someone publishes similar work parallel to us.
**Mitigation:** Preprint to ePrint by May 20 establishes priority.

**Risk:** FC'27 rejects with "too niche" feedback.
**Mitigation:** CAAW @ FC 2027 (Jan 2027) deadline leaves 8 weeks turnaround for reformatting.

**Risk:** External reviewers don't respond.
**Mitigation:** Advisor review is the minimum; external is a bonus.

### Energy risk

**Risk:** Burnout after thesis defense — hard to start paper May 1.
**Mitigation:** Take 1 full week off between defense (Apr 29) and writing (May 8 onward).

---

## Daily writing ritual (once Phase 1 begins)

1. **Morning block:** 2 hours focused writing (pomodoro × 4)
2. **Midday:** Read latest bitcoin-dev / Delving Bitcoin for 20 min — catch parallel work
3. **Afternoon:** 1 hour "edit previous day's writing" (cognitive distance helps)
4. **Evening:** Commit to git with dated message (e.g., `2026-05-12: port thm 5.3 to §3.2`)

Keep commit discipline — the thesis repo's git log was a primary anti-stall mechanism during the thesis itself.

---

## Definition of "done"

A section is "done" when all of:
- [ ] Compiles without warnings in the `paper/fc27-paper.tex` context
- [ ] No overfull `\hbox` in the log for its lines
- [ ] All `\ref{}` and `\cite{}` resolve
- [ ] Read aloud once without breath issues
- [ ] Passed advisor review (at minimum)
- [ ] Page count within budget (±10%)

The paper is "done" when all 8 sections + 3 appendices are done AND:
- [ ] Abstract reads well as a standalone document
- [ ] No more than 5 overfull hboxes total
- [ ] Anonymization verified (grep returns 0 matches)
- [ ] Preprint version exists (non-anonymized)
- [ ] Submission checklist 100% complete

---

**Last updated:** 2026-04-17
