import click
import pytest
from _pytest.tmpdir import TempPathFactory
from approvaltests.scrubbers.scrubbers import Scrubber
from prompt_toolkit.input import PipeInput

from tests import get_combined_verify_output
from tests.utils.approvals import TokenScrubber, combine_scrubbers, verify
from tests.utils.click_invoker import invoke


def make_output_scrubber(**tokens: str) -> Scrubber:
    return combine_scrubbers(click.unstyle, TokenScrubber(tokens=tokens))


def test_bootstrap_env_no_files(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_env_dotenv_exists(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env").touch()

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(result.output)


def test_bootstrap_env_dotenv_missing_template_exists(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").write_text("env_template_contents")

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(get_combined_verify_output(result.output, ".env", (cwd / ".env").read_text("utf-8")))


@pytest.mark.usefixtures("mock_questionary_input")
def test_bootstrap_env_dotenv_with_values(tmp_path_factory: TempPathFactory) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").write_text(
        """
TOKEN_1=123
# comment for token 2 - you should enter a valid value
# another comment
TOKEN_2_WITH_MULTI_LINES_COMMENT=test
TOKEN_3=test value with spaces

TOKEN_4_WITH_NO_EQUALS_SIGN
# another comment
TOKEN_5_SPECIAL_CHAR=*  
"""  # noqa: W291
    )

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(get_combined_verify_output(result.output, ".env", (cwd / ".env").read_text("utf-8")))


@pytest.mark.mock_platform_system("Darwin")
def test_bootstrap_env_dotenv_different_prompt_scenarios(
    tmp_path_factory: TempPathFactory, mock_questionary_input: PipeInput
) -> None:
    cwd = tmp_path_factory.mktemp("cwd")
    (cwd / ".env.template").write_text(
        """
TOKEN_1=123

# comment for token 2 - you should enter a valid value
# another comment
TOKEN_2_WITH_MULTI_LINES_COMMENT=
TOKEN_3=test value

TOKEN_4_WITH_SPACES =               
TOKEN_5_WITHOUT_COMMENT=
TOKEN_WITH_NO_EQUALS_SIGN
# another comment
TOKEN_6_EMPTY_WITH_COMMENT=
TOKEN_7_VALUE_WILL_BE_EMPTY=
TOKEN_8 = value with spaces
TOKEN_8_SPECIAL_CHAR=*  
"""  # noqa: W291
    )

    # provide values for tokens
    mock_questionary_input.send_text("test value for TOKEN_2_WITH_MULTI_LINES_COMMENT")
    mock_questionary_input.send_text("\n")  # enter
    mock_questionary_input.send_text("test value for TOKEN_4_WITH_SPACES")
    mock_questionary_input.send_text("\n")  # enter
    mock_questionary_input.send_text("test value for TOKEN_5_WITHOUT_COMMENT")
    mock_questionary_input.send_text("\n")  # enter
    mock_questionary_input.send_text("test value for TOKEN_6_EMPTY_WITH_COMMENT")
    mock_questionary_input.send_text("\n")  # enter
    mock_questionary_input.send_text("")  # Empty value for TOKEN_7_VALUE_WILL_BE_EMPTY
    mock_questionary_input.send_text("\n")  # enter

    result = invoke(
        "bootstrap env",
        cwd=cwd,
    )

    assert result.exit_code == 0
    verify(
        get_combined_verify_output(result.output, ".env", (cwd / ".env").read_text("utf-8")),
        scrubber=make_output_scrubber(),
    )
