# Developer Tools Distribution

How OSS developer tools specifically reach users and build reputation. Distinct from generic growth playbooks — dev tools distribution is community-first, trust-first, and driven by individual credibility more than spend.

## Canonical sources

- **Simon Willison** (simonwillison.net) — the most cited practitioner model for OSS reputation-building through public learning. Publishes what he builds, what he reads, what surprised him. His key principle: _"Show your work"_ — not launch posts, but ongoing transparent progress notes.
- **Andrej Karpathy** — builds reputation by publishing explanations of things he deeply understands. Not a product launch model; a _"teach as you go"_ model that creates durable authority.
- **Swyx / shawn.io** — "Learn in Public" essay. The canonical statement of the reputation-first dev approach: make your learning artifacts public, create a trail that compounds.
- **Adam Wathan** (Tailwind CSS) — launched with a detailed "why I built this" essay before the tool existed. The essay built the audience; the tool satisfied it.
- **TJ Holowaychuk** — OSS through prolific high-quality code; reputation built entirely through artifact quality with no marketing.
- **DHH / Basecamp** — _It Doesn't Have to Be Crazy at Work_, HEY launch. Launched with a public opinion, not a product announcement. The controversy was the distribution.

## Distribution channels for dev tools (priority order)

1. **GitHub README as landing page.** First impression for most qualified users. Animated GIF or screenshot in the first 30 lines; one-sentence value prop; one-line install. The README is a sales page — most projects treat it as documentation.
2. **Analysis post / "I found X" format.** Not "I built a tool." Instead: "I analyzed 30 days of my AI coding and here's what I found — I also open-sourced the tool I used." The finding is the hook; the tool is the proof-of-work. This format outperforms pure launch posts on HN and Reddit consistently.
3. **Targeted DMs to credible voices.** 3–5 direct contacts to people the author already respects. Not cold pitches — shared-context messages. One response from a credible voice is worth more than 100 generic upvotes.
4. **Reddit in analysis format.** r/ClaudeAI, r/LocalLLaMA, r/programming. Lead with the finding; tool is a footnote. Threads that start "I built X" get downvoted; threads that start "I found X" get traction.
5. **awesome-\* lists.** awesome-claude, awesome-llm-apps, awesome-selfhosted. Strong backlinks; qualified discovery channel; long tail. Submit a PR when the tool has a working README — don't wait for polished docs.
6. **Hacker News Show HN.** One-shot. High upside; high variance. Time it for when there is social proof already (a Willison note, a Reddit post, a credible DM response). A Show HN with zero external signal performs poorly. Never the first move.
7. **AI-dev newsletters.** TLDR AI, Ben's Bites, Latent Space, Pragmatic Engineer. Usually respond to things that already have signal — pitch *after* the first wave, not before.
8. **GitHub Trending and stars.** A consequence, not a tactic. Cannot be gamed sustainably. A 48-hour trending placement is valuable but unpredictable.

## The "analysis post" format

The highest-converting format for OSS dev tools aimed at developers:

```
Title: "I analyzed [N days/projects] of [X behavior] — here's what I found"

Structure:
1. The surprising or counter-intuitive finding (the hook)
2. The methodology (builds trust)
3. Charts or tables (visual shareability)
4. Implications / what you changed
5. Footnote: "I open-sourced the tool I built for this — [link]"
```

Key rules:
- **The finding must be genuinely surprising to the author.** If it wasn't surprising to you, it won't be interesting to readers.
- **Do not lead with the tool.** Lead with the finding.
- **Statistical caveats signal credibility.** "This is n=1" or "small sample, directional" is honest and resonates with technical audiences.
- **One finding per post.** Multi-finding posts dilute attention.

## Reputation-first vs. downloads-first

Most OSS projects optimize for stars and downloads as primary KPIs. Developer tools with a reputation goal should optimize differently:

| Metric | Downloads-first | Reputation-first |
|---|---|---|
| Success signal | GitHub stars, PyPI downloads | Cited by credible voices |
| Primary content | Product launches | Public learning artifacts |
| Audience | Broad, any developer | Narrow, relevant developers |
| Compounding asset | User base | Published thinking |
| Risk of success | Scaling, support load | Copycats, commoditization |

For reputation-first: 500 qualified stars from AI engineers and tool-builders beats 5000 hype stars from a viral HN post.

## The Willison model in practice

Simon Willison publishes a weekly "things I learned / built" note. The key mechanics:
- **Short feedback loops.** Each small discovery gets published immediately, not held for a big launch.
- **Honest about limitations.** The note says what doesn't work, not just what does.
- **Feeds a growing reference corpus.** Over time, the body of notes becomes a searchable resource that others cite.
- **No product launch required.** The tool can be a one-liner script mentioned in a note. The _note_ is the distribution unit.

Implication for a solo dev building in public: publish the learning, not the product. The product is evidence; the learning is the content.

## OSS-specific technical distribution

- **README badges.** Build status, license, PyPI version. Signal: actively maintained.
- **GitHub Discussions / Issues as community surface.** Early users' questions become SEO content and future docs.
- **Changelog / release notes as content.** Each release is a reason to re-engage the audience. Write release notes for the reader, not for the diff.
- **Pinned examples and real-world use cases.** Not toy examples — real outputs on real data. Screenshots > code blocks for initial traction.

## Practical principles

- **The tool is proof-of-work, not the product.** The publicly-defended point of view is the product. The tool demonstrates that you can back it up.
- **One channel at a time.** Multi-channel simultaneous launch dilutes the message and exhausts a solo founder. One clear signal > five weak ones.
- **Don't launch until the tool has produced a genuine insight for the author.** Pitching value you cannot yourself articulate from your own usage is a positioning failure, not a timing failure.
- **HN is a one-shot; use it last.** Reddit, Twitter, DMs first. HN after social proof exists.
- **Credibility is local.** Being known in the r/ClaudeAI community is more valuable than anonymous HN upvotes if the target users live in that community.
- **"I found X" > "I built Y."** The framing changes who reads, shares, and responds.
