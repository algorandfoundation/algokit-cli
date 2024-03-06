# Local dev UI packaging

- **Status**: Draft
- **Owner:** Patrick Dinh (MakerX)
- **Deciders**: Alessandro (Algorand Foundation), Rob Moore (MakerX), MakerX team
- **Date created**: 2024-03-06

## Context

We are building a web-based local explorer interface to support:

- Transaction / asset / account explorer
- Dev wallet integration (including KMD support)
- Network switching
- ARC-32 app studio
- Visual transaction representations and basic visual debugging interface to help new users understand what’s happening
- AlgoKit init and Algokit tasks CLI exploration user interfaces to help new users get the most out of the CLI

The explorer will be packaged as a executable as well as deployed as a website.

## Requirements

- The explorer should support a wide variety of Linux distributions, macOS (both Apple Silicon and Intel architectures), and Windows.
- The explorer can be deployed to a website. The explorer website has limited functionalities, compared to the desktop version.

## Options

### Option 1 - Election

### Option 2 - Tauri

[Tauri](https://tauri.app/about/intro) is a toolkit that helps developers make applications for the major desktop platforms - using virtually any frontend framework in existence. The core is built with Rust, and the CLI leverages Node.js making Tauri a genuinely polyglot approach to creating and maintaining great apps.

**Pros**
Tauri supports all intended operations for the local dev UI MVP via their JavaScript API without the need to write any Rust.

- It can manage the [file systems](https://tauri.app/v1/api/js/fs), launch another [process](https://tauri.app/v1/api/js/process), run a [shell command](https://tauri.app/v1/api/js/shell).
- Tauri integrates well with major web frameworks. [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) can bootstrap a working app within minutes.
  - Once bootstrapped, the web app can be bundled individually and deployed as a website. Below is the `npm script` Tauri generates for a Vite project, we can see that it supports `vite build`
  ```json
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  ```
- For [compiling binaries](https://tauri.app/v1/guides/building/), the Tauri Bundler supports
  - Windows: setup.exe, .msi
  - macOS: .app, .dmg
  - Linux: .deb, .appimage
- The Tauri Bundler supports code signing for:
  - [Windows](https://tauri.app/v1/guides/distribution/sign-windows)
  - [Linux](https://tauri.app/v1/guides/distribution/sign-linux)
  - [macOS](https://tauri.app/v1/guides/distribution/sign-macos)
- Tauri offers a [built-in updater](https://tauri.app/v1/guides/distribution/updater) for the NSIS (Windows), MSI (Windows), AppImage (Linux) and App bundle (macOS) distribution formats.
- Tauri claims to be less resource hungry than Electron, however, I haven't been able to test it intensively in this work.

**Cons**
If we need to extend the functionalities beyond the support of Tauri's JavaScript API, we will need to write the code in Rust.
