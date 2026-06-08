# /do-and-judge

Execute a single task with implementation sub-agent, independent judge verification, and automatic retry loop until passing or max retries exceeded.

- Purpose - Execute a single task with quality verification and feedback-driven iteration
- Pattern - Implement → Judge → Iterate (if needed) → Report
- Output - Verified implementation with judge scores and improvement suggestions
- Quality - Two-layer verification: self-critique (internal) + LLM-as-a-judge (external)
- Iteration - Retry with judge feedback until passing (≥4/5.0) or max retries (2)

## Pattern: Single-Task Execution with Judge Verification

```
Phase 1: Task Analysis and Model Selection
         Complexity + Risk + Scope → Model Selection
                     │
Phase 2: Dispatch Implementation Agent
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
                     │
Phase 3: Dispatch Judge Agent
         Independent verification with structured criteria
                     │
Phase 4: Parse Verdict and Iterate
         ├─ PASS (≥4) → Report Success
         └─ FAIL (<4) → Retry with Feedback (max 2)
                            └─ Return to Phase 3
                     │
Phase 5: Final Report or Escalation
         Success summary OR escalate to user after max retries
```

## Usage

```bash
# Basic usage
/do-and-judge "Refactor the UserService class to use dependency injection"

# Complex implementation
/do-and-judge "Implement rate limiting middleware with configurable limits per endpoint"

# Architecture change
/do-and-judge "Extract validation logic from UserController into separate UserValidator class"
```

## When to Use

**Good use cases:**

- Single, well-defined tasks that benefit from quality verification
- Changes that should meet a quality threshold before shipping
- Tasks where feedback-driven iteration improves results
- Any implementation where you want an independent quality gate

**Do NOT use when:**

- Multi-step tasks with dependencies → use `/do-in-steps` instead
- Independent parallel tasks → use `/do-in-parallel` instead
- High-stakes tasks needing multiple approaches → use `/do-competitively` instead
- Simple tasks where verification overhead isn't justified → use `/launch-sub-agent` instead

## Quality Enhancement Techniques

| Phase | Technique | Benefit |
|-------|-----------|---------|
| **Phase 2** | Zero-shot CoT | Systematic reasoning improves quality by 20-60% |
| **Phase 2** | Self-Critique | Implementation agents verify own work before submission |
| **Phase 3** | LLM-as-a-Judge | Independent judge catches blind spots self-critique misses |
| **Phase 4** | Feedback Loop | Retry with specific issues until passing or max retries |

## Theoretical Foundation

- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** (Wei et al., 2022) - Step-by-step reasoning improves accuracy
- **[Constitutional AI](https://arxiv.org/abs/2212.08073)** (Bai et al., 2022) - Self-critique loops before submission
- **[LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)** (Zheng et al., 2023) - Independent evaluation with structured rubrics
