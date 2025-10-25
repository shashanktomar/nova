# Refine Command

## Usage

`/refine [optional: scope]`

## Context

- Scope (optional): $ARGUMENTS
- If no scope provided, will ask user to specify what code to refine

## Your Role

You are the Refine Coordinator orchestrating specialized refinement agents to improve code quality.

## Process

### Step 1: Load Project Context

**BEFORE doing anything else**, invoke the `/prime` command to load all project documentation:

```
/prime
```

Wait for this to complete before proceeding. This ensures all agents have proper context.

### Step 2: Discover Available Refinement Agents

**Dynamically discover agents tagged with "refine":**

1. Use Glob to find all agent files:
   ```
   pattern: "*.md"
   path: ".claude/agents"
   ```

2. Read each agent file and parse the YAML frontmatter to extract:
   - `name`: The agent identifier
   - `description`: What the agent does
   - `tags`: Array of tags

3. Filter agents where `tags` includes `refine`

4. Build a list of available refinement agents with their names and descriptions

### Step 3: Identify Refinement Scope

If the user provided a scope in $ARGUMENTS, use that. Otherwise, ask:

"What code would you like to refine? You can specify:
- A specific file or directory (e.g., `src/nova/marketplace`)
- A module name (e.g., `marketplace`)
- A feature area (e.g., "CLI commands")
- "everything" or "all" for full codebase analysis"

Wait for their response and capture the scope.

### Step 4: Present Refinement Options

Display the discovered refinement agents dynamically:

```
📋 Available Refinement Agents:

[For each discovered agent with index starting at 1:]
[index]. [agent-name]
   [agent-description]

[last-index + 1]. all
   Run all refinement agents in parallel
   (Comprehensive analysis of all quality dimensions)

Which refinement would you like to perform? (Enter 1-[last-index + 1])
```

Format the description by wrapping long lines and using bullet points where appropriate for readability.

### Step 5: Capture User Selection

Wait for the user to enter their choice.

Validate the input:
- Must be a number between 1 and (number of agents + 1)
- If invalid, ask again

Confirm the selection:
- If single agent: "Running **[agent-name]** on **[scope]**..."
- If all: "Running **all refinement agents in parallel** on **[scope]**..."

### Step 6: Execute Selected Refinement

Based on user selection, invoke the appropriate agent(s) using the Task tool:

#### For Single Agent Selection:

```
Invoke Task tool with:
- subagent_type: "[agent-name]"
- description: "[Agent-name] analysis"
- prompt: "Analyze the following code with your expertise: [scope]

Please provide your specialized analysis focusing on what you do best.

Target scope: [scope]"
```

#### For "All" Selection:

**IMPORTANT: Run all discovered refinement agents IN PARALLEL using a single message with multiple Task tool calls.**

For each agent with "refine" tag, invoke Task tool with:
- subagent_type: "[agent-name]"
- description: "[Agent-name] analysis"
- prompt: "Analyze the following code with your expertise: [scope]

Please provide your specialized analysis focusing on what you do best.

Target scope: [scope]"

All agents will run simultaneously and return their results independently.

### Step 7: Consolidate Agent Findings

After the agent(s) complete, provide a consolidated summary:

#### For Single Agent:
```
✅ Refinement Analysis Complete

Agent: [agent-name]
Scope: [scope]

Key Findings:
- [High-level summary point 1]
- [High-level summary point 2]
- [High-level summary point 3]

The detailed report from the agent is shown above.
```

#### For All Agents (Parallel Execution):
```
✅ Comprehensive Refinement Analysis Complete

Agents Run (in parallel):
[List each agent with bullet point]

Scope: [scope]

📊 Consolidated Findings:

[For each agent:]
**[Agent Name]:**
- [Key finding 1]
- [Key finding 2]

All detailed reports are shown above. Review the findings and let me know what you'd like to address.
```

### Step 8: Offer Next Steps

Ask the user what they'd like to do next:

"Would you like me to:
1. **Fix high-priority issues** identified by the agents?
2. **Run another refinement** on a different area?
3. **Create an action plan** consolidating all findings?
4. **Generate a detailed report** for documentation?
5. **Do nothing** - just reviewing the findings?"

Wait for their response and proceed accordingly.

## Important Guidelines

### Dynamic Agent Discovery

- **Always discover agents dynamically** - Never hardcode agent names
- **Parse frontmatter correctly** - Extract name, description, and tags
- **Filter by "refine" tag** - Only show agents tagged for refinement
- **Handle missing agents gracefully** - If no agents found, inform user

### Agent Orchestration

- **Always run `/prime` first** - This is non-negotiable
- **Present options clearly** - Use numbered list with descriptions from agent metadata
- **Validate user input** - Ensure they select valid option number
- **Run agents in parallel when possible** - Especially for "all" option
- **Capture scope explicitly** - Don't assume, ask if unclear

### Parallel Execution for "All" Option

- **Single message, multiple Task calls** - Invoke all agents in one go
- **Let them run independently** - Don't wait between agents
- **Consolidate findings** - Synthesize results from all agents at the end
- **Maximum efficiency** - Parallel execution saves time

### Output Management

- **Let agents speak** - Don't filter their output excessively
- **Summarize key points** - Provide concise high-level takeaways
- **Consolidated view** - For "all", combine findings from all agents
- **Actionable next steps** - Always offer clear options for what to do next
- **Never provide effort estimates** - Do not include time estimates, effort assessments, or complexity ratings

### Error Handling

- If no agents found with "refine" tag, inform user and exit gracefully
- If agent discovery fails, report the error clearly
- If an agent fails during execution, note the failure and continue with others
- Always summarize what was completed successfully

## Success Criteria

A successful refinement session should:
1. ✅ Load project context via `/prime`
2. ✅ Dynamically discover refinement agents from .claude/agents/
3. ✅ Clearly present discovered options to user
4. ✅ Execute selected agent(s) with proper scope (in parallel for "all")
5. ✅ Surface key findings to the user
6. ✅ Provide consolidated summary for multiple agents
7. ✅ Offer actionable next steps
8. ✅ Maintain a clear, organized conversation flow

Remember: Your role is coordination and clarity. Dynamically discover the agents, let them do their expert analysis in parallel when possible, and focus on orchestrating a smooth, user-friendly experience.
