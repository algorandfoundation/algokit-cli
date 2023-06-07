# Frontend Templates

- **Status**: Draft (rev 2)
- **Owner:** Altynbek Orumbayev
- **Deciders**: TBD
- **Date created**: 2023-06-06
- **Date decided:** TBD
- **Date updated**: 2023-06-07

## Context

AlgoKit v2 aims provide an end-to-end development and deployment experience that includes support for the end-to-end smart contract and dApp development lifecycle. With the release of the typed clients feature - developers are now able to reduce the time it takes to fully integrate the interactions between the contract and the frontend components powering the e2e dapp user experience. Hence, as a logical continuation, the following ADR aims to expand on the current capabilities of AlgoKit to support the `frontend` templates, an [AlgoKit Principles](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles) compliant approach towards simplifying integrations of smart contracts with the dApp frontend components.

## Requirements

- **Modularity**: The dApp templating feature should follow guiding AlgoKit principles and expand on approaches already utilized in existing smart contract templates feature. This implies that giving developers flexibility to mix and match different `smart contract` templates with `frontend` templates should serve as key consideration.
- **Maintainability**: The dApp templating feature should be easy to maintain and extend. This implies that the feature should be implemented in a way that allows for easy addition of new templates and/or modification of existing ones as the complexity and variety of templates scale.
- **Seamless onramp**: The dApp templating feature should provide a seamless onramp for developers to get started with dApp development. This implies that the feature should provide a simple and intuitive way to get started with dApp development and deployment. Providing developers a choice on whether they want more flexibility or rely on default recommended practices.

## Principles

- [AlgoKit Guiding Principles](../../docs/algokit.md#Guiding-Principles) - all of the aforementioned requirements should be met in a way that is consistent with the guiding principles of AlgoKit or attempt to find a balanced trade of between the principles that satisfies the requirements.

## Options

Expanding AlgoKit templating capabilities is a non-trivial task that requires careful consideration of the trade-offs between the different approaches. The following section outlines the different options that were considered and the trade-offs associated with each of them.

### Prerequisites

I believe the following is a list of challenges that is common to all of the options and needs to be addressed:

a) A set of new parameters for `.algokit.toml` file that will allow frontend codebases to quickly figure out the default path to generated typed clients. This will allow frontend templates to quickly import the generated typed clients and start interacting with the smart contract. Default templates provided by AlgoKit can rely on `copier` to pre-define the paths while an external frontend template can rely on the new parameters to figure out the path to the generated typed client.

b) A new `dev` mode represented as a set of deployment configurations OR a new command for the algokit-cli that will allow a developer to Deploy Contract -> Spin up local frontend -> Interact with the contract via the frontend in sandbox mode. This will allow developers to quickly access, test and iterate on entire codebase e2e.

### Option 1. Monorepo Approach

In this approach, we can extend the existing templates to include frontend code. This would turn the template repositories into monorepos housing both frontend and backend code. This approach also implies tight coupling between the frontend and backend code, as they will live in the same repository. While sacrificing flexibility, I believe there is an equal amount of challenges in maintaining separate frontends and backends in separate repos. This approach is also consistent with the current approach of bundling smart contracts and typed clients in a single repository.

#### Pros

- The codebase is located in a single repository, improving code visibility and coordination.
- Versioning is simpler as all code lives in one repo.
- Ability to have a very polished frontend client tailored specifically for the smart contract template.
- Collaboration among maintainers of official templates becomes easier as all code lives in one repo and it is easier to coordinate and observe changes.

#### Cons

- Without proper supervision over automation, the repository may become large and complex, leading to slower CI/CD pipeline execution times.
- It might violate the principle of modularity and loosely coupled components, which can be beneficial for parallel development and reduced complexity.

#### Examples

Folder structure (ref official beaker template):

```md
.
├── README.md
├── copier.yaml
├── poetry.lock
├── poetry.toml
├── pyproject.toml
├── template_content
├── contracts
├── frontend
├── .algokit.toml // with new params that aid with frontend templating
└── ...
├── tests
└── tests_generated
```

