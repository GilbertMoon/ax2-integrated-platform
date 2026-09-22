import json
from pathlib import Path
from uuid import uuid4

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from lms_modules import transaction
from lms_modules.accounts_client import services as accounts
from lms_modules.core.models import Lecture
from lms_modules.notifications import services as lms_notifications
from lms_modules.storage import default_storage

from .views_manage import tutor_required

# 강의 자료(LessonMaterial) 파일 1개당 크기 상한. AssignmentFile 첨부와 동일 기준.
MAX_MATERIAL_SIZE = 50 * 1024 * 1024  # 50MB


def _serialize_lessons(lecture):
    """템플릿 JS의 `lessons` 배열 형태로 직렬화. 날짜 오름차순(회차 순)."""
    lessons = (
        lecture.lessons.all().order_by("lesson_date", "id").prefetch_related("materials", "videos")
    )
    out = []
    for lesson in lessons:
        out.append({
            "id": lesson.id,
            "title": lesson.title,
            "date": lesson.lesson_date.strftime("%Y-%m-%d"),
            "videos": [
                {
                    "title": v.title,
                    "url": v.video_url,
                }
                for v in lesson.videos.all()
            ],
            "materials": [
                {
                    "kind": mat.kind,
                    "title": mat.title,
                    "size": "기존 파일" if mat.kind == "FILE" else "",
                    "url": mat.file_url if mat.kind == "FILE" else mat.link_url,
                    "file_name": mat.file_name if mat.kind == "FILE" else None,
                }
                for mat in lesson.materials.all()
            ],
        })
    return out


def _revision(lecture):
    """저장 시점의 서버 상태 지문. 다른 탭/세션이 그새 바꿨는지 판별용 (낙관적 잠금)."""
    agg = lecture.lessons.all().order_by("-updated_at").values_list("updated_at", flat=True).first()
    count = lecture.lessons.count()
    return f"{count}:{agg.isoformat() if agg else 'empty'}"


@tutor_required
def tutor_lecture_manage_view(request):
    lecture = Lecture.get_singleton()
    return render(request, "lms_ui/tutor/lecture_manage.html", {
        "lecture": lecture,
        # 템플릿에서 {{ lessons|json_script:"lecture-lessons-data" }} 로 렌더 → 외부 JS가 파싱
        "lessons": _serialize_lessons(lecture),
        "revision": _revision(lecture),
    })


@tutor_required
@require_POST
def tutor_lecture_update_api(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "detail": "잘못된 요청"}, status=400)

    lessons_list = data.get("lessons", [])
    base_revision = data.get("base_revision")
    lecture_pk = Lecture.get_singleton().pk

    with transaction.atomic():
        lecture = Lecture.objects.select_for_update().get(pk=lecture_pk)

        # 낙관적 잠금 — 페이지를 연 뒤 다른 곳에서 변경됐으면 덮어쓰지 않는다.
        if base_revision is not None and base_revision != _revision(lecture):
            return JsonResponse(
                {
                    "status": "stale",
                    "detail": "다른 곳에서 강의안이 변경되었습니다. 새로고침 후 다시 시도해 주세요.",
                    "lessons": _serialize_lessons(lecture),
                    "revision": _revision(lecture),
                },
                status=409,
            )

        existing_ids = set(lecture.lessons.values_list("id", flat=True))
        seen_ids = set()
        new_lessons = []  # 학생 알림용 — 진짜 새로 생긴 Lesson만 담는다 (수정은 제외)

        from lms_modules.core.models import Lesson, LessonMaterial, LessonVideo

        for item in lessons_list:
            title = (item.get("title") or "").strip()
            date = item.get("date") or None
            if not title or not date:
                continue

            raw_id = item.get("id")
            lesson_id = raw_id if raw_id in existing_ids else None

            if lesson_id is not None:
                lesson = Lesson.objects.get(pk=lesson_id)
                lesson.title = title
                lesson.lesson_date = date
                lesson.save()
            else:
                lesson = Lesson.objects.create(
                    lecture=lecture, title=title, lesson_date=date
                )
                new_lessons.append(lesson)
            seen_ids.add(lesson.id)

            # Sync videos
            lesson.videos.all().delete()
            for idx, vid in enumerate(item.get("videos", [])):
                v_title = (vid.get("title") or "").strip()
                v_url = (vid.get("url") or "").strip()
                if v_url:
                    LessonVideo.objects.create(
                        lesson=lesson,
                        title=v_title,
                        video_url=v_url,
                        order=idx
                    )

            # Sync materials
            lesson.materials.all().delete()
            for mat in item.get("materials", []):
                kind = mat.get("kind", "FILE")
                url = mat.get("url")
                try:
                    file_size = int(mat.get("file_size") or 0)
                except (TypeError, ValueError):
                    file_size = 0
                LessonMaterial.objects.create(
                    lesson=lesson,
                    kind=kind,
                    title=(mat.get("title") or "").strip() or (url or ""),
                    file_url=url if kind == "FILE" else None,
                    file_name=(mat.get("file_name") or "") if kind == "FILE" else "",
                    file_size=file_size if kind == "FILE" else 0,
                    link_url=url if kind == "LINK" else None,
                )

        for stale_id in existing_ids - seen_ids:
            Lesson.objects.filter(pk=stale_id).delete()

        payload = {
            "status": "success",
            "lessons": _serialize_lessons(lecture),
            "revision": _revision(lecture),
        }

    if new_lessons:
        student_ids = [s.id for s in accounts.get_students()]
        for lesson in new_lessons:
            lms_notifications.notify_many(
                user_ids=student_ids,
                category=lms_notifications.Category.LESSON_ADDED,
                title="새 강의가 등록되었습니다.",
                message=f"{lesson.lesson_date} - {lesson.title}",
                link=reverse("lms:student:lecture-detail", args=[lesson.id]),
                target_type=lms_notifications.TargetType.LESSON,
                target_id=lesson.id,
            )

    return JsonResponse(payload)


@tutor_required
@require_POST
def tutor_lecture_material_upload(request):
    """강의 자료 파일 하나를 스토리지에 저장하고 (url, file_name, file_size) 를 반환한다.

    lessons 전체를 JSON 으로 저장하는 tutor_lecture_update_api 는 파일 바이트를
    실어 보낼 수 없어서, 파일은 이 엔드포인트로 먼저 업로드하고 그 결과 URL을
    lessons 저장 요청(JSON)에 실어 보내는 2단계 구조를 쓴다.
    """
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"status": "error", "detail": "파일이 없습니다."}, status=400)

    if uploaded.size > MAX_MATERIAL_SIZE:
        return JsonResponse(
            {"status": "error", "detail": "50MB를 초과하는 파일은 올릴 수 없습니다."},
            status=400,
        )

    safe_name = Path(uploaded.name).name
    storage_name = f"lesson_materials/{uuid4().hex}_{safe_name}"
    saved = default_storage.save(storage_name, uploaded)

    return JsonResponse(
        {
            "status": "success",
            "url": default_storage.url(saved),
            "file_name": safe_name,
            "file_size": uploaded.size,
        }
    )
