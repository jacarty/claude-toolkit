---
name: vrio-analysis
description: >
  Structured VRIO framework analysis for evaluating internal resources and capabilities
  to determine sustainable competitive advantage. Use this skill whenever the user wants
  to assess whether a resource, capability, or competency provides competitive advantage,
  or mentions VRIO, resource-based view, internal analysis, competitive advantage assessment,
  sustainable advantage, or phrases like "is this defensible", "what's our moat",
  "evaluate our capabilities", "assess our resources", or "competitive positioning of X".
  Also trigger when the user is working on strategy assignments, MBA/business programme
  activities, or strategic management exercises that involve internal resource evaluation.
  Even if the user doesn't name VRIO explicitly, use this skill when the core question is
  "does this resource/capability give us a lasting edge?"
---

# VRIO Framework Analysis

## What This Skill Does

Guides a structured evaluation of internal resources and capabilities using Barney's (1991)
VRIO framework. Produces a complete analysis with assessment table, narrative evaluation
per resource, and strategic recommendations — calibrated to the context (academic assignment,
business case, strategic planning).

## Theoretical Foundation

VRIO operationalises the Resource-Based View (RBV) of the firm. The framework asks four
sequential questions about each resource or capability:

1. **Valuable?** — Does it enable the firm to exploit opportunities or neutralise threats?
   A resource that doesn't create value is a competitive *disadvantage*.

2. **Rare?** — Is it controlled by only a small number of competing firms?
   Valuable but common resources deliver *competitive parity* — necessary to compete but
   not sufficient to win.

3. **Inimitable?** — Is it costly or difficult for competitors to obtain or replicate?
   Valuable + rare but imitable resources provide only *temporary competitive advantage*.
   Inimitability comes from four sources (use these in the narrative):
   - **Path dependency** — built through unique historical conditions and cumulative investment
   - **Causal ambiguity** — competitors cannot clearly identify what produces the advantage
   - **Social complexity** — embedded in relationships, culture, trust, or reputation
   - **Data/network effects** — value increases with scale in ways competitors cannot shortcut

4. **Organised?** — Is the firm structured to capture the value from this resource?
   This covers processes, policies, culture, incentive structures, and go-to-market alignment.
   A resource that is V+R+I but not organised is an *unused competitive advantage* — latent
   potential the firm is failing to exploit.

Only resources scoring Yes across all four dimensions deliver **sustainable competitive advantage**.

## Assessment Cascade

The VRIO logic is sequential — each "No" terminates the assessment at a specific level:

| Valuable? | Rare? | Inimitable? | Organised? | Competitive Outcome |
|-----------|-------|-------------|------------|-------------------|
| No | — | — | — | Competitive disadvantage |
| Yes | No | — | — | Competitive parity |
| Yes | Yes | No | — | Temporary competitive advantage |
| Yes | Yes | Yes | No | Unused competitive advantage |
| Yes | Yes | Yes | Yes | **Sustainable competitive advantage** |

The dashes indicate that subsequent questions become irrelevant once a "No" is reached,
though in practice it can be useful to note where a resource *could* score if the firm
addressed the blocking dimension.

## Process

### Step 1: Identify Resources/Capabilities

If the user hasn't already chosen their resources, help them identify strong candidates.
Good VRIO subjects are:

- Core technology or platform architecture (e.g. a proprietary data model, algorithm)
- Brand, reputation, or trust relationships
- Proprietary data assets or network effects
- Organisational culture or talent pipeline
- Processes, workflows, or operational capabilities
- Partnerships, ecosystems, or regulatory positions
- IP portfolios, patents, or trade secrets

Guide the user toward resources at different levels of abstraction for contrast — e.g. one
platform-level architectural resource and one product-level capability. This produces a
more interesting analysis with divergent VRIO outcomes.

### Step 2: Evaluate Each Resource

For each resource, work through V → R → I → O sequentially. For each dimension:

- State the Yes/No assessment clearly
- Provide 2-3 sentences of evidence and reasoning
- For Inimitability specifically, reference whichever sources of inimitability apply
  (path dependency, causal ambiguity, social complexity, data/network effects)
- For Organisation, assess whether the firm's structure, processes, incentives, and
  go-to-market are aligned to exploit the resource

Be honest about "No" assessments — the analytical value comes from identifying gaps,
not from manufacturing a clean sweep of Yeses.

### Step 3: Determine Competitive Outcome

Map each resource to its position in the assessment cascade. State the outcome explicitly.

### Step 4: Write the Narrative

For each resource, produce a paragraph that:

1. Opens with what the resource/capability is and why it matters
2. Walks through the VRIO dimensions with evidence
3. Names the competitive outcome
4. Identifies what would need to change to move the resource up the cascade
   (if it didn't reach sustainable advantage)

### Step 5: Strategic Recommendation

Close with a recommendation section that:

- Identifies which resource is the strongest competitive asset
- Recommends actions to protect or extend its advantage
- Flags the most significant threat to its long-term defensibility
- For resources below sustainable advantage, suggests the most impactful
  dimension to address

## Output Structure

Produce the analysis in this order:

1. **Assessment table** — one row per resource, columns for V/R/I/O and outcome
2. **Narrative per resource** — structured paragraph as described above
3. **Recommendation** — strategic implications and actions

## Calibration Notes

- **Academic context**: Reference the inimitability framework explicitly (path dependency,
  causal ambiguity, social complexity). Connect to RBV theory. Use the formal cascade
  terminology (competitive parity, temporary advantage, etc.)
- **Business context**: Lead with practical implications. Focus recommendations on
  actionable next steps. Reference specific competitors where possible.
- **Regulated industries**: Note where regulatory positioning contributes to inimitability
  or where regulatory change could erode advantage.
- **Technology firms**: Pay particular attention to data network effects, platform lock-in,
  and the risk of hyperscaler/platform owner displacement.

## Common Pitfalls to Avoid

- **Everything is sustainable**: If every resource scores Yes across the board, the analysis
  lacks critical rigour. Most firms have at most one or two truly sustainable advantages.
- **Confusing valuable with rare**: Many valuable capabilities (e.g. cloud infrastructure,
  CI/CD pipelines, basic AI/ML) are table stakes — valuable but not rare.
- **Ignoring the Organisation dimension**: A resource can be V+R+I and still fail to
  deliver advantage if the firm isn't structured to exploit it. This is where many
  analyses fall short.
- **Static assessment**: VRIO outcomes shift over time. Note where a resource's position
  is likely to erode (competitors catching up, technology commoditisation) or strengthen
  (network effects compounding, regulatory moats deepening).
