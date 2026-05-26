---
name: design-thinking-ideation
description: >
  Structured design thinking workflow for identifying business opportunities through
  empathy-driven ideation, prototyping, and test planning. Use this skill whenever the
  user wants to brainstorm business ideas, identify customer pain points, run a design
  thinking exercise, generate product concepts, explore unmet needs, or work through the
  empathise-define-ideate-prototype-test cycle. Triggers include "design thinking",
  "ideation", "identify opportunities", "customer pain points", "unmet needs", "how might we",
  "business idea generation", "brainstorm solutions", "prototype an idea", "empathise with
  users", or any exercise where the user wants to move from understanding a problem to
  generating and validating solution concepts. Also trigger for strategy or business programme
  assignments involving design thinking, innovation workshops, or AI-driven solution generation.
---

# Design Thinking Ideation — From Empathy to Prototype

## What This Skill Does

Guides a structured design thinking workflow that moves from understanding users and their
problems through to generating solution concepts and planning validation. Produces a complete
ideation document covering all five stages: Empathise, Define, Ideate, Prototype, and Test.

The workflow is particularly suited to identifying AI-driven business opportunities, but
works for any domain where the user wants to move from problem discovery to solution concept.

## Theoretical Foundation

Design thinking (Stanford d.school / IDEO) is a human-centred approach to innovation that
draws from the designer's toolkit to integrate the needs of people, the possibilities of
technology, and the requirements for business success. The five stages are not strictly
linear — practitioners iterate between them — but for a structured exercise they provide
a clear progression from empathy to action.

The key mindset shifts:
- **Empathise before solving** — resist jumping to solutions until the problem is understood
- **Diverge before converging** — generate breadth of ideas before selecting
- **Prototype to think** — build to learn, not to ship
- **Test to iterate** — feedback improves the concept, not just validates it

## Process

### Stage 1: Empathise

The goal is to build a rich understanding of potential users, their context, and their
struggles. This stage produces three outputs:

**1a. User/Customer Description**

Write a brief but specific description of the target user group. Go beyond demographics —
capture behaviours, contexts, motivations, and constraints. A useful structure:

- **Who are they?** — role, demographics, context (e.g. "mid-career finance professionals
  in regulated firms" not just "business people")
- **What does their day look like?** — key activities, tools they use, people they interact with
- **What are they trying to achieve?** — underlying goals, not just tasks
- **What constraints do they operate under?** — time, budget, regulation, organisational politics

Encourage specificity. "Small business owners" is too broad; "solo founders of B2B SaaS
companies in their first year post-launch, bootstrapped, doing their own sales" gives you
something to work with.

**1b. Pain Points (minimum two)**

Identify at least two pain points or challenges. Good pain points are:
- Specific enough to be solvable (not "everything is hard")
- Experienced frequently or at high intensity
- Currently unresolved or poorly resolved by existing solutions
- Observable in behaviour, not just assumed

Frame each pain point as what the user experiences, not what the solution should do.
Bad: "They need better analytics." Good: "They spend 3+ hours per week manually
compiling data from multiple sources to understand pipeline health, and the resulting
picture is always out of date."

**1c. Unmet Need (one significant need)**

Identify one significant unmet need that sits beneath or across the pain points. The unmet
need is the deeper "why" — what would fundamentally improve their situation if addressed.

An unmet need is distinct from a pain point: pain points are symptoms the user feels; the
unmet need is the underlying gap. Multiple pain points often trace back to a single unmet need.

Example:
- Pain point 1: "Spends hours compiling reports from multiple tools"
- Pain point 2: "Can't get a real-time view of team performance"
- Unmet need: "A single, continuously-updated source of truth for operational performance
  that doesn't require manual assembly"

### Stage 2: Define

Synthesise the empathy findings into a clear problem statement. Use the "How Might We" (HMW)
format:

> **How might we help [user group] who are experiencing [pain points] to [satisfy unmet need]?**

The HMW statement should be:
- **Narrow enough** to be actionable (not "How might we fix healthcare?")
- **Broad enough** to allow diverse solutions (not "How might we build a dashboard?")
- **Human-centred** — framed around the user's experience, not the technology
- **Free of embedded solutions** — the problem, not the answer

If the first attempt is too broad or too narrow, iterate. A good HMW statement is the
single most important output of the define stage — it shapes everything that follows.

### Stage 3: Ideate

Generate at least five distinct solution ideas. The goal is divergent thinking — quantity
and variety over quality at this stage.

Guidelines for strong ideation:
- **Range of ambition**: include at least one "quick win" (buildable in weeks), one
  substantial product concept, and one ambitious/moonshot idea
- **Range of approach**: mix technology-heavy solutions with process/service solutions,
  AI-driven with non-AI, platform with point solution
- **No self-censoring**: include ideas that feel risky or unconventional
- **Each idea gets a name and a one-paragraph description** covering what it does,
  how it works at a high level, and why it addresses the HMW statement

When generating ideas, lean into the user's domain expertise. If they work in a specific
industry or function, use that knowledge to generate ideas that are grounded in real
operational context rather than generic.

If AI-driven solutions are in scope (and they usually are for this exercise), consider:
- Where could LLMs, computer vision, or predictive models reduce manual effort?
- Where could AI act as a copilot, coach, or decision-support tool?
- Where could AI enable personalisation at scale?
- Where could AI unlock value from data the user already has but can't effectively use?

### Stage 4: Prototype

Select the most promising idea and outline a basic prototype concept. The prototype is
a thinking tool, not a product spec — it should be the minimum needed to make the idea
tangible enough to get meaningful feedback.

The prototype description should cover:

- **What it looks like** — the form factor (app, dashboard, Slack bot, report,
  physical artefact, service interaction). Be specific enough to visualise.
- **Key features** — the 2-3 core capabilities that address the HMW statement.
  Ruthlessly cut anything that isn't essential to testing the core hypothesis.
- **How it addresses the problem** — connect each key feature back to the pain
  points and unmet need from Stage 1.
- **What's faked vs. real** — in a prototype, it's fine to simulate AI outputs,
  use static data, or wizard-of-oz the backend. State what would be real and what
  would be simulated.
- **Build complexity** — rough indication of effort (could be a Figma mockup,
  a no-code tool, a spreadsheet simulation, a scripted demo, etc.)

### Stage 5: Test

Plan a simple testing method to gather feedback. The test plan should cover:

- **Who to test with** — 3-5 representative users from the target group identified
  in Stage 1. Note how you'd recruit them.
- **Test format** — how you'd present the prototype (demo, hands-on trial,
  walkthrough with narration, A/B comparison). Keep it simple.
