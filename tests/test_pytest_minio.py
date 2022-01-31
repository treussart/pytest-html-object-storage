from _pytest.config import ExitCode
from _pytest.pytester import RunResult


def run(pytester, *args):
    return pytester.runpytest("--store-minio", *args)


class TestMinio:
    def test_pass(self, pytester, set_env):
        pytester.makepyfile("def test_pass(): pass")
        result: RunResult = run(pytester)
        assert result.ret == 0
        assert "HTML report sent on MinIO object storage at" in result.stdout.str()

    def test_no_config(self, pytester):
        pytester.makepyfile("def test_no_config(): pass")
        result: RunResult = run(pytester)
        assert result.ret == ExitCode.INTERNAL_ERROR
