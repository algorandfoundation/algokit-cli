from pytest import TempPathFactory

from tests.utils.approvals import verify
from tests.utils.click_invoker import invoke

# Default algokit beaker hello world contract
# transpiled to TEAL
TEAL_FILE_CONTENT = """
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


def test_analyze_single_file(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {teal_file}", input="y\n")

    assert result.exit_code == 1
    result.output = result.output.replace(str(teal_file), "dummy/path/dummy.teal")
    verify(result.output)


def test_analyze_multiple_files(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_folder = cwd / "dummy_contracts"
    teal_folder.mkdir()
    for i in range(5):
        teal_file = teal_folder / f"dummy_{i}.teal"
        teal_file.write_text(TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {teal_folder}", input="y\n")

    assert result.exit_code == 1
    for i in range(5):
        result.output = result.output.replace(str(teal_folder / f"dummy_{i}.teal"), f"dummy_contracts/dummy_{i}.teal")
    verify(result.output)


def test_analyze_multiple_files_recursive(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_root_folder = cwd / "dummy_contracts"
    teal_folder = teal_root_folder / "subfolder"
    teal_folder.mkdir(parents=True)
    for i in range(5):
        teal_file = teal_folder / f"dummy_{i}.teal"
        teal_file.write_text(TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {teal_folder} --recursive", input="y\n")

    assert result.exit_code == 1
    for i in range(5):
        result.output = result.output.replace(
            str(teal_folder / f"dummy_{i}.teal"), f"dummy_contracts/subfolder/dummy_{i}.teal"
        )
    verify(result.output)


def test_exclude_vulnerabilities(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(TEAL_FILE_CONTENT)
    result = invoke(
        f"task analyze {teal_file} --exclude is-deletable --exclude rekey-to --exclude missing-fee-check",
        input="y\n",
    )

    assert result.exit_code == 0
    result.output = result.output.replace(str(teal_file), "dummy/path/dummy.teal")
    verify(result.output)


def test_analyze_skipping_tmpl_vars(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(
        TEAL_FILE_CONTENT.replace("pushint 4 // UpdateApplication", "pushint TMPL_VAR // UpdateApplication")
    )
    result = invoke(f"task analyze {teal_file}", input="y\n")

    assert result.exit_code == 0
    result.output = result.output.replace(str(teal_file), "dummy/path/dummy.teal")
    verify(result.output)


def test_analyze_abort_disclaimer(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.touch()
    result = invoke(f"task analyze {teal_file}", input="n\n")

    assert result.exit_code == 1
    verify(result.output)


def test_analyze_error_in_tealer(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.touch()
    result = invoke(f"task analyze {teal_file}", input="y\n")

    assert result.exit_code == 1
    result.output = result.output.replace(str(teal_file), "dummy/path/dummy.teal")
    verify(result.output)


def test_analyze_baseline_flag(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    teal_file = cwd / "dummy.teal"
    teal_file.write_text(TEAL_FILE_CONTENT)
    result = invoke(f"task analyze {teal_file} --baseline", input="y\n")
    assert result.exit_code == 0

    teal_file.write_text("\n#pragma version 8\nint 1\nreturn\n")
    result = invoke(f"task analyze {teal_file} --baseline", input="y\n")
    assert result.exit_code == 1
    result.output = result.output.replace(str(teal_file), "dummy/path/dummy.teal")
    verify(result.output)
