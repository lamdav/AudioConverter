import os
import pathlib
import shutil
import subprocess
import sys


def deploy() -> None:
    """
    Deploy Template Method.

    :return: None
    """
    check_python_version()
    dist_path = get_dist_path()
    cleanup_dist_if_exists(dist_path)
    create_dist(dist_path)
    upload(dist_path)
    print("deploy successfully completed")
    sys.exit(0)


def check_python_version() -> None:
    """
    Verify that the python version is 3.5+

    :return: None
    """
    print("checking python version...", end="")
    version_info = sys.version_info
    if version_info.major < 3 or version_info.minor < 5:
        print(
            "Python version must be 3.5+ but got {}.{}".format(
                version_info.major, version_info.minor
            )
        )
        print("FAIL")
        sys.exit(1)
    print("PASS")


def get_dist_path() -> pathlib.Path:
    """
    Return the Path object to the dist directory.

    :return: None
    """
    script_path = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    return script_path.parent.joinpath("dist")


def cleanup_dist_if_exists(dist_path: pathlib.Path) -> None:
    """
    Delete the dist directory if it exists

    :param dist_path: Path to dist directory
    :return: None
    """
    print("checking for existing dist directory...", end="")
    if dist_path.exists():
        dist_posix = dist_path.as_posix()
        print("cleaning up {}...".format(dist_posix), end="")
        shutil.rmtree(dist_posix)
    print("PASS")


def create_dist(dist_path: pathlib.Path) -> None:
    """
    Generate the new dist files.

    :param dist_path: Path to dist directory
    :return: None
    """
    print("creating distribution...", end="")
    dist_posix = dist_path.as_posix()
    dist_option = "--dist-dir={}".format(dist_posix)
    command = ["python3", "setup.py", "bdist_wheel", dist_option]
    distribution = subprocess.run(command, stdout=subprocess.PIPE)
    if distribution.returncode != 0:
        print("FAIL")
        print(distribution.stdout.decode("utf-8"))
        sys.exit(1)
    print("PASS")


def upload(dist_path: pathlib.Path) -> None:
    """
    Upload the dist directory to PyPi.

    :param dist_path: Path to dist directory
    :return: None
    """
    print("uploading distribution...", end="")
    all_dist_path = dist_path.joinpath("*")
    all_dist_posix = all_dist_path.as_posix()

    command = ["twine", "upload", all_dist_posix]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    if result.returncode != 0:
        print("FAIL")
        print(result.stdout.decode("utf-8"))
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    deploy()
