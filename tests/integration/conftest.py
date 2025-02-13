from helpers.cluster import run_and_check
import pytest
import logging
import os
from helpers.test_tools import TSV
from helpers.network import _NetworkManager


# This is a workaround for a problem with logging in pytest [1].
#
#   [1]: https://github.com/pytest-dev/pytest/issues/5502
logging.raiseExceptions = False


@pytest.fixture(autouse=True, scope="session")
def cleanup_environment():
    try:
        if int(os.environ.get("PYTEST_CLEANUP_CONTAINERS", 0)) == 1:
            logging.debug(f"Cleaning all iptables rules")
            _NetworkManager.clean_all_user_iptables_rules()
        result = run_and_check(["docker ps | wc -l"], shell=True)
        if int(result) > 1:
            if int(os.environ.get("PYTEST_CLEANUP_CONTAINERS", 0)) != 1:
                logging.warning(
                    f"Docker containters({int(result)}) are running before tests run. They can be left from previous pytest run and cause test failures.\n"
                    "You can set env PYTEST_CLEANUP_CONTAINERS=1 or use runner with --cleanup-containers argument to enable automatic containers cleanup."
                )
            else:
                logging.debug("Trying to kill unstopped containers...")
                run_and_check(
                    [f"docker kill $(docker container list  --all  --quiet)"],
                    shell=True,
                    nothrow=True,
                )
                run_and_check(
                    [f"docker rm $docker container list  --all  --quiet)"],
                    shell=True,
                    nothrow=True,
                )
                logging.debug("Unstopped containers killed")
                r = run_and_check(["docker-compose", "ps", "--services", "--all"])
                logging.debug(f"Docker ps before start:{r.stdout}")
        else:
            logging.debug(f"No running containers")

        logging.debug("Pruning Docker networks")
        run_and_check(
            ["docker network prune"],
            shell=True,
            nothrow=True,
        )
    except Exception as e:
        logging.exception(f"cleanup_environment:{str(e)}")
        pass

    yield


def pytest_addoption(parser):
    parser.addoption(
        "--run-id",
        default="",
        help="run-id is used as postfix in _instances_{} directory",
    )


def pytest_configure(config):
    os.environ["INTEGRATION_TESTS_RUN_ID"] = config.option.run_id
