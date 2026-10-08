# DRAFT — NSF SBIR Project Pitch (concept 1: retrieval reliability)
Status: DRAFT, not owner-approved. Checked: 2026-10-08 (America/New_York). The owner submits personally; one pitch is allowed at a time. Citation tags are stripped before pasting. Section limits are enforced by tests/test_packets.py. [C-PRG-03]

## 1. The Technology Innovation
Organizations increasingly connect AI assistants to their own documents through retrieval-augmented generation (RAG). [A-RD-01]
When the stored index, the served index and the source documents drift apart, answers can degrade without any error being raised. [A-RD-01]
BADGR proposes to research automated detection of these persistence and parity failures before they reach users, using fault injection, preservation checks and drift signals that do not need labelled data. [C-RD-01] [A-RD-01]
The idea grew out of the founder's work building a hybrid BM25 and vector retrieval system (C.Walts) with rollback controls. [C-PROJ-01] [C-SKL-02]
In one controlled test dated 2026-08-12, that system passed 10 of 10 preservation checks and returned a useful top-five result in 17 of 17 cases. That single test shows the checks are workable, not that the method generalizes. [C-PROJ-02]
The innovation to be tested is whether a small, automatically maintained set of checks and signals can predict real retrieval-quality loss across different retrieval stacks with acceptable false-alarm rates. [A-RD-01]
A prior-art review will establish how this differs from existing RAG evaluation and data-drift tools before the full proposal. [A-RD-01]

## 2. The Technical Objectives and Challenges
Objective 1: build a fault-injection harness that introduces catalogued persistence and parity faults into test indexes and records which faults existing checks miss. [A-RD-01]
Challenge: designing faults that are realistic rather than trivially detectable; the catalog will be drawn from documented failure reports and from the founder's debugging records. [A-RD-01] [C-PROJ-01]
Objective 2: measure detection rate and false-alarm rate for candidate signals (rank shifts, embedding drift, document-count parity, citation agreement), per fault type, with confidence intervals. [A-RD-01]
Challenge: separating true quality loss from normal variation after re-indexing; repeated runs and human-judged samples will set baselines. [A-RD-01]
Objective 3: test whether results hold on at least two retrieval stacks, so the method is not tied to one implementation. [A-RD-01] [C-SKL-02]
Risk: signals may not transfer between stacks. If so, the result still shows which faults need stack-specific checks. [A-RD-01]
Work will be run by the founder on existing local equipment; any need for larger compute or a research partner will be scoped in the full proposal. [C-HW-01] [C-BIZ-05] [A-PLAN-02]

## 3. The Market Opportunity
Initial users are hypothesized to be small organizations and the consultants who deploy document-search AI for them, who lack the staff to monitor retrieval quality after updates. [A-RD-02] [A-MKT-01]
The pain to validate: answers that quietly get worse after a document or index change, discovered only by end users. [A-RD-02]
Before the full proposal, the founder will hold customer discovery interviews to test whether this pain is real and whether buyers would pay for a pre-release reliability check. [A-RD-02]

## 4. The Company and Team
BADGRTECHNOLOGIES LLC is a Georgia LLC formed in January 2025, based in Lawrenceville, with one employee. [C-BIZ-01] [C-BIZ-02] [C-BIZ-03] [C-BIZ-05]
The founder would serve as principal investigator and builds Python/FastAPI services, retrieval pipelines (BM25, ChromaDB) and AI-agent evaluation workflows. [C-SKL-01] [C-SKL-02]
Prior roles in field hardware engineering and Tier II/III technical support involved structured defect investigation. [C-EXP-02] [C-EXP-03] [C-SKL-03]
SAM registration was submitted in September 2026 and is pending activation. [C-SAM-01]

## Missing inputs
- Prior-art review summary (needed before submission; it may change section 1).
- Customer discovery interview notes.
- Topic area choice from NSF's topic list.
- Confirm whether NSF needs SAM to be Active at pitch stage or only at proposal stage.

## Review notes
- Do not shorten the 17/17 sentence; it must stay scoped to the controlled test.
- One pitch at a time: concept 2 (routing validation) waits until this pitch gets a response.
