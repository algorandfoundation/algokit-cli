# Beaker testing strategy

- **Status**: Draft
- **Owner:** Rob Moore
- **Deciders**: Anne Kenyon (Algorand Inc.), Alessandro Cappellato (Algorand Foundation), Michael Diamant (Algorand Inc.), Benjamin Guidarelli (Algorand Foundation)
- **Date created**: 2022-11-22
- **Date decided:** TBD
- **Date updated**: 2022-11-28

## Context

AlgoKit will be providing a smart contract development experience built on top of [PyTEAL](https://pyteal.readthedocs.io/en/stable/) and [Beaker](https://developer.algorand.org/articles/hello-beaker/). Beaker is currently in a pre-production state and needs to be productionised to provide confidence for use in generating production-ready smart contracts by AlgoKit users. One of the key things to resolve to productionisation of Beaker is to improve the automated test coverage.

Beaker itself is currently split into the PyTEAL generation related code and the deployment and invocation related code (including interacting with Sandbox). This decision is solely focussed on the PyTEAL generation components of Beaker. The current automated test coverage of this part of the codebase is ~50% and is largely based on compiling and/or executing smart contracts against Algorand Sandbox. While it's generally not best practice to try and case a specific code coverage percentage, a coverage of ~80%+ is likely indicative of good coverage in a dynamic language such as Python.

The Sandbox tests provide a great deal of confidence, but are also slow to execute, which can potentially impair Beaker development and maintenance experience, especially as the coverage % is grown and/or features are added over time.

Beaker, like PyTEAL, can be considered to be a transpiler on top of TEAL. When generating smart contracts, the individual TEAL opcodes are significant, since security audits will often consider the impact at that level, and it can have impacts on (limited!) resource usage of the smart contract. As such, "output stability" is potentially an important characteristic to test for.

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

Writing [approval tests](https://approvaltests.com/) of the TEAL output generated from a given Beaker smart contract.

**Pros**

- Ensures TEAL output stability and focussing on asserting the output of Beaker rather than testing whether Algorand Protocol is working
- Runs in-memory/in-process so will execute in low 10s of milliseconds making it easy to provide high coverage with low developer feedback loop overhead
- Tests are easy to write - the assertion is a single line of code (no tedious assertions)
- The tests go from Beaker contract -> TEAL approval so don't bake implementation detail and thus allow full Beaker refactoring with regression confidence without needing to modify the tests
- Excellent regression coverage characteristics - fast test run and quick to write allows for high coverage and anchoring assertions to TEAL output is a very clear regression marker

**Cons**

- The tests rely on the approver to understand the TEAL opcodes that are emitted and verify they match the intent of the Beaker contract - anecdotally this can be difficult at times even for experienced (Py)TEAL developers
- Doesn't assert the correctness of the TEAL output, just that it matches the previously manually approved output

### Option 2: Sandbox compile tests

Writing Beaker smart contracts and checking that the TEAL output successfully compiles against algod.

**Pros**

- Ensures that the TEAL output compiles, giving some surety about the intactness of it and focussing on asserting the output of Beaker rather than testing whether Algorand Protocol is working
- Faster than executing the contract
- Tests are easy to write - the assertion is a single line of code (no tedious assertions)

**Cons**

- Order of magnitude slower than asserting TEAL output (out of process communication)
- Doesn't assert the correctness of the TEAL output, just that it compiles

### Option 3: Sandbox execution tests

Execute the smart contracts and assert the output is as expected. This can be done using dry run and/or actual transactions.

**Pros**

- Asserts that the TEAL output _executes_ correctly giving the highest confidence
- Doesn't require the test writer to understand the TEAL output
- Tests don't bake implementation detail and do assert on output so give a reasonable degree of refactoring confidence without modifying tests

**Cons**

- Tests are more complex to write
- Tests take an order of magnitude longer to run than just compilation (two orders of magnitude to run than checking TEAL output)
- Harder to get high regression coverage since it's slower to write and run the tests making it impractical to get full coverage
- Doesn't ensure output stability
- Is testing that the Algorand Protocol itself works (TEAL `x` when executed does `y`) so the testing scope is broader than just Beaker itself

## Preferred option

Option 1 (combined with Option 2 to ensure the approved TEAL actually compiles, potentially only run on CI by default to ensure fast local dev loop) for the bulk of testing to provide a rapid feedback loop for developers as well as ensuring output stability and great regression coverage.

## Selected option

Combination of option 1, 2 and 3:

- While Option 1 + 2 provides high confidence with fast feedback loop, it relies on the approver being able to determine the TEAL output does what they think it does, which isn't always the case
- Option 3 will be used judiciously to provide that extra level of confidence that the fundamentals of the Beaker output are correct for each main feature; this will involve key scenarios being tested with execution based tests, the goal isn't to get combinatorial coverage, which would be slow and time-consuming, but to give a higher degree of confidence
- The decision of when to use Option 3 as well as Option 1+2 will be made on a per-feature basis and reviewed via pull request, over time a set of principles may be able to be revised that outline a clear delineation
- Use of PyTest markers to separate execution so by default the dev feedback loop is still fast, but the full suite is always run against pull requests and merges to main
