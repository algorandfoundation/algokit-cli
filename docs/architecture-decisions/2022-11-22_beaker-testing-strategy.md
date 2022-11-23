# Beaker testing strategy

- **Status**: Draft
- **Owner:** Rob Moore
- **Deciders**: Anne Kenyon (Algorand Inc.), Alessandro Ferrari (Algorand Foundation), Michael Diamant (Algorand Inc.), Benjamin Guidarelli (Algorand Foundation)
- **Date created**: 2022-11-22
- **Date decided:** TBD
- **Date updated**: 2022-11-23

## Context

AlgoKit will be providing a smart contract development experience built on top of [PyTEAL](https://pyteal.readthedocs.io/en/stable/) and [Beaker](https://developer.algorand.org/articles/hello-beaker/). Beaker is currently in a pre-production state and needs to be productionised to provide confidence for use in generating production-ready smart contracts by AlgoKit users. One of the key things to resolve to productionisation of Beaker is to improve the automated test coverage.

Beaker itself is currently split into the PyTEAL generation related code and the deployment and invocation related code (including interacting with Sandbox). This decision is solely focussed on the PyTEAL generation components of Beaker. The current automated test coverage of this part of the codebase is ~50% and is largely based on compiling and/or executing smart contracts against Algorand Sandbox. While it's generally not best practice to try and case a specific code coverage percentage, a coverage of 80% +/- 15% is likely indicative of good coverage.

The Sandbox tests provide a great deal of confidence, but are also slow to execute, which can potentially impair Beaker development and maintenance experience, especially as the coverage % is grown and/or features are added over time.

Beaker, like PyTEAL, can be considered to be a transpiler on top of TEAL. When generating smart contracts, the individual TEAL opcodes are significant, since security audits will often consider the impact at that level and it can have impacts on (limited!) resource usage of the smart contract. As such, "output stability" is potentially an important characteristic to test for.

## Requirements

- We have a high degree of confidence that writing smart contracts in Beaker leads to expected results for production smart contracts
- We have reasonable regression coverage so features are unlikely to break as new features and refactorings are added over time
- We have a level of confidence in the "output stability" of the TEAL code generated from a Beaker smart contract

## Principles

- **Fast development feedback loops** - The feedback loop during normal development should be as fast as possible to improve the development experience of developing Beaker itself
- **Low overhead** - The overhead of writing and maintaining tests is as low as possible; tests should be quick to read and write
- **Implementation decoupled** - Tests aren't testing the implementation details of Beaker, but rather the user-facing experience and output of it; this reduces the likelihood of needing to rewrite tests when performing refactoring of the codebase

## Options

### Option 1: TEAL Approval tests

TODO

**Pros**

- TODO

**Cons**

- TODO

### Option 2: Sandbox compile tests

TODO

**Pros**

- TODO

**Cons**

- TODO

### Option 3: Sandbox dry run tests

TODO

**Pros**

- TODO

**Cons**

- TODO

### Option 4: Sandbox execution tests

TODO

**Pros**

- TODO

**Cons**

- TODO

### Option 5: Combined approach

TODO

**Pros**

- TODO

**Cons**

- TODO

## Preferred option

todo

## Selected option

todo