A good reference example of bundling frontends and backens in a single repo that relies on jinja: https://github.com/tiangolo/full-stack-fastapi-postgresql/tree/master

---

### Option 2. Separate templates repositories

In this scenario, the frontend and backend templates are maintained independently. The CLI tool will accept --backend and --frontend URLs separately, allowing developers to mix and match different smart contract templates with different frontend components.

#### Pros

- Greater flexibility for developers, as they can choose to mix and match different frontend and backend templates.
- Easier to maintain due to separate concerns (aligns with principle 8 on modularity).
  Simplifies version control for each individual component.

#### Cons

- Command invocation becomes longer, which may not be ideal for seamless onramp as it increases the complexity for new developers. However, this can be mitigated by providing a default template that includes both frontend and backend code.
- Integration between frontend and backend will require additional work, especially around utilities that need to figure out how to import the typed client to frontend as well.
- Versioning may become more complex as there are multiple repositories involved, especially considering the size of the team where ability to collaborate on a single codebase may be more beneficial.
- Ideally will require an additional set of utilities to generate template repositories for people building their own templates (as currently algokit does not provide any automated mechanism to do so other than copying official templates and modifying them)

#### Examples

- Example init with default frontend templates (assuming that algokit cli has a set of pre-defined frontend templates):

  ```bash
  $ algokit init --template-url ...
  $ ? Select frontend component: [React, Vue, Next, Angular, Svelte, None]
  $ ...
  ```

- Example init with external frontend templates:

  ```bash
  $ algokit init --template-url ... --frontend-url ...
  $ ...
  ```

---

### Option 3. Hybrid approach

In this approach, we can have a default frontend code template included with the backend in a monorepo but also provide the option for developers to specify a separate frontend template URL if desired.

#### Pros

- Combines the benefits of both monorepo and separate templates approach.
- Gives developers more flexibility while maintaining an official templates monorepo.
- Gives template creators a choice to either make a community template or contribute to an existing set of official templates (with a tradeoff on potentially longer PR reviews and etc).

#### Cons

- May add complexity to the CLI tool's implementation.
- Integration between frontend and backend will require additional work to implement a
  mechanism that allows swapping out the default frontend template with a custom one from provided url and aliasing/moving the generated typed client into the frontend.

---

## Preferred option

Keeping AlgoKit principles in mind, the Hybrid Approach might be the most balanced starting point. It can allow us as a team to collaborate on a single repository while also providing other developers the flexibility to use separate combinations of frontend templates if desired. Additionally, this approach can be implemented in 2 steps where we start with a monorepo and then extend it to support external frontend templates after further feedback and evaluation on developer experience.

## Selected option

To be discussed.

## Open questions

- Do we want to support scenarios when users already have a ready made frontend repository and want to potentially embedd algokit into it - or we are primarily focusing on solid user experience in regards to initialization and bootstrapping of the templates?
- How do we want to handle cases when user select python typed client during initialization? Do we want to provide a default python based frontend template or do we want to provide a list of available frontend templates that are compatible with the selected typed client? In most popular frontend frameworks a python client would be of no use unless we provide a python based frontend template OR treat it as a special use case when python client needs to be placed on a backend server.
- Which exact smart contract scenarios in regards to frontend are we handling. Some devs may have multiple smart contracts, some require to be deployed separately from the frontend, some may require frontend to handle deployments and upgrades. Do we opt in to only support the scenario where contract is deployed completely separately from the frontend and frontend is only used to interact with the contract? Or do we want to support more complex scenarios where frontend is used to deploy and upgrade the contract?

# Next Steps

The next steps assuming either option 1 or 3 is picked, would be to:

1. Pick a most popular web framework used by Algorand community (React, Next, Vue or else) and implement a templatized version of it into monorepo.
2. Extend the CLI tool to support separate optional flag for external frontend templates (while defaulting to official templates from monorepo that bundle official frontends).
3. Test the new templates and CLI tool functionality.
4. Update the AlgoKit documentation to explain how to use the new frontend templates.
