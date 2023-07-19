# Advanced `algokit generate` command

- **Status**: In-progress
- **Owner:** Altynbek Orumbayev, Inaie Ignacio
- **Deciders**: Rob Moore, Daniel McGregor, Alessandro Ferrari
- **Date created**: 2023-07-19
- **Date decided:** TBD
- **Date updated**: 2023-07-19

## Context

The [Frontend Templates ADR](./2023-06-06_frontend-templates.md) introduced and expanded on AlgoKit's principles of Modularity and Maintainability by introducing a new set of official templates for quickly bootstrapping standalone `react` and `fullstack` projects showcasing best practices and patterns for building frontend and fullstack applications with Algorand. As a logical next step, we want to enable developers to extend existing projects instantiated from official templates with new files and features.

## Requirements

### 1. AlgoKit user should be able to use generate command to extend existing algokit compliant projects with new `files` of any kind

This implies scenarios like:

- Adding new contracts into existing and algokit compliant projects.
  > Algokit compliant projects are projects that were instantiated from official or community templates and follow the same structure and conventions.
- Overriding existing files with new ones.
- TBD

Overal, we want to introduce a notion of `generators` which can be viewed as a modular self-sufficient template units that are hosted within template repositories and describe how to create or update files within projects instantiated from algokit templates.

Ruby on Rails has a similar concept of [generators](https://guides.rubyonrails.org/generators.html) which are used to create or update files within Rails projects. This can be used as a reference for inspiration.

### 2. Template builder should be able to access a clear guideline and refer to official templates for examples on how to create his own `generators`

This implies extension of existing starter guidelines available for template builders on [AlgoKit Docs](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/tutorials/algokit-template.md) and using one or several official templates as a reference point.

## Principles

- **Modularity**: Artifacts dependant on `advanced algokit generate` command capabilities embedded into templates should follow guiding AlgoKit principles and expand on approaches already utilized in `react`, `fullstack` and `beaker` templates. This implies that giving developers flexibility to define any extra templating logic, allowing to create or update any files within projects instantiated from algokit templates. TODO: Refine
- **Maintainability**: The `advanced algokit generate` capabilities on `algokit-cli` and related artifacts on respective official templates should be easy to maintain and extend.
- **Seamless onramp**: Great developer experience for template builders to create their own `generators` and user experience to use them via `advanced algokit generate` command should be a priority.

All of the aforementioned requirements should be met in a way that is consistent with the guiding principles of AlgoKit or attempt to find a balanced trade of between the principles that satisfies the requirements. Refer to [AlgoKit Guiding Principles](../../docs/algokit.md#Guiding-Principles) for detailed reference on the principles.

## Considered Options

Based on preliminary research, all of the options below assume that:
a) A `generator` is a self contained copier/jinja template that is hosted within a template repository and describes how to create or update files within projects instantiated from algokit templates. Hosting it along with the template is a necessity given that community based templates can follow different conventions, patterns and structure making it hard to attempt to generalize the logic of `generators` and make them work for all templates.

### Option 1: Wrapping generators into self contained copier templates hidden within algokit templates

This option implies that `generators` are self contained copier templates that are hidden within algokit templates and are not exposed to the end user. This option is inspired by [Ruby on Rails generators](https://guides.rubyonrails.org/generators.html) and [Yeoman generators](https://yeoman.io/authoring/).

The main idea is to rely on `_templates_suffix` in copier.yamls to define 2 separate types of suffixes for `templates` and for `generators`:

- Existing templates under all official algokit templates are already prefixed with `.jinja` hence we just need to explicitly prefix it with `.jinja` on root copier
- The new generators jinja templates can be prefixed (for example) with alternative file extension for jinja files such as `.j2`. Which is also a common convention for jinja templates.
- - This only works for files though for regular folders and cases like `{% if %}folder_name{% endif %}.j2` we need to wrap them into {% raw %} to that first pass when template initially initialized unwraps the content allowing second pass via generator to then use them as jinja templates. The only downside here is slightly longer file names for folders, but I think it's a reasonable tradeoff considering simplicity of the solution.

The overal structure of the template can look as follows:

```
template_content/.generators
└── create_contract # generator name
    ├── copier.yaml # generator copier.yaml
    └── smart_contracts # example for adding new contracts to existing beaker template based projects
        └── {% raw %}{{ contract_name }}{% endraw %}
            ├── contract.py.j2
            ├── {% raw %}{% if language == 'python' %}deploy_config.py{% endif %}{% endraw %}.j2
            └── {% raw %}{% if language == 'typescript' %}deploy-config.ts{% endif %}{% endraw %}.j2
...rest of the template is left as is
copier.yml
```

The final implementation part of the proposal is adjusting the `generator` command on `algokit-cli` to make sure it knows how to look for generators. The available generators can be provided to user via list picker (a.k.a ruby on rails style) by letting algokit scan contents of `algokit.toml` and look for `.generators` folder.

The proposal for new structure for defining generators in root algokit toml is as follows:

```toml
[generators.create_contract] # [generators.<generator_name>]
name = "smart-contract" # user-facing name of the generator
description = "Adds new smart contract to existing project" # description of the generator, can appear in cli for extra info
path = ".generators/create_contract"  # path that cli should grab to forward to copier copy
```

### Option 2: TBD

---

## Final Decision

## Next steps
