from django import template
from django.utils.safestring import mark_safe

from lms_modules.common.html_sanitize import clean_assignment_description

register = template.Library()


@register.filter(name="sanitize_assignment_html")
def sanitize_assignment_html(value):
    """과제 설명을 화면에 그대로 내보내기 직전, 허용 태그만 남기고 다시 정제한다."""
    return mark_safe(clean_assignment_description(value))
