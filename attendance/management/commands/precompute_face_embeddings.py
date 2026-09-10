from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from attendance.face_services import ensure_embedding_cached

User = get_user_model()


class Command(BaseCommand):
    help = "모든 학생의 얼굴 특징 벡터를 미리 계산해서 저장합니다."

    def handle(self, *args, **options):
        students = User.objects.filter(
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
            is_active=True,
        ).exclude(profile_image="")

        total = students.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("프로필 사진이 등록된 학생이 없습니다."))
            return

        self.stdout.write(f"총 {total}명의 얼굴 벡터를 확인/계산합니다...")

        success_count = 0
        fail_count = 0
        for student in students:
            name = student.first_name or student.email
            ok = ensure_embedding_cached(student)
            if ok:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ {name}"))
            else:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"  ❌ {name} (실패 - 얼굴인식 서버 확인 필요)"))

        self.stdout.write(
            self.style.SUCCESS(f"\n완료: 성공 {success_count}명 / 실패 {fail_count}명")
        )
