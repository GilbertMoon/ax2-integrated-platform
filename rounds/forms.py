from datetime import timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from rounds.models import (
    EvaluationRound,
    QuestionTemplate,
    RoundParticipant,
    TemplateQuestion,
)


def _student_queryset():
    """승인된 활성 수강생 목록."""
    return (
        User.objects.filter(
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
            is_active=True,
        )
        .order_by("student_number", "first_name", "email")
    )


class EvaluationRoundForm(forms.ModelForm):
    """평가 회차 설정 폼.

    - status는 폼에서 직접 수정하지 않는다.
    - 참가 수강생은 화면에서 직접 선택하지 않고 자동으로 결정한다.
    - 신규 회차: 승인된 활성 수강생 전체
    - 기존 회차: 기존 참가자를 유지하면서 현재 승인된 활성 수강생을 포함한다.
    """

    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.MultipleHiddenInput(),
    )

    target_team_count = forms.IntegerField(
        required=False,
        min_value=2,
    )
    
    team_score_weight = forms.IntegerField(
        label="팀 점수 비율",
        min_value=0,
        max_value=100,
        required=False,
    )

    personal_score_weight = forms.IntegerField(
        label="개인 점수 비율",
        min_value=0,
        max_value=100,
        required=False,
    )

    tutor_score_weight = forms.IntegerField(
        label="튜터 점수 비율",
        min_value=0,
        max_value=100,
        required=False,
    )

    class Meta:
        model = EvaluationRound
        fields = [
            "title",
            "description",
            "evaluation_start_at",
            "evaluation_end_at",
            "target_team_count",
            "team_score_weight",
            "personal_score_weight",
            "tutor_score_weight",
            "team_template",
            "peer_template",
            "participants",
        ]
        widgets = {
            "evaluation_start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "evaluation_end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "target_team_count": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        now = timezone.localtime()

        # 신규 회차의 기본 날짜/시간
        if not self.instance.pk:
            self.initial.setdefault(
                "evaluation_start_at",
                now + timedelta(days=1),
            )
            self.initial.setdefault(
                "evaluation_end_at",
                now + timedelta(days=2),
            )

        # 기본 가중치
        if not self.is_bound:
            self.fields["team_score_weight"].initial = (
                self.instance.team_score_weight
            )
            self.fields["personal_score_weight"].initial = (
                self.instance.personal_score_weight
            )
            self.fields["tutor_score_weight"].initial = (
                self.instance.tutor_score_weight
            )

        # 목표 팀 수는 시스템에서 관리하되 화면에서는 표시하지 않는다.
        self.fields["target_team_count"].widget = forms.HiddenInput()

        eligible_queryset = _student_queryset()

        existing_participant_ids = set()

        if self.instance.pk:
            existing_participant_ids = set(
                RoundParticipant.objects.filter(
                    round=self.instance
                ).values_list("user_id", flat=True)
            )

        # 기존 참가자가 현재 비활성 상태가 되어도
        # 기존 회차의 참가자 목록에서는 제거되지 않도록 한다.
        participant_queryset = (
            User.objects.filter(
                Q(pk__in=existing_participant_ids)
                | Q(
                    role=User.Role.STUDENT,
                    approval_status=User.ApprovalStatus.APPROVED,
                    is_active=True,
                )
            )
            .distinct()
            .order_by(
                "student_number",
                "first_name",
                "email",
            )
        )

        self.fields["participants"].queryset = participant_queryset

        if not self.is_bound:
            if self.instance.pk:
                self.initial["participants"] = list(
                    existing_participant_ids
                )
            else:
                self.initial["participants"] = list(
                    eligible_queryset.values_list("pk", flat=True)
                )

        # 신규 회차에서는 archived 템플릿을 제외한다.
        # 기존 회차에서는 현재 사용 중인 템플릿이 archived 되었더라도 유지한다.
        current_team_template_id = self.instance.team_template_id
        current_peer_template_id = self.instance.peer_template_id

        team_filter = Q(is_archived=False)

        if current_team_template_id:
            team_filter |= Q(pk=current_team_template_id)

        peer_filter = Q(is_archived=False)

        if current_peer_template_id:
            peer_filter |= Q(pk=current_peer_template_id)

        self.fields["team_template"].queryset = (
            QuestionTemplate.objects.filter(
                Q(category=QuestionTemplate.Category.TEAM)
                & team_filter
            ).order_by("name")
        )

        self.fields["peer_template"].queryset = (
            QuestionTemplate.objects.filter(
                Q(category=QuestionTemplate.Category.PEER)
                & peer_filter
            ).order_by("name")
        )

        # datetime-local 입력값을 명시적으로 처리한다.
        self.fields["evaluation_start_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["evaluation_end_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

    def clean(self):
        cleaned_data = super().clean()

        start_at = cleaned_data.get("evaluation_start_at")
        end_at = cleaned_data.get("evaluation_end_at")

        if start_at and end_at and start_at >= end_at:
            self.add_error(
                "evaluation_end_at",
                "평가 종료 일시는 시작 일시보다 늦어야 합니다.",
            )

        # 가중치가 POST되지 않은 경우 기본값을 사용한다.
        team_weight = cleaned_data.get("team_score_weight")
        personal_weight = cleaned_data.get("personal_score_weight")
        tutor_weight = cleaned_data.get("tutor_score_weight")

        if team_weight is None:
            team_weight = 40

        if personal_weight is None:
            personal_weight = 60

        if tutor_weight is None:
            tutor_weight = 0

        cleaned_data["team_score_weight"] = team_weight
        cleaned_data["personal_score_weight"] = personal_weight
        cleaned_data["tutor_score_weight"] = tutor_weight

        if team_weight + personal_weight + tutor_weight != 100:
            self.add_error(
                "team_score_weight",
                "팀·개인·튜터 점수 비율의 합은 100%여야 합니다.",
            )


        # 참가 수강생은 화면에서 직접 선택하지 않고 자동 결정한다.
        eligible_ids = set(
            _student_queryset().values_list("pk", flat=True)
        )

        if self.instance.pk:
            existing_ids = set(
                RoundParticipant.objects.filter(
                    round=self.instance
                ).values_list("user_id", flat=True)
            )

            participant_ids = existing_ids | eligible_ids
        else:
            participant_ids = eligible_ids

        cleaned_data["participants"] = User.objects.filter(
            pk__in=participant_ids
        )

        return cleaned_data

class ProjectInfoForm(forms.Form):
    """프로젝트 회차 기본 정보 폼."""

    name = forms.CharField(
        label="프로젝트명",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "프로젝트명을 입력하세요",
            }
        ),
    )

    description = forms.CharField(
        label="설명",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "프로젝트에 대한 설명을 입력하세요",
            }
        ),
    )

    team_start = forms.DateField(
        label="프로젝트 시작",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    team_end = forms.DateField(
        label="프로젝트 종료",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("team_start")
        end = cleaned.get("team_end")

        if start and end and start > end:
            self.add_error(
                "team_end",
                "프로젝트 종료일은 시작일보다 빠를 수 없습니다.",
            )

        return cleaned


class ProjectEvaluationRoundForm(forms.ModelForm):
    """프로젝트 회차에 연결된 평가 회차 설정 폼.

    프로젝트 생성/수정 화면에서 사용한다.

    status는 직접 변경하지 않는다.
    """

    participants = forms.ModelMultipleChoiceField(
        label="참가 수강생",
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select",
                "size": 10,
            }
        ),
    )

    class Meta:
        model = EvaluationRound
        fields = [
            "title",
            "description",
            "evaluation_start_at",
            "evaluation_end_at",
            "target_team_count",
            "team_score_weight",
            "personal_score_weight",
            "tutor_score_weight",
            "team_template",
            "peer_template",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "evaluation_start_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "evaluation_end_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "target_team_count": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 2,
                }
            ),
            "team_score_weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "personal_score_weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "tutor_score_weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "team_template": forms.Select(
                attrs={"class": "form-select"}
            ),
            "peer_template": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        student_queryset = _student_queryset()

        if self.instance and self.instance.pk:
            existing_participant_ids = (
                self.instance.participants.values_list(
                    "user_id",
                    flat=True,
                )
            )

            student_queryset = (
                User.objects.filter(
                    Q(
                        role=User.Role.STUDENT,
                        approval_status=User.ApprovalStatus.APPROVED,
                        is_active=True,
                    )
                    | Q(pk__in=existing_participant_ids)
                )
                .order_by(
                    "student_number",
                    "first_name",
                    "email",
                )
            )

        self.fields["participants"].queryset = student_queryset

        self.fields["team_template"].queryset = (
            QuestionTemplate.objects
            .filter(
                category=QuestionTemplate.Category.TEAM,
                is_archived=False,
            )
            .order_by("name")
        )

        self.fields["peer_template"].queryset = (
            QuestionTemplate.objects
            .filter(
                category=QuestionTemplate.Category.PEER,
                is_archived=False,
            )
            .order_by("name")
        )

        self.fields["evaluation_start_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["evaluation_end_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        if not self.instance.pk:
            now = timezone.localtime()

            default_start = now.replace(
                minute=0,
                second=0,
                microsecond=0,
            )

            default_end = default_start + timedelta(days=7)

            self.fields["evaluation_start_at"].initial = default_start
            self.fields["evaluation_end_at"].initial = default_end

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("evaluation_start_at")
        end = cleaned_data.get("evaluation_end_at")

        if start and end and start >= end:
            self.add_error(
                "evaluation_end_at",
                "종료 시각은 시작 시각보다 늦어야 합니다.",
            )

        team_weight = cleaned_data.get("team_score_weight")
        personal_weight = cleaned_data.get("personal_score_weight")
        tutor_weight = cleaned_data.get("tutor_score_weight")

        if (
            team_weight is not None
            and personal_weight is not None
            and tutor_weight is not None
            and team_weight + personal_weight + tutor_weight != 100
        ):
            self.add_error(
                "team_score_weight",
                "팀·개인·튜터 점수 비율의 합은 100%여야 합니다.",
            )

        return cleaned_data

class QuestionTemplateForm(forms.ModelForm):
    """문항 템플릿 기본 정보 폼."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        category = self.fields["category"]
        category.choices = QuestionTemplate.Category.choices

        if not self.instance.pk:
            category.initial = QuestionTemplate.Category.TEAM

    class Meta:
        model = QuestionTemplate
        fields = (
            "name",
            "description",
            "category",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "예: 5기 팀 평가",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                }
            ),
            "category": forms.Select(
                attrs={"class": "form-select"}
            ),
        }
        labels = {
            "name": "템플릿 이름",
            "description": "설명",
            "category": "평가 유형",
        }


class TemplateQuestionForm(forms.ModelForm):
    """문항 한 줄."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["prompt"].required = False

        self.fields["competency"].choices = [
            ("", "역량 미지정"),
        ] + list(TemplateQuestion.Competency.choices)

        if not self.instance.pk:
            self.fields[
                "response_type"
            ].initial = TemplateQuestion.ResponseType.RATING_5

    def _post_clean(self):
        if not (
            self.cleaned_data.get("prompt") or ""
        ).strip():
            return

        super()._post_clean()

    class Meta:
        model = TemplateQuestion
        fields = (
            "prompt",
            "response_type",
            "competency",
            "is_required",
        )
        widgets = {
            "prompt": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "예: 결과물의 완성도는 충분한가요?",
                }
            ),
            "response_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "competency": forms.Select(
                attrs={"class": "form-select"}
            ),
            "is_required": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "prompt": "문항",
            "response_type": "응답 형식",
            "competency": "역량",
            "is_required": "필수",
        }


class BaseTemplateQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        filled = [
            form
            for form in self.forms
            if form.cleaned_data
            and not form.cleaned_data.get("DELETE")
            and form.cleaned_data.get("prompt")
        ]

        if not filled:
            raise forms.ValidationError(
                "문항을 한 개 이상 입력해 주세요."
            )


TemplateQuestionFormSet = forms.inlineformset_factory(
    QuestionTemplate,
    TemplateQuestion,
    form=TemplateQuestionForm,
    formset=BaseTemplateQuestionFormSet,
    extra=3,
    can_delete=True,
)