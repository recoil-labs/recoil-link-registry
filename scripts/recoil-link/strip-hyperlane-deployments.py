#!/usr/bin/env python3
"""Remove Hyperlane's deployment data from this registry, keeping chain facts.

Idempotent: re-run after every upstream merge so new upstream chains, routes
and addresses never leak into Recoil Link.

Removed (only files identical to upstream/main, so our own deployments survive):
  - chains/*/addresses.yaml          Hyperlane core contract addresses
  - deployments/warp_routes, /avs    Hyperlane token routes and AVS config
  - metadata `deployer`, `index`, `availability` blocks that still equal
    upstream's (they describe Hyperlane's deployment)
  - blockExplorers[].apiKey lines that appear upstream (Hyperlane's keys)
Kept: all other chain metadata, logos, and any value Recoil Link has changed.
"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOP_LEVEL_KEYS = ("deployer", "index", "availability")

UPSTREAM = "upstream/main"


def upstream_blobs(prefixes):
    """Map path -> blob id for upstream files under the given prefixes."""
    out = subprocess.run(
        ["git", "ls-tree", "-r", UPSTREAM, "--", *prefixes],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    blobs = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        blobs[path] = meta.split()[2]
    return blobs


def local_blob(path):
    return subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


# Delete only files identical to Hyperlane's upstream copy, so Recoil Link's
# own addresses and routes survive re-runs.
upstream = upstream_blobs(["deployments/warp_routes", "deployments/avs", "chains"])
for rel, blob in upstream.items():
    is_deployment = rel.startswith("deployments/") or rel.endswith("/addresses.yaml")
    path = ROOT / rel
    if is_deployment and path.is_file() and local_blob(path) == blob:
        path.unlink()
for d in sorted((ROOT / "deployments").rglob("*"), reverse=True):
    if d.is_dir() and not any(d.iterdir()):
        d.rmdir()

# scripts/build.ts iterates this directory, so it must exist even when empty.
warp_dir = ROOT / "deployments" / "warp_routes"
warp_dir.mkdir(parents=True, exist_ok=True)
(warp_dir / ".gitkeep").touch()


def top_level_blocks(text: str) -> dict:
    """Top-level key -> its full block text (key line plus indented lines)."""
    blocks, key = {}, None
    for line in text.splitlines(keepends=True):
        m = re.match(r"^([A-Za-z]+):", line)
        if m:
            key = m.group(1)
            blocks[key] = ""
        if key:
            blocks[key] += line
    return blocks


def strip_metadata(text: str, upstream_text: str) -> str:
    """Drop Hyperlane-specific fields, but only where they still match upstream."""
    upstream_blocks = top_level_blocks(upstream_text)
    upstream_lines = set(upstream_text.splitlines())
    out, skipping, promote_next = [], False, None
    for line in text.splitlines(keepends=True):
        key = re.match(r"^([A-Za-z]+):", line)
        if key:
            k = key.group(1)
            skipping = (
                k in TOP_LEVEL_KEYS
                and top_level_blocks(text).get(k) == upstream_blocks.get(k)
            )
        if skipping:
            continue
        is_upstream_key = line.rstrip("\n") in upstream_lines
        # apiKey as first field of a list item: drop it, make the next field the item head.
        m = re.match(r"^(\s*)- apiKey:", line)
        if m and is_upstream_key:
            promote_next = m.group(1)
            continue
        if promote_next is not None:
            line = f"{promote_next}- {line.lstrip()}"
            promote_next = None
            out.append(line)
            continue
        if re.match(r"^\s+apiKey:", line) and is_upstream_key:
            continue
        out.append(line)
    return "".join(out)


def upstream_text(rel: str) -> str:
    res = subprocess.run(
        ["git", "show", f"{UPSTREAM}:{rel}"], cwd=ROOT, capture_output=True, text=True
    )
    return res.stdout if res.returncode == 0 else ""


for path in (ROOT / "chains").glob("*/metadata.yaml"):
    rel = str(path.relative_to(ROOT))
    original = path.read_text()
    stripped = strip_metadata(original, upstream_text(rel))
    if stripped != original:
        path.write_text(stripped)


# Regenerate the combined files (normally written by scripts/build.ts) so they
# match the stripped per-chain files. Each chain's YAML is nested under its name.
AUTO_GEN_PREFIX = "# AUTO-GENERATED; DO NOT EDIT MANUALLY\n"
chains = {}
for path in (ROOT / "chains").glob("*/metadata.yaml"):
    text = path.read_text()
    name = re.search(r"^name: *(\S+)", text, re.M).group(1).strip("\"'")
    body = [l for l in text.splitlines() if not l.startswith("#") and l.strip() != "---"]
    chains[name] = "".join(f"  {l}\n" if l else "\n" for l in body)
combined = "".join(f"{name}:\n{chains[name]}" for name in sorted(chains))
(ROOT / "chains" / "metadata.yaml").write_text(AUTO_GEN_PREFIX + combined)
addresses = {}
for path in (ROOT / "chains").glob("*/addresses.yaml"):
    body = [l for l in path.read_text().splitlines() if not l.startswith("#") and l.strip() != "---"]
    addresses[path.parent.name] = "".join(f"  {l}\n" if l else "\n" for l in body)
(ROOT / "chains" / "addresses.yaml").write_text(
    AUTO_GEN_PREFIX + ("".join(f"{n}:\n{addresses[n]}" for n in sorted(addresses)) or "{}\n")
)
if not any(p.suffix == ".yaml" and p.name != "warpRouteConfigs.yaml" for p in warp_dir.rglob("*")):
    (warp_dir / "warpRouteConfigs.yaml").write_text(AUTO_GEN_PREFIX + "{}\n")
else:
    print("note: Recoil Link warp routes present; run scripts/build.ts to regenerate warpRouteConfigs.yaml")

print(f"stripped Hyperlane deployment data; {len(chains)} chains kept")
