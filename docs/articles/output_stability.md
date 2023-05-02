# Smart Contract Output Stability

Smart contracts development is analogous to low level firmware software development; it's a highly constrained environment in terms of both compute power and memory storage, with a high risk of vulnerabilities due to lower level access to memory and less developer-oriented security tooling. 
Because of this, the assembly language code that is output for a smart contract is important - a seemingly innocuous minor change could inadvertently add a security vulnerability, or could significantly change the execution and memory profile. 
As such it is important to ensure that, even if higher level code is refactored, there are no unintended changes to the generated smart contract assembly language output. 
We refer to this property as **output stability**.

We recommend having "output stability tests" that require a developer to explicitly opt-in to accepting a change in the output of a smart contract's assembly code. This can be implemented as part of an automated build process which fails if the output changes aren't committed to source control, thus preventing deployment of the smart contract without a human review taking place (assuming automated deployment).
