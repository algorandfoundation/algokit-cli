# AlgoKit goal

AlgoKit goal command provides the user with a mechanism to run goal cli commands against the current AlgoKit sandbox.

You can explore all possible goal commands by running `algokit goal` and the results would be as follows:

```t
 GOAL is the CLI for interacting Algorand software instance. The binary 'goal' is installed alongside the algod binary and is considered an integral part of the complete installation. The binaries should be used in tandem - you should not try to use a version of goal with a different version of algod.

 Usage:
 goal [flags]
 goal [command]

 Available Commands:
 account     Control and manage Algorand accounts
 app         Manage applications
 asset       Manage assets
 clerk       Provides the tools to control transactions
 completion  Shell completion helper
 help        Help about any command
 kmd         Interact with kmd, the key management daemon
 ledger      Access ledger-related details
 license     Display license information
 logging     Control and manage Algorand logging
 network     Create and manage private, multi-node, locally-hosted networks
 node        Manage a specified algorand node
 protocols
 report
 version     The current version of the Algorand daemon (algod)
 wallet      Manage wallets: encrypted collections of Algorand account keys

 Flags:
 -d, --datadir stringArray   Data directory for the node
 -h, --help                  help for goal
 -k, --kmddir string         Data directory for kmd
 -v, --version               Display and write current build version and exit

 Use "goal [command] --help" for more information about a command.
```

For instance, running this command `algokit goal report` would result in the following:

```
 12885688322
 3.12.2.dev [rel/stable] (commit #181490e3)
 go-algorand is licensed with AGPLv3.0
 source code available at https://github.com/algorand/go-algorand

 Linux ff7828f2da17 5.15.49-linuxkit #1 SMP PREEMPT Tue Sep 13 07:51:32 UTC 2022 aarch64 GNU/Linux

 Genesis ID from genesis.json: sandnet-v1

 Last committed block: 0
 Time since last block: 0.0s
 Sync Time: 0.0s
 Last consensus protocol: future
 Next consensus protocol: future
 Round for next consensus protocol: 1
 Next consensus protocol supported: true
 Last Catchpoint:
 Genesis ID: sandnet-v1
 Genesis hash: vEg1NCh6SSXwS6O5HAfjYCCNAs4ug328s3RYMr9syBg=
```

If the sandbox `algod` docker container is not present or not running, the command will fails as follows, respectively:

```
 Error: No such container: algokit_algod
 Error: Error executing goal; ensure the Sandbox is started by executing `algokit sandbox status`
```

```
 Error response from daemon: Container 5a73961536e2c98e371465739053d174066c40d00647c8742f2bb39eb793ed7e is not running
 Error: Error executing goal; ensure the Sandbox is started by executing `algokit sandbox status`
```

For more details about `AlgoKit goal` command, please refer to [AlgoKit CLI](../cli/index.md#goal)
