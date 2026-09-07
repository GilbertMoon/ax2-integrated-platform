"""2조 LMS 학생 강의 목록/상세 화면."""

import json

from django.shortcuts import render

from lms.models import Lecture


def student_lecture_list_view(request):
    """강의 및 교안 전체 목록 페이지."""
    lecture = Lecture.get_singleton()
    lessons = (
        lecture.lessons.all()
        .prefetch_related("videos", "materials")
        .order_by("-lesson_date")
        if lecture
        else []
    )

    return render(
        request,
        "lms/student/lecture_list.html",
        {"lecture": lecture, "lessons": lessons},
    )


def student_lecture_detail_view(request, lesson_id):
    """단일 강의 영상 재생 및 교안 확인 페이지."""
    lecture = Lecture.get_singleton()
    lessons_data = []

    if lecture:
        lessons = lecture.lessons.all().prefetch_related("videos", "materials")
        for lesson in lessons:
            materials_data = []
            for material in lesson.materials.all():
                materials_data.append(
                    {
                        "kind": material.kind,
                        "title": material.title,
                        "url": (
                            material.file_url
                            if material.kind == "FILE"
                            else material.link_url
                        ),
                    }
                )

            lessons_data.append(
                {
                    "id": lesson.id,
                    "title": lesson.title,
                    "date": lesson.lesson_date.strftime("%Y-%m-%d"),
                    "videos": [
                        {"title": video.title, "url": video.video_url}
                        for video in lesson.videos.all()
                    ],
                    "materials": materials_data,
                }
            )

    return render(
        request,
        "lms/student/lecture.html",
        {
            "lecture": lecture,
            "lessons_json": json.dumps(lessons_data),
            "target_lesson_id": lesson_id,
        },
    )
