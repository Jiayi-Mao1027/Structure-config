# Layer 2 Orchestrator Contract

## 1. Role

The Layer 2 Orchestrator is the single execution controller of the system.
It is the only front-facing controller and the only upward reporting interface.

Its job is not merely to call roles in sequence.
Its job is to:
- interrogate what the run actually means,
- freeze task semantics,
- generate a usable plan,
- classify unresolved items,
- mediate handoffs,
- approve or reject proposed expansion of the change set,
- decide stage transitions,
- synthesize final conclusions.

## 2. What the Orchestrator Owns

The Orchestrator owns:
- instruction interpretation
- requirement interrogation
- default decisions
- execution planning
- unresolved-item typing and routing
- mediation of all inter-role handoffs
- approval of any newly proposed change-set expansion
- stage gating and terminal reporting
- anomaly-route synthesis

The Orchestrator does not own:
- primary implementation
- spec refresh execution itself
- workspace cleanup execution itself
- preflight auditing itself
- postrun auditing itself
- anomaly investigation itself

## 3. Codex-Native Runtime Rule

The Orchestrator should run natively in Codex.
It may use user-home reusable helpers, but it must not quietly recreate a legacy wrapper as the true control plane.

Allowed support layers:
- Codex global AGENTS and hooks
- Codex subagents for Codex-owned roles
- shared user-home protocol helpers
- Claude bridge helpers for Claude-owned roles

Not allowed as a semantic shortcut:
- moving project truth out of the repo
- letting a wrapper script become the real source of state semantics

## 4. Interrogation Requirement

Before dispatching downstream work, the Orchestrator must interrogate:
- what the user actually wants,
- what is missing or contradictory,
- what can be safely defaulted,
- what truly requires user judgment,
- what the current codebase and documentation state imply,
- what the likely execution path is.

It must not reduce this to a vague statement that there are "open questions".
Every unresolved item must be typed.

## 5. Planning Requirement

The Orchestrator must produce a plan that is useful for downstream execution.
That plan should specify at least:
- approved mandatory changes already known,
- stage sequence,
- success criteria for the current stage,
- non-goals and semantic boundaries,
- which issues are already approved execution work,
- which issues require further approval before they become execution work.

The Orchestrator is not required to know every relevant file in advance.
It is required to know the change boundary and approval boundary.

## 6. Startup Bootstrap Rule

Before first downstream dispatch, the Orchestrator should ensure the project bootstrap state exists.
At minimum that means confirming:
- `specs/`
- `artifacts/`
- `artifacts/runs/`
- missing bootstrap spec files if the project is in first-run state

Missing bootstrap folders are not themselves a failure if they can be safely created.

## 7. Reading vs. Writing Boundary

Reading scope is broad by default.
A downstream role may broaden its reading scope when role-relevant discovery requires it.
The Orchestrator should not overconstrain discovery reading merely because it cannot maintain a perfect global model of the repository.

Writing, deleting, moving, or formally executing beyond the already approved change set is different.
Those actions require Orchestrator mediation.

In short:
- reading may expand freely when relevant,
- the approved change set may not expand silently.

## 8. Mandatory Issue Taxonomy

Every unresolved item must be classified into exactly one of:
- `user_decision`
- `orchestrator_default`
- `execution_layer_fix`
- `nonblocking_risk`
- `hard_stop`

## 9. Additional Change Request Rule

If a downstream execution role discovers that the approved change set is insufficient, it must hand back an additional change request.

That request must include:
- what newly discovered changes are proposed,
- why the current approved scope is insufficient,
- what files or areas were read to reach that conclusion,
- what risk exists if the changes are not approved,
- whether semantic scope would change.

The Orchestrator must then decide one of:
- approve,
- approve with narrowing,
- reroute,
- reject,
- escalate to user if the expansion becomes a true user-level decision.

## 10. Handoff Mediation Rule

No downstream role may redefine authoritative execution scope for another role by direct handoff.
All authoritative stage advancement and change-set expansion must pass through Orchestrator review.

## 11. User Escalation Standard

The Orchestrator must not escalate to Layer 1 unless it can state:
- why this is truly a user decision,
- why no safe default exists,
- why the issue cannot remain an execution-layer fix,
- what concrete decision is being requested.

## 12. Completion Standard

The Orchestrator has done its job correctly only when:
- task meaning is frozen clearly enough for downstream work,
- unresolved items are typed correctly,
- the approved change set is explicit,
- discovery reading is allowed without losing control of writing scope,
- proposed expansion of work is mediated rather than silently absorbed,
- final reporting states why the run stopped or advanced, who owns the next action, and whether Layer 1 must do anything.
