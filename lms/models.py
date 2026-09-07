"""2조 LMS 전용 모델.

주의:
- 실제 테이블은 2조 assignment_lms DB에 존재한다.
- 4조 DB에 migration으로 생성하지 않기 위해 managed=False를 사용한다.
- 공통 사용자/팀 데이터는 Integer ID로만 참조한다.
"""

from pathlib import Path

from django.db import models


class Lecture(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "lecture"

    @classmethod
    def get_singleton(cls):
        return cls.objects.order_by("id").first()


class Lesson(models.Model):
    lecture = models.ForeignKey(
        Lecture, on_delete=models.DO_NOTHING, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    lesson_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "lesson"
        ordering = ["lesson_date"]


class LessonVideo(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.DO_NOTHING, related_name="videos"
    )
    title = models.CharField(max_length=200, blank=True)
    video_url = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        managed = False
        db_table = "lesson_video"
        ordering = ["order", "id"]


class LessonMaterial(models.Model):
    class Kind(models.TextChoices):
        FILE = "FILE", "파일"
        LINK = "LINK", "링크"

    lesson = models.ForeignKey(
        Lesson, on_delete=models.DO_NOTHING, related_name="materials"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=200)
    file_url = models.URLField(blank=True, null=True)
    link_url = models.URLField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "lesson_material"


class Assignment(models.Model):
    class WeightTier(models.TextChoices):
        HIGH = "HIGH", "상"
        MID = "MID", "중"
        LOW = "LOW", "하"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField()
    is_required = models.BooleanField(default=True)
    allow_late = models.BooleanField(default=True)
    is_team = models.BooleanField(default=False)
    weight_tier = models.CharField(
        max_length=10, choices=WeightTier.choices, default=WeightTier.MID
    )
    late_penalty = models.PositiveSmallIntegerField(default=0)
    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "assignment"


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.DO_NOTHING, related_name="submissions"
    )
    student_id = models.IntegerField(null=True, blank=True)
    team_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    last_editor_id = models.IntegerField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    final_score = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "submission"


class SubmissionFile(models.Model):
    class Kind(models.TextChoices):
        PY = "PY", ".py"
        IPYNB = "IPYNB", ".ipynb"
        OTHER = "OTHER", "그 외"

    submission = models.ForeignKey(
        Submission, on_delete=models.DO_NOTHING, related_name="files"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file_url = models.URLField()
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()

    class Meta:
        managed = False
        db_table = "submission_file"


class AiEvaluation(models.Model):
    submission = models.OneToOneField(
        Submission, on_delete=models.DO_NOTHING, related_name="ai_evaluation"
    )
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "ai_evaluation"


class Evaluation(models.Model):
    submission = models.OneToOneField(
        Submission, on_delete=models.DO_NOTHING, related_name="evaluation"
    )
    score = models.IntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "evaluation"


class AssignmentFile(models.Model):
    class Kind(models.TextChoices):
        FILE = "FILE", "파일"
        LINK = "LINK", "링크"

    assignment = models.ForeignKey(
        Assignment, on_delete=models.DO_NOTHING, related_name="attachments"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=200, blank=True)
    file_url = models.URLField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    link_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "assignment_file"
        ordering = ["order", "id"]

    @property
    def is_link(self):
        return self.kind == self.Kind.LINK

    @property
    def display_name(self):
        return self.title or self.file_name or self.link_url

    @property
    def url(self):
        return self.link_url if self.is_link else self.file_url

    @property
    def ext(self):
        if self.is_link:
            return "URL"
        suffix = Path(self.file_name).suffix.lstrip(".").upper()
        return suffix[:4] or "FILE"


class Todo(models.Model):
    student_id = models.IntegerField()
    content = models.CharField(max_length=500)
    is_done = models.BooleanField(default=False)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "todo"
        ordering = ["is_done", "-created_at"]
