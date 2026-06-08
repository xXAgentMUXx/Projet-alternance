# /do-in-steps

Execute complex tasks through sequential sub-agent orchestration with intelligent model selection and LLM-as-a-judge verification.

- Purpose - Execute dependent tasks sequentially where each step builds on previous outputs
- Pattern - Supervisor/Orchestrator with sequential dispatch, judge verification, and iteration loop
- Output - Comprehensive report with all step results, judge scores, and integration summary
- Quality - Two-layer verification: self-critique (internal) + LLM-as-a-judge (external) with iteration until passing
- Key Benefit - Prevents context pollution while ensuring quality through independent verification

## Pattern: Sequential Orchestration with Judge Verification

```
Phase 1: Task Analysis and Decomposition
         Task → Identify Dependencies → Define Step Boundaries
                     │
Phase 2: Model Selection
         For each step: Assess Complexity + Scope + Risk → Select Model
                     │
Phase 3: Sequential Execution with Judge Verification
         ┌─────────────────────────────────────────────────────────────┐
         │ For each Step N:                                           │
         │   Implementer → Self-Critique → Judge → Parse Verdict      │
         │        ▲                                    │               │
         │        │                                    ▼               │
         │        │                         PASS (≥3.5)? → Next Step  │
         │        │                         FAIL? → Retry (max 2)     │
         │        └──────── feedback ───────┘         or Escalate     │
         └─────────────────────────────────────────────────────────────┘
         Step 1 → Judge ✓ → Step 2 → Judge ✓ → Step 3 → Judge ✓ → ...
                     │
Phase 4: Final Summary and Report
         Aggregate results, judge scores, files modified, decisions made
```

## Usage

```bash
# Interface change with consumer updates
/do-in-steps "Change return type of UserService.getUser() from User to UserDTO and update all consumers"

# Feature addition across layers
/do-in-steps "Add email notification capability to the order processing system"

# Multi-file refactoring with breaking changes
/do-in-steps "Rename 'userId' to 'accountId' across the codebase - affects interfaces, implementations, and callers"
```

## When to Use

**Good use cases:**

- Changes that cascade through multiple files/layers
- Interface modifications with consumers to update
- Feature additions spanning multiple components
- Refactoring with dependency chains
- Any task where "Step N depends on Step N-1"

**Do NOT use when:**

- Independent tasks that could run in parallel → use `/do-in-parallel`
- Single-step tasks → use `/launch-sub-agent`
- Tasks needing exploration before commitment → use `/tree-of-thoughts`
- High-stakes tasks needing multiple approaches → use `/do-competitively`

## Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 3** | Self-Critique | Implementation agents verify own work before submission, catching 40-60% of issues |
| **Phase 3** | LLM-as-a-Judge | Independent judge verifies each step, catching blind spots self-critique misses |
| **Phase 3** | Iteration Loop | Failed steps retry with judge feedback until passing (max 2 retries) or escalate |
| **Phase 3** | Context Passing | Each step receives summary of previous outputs without full context pollution |

## Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics
- **[Multi-Agent Debate](https://arxiv.org/abs/2305.14325)** (Du et al., 2023) - Fresh context prevents accumulated confusion
