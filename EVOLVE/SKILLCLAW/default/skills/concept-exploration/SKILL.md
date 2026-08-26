---
name: concept-exploration
description: "Explore and refine creative project ideas before building."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, ideation, brainstorming, concept, creative, scoping, requirements, exploration]
    related_skills: [spike, plan, sketch]
---

# Concept Exploration

Use when the user presents a **creative, novel, or ambiguous project idea** and the core concept isn't settled yet. Your job is to help them refine the vision through conversation — NOT to start building.

Load this when the user says things like "I want to build X", "what if we made a Y", "let's create Z", or describes something ambitious/vague/exciting where the shape of the product is unclear.

## The core rule

**Do NOT touch code, create todos, install dependencies, or propose tech stacks until the concept is solid.** If you catch yourself writing `pip install` or `mkdir`, stop. The concept phase is conversation-only.

## Signals that the concept isn't ready

- The user changes direction mid-conversation (2D → 3D, game → simulation)
- You're asking implementation questions (what platform? what language?) before the core experience is defined
- The user says "stop" or "let's get the concept right first"
- The idea has more than 2 undefined dimensions (what do agents DO? what's the world like? what's the goal?)

## How to explore a concept

### Phase 1: Understand the spark
- What excited the user about this idea? Find the core fantasy.
- Restate what you understood. Let them correct you.
- Don't propose — listen. Ask open questions, not multiple-choice.

### Phase 2: Define the experience
Ask about the **user experience**, not the implementation:
- What does the user **see/hear/feel** when this works?
- What's the core loop? (What happens minute-to-minute?)
- Is this something you **play**, **watch**, **build**, or **use**?
- What makes it different from existing things?

### Phase 3: Scope the MVP
- What's the smallest version that captures the magic?
- What can be deferred to later?
- What are the 2-3 core mechanics that MUST work?

### Phase 4: Lock and hand off
- Summarize the concept in 3-5 bullet points
- Ask: "Is this right? Should we start building, or refine more?"
- Only THEN move to spike/plan/implementation

## Anti-patterns

1. **Rushing to tech** — Asking "Pygame or Godot?" before knowing what the thing IS
2. **Over-specifying** — Presenting a 20-question survey when the user wants a conversation
3. **Premature architecture** — Proposing neural network layers before defining what agents do
4. **Ignoring pivots** — When the user changes direction, don't anchor to the old idea. Reset and re-explore.
5. **Multiple-choice overload** — Don't present 4 options for every dimension. Ask one focused question at a time.

## When the concept IS ready

You'll know because:
- The user confirms your summary without corrections
- The core loop is defined (what happens, what changes, what the user sees)
- The MVP scope is agreed on
- The user says something like "yeah, let's build it" or "that's it"

Now hand off to `spike` (for feasibility validation), `plan` (for structured build), or direct implementation.

## Example flow

```
User: "I want to build a self-evolving AI survival game"

BAD:  "Great! What platform — Pygame, Godot, or browser?"
BAD:  "Here's my proposed architecture with neural networks..."
BAD:  [creates todo list, starts installing packages]

GOOD: "Tell me more — when you picture this working, what are you watching?
       Are you playing it, or watching it like an aquarium?"
```
