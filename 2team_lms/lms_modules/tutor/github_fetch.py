"""
apps/tutor/github_fetch.py — 👨‍🏫 튜터B

학생이 과제 제출 시 넣은 GitHub 공개 레포 파일(blob) 또는 폴더(tree) 링크를 받아온다.
AI 채점(ai_gemini)이 그 코드를 프롬프트에 넣어 참고한다.

- 무인증 (공개 레포만). GITHUB_API_TOKEN 있으면 헤더에 실어 rate limit 여유.
- github.com / raw.githubusercontent.com 만 허용 (SSRF 방어).
- blob·raw 파일 및 tree 폴더 지원. 폴더는 API 요청 20회·텍스트 512KiB로 제한한다.
- 실패는 예외 대신 None. 설계: docs/assignment-lms-github-link-eval.md
"""
from __future__ import annotations

import base64
import binascii
import re
from urllib.parse import urlparse, quote

import base64
import binascii
import requests
from django.conf import settings

_ALLOWED_HOSTS = {"github.com", "www.github.com", "raw.githubusercontent.com"}
_TIMEOUT = 10
_PROBE_TIMEOUT = 6  # 제출 시점 링크 검증용 — 본문은 안 받고 상태코드만
_MAX_BYTES = 512 * 1024  # 이보다 큰 파일은 스킵 (데이터/바이너리로 간주)

# /{owner}/{repo}/blob/{ref}/{path...}
_BLOB_RE = re.compile(r"^/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")


def is_github_url(url: str) -> bool:
    try:
        return (urlparse(url).hostname or "").lower() in _ALLOWED_HOSTS
    except ValueError:
        return False


def raw_url(url: str) -> str | None:
    """단일 파일 raw URL 로 변환. blob·raw 가 아니면 None."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host == "raw.githubusercontent.com":
        return f"https://raw.githubusercontent.com{parsed.path}"
    match = _BLOB_RE.match(parsed.path)
    if not match:
        return None
    owner, repo, ref, path = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def probe_github_file(url: str) -> str:
    """GitHub 링크가 AI 채점 가능한 단일 파일 링크인지 확인 (본문은 안 받음).

    반환:
        "ok"        blob/raw 형태 + 200
        "not_blob"  github.com 인데 blob/raw 단일 파일 형태가 아님 (레포 루트·tree·PR·gist)
        "not_found" blob/raw 형태지만 열리지 않음 (비공개·404·삭제)
        "error"     네트워크·타임아웃 — 판단 보류 (호출부가 통과시킨다)

    호출 전에 is_github_url(url) 로 GitHub 링크인지 먼저 확인할 것.
    폴더(tree) 링크는 AI 채점용 본문 읽기(_fetch_folder)는 계속 지원하되, 제출 시점
    검증(이 함수)에서는 "not_blob"으로 분류해 제출 자체는 막는다 — 정책은 apps.student 쪽.
    """
    target = raw_url(url)
    if target is None:
        return "not_blob"

    headers = {}
    token = getattr(settings, "GITHUB_API_TOKEN", "") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(target, timeout=_PROBE_TIMEOUT, headers=headers, stream=True)
        resp.close()
    except requests.RequestException:
        return "error"

    if resp.status_code == 200:
        return "ok"
    if resp.status_code in (401, 403, 404, 410):
        return "not_found"
    return "error"


def fetch_github_file(url: str) -> str | None:
    """공개 레포 파일 또는 폴더의 텍스트. 읽기 실패 시 None."""
    if not is_github_url(url):
        return None
    target = raw_url(url)
    if target is None:
        return _fetch_folder(url)

    headers = {}
    token = getattr(settings, "GITHUB_API_TOKEN", "") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(target, timeout=_TIMEOUT, headers=headers)
    except requests.RequestException:
        return None
    if resp.status_code != 200 or len(resp.content) > _MAX_BYTES:
        return None
    try:
        return resp.content.decode("utf-8")
    except UnicodeDecodeError:
        return None


_TEXT_EXTENSIONS = {'.py', '.ipynb', '.md', '.txt', '.sql', '.js', '.ts', '.html', '.css', '.json', '.yaml', '.yml', '.toml', '.sh'}


def _fetch_folder(url):
    """Read bounded public GitHub folder contents; never follow supplied download URLs."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in {'github.com', 'www.github.com'}:
        return None
    match = re.fullmatch(r'/([^/]+)/([^/]+)/tree/([^/]+)(?:/(.*))?', parsed.path)
    if not match:
        return None
    owner, repo, ref, folder = match.groups()
    folder = (folder or '').rstrip('/')
    pending = [folder]
    seen = set()
    parts = []
    size = 0
    calls = 0
    headers = {'Accept': 'application/vnd.github+json'}
    token = getattr(settings, 'GITHUB_API_TOKEN', '')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    while pending and calls < 20:
        path = pending.pop(0)
        if path in seen:
            continue
        seen.add(path)
        endpoint = f'https://api.github.com/repos/{quote(owner, safe="")}/{quote(repo, safe="")}/contents/{quote(path, safe="/")}'
        try:
            response = requests.get(endpoint, params={'ref': ref}, headers=headers, timeout=_TIMEOUT, allow_redirects=False)
            calls += 1
            if response.status_code != 200 or len(response.content) > 2 * _MAX_BYTES:
                continue
            payload = response.json()
        except (requests.RequestException, ValueError):
            continue
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                child = item.get('path', '')
                if not isinstance(child, str) or not child.startswith(path + '/' if path else '') or '..' in child.split('/'):
                    continue
                if item.get('type') == 'dir' or (item.get('type') == 'file' and '.' + child.rsplit('.', 1)[-1].lower() in _TEXT_EXTENSIONS):
                    if len(pending) < 40:
                        pending.append(child)
        elif isinstance(payload, dict) and payload.get('type') == 'file' and payload.get('encoding') == 'base64':
            try:
                body = base64.b64decode(payload.get('content', '')).decode('utf-8')
            except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
                continue
            if '\x00' in body or size + len(body.encode('utf-8')) > _MAX_BYTES:
                continue
            size += len(body.encode('utf-8'))
            parts.append(f'[GitHub file: {path}]\n{body}')
    if not parts:
        return None
    # Folder reads are bounded; never imply that every file was inspected.
    return '[폴더 제출물: 텍스트 파일만 제한적으로 수집했습니다. 전체 저장소 검토가 아닙니다.]\n' + '\n\n'.join(parts)
