# Discovery

Understanding what to build — before building it.

## Canonical sources

- **Teresa Torres** — *Continuous Discovery Habits*. Defined the modern continuous-discovery practice: weekly customer interview cadence, Opportunity Solution Tree (OST), assumption testing.
- **Tony Ulwick** — *What Customers Want*, *Jobs to be Done*. Outcome-Driven Innovation (ODI): JTBD formalized with job statements and opportunity scoring.
- **Clayton Christensen** — *The Innovator's Dilemma*, *Competing Against Luck*. The original JTBD theory; the milkshake case study.
- **Bob Moesta** — *Demand-Side Sales*. JTBD interview technique: forces of progress, timeline interviews, switch moments.
- **Steve Portigal** — *Interviewing Users*. The craft of interviewing, separated from any methodology.
- **Erika Hall** — *Just Enough Research*. Antidote to "research theatre"; how to do useful research without a research department.
- **Indi Young** — *Practical Empathy*, *Mental Models*. Listening sessions, thinking-style research.
- **Steve Blank** — *The Four Steps to the Epiphany*. Customer development: "get out of the building."

## Core frameworks

- **Opportunity Solution Tree (Torres).** Tree: `outcome → opportunities → solutions → assumption tests`. Enforces the link between every experiment and a desired outcome.
- **Job statement format.** `When [situation], I want to [motivation], so I can [expected outcome]`.
- **Forces of progress (Moesta).** Four forces acting on a buyer: push of the current situation, pull of the new solution, anxiety of the new, habit of the old. A switch happens only when push + pull > anxiety + habit.
- **Five Whys.** Keep asking why until the real cause surfaces; a symptom is not a cause.

## Win-loss analysis

Not in Torres or Moesta, but an important adjacent method — especially for products where adoption is a deliberate decision (B2B, paid tools, dev tools with meaningful setup cost):

- **Interview recent buyers *and* recent non-buyers.** The non-buyer reveals what the product doesn't yet do, why the alternative won, and what the positioning gap is. Buyers reveal what tipped the decision.
- **Win-loss is a leading PMF indicator.** If you consistently lose to "doing nothing," positioning is broken. If you consistently lose to a specific competitor, the gap is feature-level. Different problems, different fixes.
- **Timing matters.** Interview within 2 weeks of the decision while the forces are fresh (Moesta's switch-moment rule applies here too).
- **For OSS / free tools, adapt the framing.** "Adoption" replaces "purchase." The win-loss question becomes: "Why did you try it? What made you keep using it vs. drop it?"

## Quantitative discovery

Qualitative methods find the shape of the problem; quantitative methods size it and reveal patterns across the whole user base (not just those willing to talk).

- **Funnel / drop-off analysis.** Where in the activation flow do users stop? A 60% drop at step 2 is a problem statement — not a solution.
- **Cohort retention curves.** D1/D7/D30 retention by acquisition cohort shows whether the product is getting stickier over time. A flattening curve at non-zero means a core use case exists; a curve that decays to zero means it doesn't.
- **Feature adoption analysis.** Which features do retained users use? Which features do churned users never touch? The intersection reveals what actually drives value.
- **Session/usage frequency histograms.** Not average usage — distribution. If 80% of sessions come from 5% of users, the core use case is narrow (a risk and an opportunity).
- **Search and entry-point analysis.** For OSS tools: what queries lead to the README? What brings people back to the repo? GitHub traffic analytics and search-referral data are discoverable without any instrumentation.

For early-stage OSS tools with <100 users: qualitative is often sufficient and more informative. Quantitative methods become load-bearing only when there are enough users for cohorts to be statistically meaningful.

## Practical principles

- **Interview for problems, not solutions.** People are unreliable at predicting what they want; they are reliable at reporting what they tried and what went wrong.
- **Triangulate qual + quant.** Qualitative finds the shape of the problem; quantitative sizes it.
- **Continuous cadence beats sprints.** Weekly touches keep discovery compounding. Sporadic "research phases" decay between studies.
- **Separate problem validation from solution validation.** Different interviews, different artifacts.
- **Recent switchers are the gold sample.** They remember the forces; long-term users have rationalized the decision.
