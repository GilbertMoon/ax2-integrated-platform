from datetime import timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from rounds.models import EvaluationRound, QuestionTemplate, TemplateQuestion


class EvaluationRoundForm(forms.ModelForm):
    class Meta:
        model = EvaluationRound
        fields = [
            "title",
            "description",
            "status",
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
            "status": forms.Select(
                attrs={"class": "form-select"}
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

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("evaluation_start_at")
        end = cleaned_data.get("evaluation_end_at")

        if start and end and start >= end:
            self.add_error(
                "evaluation_end_at",
                "종료 시각은 시작 시각보다 늦어야 합니다.",
            )

        team_weight = cleaned_data.get("team_score_weight") or 0
        personal_weight = cleaned_data.get("personal_score_weight") or 0
        tutor_weight = cleaned_data.get("tutor_score_weight") or 0

        if team_weight + personal_weight + tutor_weight != 100:
            self.add_error(
                "team_score_weight",
                "팀·개인·튜터 점수 비율의 합은 100%여야 합니다.",
            )

        return cleaned_data


class QuestionTemplateForm(forms.ModelForm):
    """템플릿 기본 정보 폼.

    평가 유형은 빈 선택("---------") 없이 팀 평가를 기본값으로 둔다 - 유형을 고르지 않은
    템플릿은 어차피 저장할 수 없어서 빈 선택지가 실수만 늘린다.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category = self.fields["category"]
        category.choices = QuestionTemplate.Category.choices
        if not self.instance.pk:
            category.initial = QuestionTemplate.Category.TEAM

    class Meta:
        model = QuestionTemplate
        fields = ("name", "description", "category")
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "예: 5기 팀 평가"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {"name": "템플릿 이름", "description": "설명", "category": "평가 유형"}


class TemplateQuestionForm(forms.ModelForm):
    """문항 한 줄. 순서는 화면에 나온 순서대로 저장 시 다시 매긴다.

    빈 줄은 그냥 무시한다 - 응답 형식 select는 브라우저가 항상 값을 보내므로, 문항을 비워 둔
    여유 줄까지 "필수 항목" 오류를 내면 화면을 쓸 수 없다.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prompt"].required = False
        self.fields["competency"].choices = [
            ("", "역량 미지정")
        ] + TemplateQuestion.Competency.choices
        if not self.instance.pk:
            # 새 줄은 1~5점을 기본으로 둔다 - 점수 문항이 하나도 없으면 회차를 시작할 수 없다.
            self.fields["response_type"].initial = TemplateQuestion.ResponseType.RATING_5

    def _post_clean(self):
        # 문항을 비워 둔 줄은 저장하지 않으므로 모델 검증(TemplateQuestion.clean)도 건너뛴다.
        if not (self.cleaned_data.get("prompt") or "").strip():
            return
        super()._post_clean()

    class Meta:
        model = TemplateQuestion
        fields = ("prompt", "response_type", "competency", "is_required")
        widgets = {
            "prompt": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "예: 결과물의 완성도는 충분한가요?"}
            ),
            "response_type": forms.Select(attrs={"class": "form-select"}),
            "competency": forms.Select(attrs={"class": "form-select"}),
            "is_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
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
            raise forms.ValidationError("문항을 한 개 이상 입력해 주세요.")


TemplateQuestionFormSet = forms.inlineformset_factory(
    QuestionTemplate,
    TemplateQuestion,
    form=TemplateQuestionForm,
    formset=BaseTemplateQuestionFormSet,
    extra=3,
    can_delete=True,
)

class ProjectInfoForm(forms.Form):
    """프로젝트 회차 생성 폼."""

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
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    team_end = forms.DateField(
        label="프로젝트 종료",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )

    evaluationround_id = forms.ModelChoiceField(
        label="연결 평가 회차",
        queryset=EvaluationRound.objects.all().order_by("-id"),
        empty_label="평가 회차를 선택하세요",
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("team_start")
        end = cleaned.get("team_end")

        if start and end and start > end:
            raise forms.ValidationError(
                "프로젝트 종료일은 시작일보다 빠를 수 없습니다."
            )

        return cleaned