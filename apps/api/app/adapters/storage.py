"""Object storage adapter (MinIO / S3-compatible via boto3)."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import get_settings


class ObjectStore:
    def __init__(self, client: Any, bucket: str) -> None:
        self._c = client
        self._bucket = bucket

    def ensure_bucket(self) -> None:
        try:
            self._c.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._c.create_bucket(Bucket=self._bucket)

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.ensure_bucket()
        self._c.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get(self, key: str) -> bytes:
        obj = self._c.get_object(Bucket=self._bucket, Key=key)
        body: bytes = obj["Body"].read()
        return body


@lru_cache
def get_object_store() -> ObjectStore:
    s = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )
    return ObjectStore(client, s.s3_bucket)
