# PR and Earned Media

How to get third parties — journalists, influencers, communities — to carry your message.

## Canonical sources

- **Ryan Holiday** — *Trust Me, I'm Lying*, *Perennial Seller*. How media narratives are constructed; how to manufacture coverage; why "link economy" drives editorial decisions. *Perennial Seller*: the long game — building work that keeps spreading without continuous PR effort.
- **Ries & Ries** — *The Fall of Advertising and the Rise of PR*. The argument that PR, not advertising, builds brands. Advertising defends; PR creates.
- **Michael Sitrick** — *Spin*. Crisis PR and narrative control. How to manage a story before it manages you.
- **Jason Fried & DHH** — *Rework*, blog. How Basecamp built a brand without a PR firm: strong opinions, written publicly, with the company's name on them.
- **Simon Willison, Swyx (Shawn Wang)** — not books, but living examples of developer-influencer PR: consistent technical writing + a distinct point of view → becomes the primary citation source in a domain.

## Core concepts

### Earned media vs owned vs paid
- **Paid media:** you pay for placement (ads, sponsorships). Controllable, immediate, stops when budget stops.
- **Owned media:** you control the channel (blog, newsletter, GitHub, podcast). Compound but slow.
- **Earned media:** third parties carry your story (press, social sharing, citations, community posts). Highest trust, hardest to manufacture, most durable.

The hierarchy of trust: earned > owned > paid. The goal is to use owned media to earn coverage.

### The story, not the product
Journalists and influential writers cover stories, not products. A product launch is not a story. A finding, a data point, a counter-intuitive insight, a named tension in the field — these are stories. The product is evidence that the story is real.

**Story shapes that travel:**
- "I measured X and found Y, which contradicts the received wisdom about Z."
- "Here's a trend everyone is experiencing but no one has named yet."
- "I built a tool to solve problem X — here's what the data showed after 30 days."
- "This thing we all do is costing us more than we think."

### The pitch
A PR pitch to a journalist or influential writer is a short email (< 200 words) that:
1. References a specific piece they wrote — proving you actually read them.
2. States the story in one sentence — what is the insight, finding, or tension?
3. Explains why their audience will care — not why you care.
4. Offers something exclusive — data, early access, an interview, a unique angle.

The pitch is about them, not you. "I think your readers would find this interesting because..." not "I'd love to share my product with you."

### Targeting the right people
For developer tools: target writers, not publications. Publications are containers; writers have audiences and trust.

Types of targets for a developer tool:
- **Technically credible bloggers** (Simon Willison, Swyx, Julia Evans, Xe Iaso) — they publish their own findings; one mention in their newsletter reaches the exact ICP.
- **Newsletter authors** (TLDR AI, Ben's Bites, Latent Space) — curated distributions to qualified audiences; reach via a short story pitch, not a press release.
- **Community moderators** (r/LocalLLaMA, Hacker News regulars) — don't pitch them directly; produce something worth sharing in their community.
- **Journalists at niche trades** (The Pragmatic Engineer, The Register's developer section) — respond to data, benchmarks, and counter-intuitive findings.

### Data-driven PR
The highest-leverage earned media asset for a technical product is original data. A report, benchmark, or finding that no one else has published:
- Is a natural citation target (writers need sources).
- Demonstrates that you have access to information others don't.
- Travels because it answers a question people have but couldn't answer themselves.

For `ai-agents-metrics`: a public analysis of 30 days of AI coding with specific, verifiable numbers (retry rate, cost per outcome, model comparison) is inherently citable. The tool is evidence; the data is the story.

### One-shot channels
Some channels are high-reach and one-time: Show HN, a ProductHunt launch, a viral tweet. These channels burn on first use and cannot be re-entered credibly. The sequencing rule: **own media → earn social proof → then hit the one-shot channels.** A weak Show HN with no prior social proof buries the project permanently in search.

## Practical principles

- **Lead with the finding, not the product.** "I analyzed X and found Y" is a story. "I built a tool" is not.
- **Target the writer, not the outlet.** Read their last 10 pieces. Pitch one story angle that fits their beat.
- **Personalize every pitch.** A generic pitch with a product description is spam. A one-paragraph email that references a specific piece they wrote and explains why this is their next story — that gets replies.
- **Original data is the highest-leverage PR asset.** It cannot be replicated; it must be cited; it gives writers something new to say.
- **Treat influential technical bloggers as your primary PR channel, not journalists.** For developer tools, Simon Willison posting a 200-word observation is worth more than a TechCrunch article.
- **Don't pitch the same story to two competing outlets simultaneously.** Offer exclusive right of first coverage on your strongest story angle; reserve the rest for follow-ups.
- **Community posts are PR when done right.** An honest analysis post in r/ClaudeAI or a Hacker News "Ask HN" reaches the ICP directly. The format: "I measured X, found Y, methodology is Z, here's what I would have done differently." No promotional framing.
- **Press releases are for SEO, not journalists.** Modern journalists don't read press releases. The press release is useful for generating search-indexed coverage; the story pitch is what actually reaches editors.
- **The DM is a conversation opener, not a pitch.** A cold DM to an influencer that starts with "I'd love you to check out my product" fails. A DM that says "I saw your post about X — I have a data point that complicates that picture, happy to share" opens a conversation.
