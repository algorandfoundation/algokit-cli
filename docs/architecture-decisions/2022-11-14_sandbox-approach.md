# AlgoKit sandbox approach

- **Status**: Approved
- **Owner:** Rob Moore
- **Deciders**: Anne Kenyon (Algorand Inc.), Alessandro Cappellato (Algorand Foundation), Will Winder (Algorand Inc.)
- **Date created**: 2022-11-14
- **Date decided:** 2022-11-14
- **Date updated**: 2022-11-16

## Context

In order for AlgoKit to facilitate a productive development experience it needs to provide a managed Algorand sandbox experience. This allows developers to run an offline (local-only) private instance of Algorand that they can privately experiment with, run automated tests against and reset at will.

## Requirements

- The sandbox works cross-platform (i.e. runs natively on Windows, Mac and Linux)
- You can spin up algod and indexer since both have useful use cases when developing
- The sandbox is kept up to date with the latest version of algod / indexer
- There is access to KMD so that you can programmatically fund accounts to improve the developer experience and reduce manual effort
- There is access to the tealdbg port outside of algod so you can attach a debugger to it
- The sandbox is isolated and (once running) works offline so the workload is private, allows development when there is no internet (e.g. when on a plane) and allows for multiple instances to be run in parallel (e.g. when developing multiple independent projects simultaneously)
- Works in continuous integration and local development environments so you can facilitate automated testing

## Principles

- **[AlgoKit Guiding Principles](../../docs/algokit.md#Guiding-Principles)** - specifically Seamless onramp, Leverage existing ecosystem, Meet devs where they are
- **Lightweight** - the solution should have as low an impact as possible on resources on the developers machine
- **Fast** - the solution should start quickly, which makes for a nicer experience locally and also allows it to be used for continuous integration automation testing

## Options

### Option 1 - Pre-built DockerHub images

Pre-built application developer-optimised DockerHub images that work cross-platform; aka an evolved AlgoKit version of <https://github.com/MakerXStudio/algorand-sandbox-dev>.

**Pros**

- It's quick to download the images and quick to start the container since you don't need to compile Algod / indexer and the images are optimised for small size
- The only dependency needed is Docker, which is a fairly common dependency for most developers to use these days
- The images are reasonably lightweight
- The images provide an optimised application developer experience with: (devmode) algo, KMD, tealdbg, indexer
- It natively works cross-platform

**Cons**

- Some people have reported problems running WSL 2 on a small proportion of Windows environments (to get the latest Docker experience)
- Docker within Docker can be a problem in some CI environments that run agents on Docker in the first place
- Work needs to be done to create an automated CI/CD that automatically releases new versions to keep it up to date with latest algod/indexer versions

### Option 2 - Lightweight algod client implementation

Work with the Algorand Inc. team to get a lightweight algod client that can run outside of a Docker container cross-platform.

**Pros**

- Likely to be the most lightweight and fastest option - opening up better/easier isolated/parallelised automated testing options
- Wouldn't need Docker as a dependency

**Cons**

- Indexer wouldn't be supported (Postgres would require Docker anyway)
- Algorand Inc. does not distribute Windows binaries.

### Option 3 - Sandbox

Use the existing [Algorand Sandbox](https://github.com/algorand/sandbox).

**Pros**

- Implicitly kept up to date with Algorand - no extra thing to maintain
- Battle-tested by the core Algorand team day-in-day-out
- Supports all environments including unreleased feature branches (because it can target a git repo / commit hash)

**Cons**

- Sandbox is designed for network testing, not application development - it's much more complex than the needs of application developers
- Slow to start because it has to download and built algod and indexer (this is particularly problematic for ephemeral CI/CD build agents)
- It's not cross-platform (it requires bash to run sandbox.sh, although a sandbox.ps1 version could be created)

## Preferred option

Option 1 and Option 2.

Option 1 provides a fully-featured experience that will work great in most scenarios, having option 2 as a second option would open up more advanced parallel automated testing scenarios in addition to that.

## Selected option

Option 1

We're aiming to release the first version of AlgoKit within a short timeframe, which won't give time for Option 2 to be developed. Sandbox itself has been ruled out since it's not cross-platform and is too slow for both development and continuous integration.

Option 1 also results in a similar result to running Sandbox, so existing Algorand documentation, libraries and approaches should work well with this option making it a good slot-in replacement for Sandbox for application developers.

AlgoKit is designed to be modular: we can add in other approaches over time such as Option 2 when/if it becomes available.