- **Key questions to ask** — 4-6 specific questions designed to test whether the
  solution addresses the identified pain points. Mix open-ended ("Tell me what
  you're thinking as you look at this") with specific ("Would you use this instead
  of your current approach? Why/why not?").
- **What feedback you're looking for** — what signals would tell you this idea is
  worth pursuing vs. needs pivoting vs. should be abandoned? Be specific about
  success criteria.
- **How you'd iterate** — briefly describe what you'd do with the feedback.
  What would you change first? What would trigger a pivot back to Stage 3?

## Output Structure

Produce the analysis in this order, with clear section headers:

1. **Empathise** — user description, pain points, unmet need
2. **Define** — HMW problem statement
3. **Ideate** — numbered list of 5+ ideas with names and descriptions
4. **Prototype** — selected idea with prototype concept
5. **Test** — testing plan with questions, criteria, and iteration approach

## Calibration Notes

- **Academic context**: Reference design thinking methodology (Stanford d.school / IDEO).
  Demonstrate clear progression through all five stages. Show how each stage builds on
  the previous one. The HMW statement is often the most scrutinised element — get it right.
- **Business context**: Ground everything in real market dynamics and operational reality.
  Ideas should be commercially viable, not just technically interesting. Include rough
  sizing or market context where possible.
- **AI/Technology focus**: When the exercise specifically calls for AI-driven solutions,
  ensure the ideation stage explores genuinely AI-native concepts rather than conventional
  software with "AI" appended. Consider where AI creates step-change improvement vs.
  incremental efficiency.
- **Workshop/collaborative context**: If the user is facilitating a session rather than
  doing individual work, suggest how each stage could be run as a group exercise
  (sticky notes, dot voting, time-boxed rounds, etc.)

## Interaction Approach

This skill works best as a collaborative, iterative conversation rather than a single
output dump. The recommended approach:

1. Ask the user about their domain or industry focus — or whether they want to explore
   from scratch
2. Work through Empathise together — the user likely has domain knowledge that makes
   this richer than pure generation
3. Co-craft the HMW statement — this is worth getting right before moving on
4. Generate ideas, then let the user react and steer
5. Develop the prototype and test plan based on the selected idea

However, if the user provides enough context upfront or explicitly asks for a complete
output, produce all five stages in a single response. Match the user's preferred pace.

## Common Pitfalls to Avoid

- **Jumping to solutions in Stage 1**: The empathise stage should be pure problem
  understanding. If solutions start appearing here, the analysis is skipping ahead.
- **HMW too broad or too narrow**: "How might we improve healthcare?" is unsolvable;
  "How might we add a button?" is too narrow. The sweet spot allows for 5+ genuinely
  different solution approaches.
- **All ideas are the same idea**: If the five ideas in Stage 3 are really variations
  on one concept, push for more diversity. Vary the technology, the delivery model,
  the user interaction pattern, or the business model.
- **Prototype is a full product spec**: The prototype should be the minimum viable
  concept to test the core hypothesis. If it has 10+ features, it's too complex.
- **Test plan is a satisfaction survey**: "Did you like it?" tells you nothing.
  Test plans should probe whether the solution actually addresses the identified
  pain points and whether users would change their behaviour to adopt it.
