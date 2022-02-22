import io
import json
import os
import uuid
from datetime import timedelta, datetime
from typing import Union, Optional

from _pytest.config import Config, ExitCode
from _pytest.main import Session
from _pytest.terminal import TerminalReporter
from minio import Minio
from minio.commonconfig import GOVERNANCE, ENABLED, Filter
from minio.lifecycleconfig import Rule, Transition, Expiration, LifecycleConfig
from minio.retention import Retention


class HTMLMinio:
    def __init__(self, config: Config):
        self.config = config
        self.os_endpoint = os.environ.get("OBJECT_STORAGE_ENDPOINT")
        self.os_bucket = os.environ.get("OBJECT_STORAGE_BUCKET")
        self.os_username = os.environ.get("OBJECT_STORAGE_USERNAME")
        self.os_password = os.environ.get("OBJECT_STORAGE_PASSWORD")
        self.os_region_name = os.environ.get("OBJECT_STORAGE_REGION_NAME")
        self.os_scheme, self.os_secure = self._get_secure()
        self.os_retention = self._get_retention()
        self.os_policy = self._get_policy()
        self.os_provider = os.environ.get("OBJECT_STORAGE_PROVIDER")
        self.access_url = None

    def get_access_url(self, name: str) -> str:
        self.access_url = (
            f"{self.os_scheme}://{self.os_endpoint}/{self.os_bucket}/{name}"
        )
        return self.access_url

    @staticmethod
    def _get_secure() -> [str, bool]:
        if os.environ.get("OBJECT_STORAGE_SECURE") == "false":
            return "http", False
        else:
            return "https", True

    @staticmethod
    def _get_retention() -> int:
        retention = os.environ.get("OBJECT_STORAGE_RETENTION")
        if retention and int(retention) > 0:
            return int(retention)
        else:
            return 0

    def _get_policy(self) -> str:
        policy = os.environ.get("OBJECT_STORAGE_POLICY")
        if not policy or policy == "public-read":
            return "public-read"
        else:
            return ""

    def send_html(self, name, content: str):
        client = Minio(
            self.os_endpoint,
            self.os_username,
            self.os_password,
            region=self.os_region_name,
            secure=self.os_secure,
        )
        found = client.bucket_exists(self.os_bucket)
        if not found:
            client.make_bucket(self.os_bucket)
            if self.os_policy == "public-read":
                if not self.os_provider or self.os_provider == "scaleway":
                    policy = {
                        "Version": "2012-10-17",
                        "Id": f"{self.os_bucket}Policy",
                        "Statement": [
                            {
                                "Sid": "Grant List and GET to everyone",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": ["s3:ListBucket", "s3:GetObject"],
                                "Resource": [self.os_bucket, f"{self.os_bucket}/*"],
                            }
                        ],
                    }
                else:
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                                "Resource": f"arn:aws:s3:::{self.os_bucket}",
                            },
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": "s3:GetObject",
                                "Resource": f"arn:aws:s3:::{self.os_bucket}/*",
                            },
                        ],
                    }
                client.set_bucket_policy(self.os_bucket, json.dumps(policy))
            if self.os_retention:
                config = LifecycleConfig(
                    [
                        Rule(
                            ENABLED,
                            rule_filter=Filter(prefix="*/"),
                            rule_id="rule_retention",
                            expiration=Expiration(days=self.os_retention),
                        ),
                    ],
                )
                client.set_bucket_lifecycle(self.os_bucket, config)
        content_bytes = content.encode("utf-8")
        content = io.BytesIO(content_bytes)
        client.put_object(
            self.os_bucket,
            name,
            content,
            len(content_bytes),
            content_type="text/html",
        )

    def pytest_sessionfinish(self, session: Session, exitstatus: Union[int, ExitCode]):
        html = getattr(session.config, "_html", None)
        if html:
            html._post_process_reports()
            name = f"{str(uuid.uuid4())}/report.html"
            self.send_html(
                name,
                html._generate_report(session),
            )
            session.config._report_url = self.get_access_url(name)

    def pytest_terminal_summary(
        self,
        terminalreporter: TerminalReporter,
        exitstatus: Union[int, ExitCode],
        config: Config,
    ):
        terminalreporter.write_sep(
            "-", f"HTML report sent on MinIO object storage at {self.access_url}"
        )
