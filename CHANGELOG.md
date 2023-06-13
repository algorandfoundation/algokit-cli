# Changelog

<!--next-version-placeholder-->

## v1.1.2 (2023-06-13)

### Fix

* Use /v2/status for algod health check ([#282](https://github.com/algorandfoundation/algokit-cli/issues/282)) ([`91e5e36`](https://github.com/algorandfoundation/algokit-cli/commit/91e5e36886edfa5d90f6aaf77f9db6a666bbdc43))

## v1.1.1 (2023-06-13)

### Fix

* Add check for localnet start to wait for algod to be ready ([#281](https://github.com/algorandfoundation/algokit-cli/issues/281)) ([`dff0a5d`](https://github.com/algorandfoundation/algokit-cli/commit/dff0a5d45fb79317509f6a44fa3fc37b93a2d8af))

### Documentation

* Updating adr header to reflect status and deciders ([`b84a07d`](https://github.com/algorandfoundation/algokit-cli/commit/b84a07dee0c1b5fc9060b806feeb07c41b4cd4fd))

## v1.1.0 (2023-06-07)

### Feature

* Adding minimum required version for algokit. ([#273](https://github.com/algorandfoundation/algokit-cli/issues/273)) ([`10aacc2`](https://github.com/algorandfoundation/algokit-cli/commit/10aacc2c17acc55c47d69674e9ace780313aee46))
* Use official Algorand Docker images for LocalNet ([#268](https://github.com/algorandfoundation/algokit-cli/issues/268)) ([`fc5106c`](https://github.com/algorandfoundation/algokit-cli/commit/fc5106cc773a4672eb1ec8614bb60ed2dc61be42))
* Add generate client command ([#266](https://github.com/algorandfoundation/algokit-cli/issues/266)) ([`b885fb1`](https://github.com/algorandfoundation/algokit-cli/commit/b885fb16b3b9a49231a6b786d1156bd7b202fb12))

### Fix

* Don't reset localnet if only algod_config.json is missing ([#269](https://github.com/algorandfoundation/algokit-cli/issues/269)) ([`ff3ef56`](https://github.com/algorandfoundation/algokit-cli/commit/ff3ef560565bdb92951fa7d6e3bbf4437db873a0))
* Bootstrap failure during init now shows the error to avoid confusion ([`8a36e82`](https://github.com/algorandfoundation/algokit-cli/commit/8a36e82497cc342082d71df5c327837ddad221a4))
* Workaround ValueError raised when using --defaults flag with copier 7.1 ([#256](https://github.com/algorandfoundation/algokit-cli/issues/256)) ([`e224070`](https://github.com/algorandfoundation/algokit-cli/commit/e22407074bf8c8ce2b1576379c90df76a70f6df9))

### Documentation

* Document typed client dependency ([#275](https://github.com/algorandfoundation/algokit-cli/issues/275)) ([`87d7233`](https://github.com/algorandfoundation/algokit-cli/commit/87d7233bd35a1b896d15e0aea3f63e738738254f))
* Add example usage for typed clients ([`16d91f5`](https://github.com/algorandfoundation/algokit-cli/commit/16d91f5d3e5ef0115826780bc1daa918fbf031a8))
* Add generate docs ([#270](https://github.com/algorandfoundation/algokit-cli/issues/270)) ([`da8e46d`](https://github.com/algorandfoundation/algokit-cli/commit/da8e46dfda97e514be17955ad39986f42b93b5e2))
* Update localnet docs to include links to AlgoKit Utils ([`6e937a8`](https://github.com/algorandfoundation/algokit-cli/commit/6e937a8ff487955063ac1023c51ac3c83f5cbb01))
* README update ([`8702e45`](https://github.com/algorandfoundation/algokit-cli/commit/8702e45c25eb2ec422587e307151037fbf6c1914))
* Changes to wording of output stability snippet ([`f378013`](https://github.com/algorandfoundation/algokit-cli/commit/f378013db7b52c5d69f71ba606fbe3f8f50fa843))
* Added output stability article content ([`c3a89f1`](https://github.com/algorandfoundation/algokit-cli/commit/c3a89f14b461ec2a22b23f3e423d107bff72fbb9))
* Include note about pipx ensurepath ([`847013d`](https://github.com/algorandfoundation/algokit-cli/commit/847013d1733f3b11ed6d3c64b223e84dd7bc1124))
* Link to repo search, fixes #240 ([`2550f6f`](https://github.com/algorandfoundation/algokit-cli/commit/2550f6ff147fd3de9f5da6dee470e9f214500c20))

## v1.0.1 (2023-03-29)
### Documentation
* Reference overview image with absolute url ([`c987f84`](https://github.com/algorandfoundation/algokit-cli/commit/c987f84d3079cf88c262e21a542e60c74a71829a))
* Added overview image ([`4c387ee`](https://github.com/algorandfoundation/algokit-cli/commit/4c387ee7fbbae2c01498dec83fa76ffd4d4990fa))
* Make README.md links absolute ([`8435bc7`](https://github.com/algorandfoundation/algokit-cli/commit/8435bc7faaddd33e4bb204f8c965365aee097b42))

## v1.0.0 (2023-03-29)
### Feature
* **localnet:** Changing the default reset behaviour to not pull images ([`6d3f10e`](https://github.com/algorandfoundation/algokit-cli/commit/6d3f10e5690f15d04d03bc38290f2c670905ba24))

### Breaking
* 1.0 release ([`68b02ad`](https://github.com/algorandfoundation/algokit-cli/commit/68b02ad49de0c8da083fcce542a76f6342ac0020))

### Documentation
* Remove mention of virtualenv when describing bootstrap command ([`302498f`](https://github.com/algorandfoundation/algokit-cli/commit/302498f21cb59eea4e01b482d3f07eecada34909))
* Explain what running bootstrap during init will do ([`4bd58bd`](https://github.com/algorandfoundation/algokit-cli/commit/4bd58bd981eef9a382c2a16f9d0bd06ebe397ba3))
* Added file copy advice ([`2b4882c`](https://github.com/algorandfoundation/algokit-cli/commit/2b4882c1878c07da7933d9a266f80560395fbb5f))
* Added note about algokit explore after a localnet start ([`7a068b1`](https://github.com/algorandfoundation/algokit-cli/commit/7a068b1d90592e5eebd3f7af5a5f6d216c45ec1f))
* Provide feedback when calling algokit explore ([`def4ef5`](https://github.com/algorandfoundation/algokit-cli/commit/def4ef5ce5bb2eb3e7b7c0dbcdbf0d4c4f8f6b1d))
* Update --bootstrap help text on algokit init ([`ce9ebea`](https://github.com/algorandfoundation/algokit-cli/commit/ce9ebeaf9bb636f6af4cd2b98d6a32a4b4e10f15))
* Updating auto-generated docs ([`637d534`](https://github.com/algorandfoundation/algokit-cli/commit/637d534b14c92fa3b4be27f58a0e3a950ad5d75e))
* Command help text improvements for bootstrap and init ([`67eb3f6`](https://github.com/algorandfoundation/algokit-cli/commit/67eb3f6b79ac47abe4f4d1497db66acda5d0d4fd))
* Update config and completions help text ([`7e0c087`](https://github.com/algorandfoundation/algokit-cli/commit/7e0c0872c1ca9ae531c69ae37dce43f44bc74634))
* Update doctor help text ([`111bf2e`](https://github.com/algorandfoundation/algokit-cli/commit/111bf2e874fff0960ed7faf5c073dd44d8b487cd))
* Removing incorrect references to sandbox ([`7179eb8`](https://github.com/algorandfoundation/algokit-cli/commit/7179eb8c67160671d549bd8f7114f54fb03b3fad))
* Improving doctor command feature description ([`a8a2862`](https://github.com/algorandfoundation/algokit-cli/commit/a8a2862efc03448022df9fd2f9fa42e3ad883cde))
* Updating bootstrap command descriptions ([`07a5fdb`](https://github.com/algorandfoundation/algokit-cli/commit/07a5fdbaa2653ab6505fd67432fac3c36ee5d711))
* Fixing heading order in intro tutorial ([`46b5023`](https://github.com/algorandfoundation/algokit-cli/commit/46b50235b965f1e9736d3e8c67d1a95c9a13923c))
* Getting README.md ready for 1.0 ([`815712f`](https://github.com/algorandfoundation/algokit-cli/commit/815712f83a2b56172c3cc51c7615bb33cae32b2f))

## v0.6.0 (2023-03-28)
### Feature
* Prompt for template first ([`91326f3`](https://github.com/algorandfoundation/algokit-cli/commit/91326f339650f9ea33ff4746f6707f507364b81a))

### Documentation
* Autogen docs ([`9803ff7`](https://github.com/algorandfoundation/algokit-cli/commit/9803ff7764090b4d5b1d661f8e7ead3b74a49d0f))
* Added the intro tutorial ([`087852b`](https://github.com/algorandfoundation/algokit-cli/commit/087852b9be034daddca3a609bb7fd9ff0b476b6e))

## v0.5.0 (2023-03-24)
### Feature
* Change playground template to point to new repo ([`805d63c`](https://github.com/algorandfoundation/algokit-cli/commit/805d63c10be3c62a3ef8d78bd2d40d1e6d1c8c5c))
* **init:** Added --no-ide flag to allow user to prevent IDE opening ([#211](https://github.com/algorandfoundation/algokit-cli/issues/211)) ([`cd9f015`](https://github.com/algorandfoundation/algokit-cli/commit/cd9f01549fc460641bd7a64f606963efb7f4082a))

## v0.4.1 (2023-03-22)
### Fix
* **init:** Resolving issue with opening VS Code automatically on windows ([`691543d`](https://github.com/algorandfoundation/algokit-cli/commit/691543dfb7748dcb0495ceb0593dfe14e500d8fc))

## v0.4.0 (2023-03-22)
### Feature
* Increase max content width to 120 for easier reading in wider terminals ([`cadc615`](https://github.com/algorandfoundation/algokit-cli/commit/cadc6150fb0a6c7d5f1ae60ccd7bccee89fb38fb))
* Include "extra version info" in all commands not just docker compose ([`f1c1d69`](https://github.com/algorandfoundation/algokit-cli/commit/f1c1d6992faefa26c8656121e30b894dfce32c03))
* Detect if code is on path && .vscode exists and try to launch ([`78f8b3f`](https://github.com/algorandfoundation/algokit-cli/commit/78f8b3f7f655d7286b4c090002e09edc52f3009a))
* Add a command to see logs from localnet docker containers ([`31c9cc4`](https://github.com/algorandfoundation/algokit-cli/commit/31c9cc4d44f2df2abcb8014dad6633232781f6e0))

### Fix
* Make failure to run npm install during bootstrap error message more explicit ([`468a186`](https://github.com/algorandfoundation/algokit-cli/commit/468a18683ebe80f671438df6a2f4bcf1d0c7c4a5))
* When executing goal/bash inside algod container only show localnet hint if it looks like the container doesn't exist or isn't running ([`b9dc57f`](https://github.com/algorandfoundation/algokit-cli/commit/b9dc57fe24a0f28df0b4399f0f579c39ab5336d8))
* Allow going back to template selection from custom url ([`929eefb`](https://github.com/algorandfoundation/algokit-cli/commit/929eefbd9bb8b4e38b24423980d18c0bbc09e9a3))

### Documentation
* **localnet:** Removing known LocalNet issue that is fixed ([`6747642`](https://github.com/algorandfoundation/algokit-cli/commit/6747642cc2a6b79e5cfa7b71418dfbaadbbf6659))

## v0.3.3 (2023-03-09)
### Fix
* Use /v2/status when querying localnet algod container ([#198](https://github.com/algorandfoundation/algokit-cli/issues/198)) ([`0fb0488`](https://github.com/algorandfoundation/algokit-cli/commit/0fb0488e7a5ebd7da22f764e9047df9c6ef7ac31))

### Documentation
* Fix references to renamed sandbox command ([#194](https://github.com/algorandfoundation/algokit-cli/issues/194)) ([`8b2910b`](https://github.com/algorandfoundation/algokit-cli/commit/8b2910b465e67c0e428cc4dde65e7a502f2fc7c0))
* Added step in install instructions to restart terminal ([`f8e47a5`](https://github.com/algorandfoundation/algokit-cli/commit/f8e47a5ea47e6f78a39dee436381b615c794d5d5))
* Update windows install instructions ([`e9d0a9d`](https://github.com/algorandfoundation/algokit-cli/commit/e9d0a9dc2ffc7f0998978e1fa5eceb6c94a9ce52))

## v0.3.2 (2023-03-03)
### Fix
* Resolve config paths in case of folder redirection e.g. UWP python ([#191](https://github.com/algorandfoundation/algokit-cli/issues/191)) ([`0c2b291`](https://github.com/algorandfoundation/algokit-cli/commit/0c2b29179d003b17909a8dc22f655dc2b11bcdb8))

## v0.3.1 (2023-02-24)
### Fix
* Git versions prior to 2.28 no longer fail on algokit init ([#184](https://github.com/algorandfoundation/algokit-cli/issues/184)) ([`0559582`](https://github.com/algorandfoundation/algokit-cli/commit/0559582ba9fb27df9ab98b2a66606ddaeeaf6da0))
* Fix version comparison when checking for new versions ([#183](https://github.com/algorandfoundation/algokit-cli/issues/183)) ([`c272658`](https://github.com/algorandfoundation/algokit-cli/commit/c2726589b2699832844d2c67c452c01ecf742824))

## v0.3.0 (2023-02-23)
### Feature
* Add init --template-url-ref option to allow using a specific commit, tag or branch ([`5bf19a3`](https://github.com/algorandfoundation/algokit-cli/commit/5bf19a38eee8b621010956a64e2d2f9e318af9e8))
* Rename sandbox command to localnet ([`7ee55bd`](https://github.com/algorandfoundation/algokit-cli/commit/7ee55bdd5d0a87cd3aa7af1281c0867798be79ed))

### Fix
* **doctor:** Ensuring full docker version information is visible in Doctor output to improve debugging, fixes comment in #164 ([#173](https://github.com/algorandfoundation/algokit-cli/issues/173)) ([`a2c51e8`](https://github.com/algorandfoundation/algokit-cli/commit/a2c51e8018ba7b8049dc1230f7f9c1e02c24cd15))
* Handle git not being installed when running algokit ([`ccc5eb0`](https://github.com/algorandfoundation/algokit-cli/commit/ccc5eb0369892bb640914a5cf370072d28502d7f))
* **doctor:** Docker compose version parsing, fixes #164 ([`c3f4ef8`](https://github.com/algorandfoundation/algokit-cli/commit/c3f4ef80f7ca0e3da0d4841c06d81d8abe0c078d))
* Updating gitpython to resolve pip-audit vulnerability warning ([#169](https://github.com/algorandfoundation/algokit-cli/issues/169)) ([`2a10d67`](https://github.com/algorandfoundation/algokit-cli/commit/2a10d676e20f4f7d3b7d28ea24d6f5ded099d3ae))

### Documentation
* Gave context to Sandbox and PyTEAL ([`0a96e13`](https://github.com/algorandfoundation/algokit-cli/commit/0a96e13c16284dfdc8d9525310119a1351ff862a))
* Updated use cases  -> capabilities ([`ef0527a`](https://github.com/algorandfoundation/algokit-cli/commit/ef0527a87f11651efb3061711749049d36ed6d04))
* Added missing recommendation for type-safe client ([`26a6717`](https://github.com/algorandfoundation/algokit-cli/commit/26a6717e763811e0f9c23818d842ab0ea2fb2a99))
* Completed draft for architecture decision for smart contract deployment ([`40faf83`](https://github.com/algorandfoundation/algokit-cli/commit/40faf83cc97f75005f54bc344999848055f70b84))
* First draft of architecture decision for smart contract deployment ([`9e77817`](https://github.com/algorandfoundation/algokit-cli/commit/9e778170e9b4924d10b73a2fbea08accf38e3b33))
* Rename sandbox to localnet ([`aa35da7`](https://github.com/algorandfoundation/algokit-cli/commit/aa35da72f67f3dcd35adb0866a8b1ddad17fc4fe))
* Update example output for Verify installation section ([`14f6f90`](https://github.com/algorandfoundation/algokit-cli/commit/14f6f9058c3ffd69d8c3ce9b4b1160bdeb017a0b))
* Fixing incorrect description for Sandbox command ([`4bea5fa`](https://github.com/algorandfoundation/algokit-cli/commit/4bea5fa06be10a1282c1627b7979380aebc6e297))
* Fix init description in algokit.md ([#156](https://github.com/algorandfoundation/algokit-cli/issues/156)) ([`39eee95`](https://github.com/algorandfoundation/algokit-cli/commit/39eee9508f28799856692b0729bebf8b923af687))

## v0.2.0 (2023-01-16)
### Feature
* Update windows install instructions and bump version so PyPi will accept new release ([#154](https://github.com/algorandfoundation/algokit-cli/issues/154)) ([`5ff5223`](https://github.com/algorandfoundation/algokit-cli/commit/5ff52237172bddf06d3ff845b18e77c31dce9b11))

## v0.1.3 (2023-01-16)
### Documentation
* Update pipx install instructions ([`e91a06a`](https://github.com/algorandfoundation/algokit-cli/commit/e91a06a38f5b278e9ac26dfef5d7c4833633e750))

## v0.1.2 (2023-01-11)
### Documentation
* Approved ([`19eb063`](https://github.com/algorandfoundation/algokit-cli/commit/19eb063a2d8327884a5856939db4e0ea157ac26f))
* Remove --cask from Option 3 ([`cfa3b73`](https://github.com/algorandfoundation/algokit-cli/commit/cfa3b73099f6da94420bdfc9541bbce4d521993d))

## v0.1.1 (2023-01-10)
### Fix
* Adding installation documentation update re: pipx ([`75d3590`](https://github.com/algorandfoundation/algokit-cli/commit/75d359022f9fc3a3cf3ac8d21b16a449e42b1857))
* Temporarily turning off PyPi publishing while we decide on the final package name ([`6c1a2e2`](https://github.com/algorandfoundation/algokit-cli/commit/6c1a2e25d2de00a9052b7db700d8681d75b09e6a))

## v0.1.0 (2023-01-09)
### Feature
* Windows Chocolatey package ([#80](https://github.com/algorandfoundation/algokit-cli/issues/80)) ([`3f4bb04`](https://github.com/algorandfoundation/algokit-cli/commit/3f4bb04ee3ce09e7ca9ab843453f50f6a3eab98c))
* **bootstrap:** Prompt for env tokens ([#114](https://github.com/algorandfoundation/algokit-cli/issues/114)) ([`a6fe18f`](https://github.com/algorandfoundation/algokit-cli/commit/a6fe18fded0bddec91959998916fc96ac6af5008))
* **explore:** Add explore command for launching Dappflow Explorer ([#112](https://github.com/algorandfoundation/algokit-cli/issues/112)) ([`4db26b0`](https://github.com/algorandfoundation/algokit-cli/commit/4db26b08c6919fb980afa6afbb233d8793feeec1))
* **version-check:** Added check to periodically check for new releases on GitHub and inform when found ([#111](https://github.com/algorandfoundation/algokit-cli/issues/111)) ([`1772439`](https://github.com/algorandfoundation/algokit-cli/commit/1772439b02190dce159e75da110c76b200774c00))
* **doctor:** Use sys.version for fuller output (vs version_info tuple) ([#101](https://github.com/algorandfoundation/algokit-cli/issues/101)) ([`55fe4fc`](https://github.com/algorandfoundation/algokit-cli/commit/55fe4fc6984b7fecfe3e417a87cc3a1c0c0ee070))
* **completions:** Add completions support for bash and zsh ([`e7c50e5`](https://github.com/algorandfoundation/algokit-cli/commit/e7c50e58c6b371475fb6d7d2f45e85790289eadb))
* **doctor:** Tweak commands for windows ([`8f79629`](https://github.com/algorandfoundation/algokit-cli/commit/8f79629a358eb71cb28b4e739bbe445c2ec74646))
* **doctor:** Fix timezone in tests ([`d9fe303`](https://github.com/algorandfoundation/algokit-cli/commit/d9fe303934f3c093d7548228fce74c83286fa1f2))
* **doctor:** Adding tests ([`58d5708`](https://github.com/algorandfoundation/algokit-cli/commit/58d57080e53b24f60e6a4315e09e920032fdf0b0))
* **doctor:** Refactor ([`b0fe39a`](https://github.com/algorandfoundation/algokit-cli/commit/b0fe39aafe34b74bf8aebba1e9ec5f4e8048923e))
* **doctor:** Colouring output ([`6bfb300`](https://github.com/algorandfoundation/algokit-cli/commit/6bfb30093e005cb59e92aefe4714ff492ec2582b))
* **doctor:** Address pr comments and add more logic ([`e7a3090`](https://github.com/algorandfoundation/algokit-cli/commit/e7a309024d2fc5704950e1138eb44b0f242f8bdb))
* **.env file:** Add tests for default and custom values ([`58511dc`](https://github.com/algorandfoundation/algokit-cli/commit/58511dc598ac1ec4b388c45d680d9075a5650b98))
* **init:** Add `.env` file to template and passing custom values (if required) ([`e77eca8`](https://github.com/algorandfoundation/algokit-cli/commit/e77eca8bde7e5c6faa80375d6b11f44c0579be6e))
* **init:** Implemented ability to specify a commit hash so you can anchor templates from semi-trusted sources to a known good version ([#77](https://github.com/algorandfoundation/algokit-cli/issues/77)) ([`772d420`](https://github.com/algorandfoundation/algokit-cli/commit/772d420ea73a7878ef5ac9d446c79b9bfd1fbbf2))
* **sandbox:** Added `algokit sandbox console` ([`95565df`](https://github.com/algorandfoundation/algokit-cli/commit/95565dff45a6751f960ebfba64fb9ed001a67260))
* **goal:** Added algokit goal --console ([`8dd947b`](https://github.com/algorandfoundation/algokit-cli/commit/8dd947bdb4f7029bf043cb0cfebe494c17bf2729))
* **algokit:** Implementing automated, semantic versioning ([`e4859d4`](https://github.com/algorandfoundation/algokit-cli/commit/e4859d496c61ea4e4c16e9a1c910dff4e896037a))

### Fix
* **docs:** Tweaks to the reference documentation ([`6d872a1`](https://github.com/algorandfoundation/algokit-cli/commit/6d872a17bf00820c78c5e8c52caf20cd9efe9c94))
* Expression on Publish Release Packages action ([`1c08f95`](https://github.com/algorandfoundation/algokit-cli/commit/1c08f95d568b8a9264b319cf40b87b0af05a8c72))
* Attempting to isolate main branch versioning ([`5ab7089`](https://github.com/algorandfoundation/algokit-cli/commit/5ab7089a21c431eba2965f1af895eb5d4b6c6ae6))
* Improve documentation and argument values for version-prompt config ([`aee3a1a`](https://github.com/algorandfoundation/algokit-cli/commit/aee3a1a74a921659ec60e28a1b48c11d4a14d2da))
* **completions:** Explicitly use utf8 for Windows compat ([`5033f8e`](https://github.com/algorandfoundation/algokit-cli/commit/5033f8e26cd27374228a983eebb3e5c88c841958))
* **bootstrap:** Improving robustness and test coverage for bootstrap poetry command ([#89](https://github.com/algorandfoundation/algokit-cli/issues/89)) ([`a4a6823`](https://github.com/algorandfoundation/algokit-cli/commit/a4a6823b4c5015e5d0f2d361a7373820e641835d))
* **init:** Don't prompt for project name in the template - take it from the directry name in the root init command ([`fc84791`](https://github.com/algorandfoundation/algokit-cli/commit/fc847911e58bd969428c0dc6e3117501181f545d))
* Windows weird error on GitHub Actions ([`0b81808`](https://github.com/algorandfoundation/algokit-cli/commit/0b8180829be53e26b998e4c723c0d8a384d95b91))
* **git:** Update gitattributes to ensure EOL=LF ([`b13a972`](https://github.com/algorandfoundation/algokit-cli/commit/b13a97202ddeefe81c8eda5d3b058cc4a136291e))
* **build:** Run black with --check ([`e4e3875`](https://github.com/algorandfoundation/algokit-cli/commit/e4e3875b864557f86edabe2851a3f2f8f2071fa3))
* **logging:** Ensure log files get opened in UTF-8 encoding ([`bc666fe`](https://github.com/algorandfoundation/algokit-cli/commit/bc666fe7e3aed8d250d997946188f8f70b01b4d5))
* Removing deleted folder from beaker template from assert ([`8b4b46a`](https://github.com/algorandfoundation/algokit-cli/commit/8b4b46a75b6a4794d9ceb41f80f80415ef44d503))
* Temporary fix for excessive build minutes consumption and commenting out PyPi publishing code since it errors out ([`399ca0e`](https://github.com/algorandfoundation/algokit-cli/commit/399ca0eca85751c245a07abe2cbe9a73cce4172b))

### Breaking
* --ok-exit-code no longer exists on algokit bootstrap poetry, no need for copier templates to call algokit now so no need for this feature ([`a4a6823`](https://github.com/algorandfoundation/algokit-cli/commit/a4a6823b4c5015e5d0f2d361a7373820e641835d))
