# DRAFT — R&D concept sheet 1: Retrieval persistence and evaluation reliability
Status: DRAFT concept, not a funded project. Checked: 2026-10-08 (America/New_York).

## Problem hypothesis
- Retrieval-augmented AI systems can silently degrade when the stored index, the served index and the source documents drift apart; small teams often lack tests that catch this before users do. [C-RD-01] [A-RD-01]
- The founder's C.Walts work covered hybrid retrieval, persistence/parity debugging and rollback controls. [C-PROJ-01]

## Prior internal evidence (scoped)
- In one controlled test dated 2026-08-12, C.Walts returned a useful top-five result for 17 of 17 cases and passed 10 of 10 preservation checks. [C-PROJ-02]
- The 2026-08-12 test is a single controlled run; it does not establish general accuracy, scale or novelty. [C-PROJ-02] [A-RD-01]

## Technical uncertainty (what is not known)
- Whether persistence/parity faults can be detected automatically, before release, with low false-alarm rates across different retrieval stacks. [A-RD-01]
- Whether a small, fixed preservation test set predicts real-world retrieval quality after re-indexing. [A-RD-01]
- Which signals (rank shifts, embedding drift, document-count parity, citation agreement) give early warning without labelled data. [A-RD-01]

## Novelty check required
- A literature and prior-art review on RAG evaluation, index drift and regression testing must come before any novelty claim. [A-RD-01]

## Proposed experiments
- E1: build a fault-injection harness that introduces known persistence and parity faults into a test index, then measures detection rate and false alarms. [A-RD-01]
- E2: compare preservation-check pass rates against human-judged retrieval quality across repeated re-indexing runs. [A-RD-01]
- E3: test whether drift signals predict quality loss on at least two different retrieval stacks (BM25 + vector, as in C.Walts). [C-SKL-02] [A-RD-01]

## Milestones (proposed; measurable)
- M1: written prior-art review and refined hypothesis. [A-RD-01]
- M2: fault-injection harness with a documented fault catalog. [A-RD-01]
- M3: detection and false-alarm rates reported per fault type, with confidence intervals. [A-RD-01]

## Personnel limits
- Solo founder; AI tools are not staff. Any federal R&D proposal needs realistic hours and may need a subcontractor or university partner (STTR). [C-BIZ-05] [A-PLAN-02]

## Commercialization assumptions (to test)
- Small organizations adopting document-search AI may pay for a reliability check before and after changes. This is a hypothesis for customer discovery interviews, not evidence of demand. [A-RD-02] [A-MKT-01]

## Agency-fit research queue
- NSF Project Pitch (accepting pitches as of 2026-10-08). [C-PRG-03]
- Other agency SBIR topics (DOE, DoD, NIH) not yet searched. [A-RD-01]

## Missing inputs
- Prior-art review.
- 3–5 customer discovery interviews.
- Public artifact or case-study page for C.Walts (D6).

## Review notes
- No TRL, patentability, buyer or solicitation match is claimed.
