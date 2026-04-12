# Public Overlay Sync Runbook

Operational guide for syncing between the private repository and the public `oss/` subtree.

## Layout

```
codex-metrics/          ← private repo (this repo)
  oss/                  ← git subtree mirror of codex-metrics-public
  docs/retros/          ← private, never synced
  docs/audits/          ← private, never synced
  metrics/              ← private, never synced
```

The public repository lives on GitHub (`sg4tech/codex-metrics-public`).
The `public` git remote in this repo points directly to it — no local mirror.

`oss/` is the only sync surface. Everything outside it stays private.

## Check Status

```bash
make public-overlay-status
```

Shows planned sync commands and whether the `oss/` directory exists.

## Outbound: Private → Public

Push private changes from `oss/` into the public repository.

```bash
make public-overlay-push
```

This runs boundary verification first, then pushes to the `sync` branch on the public remote.
Fails loudly if the boundary check detects private content.

After the push, open a PR from `sync` → `main` on GitHub manually, wait for CI, and merge.

Use `--pr-branch` to override the target branch: `make public-overlay-push` passes it through to the script.

**When to use:** after landing a change in `oss/` that should be public.

## Inbound: Public → Private

Pull public changes (contributor patches, fixes merged to public `main`) back into `oss/`.

```bash
make public-overlay-pull
```

This runs `git subtree pull --prefix=oss public main --squash`, then re-runs boundary verification.

**When to use:** after a PR is merged into `main` on the public repo.

## Conflict Resolution

Conflicts during `subtree pull` are usually in `Makefile`, `README.md`, or source files
where both sides changed independently. Resolve them by:

1. Keeping the private (HEAD) version for features not yet in public (security scan, etc.)
2. Accepting public changes for files only modified there
3. Staging resolved files: `git add <file>`
4. Committing: `git commit`
5. Then re-running `make public-overlay-push` to push the merged result

## Boundary Verification

```bash
make public-overlay-verify
```

Scans `oss/` against `oss/config/public-boundary-rules.toml`.
Checks for forbidden paths, file extensions, and content markers (private keys, local paths, tokens).
Also runs automatically as part of `make public-overlay-push` and `make public-overlay-pull`.

## Classification Rules

| Content | Location | Synced? |
|---------|----------|---------|
| `src/`, `tests/`, `tools/`, `config/public-boundary-rules.toml` | `oss/` | Yes |
| `docs/retros/`, `docs/audits/` | outside `oss/` | Never |
| `metrics/`, local history artifacts | outside `oss/` | Never |
| `AGENTS.md`, `docs/ai-agents-metrics-policy.md` | outside `oss/` | Manual review required |

## Releasing (PyPI)

Publishing to PyPI is fully automated via GitHub Actions (`publish.yml` on the public repo).
The workflow triggers on any tag matching `v*` pushed to the public remote.

**To release a new version:**

1. Merge all changes to `main` on the public repo (via the sync → main PR flow above)
2. Create and push the tag **to the public remote only**:
   ```bash
   git fetch public --tags
   git push public v0.x.y
   ```
3. The publish workflow builds and uploads to PyPI automatically via Trusted Publishing — no token required locally

**Tag must point to a public commit.** The tag object must reference a commit
that exists in the public repo's history. Private-repo commits (merge commits
from `public-overlay-pull`, private-only changes) are not present on the public
remote, so `publish.yml` cannot check them out and the build produces a broken
`0.0.0.dev` version. Always create the tag from a public commit hash:
```bash
git fetch public --tags
git tag v0.x.y public/main      # ← points at the public HEAD
git push public v0.x.y
```

**Tag convention:** tags live only on the `public` remote (`sg4tech/ai-agents-metrics`).
Never create version tags on the private `origin` remote (`sg4tech/codex-metrics`).
If a tag accidentally lands on `origin`, delete it:
```bash
git push origin :refs/tags/vX.Y.Z
```

**Version detection:** `setuptools-scm` reads tags from the local git history.
If `make package` is run locally (not via CI), the tag must be fetched first:
```bash
git fetch public --tags
make package
```
If the tag is not reachable from the current HEAD (subtree commit mismatch),
pass the version explicitly: `SETUPTOOLS_SCM_PRETEND_VERSION=0.x.y make package`.
In practice, prefer CI for all releases — local builds are for debugging only.

## Known Limitations

**`make public-overlay-pull` fails with a dirty working tree.**
`git subtree pull` refuses to run if there are uncommitted changes.
This is a known limitation of the subtree script.

Workaround until fixed:
```bash
git stash && make public-overlay-pull && git stash pop
```

To avoid this: commit or stash all local changes before pulling.

## Do Not

- Edit public repo files directly and then push without pulling back into `oss/`
  (causes divergence that requires manual conflict resolution on next pull)
- Run `git subtree push` without running boundary verification first
- Move `docs/retros/` or `metrics/` inside `oss/`
- Create version tags on the private `origin` remote — tags belong on `public` only
