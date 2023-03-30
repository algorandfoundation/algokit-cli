# HomeBrew install strategy

- **Status**: Approved
- **Owner:** Daniel McGregor
- **Deciders**: Daniel McGregor, Rob Moore, John Woods, Alessandro Cappellato
- **Date created**: 2023-01-11
- **Date decided:** 2023-01-11

## Context

HomeBrew (brew) is a MacOS package manager, and is commonly used on MacOS systems to install applications and tools like AlgoKit. Brew offers two main installation methods.

 * Formula - A source based install, this is typically recommended for open source and command line based applications. Formula can also be "bottled" to provide pre built packages for quick installs on supported MacOS platforms.
 * Cask - A binary based install, this is typically recommended for closed source or GUI based applications.

Additionally there are also two options for how the brew install scripts could be distributed.

* Homebrew repository - This is the official repository for homebrew installs, and provides bottle support for all moderns MacOS platforms (MacOS 11+, Intel and ARM)
* Algorand hosted repository - A homebrew repository managed by Algorand Foundation.

Creating a HomeBrew Formula initially seemed like the best option for AlgoKit as it meets the [criteria](https://docs.brew.sh/Acceptable-Formulae) for a Formula. However there is a much higher maintenance cost with this approach as everything is built from source. We encountered an issue where one of our newly added python dependencies (pyclip) did not build from source [correctly](https://github.com/algorandfoundation/homebrew-tap/actions/runs/3884956190/jobs/6628201057#step:8:2871). 

The alternative install method of a cask was then considered, and while AlgoKit does not meet the [criteria](https://docs.brew.sh/Acceptable-Casks) for a cask, it does remove the need for a source build on each MacOS platform and the additional maintenance overhead of the Formula approach.

## Requirements

- **Low maintenance**: The ongoing maintenance for supporting brew installs of AlgoKit should be low and not require manual effort for each release.
- **Fast and easy install experience**: The install experience for end users of AlgoKit should be easy and not require multiple complicated steps, additionally it should install in seconds, not minutes.

## Options

### Option 1: Formula on Official Homebrew Repo

This would be the preferred option except for the two notable issues. Firstly there is a high risk of ongoing maintenance overhead due to the need to support source building all the dependencies. Ideally this would not be an issue, but we have already hit a problem with a dependency (pyclip) early on in AlgoKit's development. Secondly inclusion into the official repo is subject to Homebrew's criteria, which AlgoKit won't reach until it is more mature.

**Pros**
* Most discoverable option for end users `brew install algokit`.
* Homebrew supports automatically bottling on all modern MacOS platforms (MacOS 11+ both Intel and ARM variants) meaning fast installs for users.

**Cons**
* Inclusion is subject to Homebrew's approval process, which algokit won't meet for now at least.
* Higher maintenance cost given the source build is more fragile and is likely to break and require investigation, plus build and install approach differs significantly from Chocolatey and pipx
* Longer build time on release
* Not possible to fully automate release, it relies on a Brew maintainer approving the pull request, so there's extra operational overhead to keep track of the release pull requests

### Option 2: Formula on Algorand Repo

This option is similar to Option 1, but allows Algorand to self publish the installer without meeting Homebrews formula criteria. However one issue is that Platform support is more limited, GitHub provides action runners for intel variants for MacOS 11 + 12, but [MacOS 13](https://github.com/github/roadmap/issues/620) and [ARM](https://github.com/github/roadmap/issues/528) support are not yet available. Additional platforms could be supported by using a combination of self-hosted runners and/or third party solutions. This means pre-built bottles aren't easy to build for ARM or MacOS 13 and installation on those environments will take 5+ minutes.

**Pros**
* Algorand Foundation has control over this process and it can be fully automated
* It's what we have already implemented and working today
* Easier to move to the official Brew core repository once AlgoKit is stable and demonstrably popular (thus meeting the constraints Brew place)

**Cons**
* Supporting all modern MacOS platforms may require use of a 3rd party service and more effort, in the meantime the installation experience on ARM and MacOS 13 is slow (5+ min install)
* Less discoverable install for end users `brew install algorandfoundation/algokit` (relies on them following documentation)
* Higher maintenance cost given the source build is more fragile and is likely to break and require investigation, plus build and install approach differs significantly from Chocolatey and pipx
* Longer build time on release

### Option 3: Cask on Algorand Repo

This option uses a cask which does not have the maintenance overhead of a formula, and can be hosted in an Algorand Foundation repo to get around the fact AlgoKit does not meet the normal cask criteria.

**Pros**
* Algorand Foundation has control over this process and it can be fully automated
* Lower maintenance cost as we do not need to support source builds of dependencies and it's consistent with how algokit cli is installed via Chocolatey and pipx
* Fast install for all MacOS platforms
* Fast build time on release

**Cons**
* Less discoverable install for end users `brew install algorandfoundation/algokit`
* AlgoKit does not meet the stated criteria for a cask and as such it would unlikely to be approved as a cask in the official Homebrew Repo if that was a desired future state
* More effort to implement a new way of installing via brew

### Option 4: Cask on Official Homebrew Repo

This is not a viable option as AlgoKit does not meet the criteria for an official cask.

## Preferred option

Option 1 because it would be the best end user experience.

## Selected option

Option 3 because Option 1 isn't possible right now and it's also a higher overhead to maintain. The install experience for end users is similar with option 3 (just with a bit more typing).
