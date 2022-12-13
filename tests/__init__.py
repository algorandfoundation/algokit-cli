def get_combined_verify_output(stdout: str, additional_name: str, additional_output: str) -> str:
    """Simple way to get output combined from two sources so that approval testing still works"""
    return f"""{stdout}----
{additional_name}:
----
{additional_output}"""
