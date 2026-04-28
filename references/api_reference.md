# SkyHuman API Reference

This reference summarizes the API behavior encoded in the bundled client and derived from the workspace sources:

- `skyhuman_api.py`
- `飞天数字人 API 文档.md`
- `api-server/app/routers/checkin.py`
- `api-server/app/services/checkin_service.py`

## Auth Model

- Use the single API key configured as `TOKEN` in `skyhuman_api.py`
- Send it as `Authorization: Bearer <TOKEN>`
- Use the same token for Fly API and check-in API
- Default Fly API base URL in the bundled script: `https://skyhumanapi.pilihu.vip`
- Check-in routes remain:
  - `GET /api/checkin/status`
  - `POST /api/checkin`

## CLI Commands

### Avatar

- `avatar-create --video-url URL --title NAME`
- `avatar-create --file-id FILE_ID --title NAME`
- `avatar-create` requires exactly one of `--video-url` or `--file-id`
- `avatar-task --task-id TASK_ID`
- `avatar-wait --task-id TASK_ID`
- `avatar-list [--favorite-only]`
- `avatar-delete --avatar-code AVATAR_CODE`

### Video

- `video-create --avatar AVATAR --audio-url URL --title NAME`
- `video-create --avatar AVATAR --file-id FILE_ID --title NAME`
- `video-create` requires exactly one of `--audio-url` or `--file-id`
- `video-task --task-id TASK_ID`
- `video-wait --task-id TASK_ID`

### Upload

- `upload-create-url --file-extension mp4`
- `upload-file --file-path ./demo.wav [--file-extension wav]`

### Account

- `credit`

### Check-In

- `checkin-status`
- `checkin-do`

## Endpoint Notes

### Create Avatar

- Path: `POST /api/v2/fly/avatar/create_by_video`
- Required:
  - `title` optional
  - `video_url` or `file_id`
- Returns:
  - `task_id`

### Avatar Task

- Path: `GET /api/v2/fly/avatar/task`
- Query:
  - `task_id`
- Status:
  - `1` waiting
  - `2` processing
  - `3` completed
  - `4` failed

### Avatar List

- Path: `GET /api/v2/fly/avatar/list`
- Query:
  - `favorite_only`

### Delete Avatar

- Path: `POST /api/v2/fly/avatar/delete`
- Body:
  - `avatar_code`

### Create Video

- Path: `POST /api/v2/fly/video/create_by_audio`
- Required:
  - `avatar`
  - `audio_url` or `file_id`
  - `title` optional

### Video Task

- Path: `GET /api/v2/fly/video/task`
- Query:
  - `task_id`
- Completed payload includes:
  - `video_Url`
  - `duration`

### Create Upload URL

- Path: `POST /api/v2/fly/upload/create_upload_url`
- Body:
  - `file_extension`
- Response data includes:
  - `upload_url`
  - `content_type`
  - `file_id`

### Credit

- Path: `GET /api/v2/fly/account/credit`
- Response:
  - `left`

### Check-In Status

- Path: `GET /api/checkin/status`
- Response data includes:
  - `checked_in`
  - `score_reward`
  - `checkin_date`

### Check-In Execute

- Path: `POST /api/checkin`
- Response data includes:
  - `success`
  - `message`
  - `score_awarded`
- Special behavior:
  - The backend may return non-zero `code` together with valid `data` when the user has already checked in that day.
  - The bundled client preserves `data` in this case instead of treating it as a fatal error.

## Environment Variables

- `SKYHUMAN_BASE_URL`
- `SKYHUMAN_TOKEN`
- `SKYHUMAN_CHECKIN_BASE_URL`
- `SKYHUMAN_POLL_INTERVAL`
- `SKYHUMAN_POLL_TIMEOUT`

Compatible aliases from `skyhuman_api.py`:

- `BASE_URL`
- `TOKEN`
- `POLL_INTERVAL`
- `POLL_TIMEOUT`

## Recommended Usage Pattern

1. Set the single API key and base URL via environment variables.
2. Upload local media first when possible.
3. Use returned `file_id` for avatar or video creation.
4. Poll with `avatar-wait` or `video-wait` instead of re-implementing loops.
5. Treat completed video URLs as temporary and persist them immediately.

## Installed Path Examples

Use the installed absolute path after the skill is added to Codex:

```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py credit
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py --api-key "$SKYHUMAN_TOKEN" avatar-list
```
