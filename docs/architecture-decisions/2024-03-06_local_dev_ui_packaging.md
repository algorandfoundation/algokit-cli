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
- Integration with AlgoKit CLI, for example, calling AlgoKit init and explore AlgoKit tasks

## Requirements

- The explorer should support a wide variety of Linux distributions, macOS (both Apple Silicon and Intel architectures), and Windows.
- To facilitate AlgoKit projects, the explorer should have access to local machine resouces:
  - File system.
  - Launch child processes.
  - Launch commands from shell.
- The explorer can be deployed to a website. The explorer website has limited functionalities, compared to the desktop version.
- The explorer will be distributed via package managers: Winget for Windows, Homebrew for macOS and Snapcraft for Linux.
- The user should be notified when a new version is available. (Nice to have) self auto update is supported.

## Out of scope

- ARM Linux isn't supported.

## Options

### Option 1 - Electron

[Electron](https://www.electronjs.org/) is a framework for creating native applications with web technologies like JavaScript, HTML, and CSS. It allows developers to build cross-platform desktop apps using their existing web development skills.

**Pros**

- Electron is a mature framework with a large community and a lot of resources available.
- It supports all intended operations for the local dev UI MVP via [icpMain](https://www.electronjs.org/docs/latest/api/ipc-main) to communicate asynchronously from the main process to renderer processes.

  1. **File Systems**: we can use the Node.js `fs` module to manage file systems in Electron. See [Node.js File System (fs) module docs](https://nodejs.org/api/fs.html).

  2. **Launching Another Process**: In Electron, you can use the `child_process` module to spawn new processes. [Node.js Child Processes](https://nodejs.org/api/child_process.html). Specifically, Use the `spawn` or `exec` functions to launch another process.

  3. **Running a Shell Command**: we can again use the `child_process` module's `exec` function to run shell commands in Electron.

- Electron support an [auto update](https://www.electronjs.org/docs/latest/api/auto-updater) for windows and macOS only. For Linux, if the explorer is distributed via Snapcraft, it should get auto updated.
- Electron does not have any tooling for packaging and distribution bundled into its core modules. However, there are several third-party tools available for packaging and distribution, such as [electron-builder](https://www.electron.build/), [electron-packager](https://www.npmjs.com/package/electron-packager), and [electron-forge](https://www.electronforge.io/).
- Electron Forge is an all-in-one tool that handles the packaging and distribution of Electron apps. Under the hood, it combines a lot of existing Electron tools (e.g. @electron/packager, @electron/osx-sign, electron-winstaller, etc.) into a single interface so we do not have to worry about wiring them all together. [docs](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging#using-electron-forge)
  - It can package the app into format that we are interested in:
    - `.deb`, `.snap` for Linux
    - `.msi` for Windows
    - `.dmg` for macOS
- Link to PoC: [Electron PoC](https://github.com/negar-abbasi/electron-poc).

**Cons**

- Electron is resource hungry, for a small test app (Hello World) it uses 146.0 MB of memory and 0.47% of CPU (running on macos m2 chip with 12 cores and 16GB of memory)
- When built on local machine, the package size for macOS is ~250MB.

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
- Tauri is less resource hungry than Electron. Testing with a simple app (Hello World):
  - Tauri uses 30MB of RAM and 0.1% CPU on a M1 Mac, 32GB of RAM.
  - The package size for macOS is about 5MB.

**Cons**

- If we need to extend the functionalities beyond the support of Tauri's JavaScript API, we will need to write the code in Rust, which would be a new language in the AlgoKit ecosystem and a less common skill in market.
- At the point of writing, building with `snap` (for Linux) isn't officially supported by Tauri. There is a open [PR](https://github.com/tauri-apps/tauri/pull/6532).
  - Note: the `.snap` file can be produced by packaging the output of a Linux build.
- Tauri relies on [Webview](https://tauri.app/v1/references/webview-versions/) which are not the same across platforms. This means that we'll need to perform more testing on the styling and rendering, to ensure the CSS works across the different platform Webviews and the supported versions.
  - For reference, [here](https://github.com/tauri-apps/tauri/issues?q=is%3Aissue+webview+css) are Tauri's issues related to CSS.
- For some versions of Windows 10, WebView2 needs to be installed. This process required internet connection.

### Option 3 - Wails

[Wails](https://wails.io/) is similar to Tauri but the core is written in Go.

**Pros**

- Wails has init templates for major web framework. React + TypeScript + Vite is supported.
- Wails has a auto codegen to generate the contract between the main process and the renderer process.
- Wails doesn't have built-in code signing for Windows and Mac. However, the document on how to do code signing with GitHub actions is very detailed.
- Wails is less resource hungry compared to Electron, testing with a simple (Hello World) app:
  - Wails uses 30MB of RAM and 0.1% CPU on a M1 Mac, 32GB of RAM.
  - The package size for macOS is about 5MB.

**Cons**

- Documentation isn't as comprehensive as Electron and Tauri. Because of this, I didn't investigate much further into Wails. Tauri seems to be a more supported project, Wails doesn't give us anything additional.
- The code to interact with file systems, shell and child processes will be written in Go, which would be a new language in the AlgoKit ecosystem and a less common skill in market.
- No built-in updater. It is tracked in this [issue](https://github.com/wailsapp/wails/issues/1178).
- Wails is based on WebView, therefore, it has the same cross-platform issues with Tauri.
- Wails supports building for Windows, Mac and Linux. The documentation isn't clear:
  - I could build Windows binaries from Mac.
  - I can't build Linux binaries from Mac.
  - The document doesn't mention options to build installers.

## Preferred option

- **Option2** Tauri is the preferred option because it is well documented and has a big community behind it. Tauri supports all of our use cases. It is less resource hungry than Electron.
