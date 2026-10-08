# DRAFT — R&D concept sheet 2: AI routing-error detection and validation
Status: DRAFT concept, not a funded project. Checked: 2026-10-08 (America/New_York).

## Problem hypothesis
- Multi-agent AI systems route each request to a specialist; a wrong route can produce a confident but wrong answer, and routing errors are hard to see in logs. [C-RD-01] [A-RD-01]
- The founder's BADGR Harness project covered specialist routing, defect investigation and validation. [C-PROJ-03]

## Technical uncertainty
- Whether routing errors can be detected at run time from signals such as confidence spread, disagreement between router and specialist, or answer-type mismatch. [A-RD-01]
- How many labelled routing cases are needed before a validator's error estimates are stable. [A-RD-01]

## Novelty check required
- Prior-art review on LLM routing, mixture-of-experts gating, and agent evaluation must come first. [A-RD-01]

## Proposed experiments
- E1: build a labelled routing test set from synthetic tasks with known correct specialists. [A-RD-01]
- E2: measure how well each candidate signal detects misroutes (precision and recall at fixed alert rates). [A-RD-01]
- E3: test whether a validator that blocks or re-routes flagged requests lowers end-task error without unacceptable latency. [A-RD-01]

## Milestones (proposed; measurable)
- M1: prior-art review. [A-RD-01]
- M2: public routing test set with documented labelling rules. [A-RD-01]
- M3: signal comparison report with error bars. [A-RD-01]

## Personnel limits
- Solo founder; AI tools are not staff. [C-BIZ-05] [A-PLAN-02]

## Commercialization assumptions (to test)
- Teams running agent workflows may pay for routing audits; this is a hypothesis for customer discovery. [A-RD-02]

## Agency-fit research queue
- Evaluate after concept 1; one NSF pitch is allowed at a time. [C-PRG-03]

## Missing inputs
- Prior-art review.
- Public artifact or case-study page for BADGR Harness (D6).

## Review notes
- No TRL, patentability, buyer or solicitation match is claimed.
