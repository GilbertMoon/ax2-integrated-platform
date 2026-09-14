# ============================================================
# attendance/face_services.py (전체 교체 - 라이브니스 검사 추가 버전)
#
# 변경점:
# - 실시간 촬영 사진(find_matching_student)은 check_liveness=True로 요청
#   → 사진/화면을 갖다 대면 거부됨
# - 등록용 정적 프로필 사진(ensure_embedding_cached)은 check_liveness=False
#   → 프로필 사진 자체는 원래 "사진"이라 라이브니스 검사를 하면 안 됨
# ============================================================
import math
from datetime import time as time_cls

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from attendance.services import save_face_checkin

User = get_user_model()

MATCH_THRESHOLD = 0.4

# 이 시각 이전에 출석 체크하면 "출석", 이후면 "지각"
ATTENDANCE_DEADLINE = time_cls(9, 0)  # 오전 9시


def _cosine_distance(vec1: list[float], vec2: list[float]) -> float:
    """두 벡터 사이의 코사인 거리를 계산한다. 0에 가까울수록 유사."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 1.0
    cosine_similarity = dot_product / (norm1 * norm2)
    return 1 - cosine_similarity


def _request_embedding(
    image_bytes: bytes, check_liveness: bool = False
) -> tuple[list[float] | None, str | None]:
    """
    얼굴인식 서버에 사진을 보내서 벡터(임베딩)를 받아온다.
    check_liveness=True면 사진/화면 재촬영(스푸핑) 여부도 함께 확인한다.

    반환값: (임베딩 또는 None, 에러메시지 또는 None)
    """
    try:
        response = requests.post(
            f"{settings.FACE_SERVICE_URL}/embed/",
            files={"image": ("photo.jpg", image_bytes, "image/jpeg")},
            data={"check_liveness": "true" if check_liveness else "false"},
            timeout=settings.FACE_SERVICE_TIMEOUT,
        )
        result = response.json()

        if response.status_code == 403 and result.get("error") == "spoof_detected":
            return None, result.get("message", "실제 얼굴로 다시 촬영해주세요.")

        if response.status_code != 200:
            return None, result.get("error", "얼굴인식 서버 오류가 발생했습니다.")

        return result.get("embedding"), None

    except requests.exceptions.RequestException:
        return None, "얼굴인식 서버에 연결할 수 없습니다."


def ensure_embedding_cached(user) -> bool:
    """이 학생의 얼굴 벡터가 아직 캐시되어 있지 않으면 새로 계산해서 저장한다.
    (등록용 정적 사진이므로 라이브니스 검사는 하지 않는다)
    """
    from attendance.models import FaceEmbedding

    if not user.profile_image:
        return False

    current_image_name = user.profile_image.name
    existing = FaceEmbedding.objects.filter(user=user).first()

    if existing is not None and existing.source_image_name == current_image_name:
        return True

    with open(user.profile_image.path, "rb") as f:
        embedding, _error = _request_embedding(f.read(), check_liveness=False)

    if embedding is None:
        return False

    FaceEmbedding.objects.update_or_create(
        user=user,
        defaults={"vector": embedding, "source_image_name": current_image_name},
    )
    return True


def find_matching_student(captured_image_file):
    """
    실시간 촬영된 사진과 캐시된 학생 벡터들을 비교해서 가장 닮은 사람을 찾는다.
    라이브니스 검사를 통과해야만 다음 단계로 진행한다 (사진/화면 대체 방지).

    반환값: (matched_user 또는 None, 거리값 또는 None, 에러메시지 또는 None)
    """
    from attendance.models import FaceEmbedding

    # check_liveness=True로 요청 -> 사진/화면이면 여기서 거부됨
    captured_embedding, error_message = _request_embedding(
        captured_image_file.read(), check_liveness=True
    )
    if captured_embedding is None:
        return None, None, error_message or "얼굴을 인식하지 못했습니다."

    cached_embeddings = FaceEmbedding.objects.select_related("user").all()
    if not cached_embeddings.exists():
        return None, None, "등록된 학생 얼굴 데이터가 없습니다. 먼저 얼굴 벡터를 등록해주세요."

    best_user = None
    best_distance = None
    for cached in cached_embeddings:
        distance = _cosine_distance(captured_embedding, cached.vector)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_user = cached.user

    if best_distance is not None and best_distance <= MATCH_THRESHOLD:
        return best_user, best_distance, None
    return None, best_distance, None


def record_face_checkin(captured_image_file) -> dict:
    """업로드된 사진 파일을 받아서 출석을 자동 기록한다.
    촬영 시각이 ATTENDANCE_DEADLINE(오전 9시) 이전이면 출석, 이후면 지각으로 기록한다.
    """
    matched_user, distance, error_message = find_matching_student(captured_image_file)

    if error_message:
        return {"matched": False, "message": error_message}

    if matched_user is None:
        return {
            "matched": False,
            "message": "일치하는 학생을 찾지 못했습니다. 다시 시도해주세요.",
            "distance": distance,
        }

    today = timezone.localdate()
    now = timezone.localtime(timezone.now())
    status = "present" if now.time() < ATTENDANCE_DEADLINE else "late"

    if not save_face_checkin(today, matched_user.id, status):
        return {
            "matched": False,
            "message": "출석 대상 학생이 아닙니다. 관리자에게 문의해주세요.",
        }

    return {
        "matched": True,
        "user_id": matched_user.id,
        "display_name": matched_user.first_name or matched_user.email,
        "distance": distance,
        "status": status,
    }
