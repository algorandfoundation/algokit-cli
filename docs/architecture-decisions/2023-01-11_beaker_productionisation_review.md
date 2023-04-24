# Beaker productionisation review

- **Status**: Approved
- **Owners:** Rob Moore, Adam Chidlow
- **Deciders**: Anne Kenyon (Algorand Inc.), Alessandro Cappellato (Algorand Foundation), Jason Weathersby (Algorand Foundation), Benjamin Guidarelli (Algorand Foundation), Bob Broderick (Algorand Inc.)
- **Date created**: 2023-01-11
- **Date decided:** 2023-02-04
- **Date updated**: 2023-02-04

## Context

Beaker is a smart contract development framework for [Algorand](https://www.algorand.com/) that provides a wrapper over [PyTeal](https://pyteal.readthedocs.io/en/stable/) that focusses on providing a great developer experience through terse, expressive language constructs and making common tasks easier. Beaker is useful because it creates a higher level programming construct from PyTEAL that is easier to get started when learning and results in code that is terser and easier to read and write.

Beaker is an important part of the [AlgoKit strategy](https://github.com/algorandfoundation/algokit-cli/#algokit-cli). It helps create a more seamless onramp to Algorand development by providing an easier starting point for developers. As part of the lead up to releasing AlgoKit, it was desired to perform a v1.0 release of Beaker and explicitly mark it as being production ready. In order to provide confidence a productionisation review was conducted by [MakerX](https://www.makerx.com.au/); this document summarises the recommendations from that review.

An architecture decision was made in the lead up to this review on a [testing strategy for Beaker](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/architecture-decisions/2022-11-22_beaker-testing-strategy.md).

## Goal

The goals of this productionisation review are to:

- Get Beaker ready for production use
- Gain confidence in Beaker's software architecture and maintainability
- Reduce the likelihood of need for breaking changes soon after release by getting key recommended breaking changes identified now

## Findings summary

The Beaker codebase is well factored and had a decent initial test coverage (albeit some of that test coverage is via a series of examples that while they provide high code coverage, don't actually validate all of the functionality).

A series of changes have been landed to improve some of the fundamentals of Beaker in preparation for production launch:

- [Various improvements](https://github.com/algorand-devrel/beaker/pull/142) - Improved test coverage, improved dev experience (setup + ongoing) via Poetry, improvements to the code quality setup (linting, automatic formatting, typing), allowed Windows development on Beaker itself, significantly improved CI/CD pipeline speed, removing the examples directory and tests from being distributed wit hthe PyPi package
- [Typing improvements](https://github.com/algorand-devrel/beaker/pull/147)
- [Removed inline imports](https://github.com/algorand-devrel/beaker/pull/148)
- [Removed dead code](https://github.com/algorand-devrel/beaker/pull/149/files)
- [Added automated release management and versioning](https://github.com/algorand-devrel/beaker/pull/161)

In addition, there are a remaining set of more major (breaking) changes that are recommended. The recommendations are split into 2 categories, recommendations for immediate improvement (i.e. included in v1.0) and future suggestions that can be addressed post v1.0 launch.

The recommended additional areas for immediate improvement are:

- **Replace the class-based structure with an instance based one** - remove some areas of potential surprise for developers and simplify the Beaker codebase by moving to a composable instance-based structure rather than a static class-based structure
- **Defer PyTEAL compilation** - improve flexibility and future contract output stability by deferring PyTEAL compilation (i.e. Beaker -> TEAL transpilation) to not happen when the Beaker contract is initialised
- **Renamings** - There are some clear parameters that make sense to rename for various reasons
- **Key decorator improvements** - Refactor some of the Beaker decorators to fix some bugs and improve user experience
- **Beaker state refactor** - Refactor of the Beaker state interfaces to improve user extensibility and significantly simplify the Beaker codebase to improve maintainability

The recommended areas for future improvement are:

- Typed client generation from app spec to improve deploy-time and run-time dev experience
- `Tmpl` values in app spec so you can have type-safe deployment clients that substitute any template values reliably at contract deploy time
- Refactor storage types (blob, reserved, etc.) to allow use of in-built Python types and operators (terser, more intuitive)
- Box storage implementation improved to match local/global behaviour and also automatically delete itself on contract deletion
- Composable and stackable authorization and `@authorize` as a standalone decorator
- PyTEAL typings to be improved to support types beyond `Expr` where a more explicit type can be specified (improves typing and extensibility)
- Support referencing an app/lsig via ID/address (deployed separately, potentially automatically as part reading a Directed Acyclic Graph (DAG) in application.json of application dependencies) or bytes (deployed inline, what was previously called precompile, noting this would be deploy-time substitution, not smart contract run-time substitute like `TemplateVariable`), this also may allow precompile to be deprecated (it's a very complex implementation for what we believe to be an advanced edge case)

## Immediate recommendations

### (1) Replace the class-based structure with an instance based one

#### What?

Beaker is currently structured around users sub-classing the `beaker.Application` class. They then hold state variables (from `beaker.state.*`) as [class variables](https://pynative.com/python-class-variables/) and also contain methods which are forwarded to the `pyteal.abi.Router` instance created during `Application.compile(...)` based on decorators from `beaker.decorators.*`. We propose replacing this with an "instance based structure", drawing inspiration from highly popular Python web frameworks such as `flask` ([example](https://flask.palletsprojects.com/en/2.2.x/quickstart/#a-minimal-application)).

This change will simplify Beaker's code (improving maintainability) and, more importantly, reduce the potential for end-user error and confusion.

#### Why?

**User-facing benefits**

1. The current structure, by encouraging and supporting [bound instance methods](https://www.geeksforgeeks.org/bound-methods-python/) alongside [class variables](https://pynative.com/python-class-variables/), is a potential source of confusion for users new to writing smart contracts or PyTEAL. The distinction between what runs on `beaker.Application` instantiation, evaluation by PyTeal during compile, and finally what runs on-chain, can be difficult to grasp at first. One might assume (wrongly) that Beaker is somehow maintaining the state of `self.*` between methods, but this is not the case. Contrast this with Solidity, for example, where state can be directly manipulated because it's help within the class instance.
2. Currently, actually using `self.*` can easily lead to problems, since if they are not defined before calling `super().__init__(...)` they won't be defined when compiling. This can be fixed by not automatically compiling in `Application.__init__()` (which is also proposed in (2) below) for simple constants, however another issue is that using `self.foo = <Some beaker.state object>`, would not currently work with the introspection beaker is performing. This could potentially be fixed by itself, but developers will still need to define these values _before_ calling `super().__init__()` which is a source of confusion. Usually, idiomatic Python will call super init sooner rather than later so this is something that can trip up experienced Python developers.
3. In order to compose applications together, say if there were two ARC standard implementations that we wanted to combine into the same contract, the user doesn't need to understand Python's multiple-inheritance idiosyncrasies like [Method Resolution Order](https://www.geeksforgeeks.org/method-resolution-order-in-python-inheritance/). Additionally, by taking a functional composition approach, we can have easy to understand entry points where you can check any pre-conditions.
4. Since state variables are currently defined as class variables, this makes them "globals", which can lead to errors/bugs that are non-obvious.

   For instance, consider:

   ```python
   class MyBaseApp(beaker.Application):
       counter = beaker.ApplicationStateValue(stack_type=pyteal.TealType.uint64)

       @beaker.create
       def create(self) -> pyteal.Expr:
           return self.initialize_application_state()

   class MyApp(MyBaseApp):
       pass
   MyApp.counter.default = pyteal.Int(10)

   class MyOtherApp(MyBaseApp):
       pass

   app1 = MyApp()
   app2 = MyOtherApp()
   assert app1.approval_program != app2.approval_program  # fails
   ```

5. Setting parameters that control the program creation is awkward with the current approach of extending `beaker.Application`, currently this impacts just the `version` parameter (which specifies the TEAL version), but there are clear examples we can see for other variables that are useful to define at this point in the future (e.g. a state allocation override if you know that the state a contract will need grows in the future).
6. There are bugs in beaker which are directly caused by the class-based structure. For example, bare methods are currently evaluated as a subroutine only once:

   ```python
   class MyApp(beaker.Application):
       price = beaker.ApplicationStateValue(stack_type=pyteal.TealType.uint64)

       def __init__(self, default_price: int, version: int = pyteal.MAX_TEAL_VERSION):
           self.price.default = pyteal.Int(default_price)
           super().__init__(version=version)


   class CorrectApp(MyApp):
       @beaker.create
       def create(self, *, output: pyteal.abi.Uint64) -> pyteal.Expr:
           return pyteal.Seq(self.initialize_application_state(), output.set(self.price))


   class IncorrectApp(MyApp):
       @beaker.create
       def create(self) -> pyteal.Expr:
           return self.initialize_application_state()


   correct_app1 = CorrectApp(default_price=123)
   correct_app2 = CorrectApp(default_price=456)

   incorrect_app1 = IncorrectApp(default_price=123)
   incorrect_app2 = IncorrectApp(default_price=456)

   assert correct_app1.approval_program != correct_app2.approval_program  # success
   assert incorrect_app1.approval_program != incorrect_app2.approval_program  # failure

   ```

**Beaker maintainability benefit**

The main benefit to Beaker is the removal the complex code that modifies function signatures to remove `self` before passing to PyTEAL. Removing the instance method implementation will significantly reduce the complexity of the code and likelihood of unknown bugs surfacing from that part of the codebase.

#### Before & After (user's perspective)

While the proposed changes are fairly substantial internally, and propose a radically different architecture conceptually for beaker Applications, the migration should actually be relatively straight forward for users with existing Beaker code:

The following examples assume the import of relevant names from `beaker` and/or `pyteal` are present to simplify the code.

**Before:**

```python

class CounterApp(Application):
    counter = ApplicationStateValue(
        stack_type=TealType.uint64,
        descr="A counter for showing how to use application state",
    )

    @create
    def create(self):
        return self.initialize_application_state()

    @external(authorize=Authorize.only(Global.creator_address()))
    def increment(self, *, output: abi.Uint64):
        """increment the counter"""
        return Seq(
            self.counter.set(self.counter + Int(1)),
            output.set(self.counter),
        )

    @external(authorize=Authorize.only(Global.creator_address()))
    def decrement(self, *, output: abi.Uint64):
        """decrement the counter"""
        return Seq(
            self.counter.set(self.counter - Int(1)),
            output.set(self.counter),
        )

```

**After:**

The changes are:

- State is moved into a dedicated class `CounterState`
- `beaker.Application` is directly instantiated (along with the state, and optionally the teal `version`)
- Class methods are de-indented, `self` is removed and the decorator is prefixed with `app.` (which in turn reduces the number of imports needed from the `beaker` namespace and provides better exploratory intellisense for users)

```python

class CounterState(beaker.State):
    counter = ApplicationStateValue(
        stack_type=TealType.uint64,
        descr="A counter for showing how to use application state",
    )


app = beaker.Application(state=CounterState())

@app.create
def create():
    return app.state.initialize_application_state()

@app.external(authorize=Authorize.only(Global.creator_address()))
def increment(*, output: abi.Uint64):
    """increment the counter"""
    return Seq(
        app.state.counter.set(app.state.counter + Int(1)),
        output.set(app.state.counter),
    )

@app.external(authorize=Authorize.only(Global.creator_address()))
def decrement(*, output: abi.Uint64):
    """decrement the counter"""
    return Seq(
        app.state.counter.set(app.state.counter - Int(1)),
        output.set(app.state.counter),
    )

```

### (2) Defer PyTEAL compilation

#### What?

Currently, `beaker.Application.compile()` is called as part of `__init__()`, assuming there are no `precompiles` defined. We recommend that `compile()` always be deferred to a later point, and further that `compile()` does not mutate `Application` in any way, but instead returns a new object.

#### Why?

The deferment of the `compile()` call is actually a necessary part of recommendation #1 that we have skipped over thus far, but would be recommended anyway.

The immediate `compile()` has issues such as requiring implementors (i.e. subclasses) to call `super().__init__()` as a **final** step in their own `__init__` method - any code that runs after the super init call will have no effect on the application produced!

Immediate compilation also reduces the control the user has over the output. Although currently the only parameter that `compile` takes is a `client`, it might be useful to add (optional) parameters here to control the compilation. For example, if you can pass in the list of optimisations that should be applied, that allows you to have [output stability](../articles/output_stability.md) of your smart contract code if new optimisations are added in the future.

The separation of compiled state outside of `Application` simplifies the design, and can be done mostly transparently to end-users.

The separation of compiled state will also benefit future interoperability. It allows for more explicit decoupling of PyTEAL compilation (Beaker / PyTEAL transpilation -> TEAL) and deploment (TEAL -> compiled byte code -> Algorand network). Once `beaker.client` is split into a separate package, if the compiled state can be both generated from a beaker Application object _or_ loaded from disk (or similar), this means Beaker's ApplicationClient could be used in more situations, such as for a (say) tealish smart contract, or a C# smart contract, or a raw PyTEAL or TEAL smart contract, etc. This conforms better to the modularity principle in AlgoKit and also vice versa allows for a Beaker smart contract to be deployed by a TypeScript deployer, or C# deployer, etc.

#### Before & After - user's perspective

For most use cases, this should be a relatively small and probably imperceptible change.

We believe there are two common usage scenarios that use the output of PyTEAL compilation currently:

1. Output the `Application` via `Application.dump(...)`
2. Interact with the `Application` by passing it to `ApplicationClient(app=..., ...)`.

We propose maintaining those two scenarios without any immediate external changes, but internally:

1. `Application.dump(...)` will call `Application.compile().dump()`, and potentially trigger a `DeprecationWarning` if we decide that we want users to always explicitly call compile.
2. `ApplicationClient(app=..., ...)` will call `Application.compile()` and not retain any reference to `app`.

To make use of scenarios 1 _and_ 2, or to control compilation parameters, a user should also be able to (for instance):

```python
app = Application(...)
compiled_app: CompiledApplication = app.compile(...)
compiled_app.dump(...)
client = ApplicationClient(app=compiled_app, ...)
```

We suggest also potentially renaming `CompiledApplication.dump()`, perhaps to something along the lines of `serialize()`.

The `compile()` call is actually a transpilation call (Beaker / PyTEAL transpilation -> TEAL), although it's called compile in PyTEAL so consideration should be made to either keep consistency with PyTEAL or use the more accurate `transpile()` (which also reduces confusion around the fact that you then have to call `compile` on algod to compile the TEAL to byte code before deployment).

The exact details of what `CompiledApplication` will look like are TBD, but should be driven by the principles outlined in the "Why?" section above. Broadly, it stands to reason it would contain the approval and clear TEAL, the ABI spec and the app spec though at least.

Finally, there is likely need to use metadata from transpilation such as the mapping of source code to line numbers, but we are confident these use cases will be able to be implemented on top of the proposed change.

### (3) Renamings

Renaming `version` parameter in `Application.__init__(version: int = pyteal.MAX_VERSION)` to (e.g.) `avm_version`, to be more explicit. Otherwise developers may be confused that it's the version of the specific smart contract. It may be desirable to allow `version` to continue to be specified for some time, but to raise a `DeprecationWarning`.

Rename methods in `beaker.lib.*` to start with an uppercase. Although going against PEP-8, this prevents collisions with `builtins` such as `min` and `max`, and also follows the useful convention from PyTeal where methods that produce TEAL code (vs just running Python code at transpilation time) start with uppercase such as `Add`, `Or`, `Concat`, etc.

### (4) Key decorator improvements

Refactor some of the Beaker decorators to fix some bugs and improve user experience.

End state:

```python
# for user convenience, rather than having to import + use MethodConfig
OnCompleteActionName: TypeAlias = Literal[
    "no_op",
    "opt_in",
    "close_out",
    "clear_state",
    "update_application",
    "delete_application",
]

HandlerFunc: TypeAlias = Callable[..., Expr]
DecoratorFunc: TypeAlias = Callable[[HandlerFunc], HandlerFunc]

class Application:
    # the main decorator, capable of handling both ABI and Bare method registration
    def external(
        self,
        fn: HandlerFunc | None = None,
        /,
        *,
        # note: retain existing behaviour of if method_config is None, default to no_op with CallConfig.CALL
        method_config: MethodConfig | dict[OnCompleteActionName, CallConfig] | None = None,
        name: str | None = None,
        authorize: SubroutineFnWrapper | None = None,
        bare: bool = False,
        read_only: bool = False,
        override: bool | None = False,
    ) -> HandlerFunc | DecoratorFunc:
        ...

    # the below are just "shortcuts" to @external for simple/common use cases
    def create(
        self,
        fn: HandlerFunc | None = None,
        /,
        *,
        allow_call: bool = False,
        name: str | None = None,
        authorize: SubroutineFnWrapper | None = None,
        bare: bool = False,
        read_only: bool = False,
        override: bool | None = False,
    ) -> HandlerFunc | DecoratorFunc:
        ...


    def <delete|update|opt_in|clear_state|close_out|no_op>(
        self,
        fn: HandlerFunc | None = None,
        /,
        *,
        allow_call: bool = True,
        allow_create: bool = False,
        name: str | None = None,
        authorize: SubroutineFnWrapper | None = None,
        bare: bool = False,
        read_only: bool = False,
        override: bool | None = False,
    ) -> HandlerFunc | DecoratorFunc:
        ...
```

For reference, the current state:

```python
def internal(
    return_type_or_handler: TealType | HandlerFunc,
) -> HandlerFunc | DecoratorFunc:
    ...

def external(
    func: HandlerFunc | None = None,
    /,
    *,
    name: str | None = None,
    authorize: SubroutineFnWrapper | None = None,
    method_config: MethodConfig | None = None,
    read_only: bool = False,
) -> HandlerFunc | DecoratorFunc:
    ...

def bare_external(
    no_op: CallConfig | None = None,
    opt_in: CallConfig | None = None,
    clear_state: CallConfig | None = None,
    delete_application: CallConfig | None = None,
    update_application: CallConfig | None = None,
    close_out: CallConfig | None = None,
) -> Callable[..., HandlerFunc]:
    ...


def create(
    fn: HandlerFunc | None = None,
    /,
    *,
    authorize: SubroutineFnWrapper | None = None,
    method_config: Optional[MethodConfig] | None = None,
) -> HandlerFunc | DecoratorFunc:
    ...


def <delete|update|opt_in|clear_state|close_out|no_op>(
    fn: HandlerFunc | None = None, /, *, authorize: SubroutineFnWrapper | None = None
) -> HandlerFunc | DecoratorFunc:
    ...
```

Changes:

- Remove `@internal`:
  - if you don't pass a TealType parameter to it, i.e. intend to create an ABI internal routine, it actually just inlines the code currently due to a bug
  - when passing in a TealType parameter to it, i.e. intent to create a normal subroutine, then in combination with (1) it will be unneeded since you can use `Subroutine` from PyTEAL (since the methods don't need to be artificially modified to remove `self` anymore)
- Add `bare: bool` option:
  - Currently, this is not able to be controlled by the user - for `<create|delete|update|opt_in|clear_state|close_out|no_op>` decorators, they will create a bare method if the function takes no parameters other than maybe a `self` parameter. This has some down-sides:
    1. The user might want an ABI method rather than a bare method. In this case, currently they could use `@external(method_config=...)`, but for simple cases this is not as easy to read/type and is not intuitive to discover in the first place.
    2. The user might have more than one method that takes no parameters that is able to be called with a given `OnCompletionAction`, currently this would produce a `BareOverwriteError` in Beaker. Again, the work-around exists of calling `@external` instead, but it would be nicer and more intuitive to add a `bare` option to control this explicitly.
  - The above Python methods have `bare: bool = False`. An alternative option would be to make this `bare: bool | None = None`, where `None` would retain the current behaviour of inspecting the method signature to see if it takes parameters or not.
- Remove `@bare_external`:
  - Mostly unused, and doesn't provide the same options as the other decorators (e.g. `authorize`)
  - Instead, we can replace the case of a single option being passed to it, with the equivalent named method: for example `@bare_external(opt_in=CallConfig.CALL)` becomes `@opt_in(bare=True)`
  - For the multi-argument case: `@bare_external(no_op=CallConfig.CREATE, opt_in=CallConfig.CALL)` becomes `@external(method_config={"no_op": CallConfig.CREATE, "opt_in": CallConfig.CALL}, bare=True)`

* Add optional `name` option to all decorators, not just `@external`.
* Add `allow_call` and `allow_create` options to shortcut methods (except `@create` shortcut which should always allow `CallConfig.CREATE`).
* Remove `method_config` from `@create` shortcut - the default behaviour will remain unchanged, but any usages with `method_config` specified would be equivalent to just using `@external` directly.
* Add `override: bool | None = False` parameter.
  - If `False` (the suggested default), an error will be raised if an ABI or Bare method would replace one already registered in the Application. For bare methods, this would be keyed on the `OnCompleteAction`, and for ABI methods should be based on the method signature (ie `ABIReturnSubroutine.method_signature()`). This is suggested as the default to prevent unexpected cases of overriding, especially when using blueprints/templates from the future Smart Contracts Library.
  - If `True`, then an error will be raised if it _does not_ replace an already registered ABI or Bare method. This is similar to Java's `@Override` annotation, and can allow the user to be explicit and thus prevent unexpectedly _not_ replacing an existing method.
  - If `None`, then methods will be overwritten if present, and no error will be raised if not already present. This option is here for maximum flexibility, but should perhaps be discouraged.

### (5) Beaker state refactor

Refactor of the `beaker.state` internal interfaces to simplify Beaker code base, make it easier to add new state wrappers, and to pave the way for future enhancements. This will have a side effect of allowing users to create their own state wrappers without having to modify `beaker` itself, although we recommend marking these interfaces as internal and subject to change - at least initially.
