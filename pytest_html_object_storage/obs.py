import logging
import os
import uuid
from typing import Union

from _pytest.config import Config, ExitCode
from _pytest.main import Session
from _pytest.terminal import TerminalReporter
from obs import (
    ObsClient,
    HeadPermission,
    Rule,
    NoncurrentVersionExpiration,
    Lifecycle,
    Expiration,
)

log = logging.getLogger(__name__)


class HTMLObs:
    # https://support.huaweicloud.com/intl/en-us/sdk-python-devg-obs/obs-sdk-python-devg.pdf
    # https://github.com/huaweicloud/huaweicloud-sdk-python-obs
    def __init__(self, config: Config):
        self.config = config
        self.os_endpoint = os.environ.get("OBJECT_STORAGE_ENDPOINT")
        self.os_bucket = os.environ.get("OBJECT_STORAGE_BUCKET")
        self.os_username = os.environ.get("OBJECT_STORAGE_USERNAME")
        self.os_password = os.environ.get("OBJECT_STORAGE_PASSWORD")
        self.os_region_name = os.environ.get("OBJECT_STORAGE_REGION_NAME")
        self.os_access_domain_name = os.environ.get("OBJECT_STORAGE_ACCESS_DOMAIN_NAME")
        self.os_retention = self._get_retention()
        self.os_policy = self._get_policy()
        self.os_access_object_url = None

    @staticmethod
    def _get_policy() -> str:
        policy = os.environ.get("OBJECT_STORAGE_POLICY")
        if not policy or policy == "public-read":
            return "public-read"
        else:
            return ""

    @staticmethod
    def _get_retention() -> int:
        retention = os.environ.get("OBJECT_STORAGE_RETENTION")
        if retention and int(retention) > 0:
            return int(retention)
        else:
            return 0

    def send_html(self, name, content: str):
        obsClient = ObsClient(
            access_key_id=self.os_username,
            secret_access_key=self.os_password,
            server=self.os_endpoint,
        )

        resp = obsClient.headBucket(self.os_bucket)
        if resp.status == 404:
            log.info("Bucket does not exist")
            resp = obsClient.createBucket(
                bucketName=self.os_bucket, location=self.os_region_name
            )
            if resp.status < 300:
                log.info("Create bucket " + self.os_bucket + " successfully!")
                if self.os_retention:
                    rule = Rule(
                        prefix="",
                        status="Enabled",
                        expiration=Expiration(days=self.os_retention),
                        noncurrentVersionExpiration=NoncurrentVersionExpiration(
                            noncurrentDays=self.os_retention
                        ),
                    )
                    lifecycle = Lifecycle(rule=[rule])
                    resp = obsClient.setBucketLifecycle(self.os_bucket, lifecycle)
                    if resp.status < 300:
                        log.info("Create bucket life cycle rule successfully!")
                    else:
                        log.error(
                            f"Create bucket life cycle rule errorCode:{resp.errorCode}, "
                            f"errorMessage: {resp.errorMessage}"
                        )
            else:
                log.error(
                    f"Create bucket errorCode:{resp.errorCode}, errorMessage: {resp.errorMessage}"
                )

        resp = obsClient.putContent(self.os_bucket, name, content)
        if resp.status < 300:
            self.os_access_object_url = resp.body.objectUrl
            log.info(f"Create object successfully! objectUrl: {self.os_access_object_url}")
        else:
            log.error(
                f"Create object errorCode:{resp.errorCode}, errorMessage: {resp.errorMessage}"
            )
        if self.os_policy == "public-read":
            resp = obsClient.setObjectAcl(
                self.os_bucket, name, aclControl=HeadPermission.PUBLIC_READ
            )
            if resp.status < 300:
                log.info("Create object policy public successfully!")
            else:
                log.error(
                    f"Create object policy public errorCode:{resp.errorCode}, errorMessage: {resp.errorMessage}"
                )
        obsClient.close()

    def pytest_sessionfinish(self, session: Session, exitstatus: Union[int, ExitCode]):
        html = getattr(session.config, "_html", None)
        if html:
            html._post_process_reports()
            self.send_html(
                f"{str(uuid.uuid4())}/report.html",
                html._generate_report(session),
            )
            session.config._report_url = self.os_access_object_url

    def pytest_terminal_summary(
        self,
        terminalreporter: TerminalReporter,
        exitstatus: Union[int, ExitCode],
        config: Config,
    ):
        terminalreporter.write_sep(
            "-",
            f"HTML report sent on OBS object storage at {self.os_access_object_url}",
        )
