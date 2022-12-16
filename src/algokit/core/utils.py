def is_minimum_version(system_version: str, minimum_version: str) -> bool:
    system_version_as_tuple = tuple(map(int, system_version.split(".")))
    minimum_version_as_tuple = tuple(map(int, minimum_version.split(".")))
    return system_version_as_tuple >= minimum_version_as_tuple


def get_version_from_str(version: str) -> tuple[int, int, int]:
    # take only the first three parts x.y.z of the version to ignore weird version
    major, minor, build = map(int, version.split(".")[:3])
    return major, minor, build
