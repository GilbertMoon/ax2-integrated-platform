from urllib.parse import urlsplit

from django import forms

from bug_reports.models import BugReport


class ReportForm(forms.ModelForm):
    description = forms.CharField(
        label="오류 내용",
        max_length=10000,
        widget=forms.Textarea(
            attrs={
                "rows": 7,
                "placeholder": "어떤 작업을 하셨나요?\n예상한 결과와 실제로 발생한 문제를 알려 주세요.",
            }
        ),
    )

    class Meta:
        model = BugReport
        fields = ["title", "page_url", "description", "screenshot"]
        widgets = {
            "screenshot": forms.FileInput(attrs={"accept": "image/png,image/jpeg,image/webp"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields[
            "screenshot"
        ].help_text = "PNG, JPG, WebP · 최대 5MB. 개인정보나 비밀번호는 가려 주세요."
        self.fields["page_url"].help_text = "오류가 발생한 페이지 주소 또는 경로를 입력해 주세요."

    def clean_page_url(self):
        value = self.cleaned_data["page_url"]
        if not value:
            return value
        try:
            parsed = urlsplit(value)
            if not (
                value.startswith("/") or (parsed.scheme in {"http", "https"} and parsed.netloc)
            ):
                raise ValueError
        except ValueError as error:
            raise forms.ValidationError(
                "http(s) 주소 또는 /로 시작하는 경로를 입력해 주세요."
            ) from error
        # Query strings can contain credentials or personal information.
        if not parsed.netloc:
            return parsed.path
        # Keep ports for local development, strip any embedded user information.
        return f"{parsed.scheme}://{parsed.netloc.rsplit('@', 1)[-1]}{parsed.path}"

    def clean_screenshot(self):
        upload = self.cleaned_data.get("screenshot")
        if upload:
            if upload.size > 5 * 1024 * 1024:
                raise forms.ValidationError("캡처 이미지는 5MB 이하로 첨부해 주세요.")
            image = upload.image
            extensions = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}
            if image.format not in extensions or image.width * image.height > 20000000:
                raise forms.ValidationError(
                    "2천만 화소 이하의 PNG, JPG, WebP 이미지를 첨부해 주세요."
                )
            upload.name = "capture." + extensions[image.format]
        return upload


class StatusForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}
