# multi-agent-patterns - Multi-Agent Analysis Orchestration

Provide guidence for parallel, sequential and debate execution strategies.

**Sequential Analysis:**

```
Command → Agent 1 → Agent 2 → Agent 3 → Synthesized Result
```

**Parallel Analysis:**

```
         ┌─ Agent 1 ─┐
Command ─┼─ Agent 2 ─┼─ Synthesized Result
         └─ Agent 3 ─┘
```

**Debate Pattern:**

```
Command → Agent 1 ─┐
       → Agent 2 ─┼─ Debate → Consensus → Result
       → Agent 3 ─┘
```

## Processes

### Sequential Execution Process

1. **Load Plan**: Read plan file and create TodoWrite with all tasks
2. **Execute Task with Subagent**: For each task, dispatch a fresh subagent:

   - Subagent reads the specific task from the plan
   - Implements exactly what the task specifies
   - Writes tests following project conventions
   - Verifies implementation works
   - Commits the work
   - Reports back with summary
3. **Review Subagent's Work**: Dispatch a code-reviewer subagent:

   - Reviews what was implemented against the plan
   - Returns: Strengths, Issues (Critical/Important/Minor), Assessment
   - Quality gate: Must pass before proceeding
4. **Apply Review Feedback**:

   - Fix Critical issues immediately (dispatch fix subagent)
   - Fix Important issues before next task
   - Note Minor issues for later
5. **Mark Complete, Next Task**: Update TodoWrite and proceed to next task
6. **Final Review**: After all tasks, dispatch final reviewer for overall assessment
7. **Complete Development**: Use finishing-a-development-branch skill to verify and close

### Parallel Execution Process

1. **Load and Review Plan**: Read plan, identify concerns, create TodoWrite
2. **Execute Batch**: Execute first 3 tasks (default batch size):

   - Mark each as in_progress
   - Follow each step exactly
   - Run verifications as specified
   - Mark as completed
3. **Report**: Show what was implemented and verification output
4. **Continue**: Apply feedback if needed, execute next batch
5. **Complete Development**: Final verification and close

### Parallel Investigation Process

For multiple unrelated failures (different files, subsystems, bugs):

1. **Identify Independent Domains**: Group failures by what is broken
2. **Create Focused Agent Tasks**: Each agent gets specific scope, clear goal, constraints
3. **Dispatch in Parallel**: All agents run concurrently
4. **Review and Integrate**: Verify fixes do not conflict, run full suite

#### Quality Gates

Quality gates are enforced at key checkpoints:

| Checkpoint                   | Gate Type            | Action on Failure           |
| ------------------------------ | ---------------------- | ----------------------------- |
| After each task (sequential) | Code review          | Fix issues before next task |
| After batch (parallel)       | Human review         | Apply feedback, continue    |
| Final review                 | Comprehensive review | Address all findings        |
| Before merge                 | Full test suite      | All tests must pass         |

**Issue Severity Handling:**

- **Critical**: Fix immediately, do not proceed until resolved
- **Important**: Fix before next task or batch
- **Minor**: Note for later, do not block progress

## Why Multi-Agent Architectures

| Problem                   | Solution                                       |
| --------------------------- | ------------------------------------------------ |
| **Context Bottleneck**    | Partition work across multiple context windows |
| **Sequential Bottleneck** | Parallelize independent subtasks across agents |
| **Generalist Overhead**   | Specialize agents with lean, focused context   |

## Architecture Patterns

| Pattern                     | When to Use                                    | Trade-offs                                    |
| ----------------------------- | ------------------------------------------------ | ----------------------------------------------- |
| **Supervisor/Orchestrator** | Clear task decomposition, need human oversight | Central bottleneck, "telephone game" risk     |
| **Peer-to-Peer/Swarm**      | Flexible exploration, emergent requirements    | Coordination complexity, divergence risk      |
| **Hierarchical**            | Large projects with layered abstraction        | Overhead between layers, alignment challenges |

## Example of Implementation

```
Supervisor Pattern:
User Request → Supervisor → [Specialist A, B, C] → Aggregation → Output

Key Insight: Sub-agents exist to isolate context, not to anthropomorphize roles
```