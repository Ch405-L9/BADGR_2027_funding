# DRAFT — R&D concept sheet 1: Retrieval persistence and evaluation reliability
Status: DRAFT concept, not a funded project. Checked: 2026-10-08 (America/New_York).

## Problem hypothesis
- Retrieval-augmented AI systems can silently degrade when the stored index, the served index and the source documents drift apart; small teams often lack tests that catch this before users do.
- The founder's C.Walts work covered hybrid retrieval, persistence/parity debugging and rollback controls.

## Prior internal evidence (scoped)
- In one controlled test dated 2026-08-12, C.Walts returned a useful top-five result for 17 of 17 cases and passed 10 of 10 preservation checks.
- The 2026-08-12 test is a single controlled run; it does not establish general accuracy, scale or novelty.

## Technical uncertainty (what is not known)
- Whether persistence/parity faults can be detected automatically, before release, with low false-alarm rates across different retrieval stacks.
- Whether a small, fixed preservation test set predicts real-world retrieval quality after re-indexing.
- Which signals (rank shifts, embedding drift, document-count parity, citation agreement) give early warning without labelled data.

## Novelty check required
- A literature and prior-art review on RAG evaluation, index drift and regression testing must come before any novelty claim.

## Proposed experiments
- E1: build a fault-injection harness that introduces known persistence and parity faults into a test index, then measures detection rate and false alarms.
- E2: compare preservation-check pass rates against human-judged retrieval quality across repeated re-indexing runs.
- E3: test whether drift signals predict quality loss on at least two different retrieval stacks (BM25 + vector, as in C.Walts).

## Milestones (proposed; measurable)
- M1: written prior-art review and refined hypothesis.
- M2: fault-injection harness with a documented fault catalog.
- M3: detection and false-alarm rates reported per fault type, with confidence intervals.

## Personnel limits
- Solo founder; AI tools are not staff. Any federal R&D proposal needs realistic hours and may need a subcontractor or university partner (STTR).

## Commercialization assumptions (to test)
- Small organizations adopting document-search AI may pay for a reliability check before and after changes. This is a hypothesis for customer discovery interviews, not evidence of demand.

## Agency-fit research queue
- NSF Project Pitch (accepting pitches as of 2026-10-08).
- Other agency SBIR topics (DOE, DoD, NIH) not yet searched.
