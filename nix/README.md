# Nix Development Environment

**This is only intended for NixOS users.** If you are on a standard Linux distribution or macOS, follow the regular setup instructions in the project root README instead.

NixOS cannot run the pre-built Firefox binaries that OpenWPM downloads without an FHS-compatible environment. The `shell.nix` in this directory provides that environment.

## Usage

```sh
nix-shell nix/shell.nix
```

This drops you into an FHS environment with the `openwpm` conda env already activated.
