from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import is_operations_user
from bug_reports.forms import ReportForm, StatusForm
from bug_reports.models import BugReport


def visible_reports(user):
    reports = BugReport.objects.select_related("reporter", "updated_by")
    return reports if is_operations_user(user) else reports.filter(reporter=user)


@login_required
@require_GET
def index(request):
    reports = visible_reports(request.user)
    status = request.GET.get("status", "")
    if status in BugReport.Status.values:
        reports = reports.filter(status=status)
    return render(
        request,
        "bug_reports/index.html",
        {
            "page": Paginator(reports, 20).get_page(request.GET.get("page")),
            "operations": is_operations_user(request.user),
            "statuses": BugReport.Status.choices,
            "selected_status": status,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    form = ReportForm(
        request.POST or None,
        request.FILES or None,
        initial={"page_url": request.GET.get("page", "")[:1000]},
    )
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.save()
        messages.success(
            request, "오류 신고가 접수되었습니다. 처리 상태는 이 화면에서 확인할 수 있습니다."
        )
        return redirect("bug_reports:detail", pk=report.pk)
    return render(request, "bug_reports/create.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, pk):
    report = get_object_or_404(visible_reports(request.user), pk=pk)
    operations = is_operations_user(request.user)
    if request.method == "POST" and not operations:
        raise PermissionDenied
    form = StatusForm(request.POST or None, instance=report)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.updated_by = request.user
        report.save()
        messages.success(request, "처리 상태를 저장했습니다.")
        return redirect("bug_reports:detail", pk=pk)
    return render(
        request,
        "bug_reports/detail.html",
        {"report": report, "form": form, "operations": operations},
    )


@login_required
@require_GET
def screenshot(request, pk):
    report = get_object_or_404(visible_reports(request.user), pk=pk)
    if not report.screenshot:
        raise Http404
    try:
        result = FileResponse(
            report.screenshot.open("rb"),
            filename=f"report-{report.pk}.{report.screenshot.name.rsplit('.', 1)[-1]}",
        )
    except FileNotFoundError as error:
        raise Http404 from error
    result["Cache-Control"] = "private, no-store"
    result["X-Content-Type-Options"] = "nosniff"
    return result
