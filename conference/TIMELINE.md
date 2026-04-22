# Conference Submission Timeline — Quick Reference

**Primary path:** FC 2027 main conference submission, ~Sep 15, 2026 deadline.

See `SUBMISSION-STRATEGY.md` for full context.

---

## Chronological deadline calendar (confirm each date ~3 months prior)

### 2026

| Date | Event | Action required |
|---|---|---|
| **Apr 29, 2026** | Thesis defense (VT, Arlington) | Defend |
| **May 1–7** | Final thesis submission to VT graduate school | Submit per VT ETD procedure |
| **May 8–15** | Create LNCS paper skeleton | Port `thesis.tex` → `fc27-paper.tex` in `llncs.cls` |
| **May 15** | **★ IACR ePrint submission** | Upload 15pp + appendix, non-anonymized |
| **May 20** | arXiv mirror | Upload same PDF + .tex source, cross-link with ePrint |
| **May 22–25** | Announce on bitcoin-dev, Delving Bitcoin | Get community feedback |
| **May 26–31** | First draft of FC'27 paper | Compress 110pp → 15pp, anonymize |
| **Jun 1–15** | Advisor review round 1 | Send to Matsuo/Lou/Meng |
| **Jun 15–30** | Revise draft | Incorporate committee feedback |
| **Jul 1–15** | External review | Send to Rubin / Ingala / O'Beirne / Poelstra |
| **Jul 10** | ⚠ **ACM DeFi @ CCS 2026 deadline (optional)** | 8pp workshop paper if desired |
| **Jul 15–31** | Final revisions | Incorporate external feedback |
| **Aug 1–31** | Polish + artifact prep | Reproducibility appendix, Zenodo upload |
| **Aug 6** | ⚠ NDSS 2027 Fall cycle deadline (stretch, skip) | Only if Fee-Inversion reframed as attack |
| **Sep 15** | ★★★ **FC 2027 SUBMISSION DEADLINE** ★★★ | Submit via FC'27 HotCRP |
| **Oct–Nov** | Review period | No action |
| **Nov 13** | ⚠ IEEE S&P 2027 Cycle 2 deadline (stretch, skip) | Only if mechanized proofs added |
| **Nov ~20–25** | **FC 2027 notification** | React to outcome |

### If FC accepts:

| Date | Event | Action required |
|---|---|---|
| **Dec 1–15, 2026** | Rebuttal + revisions | Address reviewer comments |
| **Jan 12, 2027** | FC'27 camera-ready | Finalize and submit |
| **Mar 2–6, 2027** | FC'27 conference | Travel, present, network |

### If FC rejects (cascade):

| Date | Event | Action required |
|---|---|---|
| **Dec 2026** | Diagnose rejection | Read reviews, prioritize revisions |
| **Jan 15, 2027** | **CAAW 2027 @ FC deadline (primary fallback)** | 12pp workshop; empirical-focused reframing |
| **Feb 2027** | MARBLE 2027 deadline | Mathematical-economics framing |
| **May 28, 2027** | AFT 2027 deadline | 20pp LIPIcs; cross-chain reframing |
| **Dec 1, 2027** | ICBC 2028 SoK deadline | 16pp IEEE; systematization framing |

---

## 30-day sprint schedule (May 1 – May 31, 2026)

**Goal:** Have a solid preprint posted to ePrint + arXiv within 30 days of defense.

### Week 1 (May 1–7)
- Submit thesis to VT graduate school
- Back up thesis repo, tag final version as `v1.0-defended`
- Download `llncs.cls`, `splncs04.bst`, LNCS sample document
- Create `Thesis/conference-paper/` subdir; copy `thesis.tex` → `fc27-paper.tex`

### Week 2 (May 8–14)
- Port `\documentclass` → LNCS
- Remove VT frontmatter (title page, dedication, acks, committee)
- Replace VTthesis-specific macros with LNCS equivalents
- Rebuild bibliography under `splncs04.bst`
- Verify compile

### Week 3 (May 15–21)
- Compress chapters into 15pp target
  - Intro: 9pp → 1.5pp
  - Background: 13pp → 2pp + consolidated mechanism figure
  - Methodology: 12pp → 1.5pp
  - Results: 17pp → 3pp + 2 key tables
  - Security (the heart): 35pp → 5pp
  - Formal models: → 1pp + full Alloy in appendix
  - Discussion: → 0.5pp
  - Related Work: → 1pp
  - Conclusion: → 0.5pp
- **Anonymize for ePrint? No** — ePrint is non-anonymous by convention, so keep author names/affiliation here
- Upload to IACR ePrint: eprint.iacr.org/submit

### Week 4 (May 22–28)
- Upload to arXiv (cs.CR primary, cs.DC secondary)
- Cross-link ePrint ↔ arXiv
- Announce on bitcoin-dev mailing list + Delving Bitcoin forum
- Start drafting the anonymized FC version

### Week 5 (May 29–31) + overflow into June
- Begin anonymization for FC'27
- Share non-anonymized preprint with advisors
- Begin collecting external feedback

---

## Critical dates to verify in mid-2026

These are estimated based on historical patterns. Confirm ~3 months before each target:

| Venue | Estimated deadline | Verify at |
|---|---|---|
| **FC 2027** | **~Sep 15, 2026** | https://ifca.ai (watch for `fc27.ifca.ai`, expected live ~Jun 2026) |
| **CAAW 2027** | ~Jan 15, 2027 | https://caaw.io/2027/ |
| **ACM DeFi 2026** | ~Jul 10, 2026 | https://defiwork.shop/defi2026/ |
| **MARBLE 2027** | ~Feb 15, 2027 | https://marble-conference.org |
| **AFT 2027** | ~May 28, 2027 | https://aft.acm.org |
| **ICBC 2028 SoK** | ~Dec 1, 2027 | https://icbc2028.ieee-icbc.org |
| **NDSS 2027 Fall** | ~Aug 6, 2026 | https://ndss-symposium.org |
| **IEEE S&P 2027 C2** | ~Nov 13, 2026 | https://ieee-security.org |

---

## Drop-dead dates (miss these, the plan falls apart)

1. **May 31, 2026** — Preprint must be on ePrint/arXiv by now or community loses freshness
2. **Sep 15, 2026** — FC'27 submission. **No earlier submission is better.** Do not submit to ACM DeFi (Jul 10) if it would compromise the FC draft
3. **Jan 15, 2027** — If FC rejects Nov 20, you have 8 weeks to produce a CAAW version

---

## Ongoing passive actions (monthly)

- Check `bitcoin-dev` and Delving Bitcoin for new covenant research (update refs if needed)
- Check arXiv `cs.CR` weekly for parallel work on covenants/vaults
- Monitor FC'27, CAAW 2027, NDSS CFP pages for confirmed dates
- Keep ePrint/arXiv versions in sync if material changes

---

**Last verified:** 2026-04-17
**Next verification:** 2026-06-01 (confirm FC'27 deadline on official CFP)
