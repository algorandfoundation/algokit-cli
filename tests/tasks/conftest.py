from algokit_utils import Account
from algosdk import transaction

DUMMY_SUGGESTED_PARAMS = transaction.SuggestedParams(  # type: ignore[no-untyped-call]
    fee=0,
    first=33652328,
    last=33653328,
    gen="testnet-v1.0",
    gh="SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
    min_fee=1000,
    flat_fee=True,
    consensus_version="https://github.com/algorandfoundation/specs/tree/abd3d4823c6f77349fc04c3af7b1e99fe4df699f",
)
DUMMY_ACCOUNT = Account(
    private_key="iLsfFiRDwi0ijFdvdyO1PGkYxooOanbJSgpJ4pPKjKZluk70pvuPX4dYD1Jir85uZP+AImM/8SBmdPRpBSTFAg==",
    address="MW5E55FG7OHV7B2YB5JGFL6ONZSP7ABCMM77CIDGOT2GSBJEYUBOF3UYKA",
)
DUMMY_TEAL_FILE_CONTENT = """
#pragma version 8
intcblock 0 1
bytecblock 0x
txn NumAppArgs
intc_0 // 0
==
bnz main_l4
txna ApplicationArgs 0
pushbytes 0x02bece11 // "hello(string)string"
==
bnz main_l3
err
main_l3:
txn OnCompletion
intc_0 // NoOp
==
txn ApplicationID
intc_0 // 0
!=
&&
assert
callsub hellocaster_3
intc_1 // 1
return
main_l4:
txn OnCompletion
intc_0 // NoOp
==
bnz main_l10
txn OnCompletion
pushint 4 // UpdateApplication
==
bnz main_l9
txn OnCompletion
pushint 5 // DeleteApplication
==
bnz main_l8
err
main_l8:
txn ApplicationID
intc_0 // 0
!=
assert
callsub delete_1
intc_1 // 1
return
main_l9:
txn ApplicationID
intc_0 // 0
!=
assert
callsub update_0
intc_1 // 1
return
main_l10:
txn ApplicationID
intc_0 // 0
==
assert
intc_1 // 1
return

// update
update_0:
proto 0 0
txn Sender
global CreatorAddress
==
// unauthorized
assert
intc_0 // 0
return

// delete
delete_1:
proto 0 0
txn Sender
global CreatorAddress
==
// unauthorized
assert
intc_0 // 0
// Check app is deletable
assert
retsub

// hello
hello_2:
proto 1 1
bytec_0 // ""
pushbytes 0x48656c6c6f2c20 // "Hello, "
frame_dig -1
extract 2 0
concat
frame_bury 0
frame_dig 0
len
itob
extract 6 0
frame_dig 0
concat
frame_bury 0
retsub

// hello_caster
hellocaster_3:
proto 0 0
bytec_0 // ""
dup
txna ApplicationArgs 1
frame_bury 1
frame_dig 1
callsub hello_2
frame_bury 0
pushbytes 0x151f7c75 // 0x151f7c75
frame_dig 0
concat
log
retsub
"""
