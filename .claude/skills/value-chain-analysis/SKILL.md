---
name: value-chain-analysis
description: >
  Structured Value Chain Analysis using Porter's (1985) framework to identify where and how
  a firm creates value and competitive advantage through its activities. Use this skill whenever
  the user wants to analyse how a company creates value, map primary and support activities,
  identify cost drivers or differentiation sources, find operational improvements, or mentions
  "value chain", "Porter's value chain", "primary activities", "support activities",
  "where does the value come from", "how do they make money", "operational analysis",
  or "activity-based analysis". Also trigger when the user is working on strategy assignments
  or business programme exercises involving internal activity mapping, cost structure analysis,
  or identifying sources of competitive advantage at the activity level. Use this skill even when
  the user doesn't name the framework explicitly but the core question is "where in the business
  is value created or destroyed?"
---

# Value Chain Analysis — Porter's Framework

## What This Skill Does

Guides a structured analysis of a firm's internal activities using Porter's (1985) Value Chain
framework. Identifies where value is created, where costs accumulate, and where competitive
advantage (cost leadership or differentiation) originates — producing a mapped activity
analysis with strategic recommendations.

## Theoretical Foundation

Porter's Value Chain decomposes a firm into strategically relevant activities to understand
cost behaviour and differentiation sources. The premise is that competitive advantage comes
not from the firm as a whole but from the specific activities it performs and how they
interconnect.

The framework divides activities into two categories:

### Primary Activities

These directly create, deliver, and support the product or service:

1. **Inbound Logistics** — receiving, storing, and distributing inputs. For traditional firms:
   raw materials, warehousing, inventory control. For SaaS/digital firms: data ingestion,
   API integrations, third-party data feeds, cloud resource provisioning.

2. **Operations** — transforming inputs into the final product or service. For traditional
   firms: manufacturing, assembly, quality control. For SaaS/digital firms: software
   development, CI/CD pipelines, platform engineering, algorithm/model training,
   infrastructure operations (compute, storage, networking).

3. **Outbound Logistics** — delivering the product to customers. For traditional firms:
   warehousing, distribution, shipping. For SaaS/digital firms: deployment pipelines,
   CDN delivery, tenant provisioning, release management, self-service onboarding.

4. **Marketing & Sales** — activities that inform buyers and induce purchase. Includes
   branding, advertising, sales force, channel management, pricing strategy. For SaaS:
   also includes product-led growth mechanics, freemium/trial funnels, developer
   relations, partner ecosystems.

5. **Service** — activities that maintain or enhance product value post-purchase. Includes
   customer support, training, maintenance, returns. For SaaS: customer success,
   onboarding, documentation, community forums, managed services, SLA management.

### Support Activities

These enable and enhance the efficiency of primary activities:

1. **Firm Infrastructure** — general management, planning, finance, legal, quality
   management, governance. Sets the organisational context in which all other activities
   operate. Includes compliance and regulatory functions.

2. **Human Resource Management** — recruiting, hiring, training, development,
   compensation. Critical in knowledge-intensive firms where talent is a primary
   value driver.

3. **Technology Development** — R&D, process automation, technology platforms, IT
   systems. In tech firms this often overlaps with Operations — the skill should help
   the user draw the boundary clearly.

4. **Procurement** — purchasing inputs, negotiating supplier relationships, vendor
   management. For SaaS: includes cloud provider contracts, third-party API/data
   licensing, tooling acquisition.

### Margin

The difference between total value created and the collective cost of performing all
activities. The goal of value chain analysis is to find activities where the firm can
either reduce costs or increase willingness-to-pay, expanding margin.

## Adapting the Framework

Porter's original framework was designed for manufacturing. When applying to
services, SaaS, platform businesses, or digital firms, the activity labels need
reinterpretation. The skill should:

- Relabel activities to fit the firm's actual operations (e.g. "Inbound Logistics"
  becomes "Data Ingestion & Integration" for a data platform company)
- Acknowledge that some boundaries blur in digital firms (Technology Development
  is both a support activity AND central to Operations)
- Consider network effects and platform dynamics where relevant
- Note where the value chain extends beyond the firm (partner ecosystems,
  marketplaces, open-source communities)

## Process

### Step 1: Scope the Analysis

