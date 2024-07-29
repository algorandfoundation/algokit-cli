# Changelog

<!--next-version-placeholder-->

## v2.2.2 (2024-07-29)



## v2.2.1 (2024-07-23)

### Documentation

* Extra notes on edge case with python installation on debian ([#539](https://github.com/algorandfoundation/algokit-cli/issues/539)) ([`f358e24`](https://github.com/algorandfoundation/algokit-cli/commit/f358e24122df759585034c7e3541f5a8f4c446f1))

## v2.2.0 (2024-07-08)

### Feature

* Adding default algorand network configs to use when no .env.{network} found ([#533](https://github.com/algorandfoundation/algokit-cli/issues/533)) ([`a726756`](https://github.com/algorandfoundation/algokit-cli/commit/a726756b2f96557a8e54e1f89c4926dc206265d3))

### Fix

* Given that .copier-answers.yml is now expected at .algokit folder, improve defaults lookup ([#535](https://github.com/algorandfoundation/algokit-cli/issues/535)) ([`5d319d3`](https://github.com/algorandfoundation/algokit-cli/commit/5d319d323a5a38e77d65895048e6a2a30e8b64d8))

## v2.1.4 (2024-06-27)

### Fix

* Filter null values from asset metadata ([#529](https://github.com/algorandfoundation/algokit-cli/issues/529)) ([`05411d6`](https://github.com/algorandfoundation/algokit-cli/commit/05411d638c0ef7600df3428a5da74f8666d226a7))

## v2.1.3 (2024-06-25)

### Fix

* Some localnet proxy tweaks ([#526](https://github.com/algorandfoundation/algokit-cli/issues/526)) ([`2c7999d`](https://github.com/algorandfoundation/algokit-cli/commit/2c7999daefc5071dd89a6dcdc2f0a3f7f3ef819b))

## v2.1.2 (2024-06-20)

### Fix

* Localnet status and proxy dns issue ([#525](https://github.com/algorandfoundation/algokit-cli/issues/525)) ([`a0c5bc6`](https://github.com/algorandfoundation/algokit-cli/commit/a0c5bc69e71fc64864f9f10ddd92f8c967f03416))
* Add localnet proxy to add Access-Control-Allow-Private-Network header ([#523](https://github.com/algorandfoundation/algokit-cli/issues/523)) ([`2267e9e`](https://github.com/algorandfoundation/algokit-cli/commit/2267e9e2ff2b707dc246021578b8dbc6bd43a021))

### Documentation

* Moving descriptions of workspace vs standalone to project.md ([#522](https://github.com/algorandfoundation/algokit-cli/issues/522)) ([`946c53a`](https://github.com/algorandfoundation/algokit-cli/commit/946c53a3d90fad983a21856c0cad969f37d90e6f))
* Minor revamp in project/config docs ([#521](https://github.com/algorandfoundation/algokit-cli/issues/521)) ([`872f6b1`](https://github.com/algorandfoundation/algokit-cli/commit/872f6b1dd01f843255fa2b76cb7e857c23aee4aa))

## v2.1.1 (2024-06-17)

### Fix

* Ensure utf-8 is used as part of cli animate method invocation (windows compatibility) ([#518](https://github.com/algorandfoundation/algokit-cli/issues/518)) ([`ba9e090`](https://github.com/algorandfoundation/algokit-cli/commit/ba9e0902880298beb6a883096d26b25e77d31422))

## v2.1.0 (2024-06-12)

### Feature

* GitHub Codespaces support in LocalNet command group ([#456](https://github.com/algorandfoundation/algokit-cli/issues/456)) ([`7eeaead`](https://github.com/algorandfoundation/algokit-cli/commit/7eeaeadc577dd12fa93c87cae18da497770d6f35))

### Documentation

* Updated docs to include updated links for project features ([`7c56b18`](https://github.com/algorandfoundation/algokit-cli/commit/7c56b181d984f3301e2abc59ea91128f2845ec66))

## v2.0.6 (2024-05-22)

### Fix

* Remove ConsensusProtocol = future; unpin algod ([#505](https://github.com/algorandfoundation/algokit-cli/issues/505)) ([`55fbda5`](https://github.com/algorandfoundation/algokit-cli/commit/55fbda511310c094675dca7ff45131006083df66))

## v2.0.5 (2024-05-21)

### Fix

* Pin localnet algod container to fix conduit issue in latest algod ([#502](https://github.com/algorandfoundation/algokit-cli/issues/502)) ([`6e760e9`](https://github.com/algorandfoundation/algokit-cli/commit/6e760e9c887187f053ea6a11b969ddc8cda3fb6a))

## v2.0.4 (2024-05-20)

### Fix

* Task transfer on rekeyed account and update dependencies ([#498](https://github.com/algorandfoundation/algokit-cli/issues/498)) ([`8592cbf`](https://github.com/algorandfoundation/algokit-cli/commit/8592cbff4b9c45b4394eb853761255a8d11b7510))

### Documentation

* Add troubleshooting section ([#496](https://github.com/algorandfoundation/algokit-cli/issues/496)) ([`ef1a504`](https://github.com/algorandfoundation/algokit-cli/commit/ef1a5046a7b3ba6ddf22e65a4b1fe7868196e625))
* Refine quick start ([#487](https://github.com/algorandfoundation/algokit-cli/issues/487)) ([`1964dec`](https://github.com/algorandfoundation/algokit-cli/commit/1964decd340a7847005cab4be408f6273fd5cb53))
* Remove spelling mistake in intro.md instalation docs ([#491](https://github.com/algorandfoundation/algokit-cli/issues/491)) ([`70c55e0`](https://github.com/algorandfoundation/algokit-cli/commit/70c55e050caf4309c76ae5aae1dd7a284db93382))

## v2.0.3 (2024-04-16)

### Fix

* Remove deprecated version from localnet compose file ([#476](https://github.com/algorandfoundation/algokit-cli/issues/476)) ([`4a3b1f0`](https://github.com/algorandfoundation/algokit-cli/commit/4a3b1f0c2dec5d03d12b42617ff546bd94d1da57))

### Documentation

* Minor refinements in npm min version spec ([#474](https://github.com/algorandfoundation/algokit-cli/issues/474)) ([`a887430`](https://github.com/algorandfoundation/algokit-cli/commit/a8874304319efc3449336a4bbb817471613d6743))

## v2.0.2 (2024-04-02)

### Fix

* Pin pyyaml-include transitive dep ([#472](https://github.com/algorandfoundation/algokit-cli/issues/472)) ([`970536c`](https://github.com/algorandfoundation/algokit-cli/commit/970536cb7246fcaf6b84aacda95a74f8ff9bc285))

### Documentation

* Adding node.js to prerequisites for installation as FYI ([`8147173`](https://github.com/algorandfoundation/algokit-cli/commit/8147173ba827ac3be4c4dec28a97abc16abbd2cf))

## v2.0.1 (2024-03-29)

### Documentation

* Few tweaks post release ([#465](https://github.com/algorandfoundation/algokit-cli/issues/465)) ([`a4a5645`](https://github.com/algorandfoundation/algokit-cli/commit/a4a5645c11790eba1162f7d80ade26fe40f83944))

## v2.0.0 (2024-03-27)

### Feature

* Algokit-cli v2 ([#462](https://github.com/algorandfoundation/algokit-cli/issues/462)) ([`182c449`](https://github.com/algorandfoundation/algokit-cli/commit/182c449544e4a23e17919e9629dfdc5ddbf399a5))
* LocalNet should run as an archival node so that you can access all blocks (useful for testing) ([#461](https://github.com/algorandfoundation/algokit-cli/issues/461)) ([`794cccc`](https://github.com/algorandfoundation/algokit-cli/commit/794cccce2bb4aeccfe56813af754406b87ba5112))

### Breaking

* 2.0 release ([`182c449`](https://github.com/algorandfoundation/algokit-cli/commit/182c449544e4a23e17919e9629dfdc5ddbf399a5))

## v1.13.1 (2024-03-20)

### Fix

* Create the npm dir in the app data directory on windows, as npx needs it ([#458](https://github.com/algorandfoundation/algokit-cli/issues/458)) ([`3195a1c`](https://github.com/algorandfoundation/algokit-cli/commit/3195a1c8cd21835d04a472d0d156ca08ef9030ec))

## v1.13.0 (2024-03-13)

### Feature

* Add command to compile python to TEAL with Puyapy ([`1030799`](https://github.com/algorandfoundation/algokit-cli/commit/10307990a07fd3fa8ba60f6886f5b4be722dc065))

### Fix

* Adjust how we run npx, so it supports all windows versions ([#454](https://github.com/algorandfoundation/algokit-cli/issues/454)) ([`a997953`](https://github.com/algorandfoundation/algokit-cli/commit/a997953871251b0f1dfed3ad6e2cb8901c2c5cd3))

### Documentation

* Ref commit for snapcraft ([#452](https://github.com/algorandfoundation/algokit-cli/issues/452)) ([`0ab21bc`](https://github.com/algorandfoundation/algokit-cli/commit/0ab21bcd2b7a6d188791a3480eab7fe1b885667d))
* Update playground init docs ([#451](https://github.com/algorandfoundation/algokit-cli/issues/451)) ([`1a15d5d`](https://github.com/algorandfoundation/algokit-cli/commit/1a15d5def4e610f0b10a41918f5d4055dea19efc))
* Change last name in 2023-07-19_advanced_generate_command.md ([#448](https://github.com/algorandfoundation/algokit-cli/issues/448)) ([`8df02df`](https://github.com/algorandfoundation/algokit-cli/commit/8df02df981c0b68cfea2a4dc4698759d5e393974))

## v1.12.3 (2024-03-06)

### Fix

* Path resolution to ensure git is initialized at workspace level ([#447](https://github.com/algorandfoundation/algokit-cli/issues/447)) ([`4fa1eaf`](https://github.com/algorandfoundation/algokit-cli/commit/4fa1eafe604129bb0595d0774ee4eb1484d3c13b))

### Documentation

* Updating dockerhub links on localnet docs ([#445](https://github.com/algorandfoundation/algokit-cli/issues/445)) ([`9d4df31`](https://github.com/algorandfoundation/algokit-cli/commit/9d4df31abe1de07909c7d03de1dc2dcc4334d7dc))

## v1.12.2 (2024-03-01)

### Fix

* Algod container proper SIGTERM handling ([#438](https://github.com/algorandfoundation/algokit-cli/issues/438)) ([`1a654ca`](https://github.com/algorandfoundation/algokit-cli/commit/1a654ca6b1519beda0a1d23fefb9673591cd5eea))

### Documentation

* Update named localnet documents on config file locations ([#444](https://github.com/algorandfoundation/algokit-cli/issues/444)) ([`643ab01`](https://github.com/algorandfoundation/algokit-cli/commit/643ab011bae488d24c18e8351e29de439a31c24e))
* Minor patch in the badge ([#440](https://github.com/algorandfoundation/algokit-cli/issues/440)) ([`7d82db0`](https://github.com/algorandfoundation/algokit-cli/commit/7d82db08a127ef486f31687affca184f1229039b))

## v1.12.1 (2024-02-26)



## v1.12.0 (2024-02-26)

### Feature

* Init wizard v2 ([#415](https://github.com/algorandfoundation/algokit-cli/issues/415)) ([`55d6922`](https://github.com/algorandfoundation/algokit-cli/commit/55d6922e5ae1c8b1f6e42a910f387739344f53a5))

### Fix

* Upload windows artifact to release ([#429](https://github.com/algorandfoundation/algokit-cli/issues/429)) ([`d922a49`](https://github.com/algorandfoundation/algokit-cli/commit/d922a493f8f92c61ae56df0043a356f8fd523f4d))

## v1.11.4 (2024-02-19)

### Fix

* Fix issue of goal command interacting with filename containing dot ([#424](https://github.com/algorandfoundation/algokit-cli/issues/424)) ([`22ece81`](https://github.com/algorandfoundation/algokit-cli/commit/22ece811af63c69734169029db1a477730d1e0ad))

### Documentation

* Adr init wizard v2 and related improvements ([#411](https://github.com/algorandfoundation/algokit-cli/issues/411)) ([`8c5445a`](https://github.com/algorandfoundation/algokit-cli/commit/8c5445a558e503590fee636a9e5826026a5aacaf))

## v1.11.3 (2024-02-08)

### Fix

* Binary execution mode compatibility ([#406](https://github.com/algorandfoundation/algokit-cli/issues/406)) ([`5cb9b1f`](https://github.com/algorandfoundation/algokit-cli/commit/5cb9b1f8e1f7fc3cc7114cba5cef78c9fcc7df95))

### Documentation

* ADR - native binaries distribution via snap/winget/brew ([#404](https://github.com/algorandfoundation/algokit-cli/issues/404)) ([`b7301bf`](https://github.com/algorandfoundation/algokit-cli/commit/b7301bf7ef4d776aa0b0b16e061f2a546780cabb))
* Improve onboarding experience  ([`a4d6bb5`](https://github.com/algorandfoundation/algokit-cli/commit/a4d6bb502ed5bbfe87682ea863590c47393aed6a))

## v1.11.2 (2024-02-01)

### Fix

* Bump algokit-client-generator to 1.1.1 ([#403](https://github.com/algorandfoundation/algokit-cli/issues/403)) ([`28dd709`](https://github.com/algorandfoundation/algokit-cli/commit/28dd709314b5557b1351a6db6f2305e168438d28))

## v1.11.1 (2024-01-30)

### Fix

* Patching tealer 3.12 compatibility ([#401](https://github.com/algorandfoundation/algokit-cli/issues/401)) ([`05ea554`](https://github.com/algorandfoundation/algokit-cli/commit/05ea554fcad9fdf3eb5b038231eaf1155f9e5ce7))
* Patch cd pipeline merge conflict ([#399](https://github.com/algorandfoundation/algokit-cli/issues/399)) ([`806d0e2`](https://github.com/algorandfoundation/algokit-cli/commit/806d0e269f9e621c3ed8f47a8fd3d4e24a5a366c))

## v1.11.0 (2024-01-28)

### Feature

* Upgrading to latest version of algokit-client-generator-ts ([#398](https://github.com/algorandfoundation/algokit-cli/issues/398)) ([`1b6773b`](https://github.com/algorandfoundation/algokit-cli/commit/1b6773b1bbfcc5191e0da86af4e445de29ae3058))

### Documentation

* Adr on native binaries ([#395](https://github.com/algorandfoundation/algokit-cli/issues/395)) ([`42f61d1`](https://github.com/algorandfoundation/algokit-cli/commit/42f61d1a5ffdb411947a7581a36df1ed53786a25))

## v1.10.0 (2024-01-24)

### Feature

* Adding algokit analyze - perform static analysis with tealer integration ([#370](https://github.com/algorandfoundation/algokit-cli/issues/370)) ([`3e56a4b`](https://github.com/algorandfoundation/algokit-cli/commit/3e56a4b4e1f59d747cd7eb4e2cfea8b8d9c7c670))

### Fix

* Installation process for tealer (windows compatibility) ([#396](https://github.com/algorandfoundation/algokit-cli/issues/396)) ([`971aff4`](https://github.com/algorandfoundation/algokit-cli/commit/971aff46a6b5502135122bff951ee2d9c15fa80f))

## v1.9.3 (2024-01-11)



## v1.9.2 (2024-01-09)

### Fix

* Run localnet on goal command ([#380](https://github.com/algorandfoundation/algokit-cli/issues/380)) ([`5a06ddc`](https://github.com/algorandfoundation/algokit-cli/commit/5a06ddce965716ea4fb47a1d8a19b8cb65d17b77))

### Documentation

* Update the list of AlgoKit CLI high-level features in the docs ([`8e3b827`](https://github.com/algorandfoundation/algokit-cli/commit/8e3b8273d65a1fbcd7e3bf600b96c82500eef538))

## v1.9.1 (2023-12-29)



## v1.9.0 (2023-12-29)

### Feature

* Add support for a customisable named localnet ([#373](https://github.com/algorandfoundation/algokit-cli/issues/373)) ([`41c4946`](https://github.com/algorandfoundation/algokit-cli/commit/41c4946fce6894a9f6548bf4a2cbdd499dec4cb4))

## v1.8.2 (2023-12-20)



## v1.8.1 (2023-12-19)

### Fix

* Update multiformats version as it needs to be in sync with multiformats-config ([#372](https://github.com/algorandfoundation/algokit-cli/issues/372)) ([`67a5966`](https://github.com/algorandfoundation/algokit-cli/commit/67a59662c67d7f1d2e5eedeb1e8d62289e0ad5ac))

## v1.8.0 (2023-12-14)

### Feature

* Update generators to support generating typed clients with simulate functionality ([#368](https://github.com/algorandfoundation/algokit-cli/issues/368)) ([`90c876b`](https://github.com/algorandfoundation/algokit-cli/commit/90c876b819f4f9bba040e8630584cedc13678f5a))
* Use Pinata ipfs instead of web3.storage ([#367](https://github.com/algorandfoundation/algokit-cli/issues/367)) ([`fc7ee5d`](https://github.com/algorandfoundation/algokit-cli/commit/fc7ee5d36c09b91251c46ab2be670015ac106164))

### Fix

* Replacing Yaspin with Simplified Spinners for Windows Systems ([#369](https://github.com/algorandfoundation/algokit-cli/issues/369)) ([`e12311e`](https://github.com/algorandfoundation/algokit-cli/commit/e12311e3be087e78aed092dd9b2670f8183afea3))

## v1.7.3 (2023-12-08)

### Fix

* Adding confirmation prompt prior to execution of algokit generators ([#366](https://github.com/algorandfoundation/algokit-cli/issues/366)) ([`eeb5bae`](https://github.com/algorandfoundation/algokit-cli/commit/eeb5bae18c4ffb2384f92627d19a4308a46bfdf0))

## v1.7.2 (2023-12-04)

### Fix

* Removing outdated reference to `algokit sandbox` command ([#362](https://github.com/algorandfoundation/algokit-cli/issues/362)) ([`e6cd395`](https://github.com/algorandfoundation/algokit-cli/commit/e6cd395bf600485be6edbe4e68c9ba4885598000))
* Fixing Localnet status ([#365](https://github.com/algorandfoundation/algokit-cli/issues/365)) ([`8277572`](https://github.com/algorandfoundation/algokit-cli/commit/8277572db58d14bfcbda5e8bda18673d536b84a0))
* Update vulnerable package dependency versions ([#361](https://github.com/algorandfoundation/algokit-cli/issues/361)) ([`450e02d`](https://github.com/algorandfoundation/algokit-cli/commit/450e02ddba02c98d9c8fe8a6baedaf84ef7e9460))

## v1.7.1 (2023-11-22)

### Fix

* Hotfixing conduit path for localnet windows compatibility ([#360](https://github.com/algorandfoundation/algokit-cli/issues/360)) ([`897e335`](https://github.com/algorandfoundation/algokit-cli/commit/897e33554252083ed2b0d8a18a49969ef82a097b))

## v1.7.0 (2023-11-22)

### Feature

* Migrating localnet to latest indexer v3.x images ([#351](https://github.com/algorandfoundation/algokit-cli/issues/351)) ([`04ef300`](https://github.com/algorandfoundation/algokit-cli/commit/04ef3008366028118358e342c0e83e08f3c095ba))

## v1.6.3 (2023-11-14)

### Fix

* Correctly convert list of tuple to dictionary ([#353](https://github.com/algorandfoundation/algokit-cli/issues/353)) ([`ad71719`](https://github.com/algorandfoundation/algokit-cli/commit/ad717190f5822964d726555b7d7f8e1f5453cdfa))

## v1.6.2 (2023-11-10)

### Fix

* Support detect ~/test.txt as valid goal paths ([#347](https://github.com/algorandfoundation/algokit-cli/issues/347)) ([`8ac5ec5`](https://github.com/algorandfoundation/algokit-cli/commit/8ac5ec5843cf243fb051e504d821b719c37cbe38))
* Support the multiple file outputs of goal clerk split ([#346](https://github.com/algorandfoundation/algokit-cli/issues/346)) ([`fd9cd54`](https://github.com/algorandfoundation/algokit-cli/commit/fd9cd54137ca40595220fe916799eb682971387b))

## v1.6.1 (2023-11-08)

### Documentation

* Typo resolved ([#341](https://github.com/algorandfoundation/algokit-cli/issues/341)) ([`e71ff96`](https://github.com/algorandfoundation/algokit-cli/commit/e71ff964a9879a30689be049d3af3ec3002c3198))
* Fixing typo in docs ([#339](https://github.com/algorandfoundation/algokit-cli/issues/339)) ([`e8eba42`](https://github.com/algorandfoundation/algokit-cli/commit/e8eba421b32767ae9d57d8bbe75f86c268f5cbf7))

## v1.6.0 (2023-10-26)

### Feature

* Algokit tasks - 1.6.0 release ([#334](https://github.com/algorandfoundation/algokit-cli/issues/334)) ([`e35f4f8`](https://github.com/algorandfoundation/algokit-cli/commit/e35f4f836f5433449a6685d1aeca01b8fd416fe2))

### Fix

* Pinning aiohttp beta to hotfix 3.12 support ([#338](https://github.com/algorandfoundation/algokit-cli/issues/338)) ([`96fc7e6`](https://github.com/algorandfoundation/algokit-cli/commit/96fc7e668c3a5b4fb9f00216ee6278b8ded1cf87))

## v1.5.3 (2023-10-23)



## v1.5.2 (2023-10-20)

### Fix

* Docker compose ps parsing for version >= 2.21 ([#336](https://github.com/algorandfoundation/algokit-cli/issues/336)) ([`06ba5e9`](https://github.com/algorandfoundation/algokit-cli/commit/06ba5e908a879a45ab793ffbc6c9436eeeb5b370))

### Documentation

* Updating docs for the issue on python 3.12 ([#332](https://github.com/algorandfoundation/algokit-cli/issues/332)) ([`288b561`](https://github.com/algorandfoundation/algokit-cli/commit/288b5617f284b5135f272cdb4c1c160c2aa6fc33))

## v1.5.1 (2023-10-17)



## v1.5.0 (2023-10-04)

### Feature

* Algokit `dispenser` ([#309](https://github.com/algorandfoundation/algokit-cli/issues/309)) ([`6b7a514`](https://github.com/algorandfoundation/algokit-cli/commit/6b7a51421d42d90192c866ff7ce7307a4b180b9c))

### Documentation

* Explicit reference on how to obtain the dispenser address ([#321](https://github.com/algorandfoundation/algokit-cli/issues/321)) ([`d7db09c`](https://github.com/algorandfoundation/algokit-cli/commit/d7db09c50e41ec8840f908f6a3db223622562269))

## v1.4.2 (2023-09-29)

### Documentation

* Adding tealscript template ([#318](https://github.com/algorandfoundation/algokit-cli/issues/318)) ([`a855530`](https://github.com/algorandfoundation/algokit-cli/commit/a855530923a308e3826d4203b851cfbc49420bed))
* Fixed links to tutorials ([`8207043`](https://github.com/algorandfoundation/algokit-cli/commit/820704305d7bb66d3f5e7c6627e53594a74f9e45))

## v1.4.1 (2023-08-21)

### Fix

* Localnet displays a warning when image is out of date ([#308](https://github.com/algorandfoundation/algokit-cli/issues/308)) ([`be5a5df`](https://github.com/algorandfoundation/algokit-cli/commit/be5a5df0883b378a0dd889b9996ff68850df5698))
* Adding fixes to allow working with local filesystem files when interacting with algokit goal commands ([#304](https://github.com/algorandfoundation/algokit-cli/issues/304)) ([`caca2b5`](https://github.com/algorandfoundation/algokit-cli/commit/caca2b59b07817648ae7d8f208fe02f895cee92e))

## v1.4.0 (2023-08-14)

### Feature

* Advanced algokit generate command ([#306](https://github.com/algorandfoundation/algokit-cli/issues/306)) ([`0381862`](https://github.com/algorandfoundation/algokit-cli/commit/038186239c6787b0e80d49ea6a0e5e4135ce4240))

## v1.3.0 (2023-08-01)

### Feature

* Add new "deploy" command to execute user/template defined logic to deploy smart contracts to an Algorand network ([#295](https://github.com/algorandfoundation/algokit-cli/issues/295)) ([`6673f80`](https://github.com/algorandfoundation/algokit-cli/commit/6673f8062989172674471056baf1e8a7f34753b7))

### Fix

* Pip-audit dependencies ([#307](https://github.com/algorandfoundation/algokit-cli/issues/307)) ([`142dba3`](https://github.com/algorandfoundation/algokit-cli/commit/142dba3651731003936c32ff9a6144c58289c829))
* Handle deploy commands on windows that are actually `.cmd` files or similar ([#303](https://github.com/algorandfoundation/algokit-cli/issues/303)) ([`17791c7`](https://github.com/algorandfoundation/algokit-cli/commit/17791c7ca7f5aabe510b1dcaa1d09b9ed403233b))

### Documentation

* Advanced algokit generate command ADR ([#305](https://github.com/algorandfoundation/algokit-cli/issues/305)) ([`cb0ac17`](https://github.com/algorandfoundation/algokit-cli/commit/cb0ac17e9afda66e74ae2c63d0729c3b34f2a4b7))
* Adding algokit template documentation ([#300](https://github.com/algorandfoundation/algokit-cli/issues/300)) ([`6e19743`](https://github.com/algorandfoundation/algokit-cli/commit/6e19743bacf3856f91e2610cff58676a17e99deb))

## v1.2.0 (2023-07-04)

### Feature

* Detecting whether opening folder contains *.code-workspace file ([#294](https://github.com/algorandfoundation/algokit-cli/issues/294)) ([`e902d55`](https://github.com/algorandfoundation/algokit-cli/commit/e902d55a6077d60eb3c5b3fa809e1ba80b61b37e))
* Adding react and fullstack templates ([#291](https://github.com/algorandfoundation/algokit-cli/issues/291)) ([`5af81f1`](https://github.com/algorandfoundation/algokit-cli/commit/5af81f100b16ce1281980ff3067df648fb5c9b4f))

### Fix

* Hotfixing a bug that is caused by pydantic v2 being installed as a copier dependency ([#297](https://github.com/algorandfoundation/algokit-cli/issues/297)) ([`31b580b`](https://github.com/algorandfoundation/algokit-cli/commit/31b580b2364e123fd81fdab14da93b704ea4bdda))
* Update algokit-client-generators ([#293](https://github.com/algorandfoundation/algokit-cli/issues/293)) ([`cf0f46f`](https://github.com/algorandfoundation/algokit-cli/commit/cf0f46ffba9c3a33e75bad56195589bed3c5dc3a))

### Documentation

* Switching to more reliable visitors badge provider ([`51dce8b`](https://github.com/algorandfoundation/algokit-cli/commit/51dce8be83f0b72765ddffc9ea67886235d83fbb))
* Fixing underline caused by whitespace in html tags on readme ([`f824596`](https://github.com/algorandfoundation/algokit-cli/commit/f824596d845fce31fe6d32fd9dc14fa0086746ca))

## v1.1.6 (2023-06-21)

### Fix

* Increase timeout when doing algod health check ([#290](https://github.com/algorandfoundation/algokit-cli/issues/290)) ([`2b39970`](https://github.com/algorandfoundation/algokit-cli/commit/2b39970c53d358050639fbcb02ab6e99c1808d98))

### Documentation

* Adding readme assets ([`e300fa9`](https://github.com/algorandfoundation/algokit-cli/commit/e300fa929850b1f3677cb3545b8f284e8f3a7ef9))

## v1.1.5 (2023-06-15)

### Fix

* Update typescript algokit-client-generator to 2.2.1 ([#286](https://github.com/algorandfoundation/algokit-cli/issues/286)) ([`bbb86b4`](https://github.com/algorandfoundation/algokit-cli/commit/bbb86b4049ed6d81f3bd73a0e207deae8f200459))

## v1.1.4 (2023-06-14)

### Fix

* Update typescript algokit-client-generator ([#284](https://github.com/algorandfoundation/algokit-cli/issues/284)) ([`37d5082`](https://github.com/algorandfoundation/algokit-cli/commit/37d5082f86fd3db43ebb7c96558a484267883067))

## v1.1.3 (2023-06-13)

### Fix

* Update python algokit-client-generator ([#283](https://github.com/algorandfoundation/algokit-cli/issues/283)) ([`5330baa`](https://github.com/algorandfoundation/algokit-cli/commit/5330baaf8617a1b5b640d5efecdcbe05fd2ea2a3))

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
