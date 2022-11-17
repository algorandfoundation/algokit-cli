from approvaltests import get_default_reporter, reporters, set_default_reporter
from approvaltests.reporters.generic_diff_reporter_factory import NoConfigReporter

# There's an interaction with approvaltests and pytest-approvals that
# causes no reporter to be configured.
# This workaround allows using command line flags to pytest to set a custom reporter e.g. PyCharm:
# --approvaltests-add-reporter-args='diff' --approvaltests-add-reporter='<very long path to current pycharm version>'
# but doesn't break in CI/CD or VSCode
if isinstance(get_default_reporter(), NoConfigReporter):
    set_default_reporter(reporters.PythonNativeReporter())
