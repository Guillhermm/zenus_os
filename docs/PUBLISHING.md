# Publishing Guide

How releases are built and where packages are published.

---

## Distribution channels

| Channel | Install command | Audience |
|---------|----------------|----------|
| **PyPI** | `pip install zenus-cli` | Python developers |
| **Snap** | `snap install --classic zenus` | Linux desktop users |
| **GitHub Releases** | Download from releases page | Manual / offline installs |
| **Source** | `./install.sh` | Power users, contributors |

---

## Release flow

Releases are triggered by pushing a version tag:

```bash
git tag v0.6.0
git push origin v0.6.0
```

The `release.yml` workflow then runs automatically:

```
tag push
  └── test (gate)
        ├── publish-pypi       → PyPI (zenus-visualization, zenus-core, zenus-cli, zenus-tui)
        ├── build-snap         → .snap artifact
        │     └── publish-snap → Snap Store (if SNAP_PUBLISH=true)
        └── github-release     → GitHub Release with snap + install.sh attached
```

Pre-release tags (`v0.6.0-alpha`, `v0.6.0-beta`, `v0.6.0-rc.1`) are published as
GitHub pre-releases and to Snap Store `edge` channel.

---

## One-time setup (required before first release)

### 1. PyPI token

1. Create an account at [pypi.org](https://pypi.org)
2. Go to Account Settings → API tokens → Add API token
3. Scope: "Entire account" for the first publish; per-project after packages exist
4. In GitHub repo → Settings → Secrets → Actions → New repository secret:
   - Name: `PYPI_TOKEN`
   - Value: the token (starts with `pypi-`)

Packages published: `zenus-visualization`, `zenus-core`, `zenus-cli`, `zenus-tui`

> **Note:** After the first release, consider switching to PyPI Trusted Publishing
> (OIDC) to eliminate the need for a long-lived token. See:
> https://docs.pypi.org/trusted-publishers/

### 2. Snap Store (optional for first release)

The snap artifact is always built and attached to the GitHub Release.
Publishing to the Snap Store is optional and controlled by a repository variable.

To enable Snap Store publishing:

1. Register the snap name: `snapcraft register zenus`
2. Export credentials: `snapcraft export-login --snaps zenus --acls package_upload credentials.txt`
3. In GitHub repo → Settings → Secrets → Actions:
   - Name: `SNAPCRAFT_STORE_CREDENTIALS`
   - Value: contents of `credentials.txt`
4. In GitHub repo → Settings → Variables → Actions:
   - Name: `SNAP_PUBLISH`
   - Value: `true`

Until `SNAP_PUBLISH=true` is set, the snap is built and attached to GitHub Releases
but not pushed to the Snap Store. Users can install locally:

```bash
snap install --classic --dangerous zenus_0.6.0_amd64.snap
```

### 3. Branch protection (recommended)

In GitHub repo → Settings → Branches → Add rule for `main`:
- Require status checks: `Test (Python 3.11)` (from ci.yml)
- Require branches to be up to date before merging

---

## Package dependency order

The four published packages have this dependency chain:

```
zenus-visualization  (no local deps)
       └── zenus-core
             ├── zenus-cli
             └── zenus-tui
```

The release workflow publishes them in this order. The path dependencies
(`{path = "../core", develop = true}`) are automatically patched to versioned
PyPI references (`"^0.6.0"`) before building.

---

## Versioning

Zenus follows [Semantic Versioning](https://semver.org):

- `MAJOR.MINOR.PATCH` — stable releases
- `MAJOR.MINOR.PATCH-alpha.N` — alpha (significant features in progress)
- `MAJOR.MINOR.PATCH-beta.N` — beta (feature complete, stabilizing)
- `MAJOR.MINOR.PATCH-rc.N` — release candidate

All four packages (`zenus-visualization`, `zenus-core`, `zenus-cli`, `zenus-tui`)
share the same version number and are always released together.

---

## Tagging

```bash
# Update CHANGELOG: move [Unreleased] to [0.6.0] with today's date
# Commit the changelog update
git add CHANGELOG.md
git commit -m "Release v0.6.0"

# Tag and push — this triggers the release workflow
git tag v0.6.0
git push origin main v0.6.0
```

The workflow reads the version from the tag and stamps it into all pyproject.toml
files and snapcraft.yaml during the build — no manual version editing in those
files is needed at release time.
