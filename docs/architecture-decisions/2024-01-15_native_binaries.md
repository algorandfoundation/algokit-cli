## AlgoKit CLI Enhancements

### Objective

To install the AlgoKit CLI using operating system native binaries without needing to install Python.

### Status

In-review

### Owner

- Altynbek Orumbayev (MakerX)
- Negar Abbasi (MakerX)

### Deciders

{Deciders}

### Dates

Created: {YYYY-MM-DD}
Decided: {YYYY-MM-DD}
Updated: {YYYY-MM-DD}

### Context

The primary motivation for this decision is to streamline the installation process of AlgoKit CLI and reduce the friction associated with installing it on various operating systems. Currently, users often encounter minor environment-specific bugs during installation, which can be a significant deterrent. By providing native binaries, we aim to speed up the installation time and eliminate these bugs, thereby improving the overall user experience.

### Requirements

- The native binaries should be easy to maintain and understand from a CI/CD deployment perspective.
- The solution should support a wide variety of Linux distributions, macOS (both Apple Silicon and Intel architectures), and Windows.
- The solution should integrate seamlessly with existing installation options, including Homebrew, or provide an easier alternative.
- The solution should be designed with future scalability in mind, allowing for the addition of support for other operating systems as needed.
- The solution should not significantly increase the complexity of the build process.
- The solution should provide clear error messages and debugging information to assist in troubleshooting any issues that may arise.

### Options

The following below where reviewed as possible options for this decision:

1. PyInstaller
2. cx_Freeze
3. PyOxidizer
4. Py2exe

### Considerations

PyInstaller and cx_Freeze have similar usage. PyInstaller requires installation via pip and a .spec file for configuration. The .spec file can be created manually or automatically using the PyInstaller command-line tool. Once the .spec file is created, PyInstaller can create the standalone executable file.

#### PyInstaller

The output of PyInstaller is specific to the active operating system and the active version of Python. This means that to prepare a distribution for a different OS, a different version of Python, or a 32-bit or 64-bit OS, you run PyInstaller on that OS, under that version of Python. The Python interpreter that executes PyInstaller is part of the bundle, and it is specific to the OS and the word size.

Example: [Github action](https://github.com/pyinstaller/pyinstaller/issues/6296#issuecomment-943620645)
Supported packages: [List](https://github.com/pyinstaller/pyinstaller/wiki/Supported-Packages)
Uncommon used packages that need to be checked: copier, questionary, pyclip, shellingham, mslex, auth0-python, multiformats.

##### Pros

- Easy to use and configure
- Supports multiple platforms and architectures
- Can handle complex packages and dependencies
- Generates a single file executable
- Active development and community support
- Generate executable file: 10-15 mins

##### Cons

- Larger executable files compared to cx_Freeze
- Occasionally requires manual configuration for more complex packages
- Not as customizable as cx_Freeze
- Load time is long = 5-10 sec

#### cx_Freeze

##### Pros

- Easy to use and configure
- Supports multiple platforms
- Produces small executable files
- Can generate an installer for distribution
- Supports Python 3.x versions

##### Cons

- Limited documentation and community support
- Not very flexible with configuring the executable file
- Doesn’t support some complex packages and modules

#### Nuitka

##### Pros
- Nuitka translates Python code into C++ and then compiles it, which can result in performance improvements.
- Cross-Platform: Supports multiple platforms including Windows, macOS, and Linux.

##### Cons
- Compilation Time: The process of converting Python to C++ and then compiling can be time-consuming.
- Size of Executable: The resulting executables can be larger due to the inclusion of the Python interpreter and the compiled C++ code.
- Limited Support: Nuitka does not support Python 3.12.

### Packaging

#### Windows (winget)

Use [py2exe](https://www.py2exe.org/) to support python 12. Create an installer for your Windows binary using tools like Inno Setup or NSIS. Publish installer on winget by following the guidelines provided by [Microsoft](https://learn.microsoft.com/en-us/windows/package-manager/package/). This involves creating a manifest file for the application and submitting it to the winget-pkgs GitHub repository.

#### Linux (Snap)

Package the application as a Snap for Linux. Snaps work across different Linux distributions and isolate the application from the rest of the system, improving security and dependency management. Follow the [Snapcraft guidelines](https://snapcraft.io/docs/snapcraft-tutorials) to package your application. Once packaged, you can publish it on the Snap Store, making it available for a wide range of Linux users.

#### Github Action

A [Github action](https://github.com/snapcore/action-publish) for publishing snaps

### Note

By using native binaries and package managers, you can handle updates more consistently. Both winget and Snap support automatic updates. However, not all Python code can be compiled into a binary executable, especially if it relies on dynamic imports or other runtime features. Additionally, there may be platform-specific limitations or considerations to take into account when compiling Python code into an executable.

### Preferred Option

{Which option do we want to select and why}

### Selected Option

{Which option did we select and why (can sometimes be different from the preferred option)}

### Next Steps

{Any next steps we agree to do as part of this decision that are relevant to document}

---

Implementation Tips for the Hybrid Approach:

Package Managers (Homebrew, Chocolatey, pipx):

- [ ] Update your package definitions to point to the new binary releases.
- [ ] Ensure that the package manager correctly sets up the binary in the user's environment (e.g., adding it to the PATH).
- [ ] Automate the update of package definitions in sync with your release cycle.
      Curl/Bash Installation Script:

- [ ] Write a script that detects the OS and CPU architecture, downloads the corresponding binary, and installs it properly.
- [ ] Host this script on a reliable server or directly in your GitHub repository.
- [ ] Include clear instructions in your documentation on how to use this script.
      GitHub Releases:

- [ ] Automate the process of attaching binaries to GitHub Releases using GitHub Actions.
- [ ] Clearly label each binary for its respective OS and architecture.
- [ ] Provide instructions for manual download and setup.
      Documentation:

- [ ] Update your documentation to include all available installation methods.
- [ ] Provide detailed instructions for each method to guide users through the installation process.
      Testing and Feedback:

- [ ] Regularly test each installation method to ensure they work seamlessly.
- [ ] Gather user feedback to understand their preferences and pain points.
