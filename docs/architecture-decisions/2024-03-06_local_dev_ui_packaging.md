# Local dev UI packaging

- **Status**: Draft
- **Owner:** Patrick Dinh (MakerX), Negar Abbasi (MakerX)
- **Deciders**: Alessandro (Algorand Foundation), Rob Moore (MakerX), MakerX team
- **Date created**: 2024-03-06

## Context

We are building a web-based local development interface to support:

- Transaction / asset / account exploration
- Dev wallet integration (including KMD support)
- Network switching
- ARC-32 app studio
- Visual transaction representations and basic visual debugging interface to help new users understand what’s happening
- AlgoKit init and Algokit tasks CLI exploration user interfaces to help new users get the most out of the CLI

The explorer will be packaged as a executable as well as deployed as a website.

## Requirements

- The explorer should support a wide variety of Linux distributions, macOS (both Apple Silicon and Intel architectures), and Windows.
- To facilitate AlgoKit projects, the explorer should have access to local machine resouces:
  - File system.
  - Launch child processes.
  - Launch commands from shell.
- The explorer can be deployed to a website. The explorer website has limited functionalities, compared to the desktop version.

## Options

### Option 1 - Electron

[Electron](https://www.electronjs.org/) is a framework for creating native applications with web technologies like JavaScript, HTML, and CSS. It allows developers to build cross-platform desktop apps using their existing web development skills.

- Electron is a mature framework with a large community and a lot of resources available.
- It supports all intended operations for the local dev UI MVP via [icpMain](https://www.electronjs.org/docs/latest/api/ipc-main) to communicate asynchronously from the main process to renderer processes.

  1. **File Systems**: we can use the Node.js `fs` module to manage file systems in Electron. See [Node.js File System (fs) module docs](https://nodejs.org/api/fs.html).

  2. **Launching Another Process**: In Electron, you can use the `child_process` module to spawn new processes. [Node.js Child Processes](https://nodejs.org/api/child_process.html). Specifically, Use the `spawn` or `exec` functions to launch another process.

  3. **Running a Shell Command**: we can again use the `child_process` module's `exec` function to run shell commands in Electron.

- Electron support an [auto update](https://www.electronjs.org/docs/latest/api/auto-updater) for windows and macOS only.
- Electron does not have any tooling for packaging and distribution bundled into its core modules. However, there are several third-party tools available for packaging and distribution, such as [electron-builder](https://www.electron.build/), [electron-packager](https://www.npmjs.com/package/electron-packager), and [electron-forge](https://www.electronforge.io/).
- Electron Forge is an all-in-one tool that handles the packaging and distribution of Electron apps. Under the hood, it combines a lot of existing Electron tools (e.g. @electron/packager, @electron/osx-sign, electron-winstaller, etc.) into a single interface so we do not have to worry about wiring them all together. [docs](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging#using-electron-forge)
- Resource used (running on macos m2 chip with 12 cores and 16GB of memory):
  - 146.0 MB of memory
  - 0.47% of CPU
- Link to PoC: [Electron PoC](https://github.com/negar-abbasi/electron-poc)

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

- If we need to extend the functionalities beyond the support of Tauri's JavaScript API, we will need to write the code in Rust, which would be a new language in the AlgoKit ecosystem and a less common skill in market.
- An ARM based Linux runner is required to build binaries for ARM Linux. Currently, GitHub doesn't support ARM based runners yet, but will be [soon](https://github.blog/changelog/2023-10-30-accelerate-your-ci-cd-with-arm-based-hosted-runners-in-github-actions/) in the future.
- At the point of writing, building with `snap` (for Linux) isn't officially supported by Tauri. There is a open [PR](https://github.com/tauri-apps/tauri/pull/6532).
- Tauri relies on [Webview](https://tauri.app/v1/references/webview-versions/) which are not the same across platforms. This means that we'll need to perform more testing on the styling and rendering, to ensure the CSS works across the different platform Webviews and the supported versions.
  - This can be a none issue because we will need to make our CSS works across modern browsers for the website.
  - For reference, [here](https://github.com/tauri-apps/tauri/issues?q=is%3Aissue+webview+css) are Tauri's issues related to CSS.

### Option 3 - Wails

[Wails](https://wails.io/) is similar to Tauri but the core is written in Go.

**Pros**

- Wails has init templates for major web framework. React + TypeScript + Vite is supported.
- Wails has a auto codegen to generate the contract between the main process and the renderer process.
- Wails doesn't have built-in code signing for Windows and Mac. However, the document on how to do code signing with GitHub actions is very detailed.

**Cons**

- Documentation isn't as comprehensive as Electron and Tauri.
- The code to interact with file systems, shell and child processes will be written in Go, which would be a new language in the AlgoKit ecosystem and a less common skill in market.
- No built-in updater. It is tracked in this [issue](https://github.com/wailsapp/wails/issues/1178).
- Wails is based on WebView, therefore, it has the same cross-platform issues with Tauri.
- Wails supports building for Windows, Mac and Linux. The documentation isn't clear:
  - I could build Windows binaries from Mac.
  - I can't build Linux binaries from Mac.
  - The document doesn't mention options to build installers.
