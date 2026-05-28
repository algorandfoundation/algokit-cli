---
title: "AlgoKit Vibe"
---

The `algokit vibe` command group helps you install and initialize [VibeKit](https://getvibekit.ai/) for AlgoKit projects.

## Commands

### `algokit vibe setup`

Installs VibeKit (if missing) and runs `vibekit init` in your current project.

- If `vibekit` is not found, AlgoKit prompts to install it.
- Installation is OS-specific:
  - macOS/Linux: `curl -fsSL https://getvibekit.ai/install | sh`
  - Windows: `irm https://getvibekit.ai/install | iex`
- If installation is declined, the command exits with manual install guidance.

When initializing, AlgoKit also provides best-effort LocalNet context to VibeKit through environment variables:

- `ALGOKIT_LOCALNET_ALGOD_URL`
- `ALGOKIT_LOCALNET_ALGOD_TOKEN`
- `ALGOKIT_LOCALNET_INDEXER_URL`
- `ALGOKIT_LOCALNET_INDEXER_TOKEN`
- `ALGOKIT_LOCALNET_RUNNING`

If LocalNet inspection fails, `vibekit init` still runs.

### `algokit vibe status`

Runs `vibekit status` to check VibeKit status for the current environment.

If VibeKit is missing, this command exits with installation guidance.
