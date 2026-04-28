#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.31.0",
# ]
# ///
"""
SkyHuman API helper CLI.

Wrap avatar, video, upload, credit, and check-in operations in a stable,
scriptable interface for skill users.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


DEFAULT_BASE_URL = "https://skyhumanapi.pilihu.vip"
DEFAULT_POLL_INTERVAL = 10
DEFAULT_POLL_TIMEOUT = 600
STATUS_TEXT = {
    1: "waiting",
    2: "processing",
    3: "completed",
    4: "failed",
}


class ApiError(Exception):
    """Structured API error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.payload = payload or {}

    def to_dict(self) -> dict:
        return {
            "error": str(self),
            "status_code": self.status_code,
            "code": self.code,
            "payload": self.payload,
        }


def _compact_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _env(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


class SkyHumanClient:
    """HTTP client for Fly API and check-in API."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        checkin_base_url: Optional[str],
        poll_interval: int,
        poll_timeout: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.checkin_base_url = (checkin_base_url or "").rstrip("/") or None
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self.session = requests.Session()

    @staticmethod
    def _headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _content_type_for_file(file_path: Path, fallback: str = "application/octet-stream") -> str:
        guessed, _ = mimetypes.guess_type(str(file_path))
        return guessed or fallback

    def _request(
        self,
        *,
        method: str,
        url: str,
        token: str,
        params: Optional[dict] = None,
        json_payload: Optional[dict] = None,
        allow_nonzero_code: bool = False,
    ) -> dict:
        response = self.session.request(
            method=method,
            url=url,
            headers=self._headers(token),
            params=params,
            json=json_payload,
            timeout=120,
        )

        if response.status_code == 401:
            raise ApiError("Unauthorized token", status_code=401)
        if response.status_code != 200:
            raise ApiError(
                "HTTP request failed",
                status_code=response.status_code,
                payload={"response_text": response.text},
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiError(
                "Response is not valid JSON",
                status_code=response.status_code,
                payload={"response_text": response.text},
            ) from exc

        code = payload.get("code")
        if code not in (None, 0) and not allow_nonzero_code:
            raise ApiError(
                payload.get("message") or "Business request failed",
                status_code=response.status_code,
                code=code,
                payload=payload,
            )

        return payload

    def _fly_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json_payload: Optional[dict] = None,
        allow_nonzero_code: bool = False,
    ) -> dict:
        return self._request(
            method=method,
            url=f"{self.base_url}{path}",
            token=self.token,
            params=params,
            json_payload=json_payload,
            allow_nonzero_code=allow_nonzero_code,
        )

    def _checkin_request(
        self,
        method: str,
        path: str,
        *,
        allow_nonzero_code: bool = False,
    ) -> dict:
        base_url = self.checkin_base_url or self.base_url
        return self._request(
            method=method,
            url=f"{base_url}{path}",
            token=self.token,
            allow_nonzero_code=allow_nonzero_code,
        )

    def create_avatar(
        self,
        *,
        title: str,
        video_url: Optional[str],
        file_id: Optional[str],
    ) -> dict:
        if not video_url and not file_id:
            raise ApiError("avatar-create requires --video-url or --file-id")

        payload: Dict[str, Any] = {"title": title}
        if video_url:
            payload["video_url"] = video_url
        if file_id:
            payload["file_id"] = file_id

        data = self._fly_request(
            "POST",
            "/api/v2/fly/avatar/create_by_video",
            json_payload=payload,
        )
        return {
            "task_id": data.get("task_id"),
            "request_id": data.get("request_id"),
        }

    def query_avatar_task(self, task_id: str) -> dict:
        data = self._fly_request(
            "GET",
            "/api/v2/fly/avatar/task",
            params={"task_id": task_id},
        )
        data["status_text"] = STATUS_TEXT.get(data.get("status"), "unknown")
        return data

    def wait_avatar_done(self, task_id: str) -> dict:
        start = time.time()
        while True:
            elapsed = int(time.time() - start)
            if elapsed > self.poll_timeout:
                raise ApiError(
                    "Timed out while waiting for avatar task",
                    payload={"task_id": task_id, "elapsed_seconds": elapsed},
                )

            data = self.query_avatar_task(task_id)
            status = data.get("status")
            if status == 3:
                return {
                    "task_id": task_id,
                    "status": status,
                    "status_text": data.get("status_text"),
                    "avatar": data.get("avatar"),
                    "elapsed_seconds": elapsed,
                    "request_id": data.get("request_id"),
                }
            if status == 4:
                raise ApiError(
                    "Avatar task failed",
                    code=data.get("code"),
                    payload=data,
                )
            time.sleep(self.poll_interval)

    def get_avatar_list(self, favorite_only: bool) -> dict:
        data = self._fly_request(
            "GET",
            "/api/v2/fly/avatar/list",
            params={"favorite_only": favorite_only},
        )
        avatars = data.get("data", {}).get("avatars", [])
        return {
            "count": len(avatars),
            "avatars": avatars,
            "request_id": data.get("request_id"),
        }

    def delete_avatar(self, avatar_code: str) -> dict:
        data = self._fly_request(
            "POST",
            "/api/v2/fly/avatar/delete",
            json_payload={"avatar_code": avatar_code},
        )
        return {
            "deleted": True,
            "avatar_code": avatar_code,
            "request_id": data.get("request_id"),
        }

    def create_video(
        self,
        *,
        avatar: str,
        title: str,
        audio_url: Optional[str],
        file_id: Optional[str],
    ) -> dict:
        if not audio_url and not file_id:
            raise ApiError("video-create requires --audio-url or --file-id")

        payload: Dict[str, Any] = {
            "avatar": avatar,
            "title": title,
        }
        if audio_url:
            payload["audio_url"] = audio_url
        if file_id:
            payload["file_id"] = file_id

        data = self._fly_request(
            "POST",
            "/api/v2/fly/video/create_by_audio",
            json_payload=payload,
        )
        return {
            "task_id": data.get("task_id"),
            "request_id": data.get("request_id"),
        }

    def query_video_task(self, task_id: str) -> dict:
        data = self._fly_request(
            "GET",
            "/api/v2/fly/video/task",
            params={"task_id": task_id},
        )
        data["status_text"] = STATUS_TEXT.get(data.get("status"), "unknown")
        return data

    def wait_video_done(self, task_id: str) -> dict:
        start = time.time()
        while True:
            elapsed = int(time.time() - start)
            if elapsed > self.poll_timeout:
                raise ApiError(
                    "Timed out while waiting for video task",
                    payload={"task_id": task_id, "elapsed_seconds": elapsed},
                )

            data = self.query_video_task(task_id)
            status = data.get("status")
            if status == 3:
                return {
                    "task_id": task_id,
                    "status": status,
                    "status_text": data.get("status_text"),
                    "video_url": data.get("video_Url"),
                    "duration": data.get("duration"),
                    "elapsed_seconds": elapsed,
                    "request_id": data.get("request_id"),
                }
            if status == 4:
                raise ApiError(
                    "Video task failed",
                    code=data.get("code"),
                    payload=data,
                )
            time.sleep(self.poll_interval)

    def create_upload_url(self, file_extension: str) -> dict:
        normalized_extension = file_extension.strip().lstrip(".").lower()
        if not normalized_extension:
            raise ApiError("file extension is required")

        data = self._fly_request(
            "POST",
            "/api/v2/fly/upload/create_upload_url",
            json_payload={"file_extension": normalized_extension},
        )
        result = data.get("data", {})
        result["request_id"] = data.get("request_id")
        return result

    def upload_file(self, file_path: str, file_extension: Optional[str]) -> dict:
        source = Path(file_path).expanduser().resolve()
        if not source.exists():
            raise ApiError("Local file does not exist", payload={"file_path": str(source)})
        if not source.is_file():
            raise ApiError("Local path is not a file", payload={"file_path": str(source)})

        extension = file_extension or source.suffix.lstrip(".")
        if not extension:
            raise ApiError("Could not infer file extension", payload={"file_path": str(source)})

        info = self.create_upload_url(extension)
        upload_url = info.get("upload_url")
        content_type = info.get("content_type") or self._content_type_for_file(source)
        if not upload_url:
            raise ApiError("Upload URL missing from response", payload=info)

        with source.open("rb") as file_handle:
            response = self.session.put(
                upload_url,
                headers={"Content-Type": content_type},
                data=file_handle,
                timeout=300,
            )

        if response.status_code not in (200, 201):
            raise ApiError(
                "File upload failed",
                status_code=response.status_code,
                payload={"response_text": response.text},
            )

        info["uploaded"] = True
        info["file_path"] = str(source)
        return info

    def get_credit(self) -> dict:
        data = self._fly_request("GET", "/api/v2/fly/account/credit")
        return {
            "left": data.get("left"),
            "request_id": data.get("request_id"),
        }

    def get_checkin_status(self) -> dict:
        data = self._checkin_request("GET", "/api/checkin/status")
        result = data.get("data", {}) or {}
        result["request_id"] = data.get("request_id")
        return result

    def do_checkin(self) -> dict:
        data = self._checkin_request(
            "POST",
            "/api/checkin",
            allow_nonzero_code=True,
        )
        result = data.get("data", {}) or {
            "success": data.get("code") == 0,
            "message": data.get("message", ""),
            "score_awarded": 0,
        }
        result["code"] = data.get("code")
        result["request_id"] = data.get("request_id")
        return result


def _env_int_alias(names: tuple[str, ...], default: int) -> int:
    value = _env(*names)
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        joined = ", ".join(names)
        raise ApiError(f"Environment variable {joined} must be an integer") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SkyHuman API helper CLI")
    parser.add_argument(
        "--base-url",
        default=_env("SKYHUMAN_BASE_URL", "BASE_URL", default=DEFAULT_BASE_URL),
        help="Fly API base URL",
    )
    parser.add_argument(
        "--token", "--api-key",
        dest="token",
        default=_env("SKYHUMAN_TOKEN", "TOKEN"),
        help="API key from the SkyHuman backend personal-center page",
    )
    parser.add_argument(
        "--checkin-base-url",
        default=os.getenv("SKYHUMAN_CHECKIN_BASE_URL"),
        help="Base URL for /api/checkin endpoints",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=_env_int_alias(("SKYHUMAN_POLL_INTERVAL", "POLL_INTERVAL"), DEFAULT_POLL_INTERVAL),
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=_env_int_alias(("SKYHUMAN_POLL_TIMEOUT", "POLL_TIMEOUT"), DEFAULT_POLL_TIMEOUT),
        help="Polling timeout in seconds",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    avatar_create = subparsers.add_parser("avatar-create", help="Create avatar from video URL or file ID")
    avatar_create.add_argument("--title", default="未命名")
    avatar_create_input = avatar_create.add_mutually_exclusive_group(required=True)
    avatar_create_input.add_argument("--video-url")
    avatar_create_input.add_argument("--file-id")

    avatar_task = subparsers.add_parser("avatar-task", help="Query avatar task")
    avatar_task.add_argument("--task-id", required=True)

    avatar_wait = subparsers.add_parser("avatar-wait", help="Wait for avatar task completion")
    avatar_wait.add_argument("--task-id", required=True)

    avatar_list = subparsers.add_parser("avatar-list", help="List avatars")
    avatar_list.add_argument("--favorite-only", action="store_true")

    avatar_delete = subparsers.add_parser("avatar-delete", help="Delete avatar")
    avatar_delete.add_argument("--avatar-code", required=True)

    video_create = subparsers.add_parser("video-create", help="Create video from audio URL or file ID")
    video_create.add_argument("--avatar", required=True)
    video_create.add_argument("--title", default="未命名")
    video_create_input = video_create.add_mutually_exclusive_group(required=True)
    video_create_input.add_argument("--audio-url")
    video_create_input.add_argument("--file-id")

    video_task = subparsers.add_parser("video-task", help="Query video task")
    video_task.add_argument("--task-id", required=True)

    video_wait = subparsers.add_parser("video-wait", help="Wait for video task completion")
    video_wait.add_argument("--task-id", required=True)

    upload_create = subparsers.add_parser("upload-create-url", help="Create upload URL")
    upload_create.add_argument("--file-extension", required=True)

    upload_file = subparsers.add_parser("upload-file", help="Upload a local file")
    upload_file.add_argument("--file-path", required=True)
    upload_file.add_argument("--file-extension")

    subparsers.add_parser("credit", help="Get remaining credit")
    subparsers.add_parser("checkin-status", help="Get daily check-in status")
    subparsers.add_parser("checkin-do", help="Perform daily check-in")

    return parser


def _require_token(token: Optional[str], purpose: str) -> str:
    if token:
        return token
    raise ApiError(f"Missing token for {purpose}. Use --token or set SKYHUMAN_TOKEN.")


def run_command(args: argparse.Namespace) -> dict:
    resolved_token = _require_token(args.token, args.command)

    client = SkyHumanClient(
        base_url=args.base_url,
        token=resolved_token,
        checkin_base_url=args.checkin_base_url,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
    )

    if args.command == "avatar-create":
        return client.create_avatar(title=args.title, video_url=args.video_url, file_id=args.file_id)
    if args.command == "avatar-task":
        return client.query_avatar_task(args.task_id)
    if args.command == "avatar-wait":
        return client.wait_avatar_done(args.task_id)
    if args.command == "avatar-list":
        return client.get_avatar_list(args.favorite_only)
    if args.command == "avatar-delete":
        return client.delete_avatar(args.avatar_code)
    if args.command == "video-create":
        return client.create_video(
            avatar=args.avatar,
            title=args.title,
            audio_url=args.audio_url,
            file_id=args.file_id,
        )
    if args.command == "video-task":
        return client.query_video_task(args.task_id)
    if args.command == "video-wait":
        return client.wait_video_done(args.task_id)
    if args.command == "upload-create-url":
        return client.create_upload_url(args.file_extension)
    if args.command == "upload-file":
        return client.upload_file(args.file_path, args.file_extension)
    if args.command == "credit":
        return client.get_credit()
    if args.command == "checkin-status":
        return client.get_checkin_status()
    if args.command == "checkin-do":
        return client.do_checkin()
    raise ApiError("Unsupported command", payload={"command": args.command})


def main() -> int:
    try:
        parser = build_parser()
        args = parser.parse_args()
        result = run_command(args)
        _compact_json(result)
        return 0
    except ApiError as exc:
        _compact_json(exc.to_dict())
        return 1
    except requests.RequestException as exc:
        _compact_json({"error": "Network request failed", "details": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
