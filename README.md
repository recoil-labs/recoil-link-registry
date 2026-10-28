# Recoil Link Registry

Chain metadata and deployment addresses for [Recoil Link](https://github.com/recoil-labs/recoil-link), the interchain messaging protocol by Recoil Labs. The `rlink` CLI and the Recoil Link SDK read this repository by default.

## Status

- **Chains:** metadata for 348 chains (RPC URLs, chain IDs, native tokens, block explorers), inherited from the Hyperlane registry.
- **Deployments:** none yet. Hyperlane's contract addresses, warp routes, deployer info and explorer API keys have been removed, so Recoil Link tooling can never use Hyperlane's contracts by accident. `addresses.yaml` files are added per chain as Recoil Link deploys.

## Keeping in sync with upstream

This is a fork of [hyperlane-xyz/hyperlane-registry](https://github.com/hyperlane-xyz/hyperlane-registry) (MIT). To pull new chains and metadata fixes:

```sh
git fetch upstream && git merge upstream/main
python3 scripts/recoil-link/strip-hyperlane-deployments.py
```

The script is idempotent and only deletes files identical to the upstream copy, so Recoil Link's own `addresses.yaml` files and warp routes are kept.

## Contents

### Chains

A list of chains and the relevant information that Hyperlane utilities and apps will require to interact with chains.
Structured as a folder for each chain. Each folder should contain a `metadata.yaml`, `addresses.yaml`, and a `logo.svg` file.

### Deployments

#### Core

Configs and artifacts for [Hyperlane Core Contract](https://docs.hyperlane.xyz/docs/guides/chains/deploy-hyperlane) deployments.

#### Warp

Address artifacts for [Warp Route](https://docs.hyperlane.xyz/docs/applications/warp-routes/overview) token deployments.

#### Install `gitleaks`

You need `gitleaks` installed on your machine. You can download it from [official page](https://github.com/gitleaks/gitleaks) or use a package manager of your choice.

## Contributing

This registry is maintained by the core Hyperlane team but community members are encouraged to add chain and deployment information here! See the [Contribution Guide](./CONTRIBUTING.md) for more information.
