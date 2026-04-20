# Images

Binary assets used by documentation — primarily README preview images
that appear in link unfurls (Twitter, Slack, Reddit, GitHub repo cards).

## report-preview.png — how to (re)generate

The slot reserved at the top of the main README expects a screenshot of a
rendered HTML report, ideally showing a chart with real data.

1. Generate a report from your own warehouse:

       ai-agents-metrics render-html --output /tmp/report.html

2. Open `/tmp/report.html` in a browser at ~1200px viewport width.

3. Screenshot the page (or a key chart). Recommended dimensions for
   link-unfurl previews: **1200 × 630 px** (Twitter/OG standard).

4. Save to `docs/images/report-preview.png`.

5. Uncomment the `![HTML report preview](...)` line in the root README.

There is no committed default image — each release can ship a fresh one.
