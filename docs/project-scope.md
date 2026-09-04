# Project scope

AWP provides a common format for agents that already have their own working environments. The purpose of AWP is to:

1. Enable a user or agent to send another agent a project or problem description that preserves more durable semantic state than ordinary Markdown alone.
2. Provide a new agent with a clear, shared project orientation before it must inspect the wider repository.
3. Allow an agent or user to return to a project and resume from a recorded checkpoint rather than reconstructing its state from scratch.
4. Enable multiple agents to negotiate interdependent code changes above the byte-level coordination provided by Git or similar source-control systems.

AWP does not replace an agent runtime, source control, artifact storage, authentication, authorization, consensus, or a project-specific workflow. It carries portable semantic state that those systems can inspect or exchange.
