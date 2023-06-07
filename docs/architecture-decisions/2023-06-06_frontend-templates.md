# Frontend Templates

- **Status**: Draft
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

The table below summarizes key points of each implementation option, consequent section dive into each of the options in more detail.

| Options                                  | Pros                                                        | Cons                                                                                                                                                           |
| ---------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Extend Existing Smart Contract Templates | Cohesive developer experience, Simplified project structure | Limited flexibility, Increased complexity                                                                                                                      |
| Monorepo Approach                        | Flexibility, Cohesive developer experience                  | Increased complexity, Potential for confusion                                                                                                                  |
| Separate Frontend Templates              | Flexibility, Simplified maintenance                         | Longer and more complex `init` invocation command (can be solved by interacively asking for extra details on templates during init phase), Versioning overhead |
| Hybrid Approach                          | Flexibility, Simplified maintenance                         | Increased complexity, Implementation complexity, Versioning overhead                                                                                           |

### Option 1. Extend Existing Smart Contract Templates

In this approach, we would extend the existing smart contract templates to include frontend code. This would mean that each template would contain both the smart contract and frontend code.

A generalized project structure for this approach would look as follows:

```md
template repository
├── Smart Contract Template
│ ├── Contracts Code
│ └── Frontend Code
└── CI/CD and Deployment Configurations
```

#### Pros

- Cohesive developer experience - developers would be able to get started with dApp development by simply cloning the template repository and running the `init` command.
- Simplified project structure - developers would be able to focus on the development of the dApp without having to worry about the project structure.

#### Cons

- Limited flexibility - developers would be limited to the frontend and backend code that is included in the template.
- Increased complexity - the complexity of the templates would increase as the number of templates increases. In addition, using `copier` for templatizing large variety of templates would require a lot of boilerplate code and solid test coverage that will increase in complexity as number of templates grow inside the monorepo.

### Option 2. Monorepo Approach

In this approach, we would create a monorepo that would contain all of the different templates. This would mean that each template would be a separate package within the monorepo.

A generalized project structure for this approach would look as follows:

```md
templates monorepo
├── Smart Contract Template 1
│ ├── Contracts Code
│ └── Frontend Code
├── Smart Contract Template 2
│ ├── Contracts Code
│ └── Frontend Code
└── CI/CD and Deployment Configurations
```

#### Pros

- Flexibility - developers would be able to mix and match different templates.
- Cohesive developer experience - developers would be able to get started with dApp development by simply cloning the template repository via the `init` command, followed by selection of specific combination of backend/frontend available in official templates monorepo.

#### Cons

- Increased complexity - the complexity of the templates would increase as the number of templates increases. In addition, using `copier` for templatizing large variety of templates would require a lot of boilerplate code and solid test coverage that will increase in complexity as number of templates grow inside the monorepo.
- Potential for confusion - developers would have to be aware of the different templates available in the monorepo and the different combinations of templates that are supported. This can be addressed by enhancing the cli to provide a list of available templates and the different combinations of templates that are supported during initialization.

### Option 3. Separate Frontend Templates

In this approach, we propose a new `type` of template repositories called `frontend` templates. These templates would contain only the frontend code and would be used in conjunction with the existing smart contract templates.

A generalized project structure for this approach would look as follows:

```md
Template repository
├── Smart Contract Template (pulled from contracts template repo of choice)
│ └── Contracts Code
├── Frontend Template (pulled from frontend template repo of choice)
│ └── Frontend Code
└── CI/CD and Deployment Configurations
```

#### Pros

- Flexibility - developers would be able to mix and match different templates, which can be enhanced by providing an interactive selector during the `init` command.
- Simplified maintenance - the frontend templates would be maintained separately from the smart contract templates. This would allow for easier maintenance and extension of the templates.

#### Cons

- Longer and more complex `init` invocation command - developers would have to specify the frontend template that they want to use during the `init` command invocation. This can be addressed by enhancing the cli to provide a list of available frontend templates during initialization in interactive manner, hiding the complexity of the initial command.
- Versioning overhead - versioning of the frontend templates would have to be managed separately from the smart contract templates. This can be addressed by using the same versioning scheme for both the smart contract and frontend templates.

### Option 4. Hybrid Approach

In this approach, we would combine the monorepo approach with the separate frontend templates approach. This would mean that we would create a monorepo that would contain all of the different smart contract and frontend templates while still allowing developers to install external community based smart contract and frontend templates.

#### Pros

- Flexibility - developers would be able to mix and match different templates.
- Simplified maintenance - the frontend templates would be maintained separately from the smart contract templates. This would allow for easier maintenance and extension of the templates.

#### Cons

- Increased complexity - the complexity of the templates would increase as the number of templates increases. In addition, using `copier` for templatizing large variety of templates would require a lot of boilerplate code and solid test coverage that will increase in complexity as number of templates grow inside the monorepo.
- Implementation complexity - the implementation of this approach would be more complex than the other approaches as it will require proper implementation of the monorepos as well as support for external community based templates outside of the monorepo.
- Versioning overhead - versioning of the frontend templates would have to be managed separately from the smart contract templates. This can be addressed by using the same versioning scheme for both the smart contract and frontend templates.

## Preferred option

Based on the principles outlined in the problem statement, the best approach would seem to be to create separate frontend templates or use a hybrid approach where we maintain a monorepo with all official template packages while still supporting frontend community templates. Despite additional overhead in initial implementation, this approach provides the most flexibility and aligns with the principle of meeting developers where they are. It also supports the principle of modularity and allows for sustainable, long-term maintenance.

While the invocation command would become longer, this is a minor inconvenience compared to the benefits of flexibility and simplicity. The CLI tool could be extended to provide sensible defaults and shortcuts to mitigate this issue.

## Selected option

To be discussed.

## Open questions

- Do we want to support scenarios when users already have a ready made frontend repository and want to potentially embedd algokit into it - or we are primarily focusing on solid user experience in regards to initialization and bootstrapping of the templates?
- How do we want to handle cases when user selects python typed client during initialization? Do we want to provide a default python based frontend template or do we want to provide a list of available frontend templates that are compatible with the selected typed client? In most popular frontend frameworks a python client would be of no use unless we provide a python based frontend template OR treat it as a special use case when python client needs to be placed on a backend server.
- Which exact smart contract scenarios in regards to frontend are we handling. Some devs may have multiple smart contracts, some require to be deployed separately from the frontend, some may require frontend to handle deployments and upgrades. Do we opt in to only support the scenario where contract is deployed completely separately from the frontend and frontend is only used to interact with the contract? Or do we want to support more complex scenarios where frontend is used to deploy and upgrade the contract?

# Next Steps

The next steps would be to:

1. Create frontend templates for most popular web frameworks used by Algorand community (React, Next, Vue or else).
2. Extend the CLI tool to support separate URLs for frontend and backend templates.
3. Test the new templates and CLI tool functionality.
4. Update the AlgoKit documentation to explain how to use the new frontend templates.
