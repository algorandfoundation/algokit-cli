# Local dev UI packaging

- **Status**: Draft
- **Owner:** Patrick Dinh (MakerX), Negar Abbasi (MakerX)
- **Deciders**: Alessandro (Algorand Foundation), Rob Moore (MakerX), MakerX team
- **Date created**: 2024-03-06

## Context

We are building a web-based local development interface to support:

- Exploring transactions, assets and accounts
- Visualising transactions
- Launching a VS Code debug session from an application call transaction
- Integrating and using a dev wallet via KMD
- Network switching between LocalNet, TestNet and MainNet
- Calling deployed ABI apps
- Integration with the AlgoKit CLI to perform any relevant actions
- Launching the interface from the AlgoKit CLI

## Requirements

The local development interface should have:

- Support for a wide variety of Linux distributions, macOS (both Apple Silicon and Intel architectures), and Windows 10+.
- Local system access to:
  - The user home directory on the file system.
  - Launch child processes.
  - Launch the UI from the AlgoKit CLI.
  - Launch shell commands.
- The ability for the explorer portion to be deployed to a static web host.
- The ability to be installed via the following channels:
  - Winget for Windows.
  - Homebrew for macOS.
  - Snapcraft for Linux.
- The ability for users to see a notification when a new version is available and can update.

## Out of scope

- Support for ARM processors on Linux or Windows.

## Options

### Option 1 - Electron

[Electron](https://www.electronjs.org/) is a framework for creating native applications with web technologies like JavaScript, HTML, and CSS. It allows developers to build cross-platform desktop apps using their existing web development skills.

Link to PoC is here: [Electron PoC](https://github.com/negar-abbasi/electron-poc).

**Pros**

- Electron is a mature framework with a large community and a lot of resources available.
- Uses standard JavaScript and Node APIs, which most developers are very familiar with.
- It supports all the local system access requirements via [icpMain](https://www.electronjs.org/docs/latest/api/ipc-main), allowing asynchronous communication from the main process to renderer processes.
  - File system access is enabled using the Node.js `fs` module. See [Node.js File System (fs) module docs](https://nodejs.org/api/fs.html).
  - Launching processes is enabled using the Node.js `child_process` module to spawn new processes. [Node.js Child Processes](https://nodejs.org/api/child_process.html). Specifically, well use the `spawn` or `exec` functions.
  - Running shell commands is enabled via the Node.js `child_process` module's `exec` function.
- Electron supports an [auto update](https://www.electronjs.org/docs/latest/api/auto-updater) for windows and macOS only. For Linux, if the explorer is distributed via Snapcraft, it should get auto updated.
- Electron does not have any built in tooling for packaging and distribution. There are however several third-party tools available for packaging and distribution, such as [electron-builder](https://www.electron.build/), [electron-packager](https://www.npmjs.com/package/electron-packager), and [electron-forge](https://www.electronforge.io/).
- Electron Forge is an all-in-one tool that handles the packaging and distribution of Electron apps. Under the hood, it combines a lot of existing Electron tools (e.g. @electron/packager, @electron/osx-sign, electron-winstaller, etc.) into a single interface so we do not have to worry about wiring them all together. [docs](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging#using-electron-forge)
  - It can package the app into format that we are interested in:
    - `.deb`, `.snap` for Linux
    - `.msi` for Windows
    - `.dmg` for macOS

**Cons**

- Electron is resource hungry, for a small test app (Hello World) it uses 146.0 MB of memory and 0.47% of CPU (running on macOS M2 CPU with 12 cores and 16GB RAM)
- When built on a local dev machine, the package size for macOS is ~250MB.

### Option 2 - Tauri

[Tauri](https://tauri.app/about/intro) is a toolkit that helps developers make applications for the major desktop platforms - using virtually any frontend framework in existence. The core is built with Rust, and the CLI leverages Node.js making Tauri a genuinely polyglot approach to creating and maintaining great apps.

**Pros**

- Tauri supports all requirements for the local development interface via their JavaScript API without the need to write any Rust.
- It can manage the [file systems](https://tauri.app/v1/api/js/fs), launch another [process](https://tauri.app/v1/api/js/process), run a [shell command](https://tauri.app/v1/api/js/shell).
- Tauri integrates well with major web frameworks. [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) and a good template project can be bootstrapped and working within minutes.

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
- Tauri is reasonably efficient, for a small test app (Hello World) it uses 30 MB of RAM and 0.1% CPU (running on macOS M1 CPU and 32GB RAM).
- When built on a local dev machine, the package size for macOS is ~5MB.

**Cons**

- If we need to extend the functionality beyond the support of Tauri's JavaScript API, we will need to write the code in Rust, which would be a new language in the AlgoKit ecosystem and a less common skill in the team.
- At the point of writing, building with `snap` (for Linux) isn't officially supported by Tauri. There is a open [PR](https://github.com/tauri-apps/tauri/pull/6532). We can however support snap by packaging the Linux build output ourselves.
- Tauri relies on [Webview](https://tauri.app/v1/references/webview-versions/) which are not the same across platforms. This means that we'll need to perform more testing on the styling and rendering, to ensure a consistent experience across the different platform Webviews and the supported versions.
  - For reference, [here](https://github.com/tauri-apps/tauri/issues?q=is%3Aissue+webview+css) are Tauri's issues related to CSS.
- For some versions of Windows 10, WebView2 needs to be installed. This process requires internet connection whilst installing.

### Option 3 - Wails

[Wails](https://wails.io/) is similar to Tauri but the core is written in Go.

**Pros**

- Wails has init templates for major web framework. React + TypeScript + Vite is supported.
- Wails has an auto codegen to generate the contract between the main process and the renderer process.
- Wails doesn't have built-in code signing for Windows and Mac. However, the document on how to do code signing with GitHub actions is very detailed.
- Wails is reasonably efficient, for a small test app (Hello World) it uses 30 MB of RAM and 0.1% CPU (running on macOS M1 CPU and 32GB RAM).
- When built on a local dev machine, the package size for macOS is ~5MB.

**Cons**

- Documentation isn't as comprehensive as Electron and Tauri. Because of this, I didn't investigate much further into Wails. Tauri seems to be a more supported project, Wails doesn't give us anything additional.
- The code to interact with file systems, shell and child processes will be written in Go, which would be a new language in the AlgoKit ecosystem and a less common skill in the team.
- No built-in updater. It is tracked in this [issue](https://github.com/wailsapp/wails/issues/1178).
- Wails is based on WebView, therefore, it has the same cross-platform issues with Tauri.
- Wails supports building for Windows, Mac and Linux. The documentation however isn't super clear:
  - I could build Windows binaries from Mac.
  - I couldn't build Linux binaries from Mac.
  - The document doesn't mention options to build installers.

## Preferred option

- **Option2** Tauri is the preferred option because it is well documented and has a big community behind it. Tauri supports all of our use cases and is less resource hungry than Electron.

## Selected option

Option 2

Given the good community support, great docs, low resource consumption and not needing to write much (if any) Rust, Tauri (Option 2) appears to fit our needs very well.