Clarify what's being analysed:
- The whole firm, a specific business unit, or a specific product line?
- What industry context? (affects which activities matter most)
- Is the goal cost analysis, differentiation analysis, or both?
- Are there specific competitors to benchmark against?

If the user hasn't specified, default to whole-firm analysis with a focus on
identifying differentiation sources.

### Step 2: Map Primary Activities

For each of the five primary activities:
- Describe what the firm actually does in this category
- Identify key sub-activities at a useful level of granularity
  (e.g. not just "Operations" but "agile development sprints, security scanning
  pipeline, multi-cloud deployment orchestration")
- Assess whether each activity is a **cost driver** or **differentiation source**
  (or both, or neither — some activities are necessary but undifferentiated)
- Note linkages between activities where coordination creates additional value

### Step 3: Map Support Activities

For each of the four support activities:
- Describe how it enables primary activities
- Identify which primary activities it most significantly impacts
- Assess whether it contributes to cost advantage, differentiation, or both

### Step 4: Identify Value Drivers and Cost Drivers

Synthesise across all activities:
- Which 2-3 activities are the most significant sources of differentiation?
- Which 2-3 activities are the largest cost centres?
- Where are the most important linkages (activities that amplify each other's value)?
- Where are there inefficiencies, redundancies, or missed opportunities?

### Step 5: Competitive Comparison (if applicable)

If competitors have been identified:
- Where does the firm perform activities differently from competitors?
- Which activity differences explain competitive advantage or disadvantage?
- Where could the firm learn from competitors' approaches?

### Step 6: Strategic Recommendations

Based on the analysis:
- Recommend where to invest to strengthen differentiation
- Identify activities that could be optimised for cost
- Flag activities that could be outsourced vs. those that must remain in-house
  (core to competitive advantage)
- Note where AI, automation, or technology could transform specific activities
- Identify the biggest risk to the current value chain configuration

## Output Structure

1. **Activity Map** — a structured listing of primary and support activities with
   descriptions tailored to the specific firm/industry
2. **Value and Cost Analysis** — for each activity, whether it drives differentiation,
   cost, or both, with evidence
3. **Linkage Analysis** — key interdependencies between activities that create
   additional value
4. **Strategic Recommendations** — prioritised actions to strengthen the value chain

## Calibration Notes

- **Academic context**: Reference Porter (1985) explicitly. Use the formal activity
  labels. Discuss the relationship between value chain analysis and competitive
  strategy (cost leadership vs. differentiation). Connect to other frameworks
  where relevant (VRIO for whether activity-based advantages are sustainable,
  Five Forces for industry context).
- **Business context**: Lead with practical implications. Use the firm's own
  terminology for activities. Focus recommendations on specific, actionable changes.
- **SaaS/Technology firms**: Reinterpret the traditional categories. Product
  development and engineering are typically the dominant value-creating activities.
  Customer success often matters more than traditional "service". Platform and
  ecosystem dynamics may be more important than classical logistics.
- **Regulated industries**: Note where compliance activities add cost without
  differentiation, and where regulatory expertise itself becomes a source of
  competitive advantage.

## Common Pitfalls to Avoid

- **Forcing traditional labels onto digital businesses**: If "Inbound Logistics"
  doesn't meaningfully apply, say so and reframe. The value is in the analysis,
  not in filling every box.
- **Listing activities without assessing value**: The analysis should identify
  *where* advantage comes from, not just describe what the firm does.
- **Ignoring linkages**: Often the most important insights come from how activities
  interact (e.g. tight integration between R&D and Customer Success creating a
  feedback loop that improves the product faster than competitors).
- **Static snapshot**: Note where the value chain is evolving — activities being
  automated, outsourced, or transformed by AI.
- **Confusing the value chain with the customer journey**: The value chain maps
  internal activities; the customer journey maps external touchpoints. They're
  complementary but distinct.

## Relationship to Other Frameworks

- **VRIO**: Value chain identifies *which activities* create advantage; VRIO assesses
  *whether that advantage is sustainable*. They pair well — use value chain to find
  the activities, then VRIO to test their defensibility.
- **Porter's Five Forces**: External industry analysis that provides context for
  which value chain configurations will be most effective.
- **SWOT**: Value chain findings feed into the Strengths and Weaknesses quadrants.
- **PESTLE**: External macro factors that may force changes to the value chain
  (e.g. regulation, technology shifts).
