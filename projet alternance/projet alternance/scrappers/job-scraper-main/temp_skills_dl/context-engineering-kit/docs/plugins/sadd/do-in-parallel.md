# /do-in-parallel

Execute tasks in parallel across multiple targets with intelligent model selection, independence validation, and quality-focused prompting.

- Purpose - Execute the same task across multiple independent targets in parallel
- Pattern - Supervisor/Orchestrator with parallel dispatch and context isolation
- Output - Multiple solutions, one per target, with aggregated summary
- Quality - Enhanced with Zero-shot CoT, Constitutional AI self-critique, and intelligent model selection
- Efficiency - Dramatic time savings through concurrent execution of independent work

## Pattern: Parallel Orchestration with Independence Validation

This command implements a six-phase parallel orchestration pattern:

```
Phase 1: Parse Input and Identify Targets
                     │
Phase 2: Task Analysis with Zero-shot CoT
         ┌─ Task Type Identification ─────────────────┐
         │ (transformation, analysis, documentation)  │
         ├─ Per-Target Complexity Assessment ─────────┤
         │ (high/medium/low)                          │
         ├─ Independence Validation ──────────────────┤
         │ ⚠️ CRITICAL: Must pass before proceeding   │
         └────────────────────────────────────────────┘
                     │
Phase 3: Model and Agent Selection
         Is task COMPLEX? → Opus
         Is task SIMPLE/MECHANICAL? → Haiku
         Otherwise → Opus (default for balanced work)
                     │
Phase 4: Construct Per-Target Prompts
         [CoT Prefix] + [Task Body] + [Self-Critique Suffix]
         (Same structure for ALL agents, customized per target)
                     │
Phase 5: Parallel Dispatch (ALL agents in SINGLE response)
         ┌─ Agent 1 (target A) ─┐
         ├─ Agent 2 (target B) ─┼─→ Concurrent Execution
         └─ Agent 3 (target C) ─┘
                     │
Phase 6: Collect and Summarize Results
         Aggregate outcomes, report failures, suggest remediation
```

## Usage

```bash
# Inferred targets from task description
/do-in-parallel "Apply consistent logging format to src/handlers/user.ts, src/handlers/order.ts, and src/handlers/product.ts"
```

## Advanced Options

```bash
# Basic usage with file targets
/do-in-parallel "Simplify error handling to use early returns" \
  --files "src/services/user.ts,src/services/order.ts,src/services/payment.ts"

# With named targets
/do-in-parallel "Generate unit tests achieving 80% coverage" \
  --targets "UserService,OrderService,PaymentService"

# With model override
/do-in-parallel "Security audit for injection vulnerabilities" \
  --files "src/db/queries.ts,src/api/search.ts" \
  --model opus
```

## When to Use

**Good use cases:**

- Same operation across multiple files (refactoring, formatting)
- Independent transformations (each file stands alone)
- Batch documentation generation (API docs per module)
- Parallel analysis tasks (security audit per component)
- Multi-file code generation (tests per service)

**Do NOT use when:**

- Only one target → use `/launch-sub-agent` instead
- Targets have dependencies → use `/do-in-steps` instead
- Tasks require sequential ordering → use `/do-in-steps` instead
- Shared state needed between executions → use `/do-in-steps` instead
- Quality-critical tasks needing comparison → use `/do-competitively` instead

## Context Isolation Best Practices

- **Minimal context**: Each sub-agent receives only what it needs for its target
- **No cross-references**: Don't tell Agent A about Agent B's target
- **Let them discover**: Sub-agents read files to understand local patterns
- **File system as truth**: Changes are coordinated through the filesystem

## Theoretical Foundation

**Zero-shot Chain-of-Thought** (Kojima et al., 2022)

- "Let's think step by step" improves reasoning by 20-60%
- Applied to each parallel agent independently
- Reference: [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916)

**Constitutional AI / Self-Critique** (Bai et al., 2022)

- Each agent self-verifies before completing
- Catches issues without coordinator overhead
- Reference: [Constitutional AI](https://arxiv.org/abs/2212.08073)

**Multi-Agent Context Isolation** (Multi-agent architecture patterns)

- Fresh context prevents accumulated confusion
- Focused tasks produce better results than context-polluted sessions
- Reference: [Multi-Agent Debate](https://arxiv.org/abs/2305.14325) (Du et al., 2023)
