# Releasing

Two stages: CI builds the package, then a human promotes it into the Dify
catalog.

## 1. Build (automated)

1. Bump `version` in `manifest.yaml`.
2. Commit and push to `main`.
3. Create a GitHub release tagged `v<version>` — e.g. `v0.0.3` for
   `version: 0.0.3`. CI fails the build if the tag and manifest disagree.

The workflow packages the plugin and attaches `anakin-<version>.difypkg` to the
release. It also uploads the same file as a build artifact, so a
`workflow_dispatch` run can produce a package without cutting a release.

## 2. Promote to the Dify Marketplace (manual)

The catalog is `langgenius/dify-plugins`, a monorepo of every vendor's built
packages. Publishing means opening a PR into it from our fork.

1. Download `anakin-<version>.difypkg` from the release.
2. In [`Anakin-Inc/anakin-dify-plugins`](https://github.com/Anakin-Inc/anakin-dify-plugins),
   commit it to `anakin/anakin/` on a branch — matching the existing
   `anakin.difypkg` and `anakin_0.0.2.difypkg`.
3. Open a PR from that branch to `langgenius/dify-plugins`.

Keep the fork in sync with upstream before branching, or the PR will carry
unrelated changes:

```sh
gh repo sync Anakin-Inc/anakin-dify-plugins --source langgenius/dify-plugins
```

### Why this step is not automated

Pushing to the catalog fork from this repository's CI would need a personal
access token, since `GITHUB_TOKEN` cannot write to another repository. That
token would expire and break releases silently, months later, for a plugin
that ships about twice a year. A missing manual step is visible; an expired
credential is not.

## Repository layout

| Repo | Holds |
|---|---|
| `anakin-dify-plugin` | this repo — plugin source |
| `anakin-dify-plugins` | fork of the Dify catalog; built `.difypkg` files only |

Source must never be committed to the catalog fork. `anakin/anakin/` in the
catalog holds packages; putting source there overwrites upstream's package
directory.

## Tool parity with the MCP server

The plugin mirrors the Anakin MCP server's tools (`anakin-mcp`), plus
`url_scraper`/`batch_scraper` (split from MCP's `scrape`) and `web_scraper`.
When a tool or parameter lands in `anakin-mcp`, add it here and cut a release;
`tests/test_manifest.py` fails if a tool YAML is not registered in
`provider/anakin.yaml`.
