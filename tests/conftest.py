import os

from approvaltests import Reporter, reporters, set_default_reporter
from approvaltests.reporters.generic_diff_reporter_config import create_config
from approvaltests.reporters.generic_diff_reporter_factory import GenericDiffReporter

if os.getenv("CI", ""):
    set_default_reporter(reporters.PythonNativeReporter())
else:

    default_reporters: list[Reporter] = (
        [
            GenericDiffReporter(
                create_config(
                    [
                        os.getenv("APPROVAL_REPORTER"),
                        os.getenv("APPROVAL_REPORTER_PATH"),
                        os.getenv("APPROVAL_REPORTER_ARGS", "").split(),
                    ]
                )
            )
        ]
        if os.getenv("APPROVAL_REPORTER", "")
        else []
    )
    default_reporters.extend(
        [
            GenericDiffReporter(create_config(["kdiff3", "/usr/bin/kdiff3"])),
            GenericDiffReporter(create_config(["DiffMerge", "/Applications/DiffMerge.app/Contents/MacOS/DiffMerge"])),
            GenericDiffReporter(
                create_config(["TortoiseGit", "{ProgramFiles}\\TortoiseGit\\bin\\TortoiseGitMerge.exe"])
            ),
            reporters.ReportWithBeyondCompare(),
            reporters.ReportWithWinMerge(),
            # reporters.ReportWithVSCode(),
            reporters.PythonNativeReporter(),
        ]
    )
    set_default_reporter(reporters.FirstWorkingReporter(*default_reporters))
