(function () {
  "use strict";
  const root = document.getElementById("prd-home-app");
  if (!root) return;

  const state = {
    scope: "mine",
    tab: "all",
    status: "",
    sort: "default",
    page: 1,
    dashboardMode: null,
    dashboardView: "tutoring",
    participantUserId: null,
    roundScope: "all",
    projectScope: "all",
    roundTitles: new Map()
  };

  const labels = {
    new_product: "신규 프로젝트",
    new_feature: "신규 기능",
    improvement: "기능 개선",
    in_progress: "진행 중",
    completed: "완료",
    held: "보류",
    dropped: "드랍"
  };

  const statusClasses = {
    in_progress: "status-in-progress",
    completed: "status-completed",
    held: "status-held",
    dropped: "status-dropped"
  };

  const prdTypeIcons = {
    new_product: "idea-icon-rocket-takeoff",
    new_feature: "idea-icon-lightning-charge",
    improvement: "idea-icon-magic"
  };

  const projectScopeLabels = {
    round_team: "회차 팀",
    team: "일반 팀",
    personal: "개인"
  };

  const list = document.getElementById("home-list");
  const loading = document.getElementById("home-loading");
  const empty = document.getElementById("home-empty");
  const alertBox = document.getElementById("home-alert");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const deleteConfirmElement = document.getElementById("home-delete-confirm-modal");
  const deleteConfirmModal = bootstrap.Modal.getOrCreateInstance(deleteConfirmElement);
  const deleteConfirmButton = document.getElementById("home-delete-confirm");
  const deleteError = document.getElementById("home-delete-error");

  let pendingDeletion = null;
  let studentSearchTimer = null;
  let studentSearchRequest = 0;
  let currentUser = null;

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function avatarText(value) {
    const name = String(value || "?").trim();
    if (!name) return "?";
    return Array.from(name).slice(-2).join("");
  }

  function userId(user) {
    if (!user) return null;
    const raw = user.user_id ?? user.id;
    if (raw === null || raw === undefined || raw === "") return null;
    const numeric = Number(raw);
    return Number.isSafeInteger(numeric) ? numeric : String(raw);
  }

  function isCurrentUser(user) {
    if (!currentUser || !user) return false;
    const targetId = userId(user);
    const currentId = userId(currentUser);

    if (targetId !== null && currentId !== null) {
      return String(targetId) === String(currentId);
    }

    return Boolean(
      user.display_name &&
      currentUser.display_name &&
      user.display_name === currentUser.display_name
    );
  }

  function avatarColor(user) {
    const rawId = Number(user.user_id ?? user.id);
    if (Number.isSafeInteger(rawId)) {
      return (Math.imul(rawId, -1640531527) >>> 0) % 8;
    }

    const name = user.display_name || "?";
    let hash = 0;
    for (let index = 0; index < name.length; index += 1) {
      hash = ((hash * 31) + name.charCodeAt(index)) >>> 0;
    }
    return hash % 8;
  }

  function avatarClass(baseClass, user) {
    return baseClass + (
      isCurrentUser(user)
        ? " is-current-user"
        : " avatar-color-" + avatarColor(user)
    );
  }

  function firstErrorDetail(value) {
    if (typeof value === "string") return value.trim();

    if (Array.isArray(value)) {
      for (const item of value) {
        const detail = firstErrorDetail(item);
        if (detail) return detail;
      }
      return "";
    }

    if (value && typeof value === "object") {
      for (const item of Object.values(value)) {
        const detail = firstErrorDetail(item);
        if (detail) return detail;
      }
    }

    return "";
  }

  async function requestJson(url, options, fallbackMessage) {
    let response;

    try {
      response = await fetch(url, {
        credentials: "same-origin",
        ...(options || {})
      });
    } catch (networkError) {
      throw new Error("서버에 연결하지 못했습니다. 네트워크 상태를 확인해 주세요.");
    }

    const contentType = response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
      throw new Error(
        response.status === 401 || response.redirected
          ? "로그인 상태가 만료되었습니다. 페이지를 새로고침해 주세요."
          : fallbackMessage
      );
    }

    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(
        firstErrorDetail(payload.error?.details) ||
        payload.error?.message ||
        fallbackMessage
      );
    }

    return payload.data;
  }

  function showError(message) {
    alertBox.className = "alert alert-danger";
    alertBox.textContent = message;
  }

  async function mutation(url, body) {
    return requestJson(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(body)
      },
      "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
    );
  }

  function pageUrl(id) {
    return "/ideas/prds/" + encodeURIComponent(id) + "/write/";
  }

  function brainstormUrl(id) {
    return "/ideas/prds/" + encodeURIComponent(id) + "/brainstorm/";
  }

  function deleteUrl(id) {
    return root.dataset.deleteApiUrlTemplate.replace(
      "/0/delete/",
      "/" + encodeURIComponent(id) + "/delete/"
    );
  }

  function askToDelete(item) {
    pendingDeletion = item;
    document.getElementById("home-delete-prd-title").textContent = item.title;
    deleteError.classList.add("d-none");
    deleteError.textContent = "";
    deleteConfirmButton.disabled = false;
    deleteConfirmModal.show();
  }

  function localDateKey(date) {
    return [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, "0"),
      String(date.getDate()).padStart(2, "0")
    ].join("-");
  }

  function deadlineState(item) {
    if (!item.deadline || item.status === "completed" || item.status === "dropped") {
      return "";
    }

    const today = localDateKey(new Date());

    if (item.deadline < today) return "overdue";
    if (item.deadline === today) return "today";

    return "";
  }

  function relativeTime(value) {
    const seconds = Math.max(
      0,
      Math.floor((Date.now() - new Date(value).getTime()) / 1000)
    );

    if (seconds < 60) return "방금 전";
    if (seconds < 3600) return Math.floor(seconds / 60) + "분 전";
    if (seconds < 86400) return Math.floor(seconds / 3600) + "시간 전";
    if (seconds < 172800) return "어제";
    if (seconds < 604800) return Math.floor(seconds / 86400) + "일 전";

    return new Intl.DateTimeFormat("ko-KR", {
      month: "numeric",
      day: "numeric"
    }).format(new Date(value));
  }

  function shortDate(value) {
    if (!value) return "";

    const parts = String(value).split("-");
    if (parts.length !== 3) return String(value);

    return parts[0].slice(-2) + "-" + parts[1] + "-" + parts[2];
  }

  function renderRecentList(target, activities) {
    target.replaceChildren();

    if (!activities.length) {
      const emptyState = el("div", "home-activity-empty idea-empty-compact");
      const icon = el("span", "idea-empty-icon");
      icon.append(el("i", "idea-icon idea-icon-lightning-charge"));
      emptyState.append(
        icon,
        el("strong", "", "아직 최근 활동이 없습니다."),
        el("span", "", "PRD를 만들거나 수정하면 주요 변경 내역이 여기에 모입니다.")
      );
      target.append(emptyState);
      return;
    }

    activities.forEach(function (activity) {
      const link = el("a", "home-recent-item");
      link.href = pageUrl(activity.prd_id);

      const user = {
        user_id: activity.actor_user_id,
        display_name: activity.actor_display_name
      };

      const avatar = el(
        "span",
        avatarClass("home-recent-avatar", user),
        avatarText(activity.actor_display_name)
      );

      const copy = el("div", "home-recent-copy");
      const sentence = el("p");

      sentence.append(
        el("strong", "", activity.actor_display_name),
        document.createTextNode("님이 "),
        el("em", "", activity.prd_title),
        document.createTextNode("의 " + activity.description)
      );

      const time = el("time", "", relativeTime(activity.created_at));
      time.dateTime = activity.created_at;

      copy.append(sentence, time);
      link.append(avatar, copy);
      target.append(link);
    });
  }

  function renderActivity(data) {
    const weeklyRoot = document.getElementById("home-weekly-activity");
    const recentRoot = document.getElementById("home-recent-activity");

    if (!weeklyRoot || !recentRoot) return;

    const days = data.weekly_activity || [];
    const maximum = Math.max(
      1,
      ...days.map(function (day) {
        return day.count;
      })
    );
    const today = localDateKey(new Date());

    weeklyRoot.replaceChildren();

    days.forEach(function (day) {
      const item = el(
        "div",
        "home-activity-day" + (day.date === today ? " is-today" : "")
      );
      const track = el("div", "home-activity-track");
      const bar = el("i", "home-activity-bar");

      bar.style.height = (
        day.count
          ? Math.max(12, Math.round(day.count * 100 / maximum))
          : 6
      ) + "%";

      track.title = day.date + " · " + day.count + "회";
      track.append(bar);

      item.append(
        track,
        el("span", "", day.day_label),
        el("strong", "", day.count ? day.count + "회" : "–")
      );

      weeklyRoot.append(item);
    });

    const activities = data.recent_activity || [];
    renderRecentList(recentRoot, activities);

    const moreButton = document.getElementById("recent-activity-more");

    if (moreButton) {
      moreButton.classList.toggle(
        "d-none",
        (data.recent_activity_pagination?.total_items || 0) <= activities.length
      );
    }
  }

  async function fetchData() {
    loading.classList.remove("d-none");
    list.replaceChildren();
    empty.classList.add("d-none");
    alertBox.className = "alert d-none";

    const query = new URLSearchParams({
      scope: state.scope,
      tab: state.tab,
      sort: state.sort,
      page: String(state.page)
    });

    if (state.status) query.append("status", state.status);
    if (state.participantUserId) {
      query.append("participant_user_id", String(state.participantUserId));
    }
    if (state.roundScope !== "all") {
      query.append("round_scope", state.roundScope);
    }
    if (state.projectScope !== "all") {
      query.append("project_scope", state.projectScope);
    }
    if (state.dashboardMode === "tutor" || state.dashboardView !== "tutoring") {
      query.append("dashboard_view", state.dashboardView);
    }

    try {
      const data = await requestJson(
        root.dataset.apiUrl + "?" + query,
        null,
        "홈 정보를 불러오지 못했습니다."
      );
      render(data);
    } catch (error) {
      showError(error.message);
    } finally {
      loading.classList.add("d-none");
    }
  }

  function applyDashboardMode(data) {
    const tutorMode = data.dashboard_mode === "tutor";
    const tutorManagementMode =
      tutorMode && data.dashboard_view === "tutoring";

    state.dashboardMode = data.dashboard_mode;
    state.dashboardView = data.dashboard_view || "editing";

    document
      .getElementById("standard-home-navigation")
      .classList.toggle("d-none", tutorMode);

    document
      .getElementById("standard-home-tabs")
      .classList.toggle("d-none", tutorMode);

    document
      .getElementById("tutor-home-heading")
      .classList.toggle("d-none", !tutorMode);

    document
      .getElementById("tutor-dashboard-navigation")
      .classList.toggle("d-none", !tutorMode);

    document
      .getElementById("tutor-student-filter")
      .classList.toggle("d-none", !tutorManagementMode);

    document
      .getElementById("home-hero-actions")
      .classList.remove("d-none");

    document
      .querySelectorAll(".tutor-dashboard-tab")
      .forEach(function (button) {
        const active =
          button.dataset.dashboardView === state.dashboardView;

        button.classList.toggle("active", active);
        button.setAttribute("aria-selected", String(active));
      });

    if (!tutorMode) return;

    document.getElementById("home-subtitle").textContent =
      tutorManagementMode
        ? "함께 참여 중인 프로젝트를 학생별로 찾고 진행 상황을 한눈에 확인하세요."
        : "직접 만들거나 편집 역할로 참여한 PRD를 작성하고 관리하세요.";

    document.getElementById("home-scope-description").textContent =
      tutorManagementMode
        ? "튜터 역할로 참여한 PRD만 표시됩니다."
        : "직접 만들었거나 편집자로 참여한 PRD입니다.";
  }

  function render(data) {
    currentUser = data.user || null;

    applyDashboardMode(data);

    const tutorMode = data.dashboard_mode === "tutor";
    const tutorManagementMode =
      tutorMode && data.dashboard_view === "tutoring";

    renderFilterOptions(data.filter_options || {});

    document.getElementById("home-greeting").textContent =
      "안녕하세요, " + data.user.display_name + "님 👋";

    const k = data.kpis;

    document.getElementById("kpi-total").textContent =
      k.total_prds + "건";
    document.getElementById("kpi-progress").textContent =
      k.in_progress_prds + "건";
    document.getElementById("kpi-average").textContent =
      k.average_completion_rate + "%";
    document.getElementById("kpi-completed").textContent =
      k.completed_prds + "건";
    document.getElementById("kpi-held").textContent =
      k.held_prds + "건";
    document.getElementById("kpi-due").textContent =
      k.due_this_week + "건";

    renderActivity(data);

    list.replaceChildren();
    empty.classList.toggle("d-none", data.items.length !== 0);

    document.getElementById("home-empty-title").textContent =
      tutorManagementMode
        ? (
            state.participantUserId
              ? "선택한 학생과 함께하는 PRD가 없습니다."
              : "튜터로 참여한 PRD가 없습니다."
          )
        : state.scope === "viewer"
          ? "뷰어로 참여한 PRD가 없습니다."
          : "조건에 맞는 PRD가 없습니다.";

    document.getElementById("home-empty-copy").textContent =
      tutorManagementMode
        ? "회차나 학생 범위를 바꾸면 다른 담당 PRD를 확인할 수 있어요."
        : state.scope === "viewer"
          ? "뷰어 권한으로 초대된 PRD가 생기면 이 목록에서 바로 확인할 수 있어요."
          : "첫 문서를 만들면 아이디어부터 작성 진행 상황까지 한곳에서 이어서 관리할 수 있어요.";

    document
      .getElementById("home-empty-create")
      .classList.toggle(
        "d-none",
        tutorManagementMode || state.scope === "viewer"
      );

    data.items.forEach(function (item) {
      const col = el("div", "col-12 col-md-6 col-xl-4");

      const card = el(
        "article",
        "card h-100 border idea-card-hover idea-clickable"
      );
      card.tabIndex = 0;
      card.setAttribute("role", "link");

      const body = el("div", "card-body d-flex flex-column");
      const cardTop = el("div", "prd-card-top mb-2");
      const badges = el("div", "d-flex flex-wrap gap-2");

      const typeBadge = el(
        "span",
        "badge home-type-badge home-type-" + (item.prd_type || "unknown")
      );
      const typeIcon = el("i", "idea-icon " + (prdTypeIcons[item.prd_type] || "idea-icon-file-earmark-text"));
      typeIcon.setAttribute("aria-hidden", "true");
      typeBadge.append(typeIcon, document.createTextNode(labels[item.prd_type] || item.prd_type));

      badges.append(
        typeBadge,
        el(
          "span",
          "badge " + (statusClasses[item.status] || "status-dropped"),
          labels[item.status] || item.status
        )
      );

      if (tutorMode) {
        const scopeText =
          projectScopeLabels[item.project_scope] || item.project_scope;

        const roundText = item.round_id
          ? (
              state.roundTitles.get(String(item.round_id)) ||
              "회차 #" + item.round_id
            ) + " · " + scopeText
          : scopeText;

        badges.append(
          el("span", "badge tutor-scope-badge", roundText)
        );
      }

      const roleLabels = {
        owner: "소유자",
        editor: "편집자",
        viewer: "뷰어",
        tutor: "튜터"
      };

      const roleClasses = {
        owner: "owner-role-badge",
        editor: "editor-role-badge",
        viewer: "viewer-role-badge",
        tutor: "tutor-role-badge"
      };

      const visibleRole = item.is_creator ? "owner" : item.my_role;

      // 홈 카드에서는 "소유자/뷰어"가 이미 탭 맥락으로 충분히 설명된다.
      // 의미가 있는 편집자/튜터 역할만 보조 태그로 남긴다.
      if (
        visibleRole &&
        ["editor", "tutor"].includes(visibleRole) &&
        roleLabels[visibleRole]
      ) {
        const roleBadge = el(
          "span",
          "badge " + roleClasses[visibleRole],
          roleLabels[visibleRole]
        );

        badges.append(roleBadge);
      }

      if (item.show_new_badge) {
        badges.append(
          el("span", "badge home-new-badge", "NEW")
        );
      }

      const dueState = deadlineState(item);

      const titleRow = el("div", "prd-card-title-row");
      const title = el("h3", "h6 fw-bold", item.title);
      const brain = el(
        "a",
        "prd-card-brainstorm",
        "아이디어 맵"
      );

      brain.href = brainstormUrl(item.id);
      brain.prepend(
        el("i", "idea-icon idea-icon-lightbulb-fill")
      );
      brain.addEventListener("click", function (event) {
        event.stopPropagation();
      });

      cardTop.append(badges);
      titleRow.append(title, brain);

      const description = el(
        "p",
        "small text-secondary prd-card-description",
        item.description || "한 줄 소개가 없습니다."
      );

      const progressText = el(
        "div",
        "d-flex justify-content-between small mb-1 mt-auto"
      );

      progressText.append(
        el("span", "text-secondary", "완성도"),
        el("strong", "", item.completion_rate + "%")
      );

      const progress = el("div", "progress mb-3");
      progress.style.height = "6px";

      const bar = el("div", "progress-bar");
      bar.style.width = item.completion_rate + "%";
      progress.append(bar);

      const footer = el(
        "div",
        "d-flex justify-content-between align-items-center pt-2 border-top"
      );

      const avatars = el(
        "div",
        "d-flex align-items-center"
      );

      item.participants.forEach(function (participant) {
        const avatar = el(
          "span",
          avatarClass("participant-avatar", participant),
          avatarText(participant.display_name)
        );

        avatars.append(avatar);
      });

      if (item.participant_count > 4) {
        avatars.append(
          el(
            "span",
            "small text-secondary ms-1",
            "+" + (item.participant_count - 4)
          )
        );
      }

      const meta = el(
        "div",
        "small text-secondary text-end prd-card-deadline" +
          (dueState ? " is-" + dueState : "")
      );

      if (!item.deadline) {
        const noDeadline = el(
          "span",
          "prd-card-no-deadline"
        );

        noDeadline.append(
          document.createTextNode("마감일 없음")
        );

        meta.append(noDeadline);
      } else if (dueState === "today") {
        const todayAlert = el(
          "span",
          "prd-card-deadline-alert"
        );

        todayAlert.append(
          el("span", "prd-card-deadline-bang", "!"),
          document.createTextNode(" 오늘 마감 · D-Day")
        );

        meta.append(todayAlert);
      } else {
        const deadlineDate = el(
          "span",
          "prd-card-deadline-date",
          "마감 " + shortDate(item.deadline)
        );

        meta.append(deadlineDate);

        if (item.d_day) {
          meta.append(
            document.createTextNode(" · " + item.d_day)
          );
        }
      }

      footer.append(avatars, meta);

      body.append(
        cardTop,
        titleRow,
        description,
        progressText,
        progress,
        footer
      );

      card.append(body);

      card.addEventListener("click", function () {
        window.location.href = pageUrl(item.id);
      });

      card.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          window.location.href = pageUrl(item.id);
        }
      });

      if (item.can_delete) {
        const menuWrap = el(
          "div",
          "dropdown prd-card-menu"
        );

        const menuButton = el(
          "button",
          "prd-card-menu-button"
        );

        menuButton.type = "button";
        menuButton.dataset.bsToggle = "dropdown";
        menuButton.setAttribute(
          "aria-expanded",
          "false"
        );
        menuButton.setAttribute(
          "aria-label",
          item.title + " 메뉴"
        );
        menuButton.append(
          el("i", "idea-icon idea-icon-three-dots")
        );

        const menu = el(
          "ul",
          "dropdown-menu dropdown-menu-end"
        );

        const menuItem = el("li");
        const remove = el(
          "button",
          "dropdown-item text-danger",
          "삭제"
        );

        remove.type = "button";
        remove.prepend(
          el("i", "idea-icon idea-icon-trash3 me-2")
        );

        [
          menuWrap,
          menuButton,
          menu,
          remove
        ].forEach(function (node) {
          node.addEventListener(
            "click",
            function (event) {
              event.stopPropagation();
            }
          );
        });

        remove.addEventListener(
          "click",
          function () {
            askToDelete(item);
          }
        );

        menuItem.append(remove);
        menu.append(menuItem);
        menuWrap.append(menuButton, menu);
        card.append(menuWrap);
      }

      col.append(card);
      list.append(col);
    });

    renderPages(data.pagination);
  }

  function renderFilterOptions(options) {
    const select = document.getElementById("home-round-filter");
    const selectedValue = state.roundScope;

    state.roundTitles = new Map();
    select.replaceChildren(
      new Option("모든 회차", "all")
    );

    (options.rounds || []).forEach(function (round) {
      const value = String(round.id);
      state.roundTitles.set(value, round.title);
      select.append(
        new Option(round.title, value)
      );
    });

    if (options.has_roundless) {
      select.append(
        new Option("회차 없음", "none")
      );
    }

    const valueExists = Array
      .from(select.options)
      .some(function (option) {
        return option.value === selectedValue;
      });

    state.roundScope = valueExists
      ? selectedValue
      : "all";

    select.value = state.roundScope;
    window.StudioControls?.syncSelect(select);
  }

  function renderSelectedStudent(student) {
    const selected = document.getElementById(
      "tutor-selected-student"
    );

    selected.replaceChildren();

    if (!student) {
      selected.classList.add("d-none");
      return;
    }

    const avatar = el(
      "span",
      avatarClass("tutor-student-avatar", student),
      avatarText(student.display_name)
    );

    const copy = el(
      "span",
      "tutor-selected-copy"
    );

    copy.append(
      el("small", "", "선택한 학생"),
      el("strong", "", student.display_name)
    );

    const clear = el(
      "button",
      "tutor-student-clear"
    );

    clear.type = "button";
    clear.setAttribute(
      "aria-label",
      "학생 선택 해제"
    );
    clear.append(
      el("i", "idea-icon idea-icon-x-lg")
    );
    clear.addEventListener(
      "click",
      clearTutorStudentFilter
    );

    selected.append(
      avatar,
      copy,
      clear
    );
    selected.classList.remove("d-none");
  }

  function clearTutorStudentFilter() {
    const input = document.getElementById(
      "tutor-student-query"
    );
    const results = document.getElementById(
      "tutor-student-results"
    );

    const hadStudentFilter =
      state.participantUserId !== null;

    studentSearchRequest += 1;
    state.participantUserId = null;
    state.page = 1;

    input.value = "";
    results.classList.add("d-none");

    document
      .getElementById("tutor-student-help")
      .textContent =
        "전체 담당 프로젝트를 표시하고 있습니다. 학생 이름을 2자 이상 입력해 주세요.";

    renderSelectedStudent(null);

    if (hadStudentFilter) {
      fetchData();
    }
  }

  function renderStudentResults(data) {
    const resultRoot = document.getElementById(
      "tutor-student-results"
    );

    resultRoot.replaceChildren();

    if (!data.items.length) {
      resultRoot.append(
        el(
          "div",
          "tutor-student-empty",
          "함께 참여 중인 편집자를 찾지 못했습니다."
        )
      );
      resultRoot.classList.remove("d-none");
      return;
    }

    data.items.forEach(function (student) {
      const button = el(
        "button",
        "tutor-student-result"
      );
      button.type = "button";

      const avatar = el(
        "span",
        avatarClass("tutor-student-avatar", student),
        avatarText(student.display_name)
      );

      const copy = el(
        "span",
        "tutor-student-result-copy"
      );

      copy.append(
        el("strong", "", student.display_name),
        el(
          "small",
          "",
          student.email ||
            "함께하는 프로젝트 " +
              student.project_count +
              "개"
        )
      );

      button.append(
        avatar,
        copy,
        el(
          "span",
          "tutor-project-count",
          student.project_count + "개"
        )
      );

      button.addEventListener(
        "click",
        function () {
          state.participantUserId =
            student.user_id;
          state.page = 1;

          renderSelectedStudent(student);
          resultRoot.classList.add("d-none");

          document
            .getElementById("tutor-student-help")
            .textContent =
              student.display_name +
              " 학생이 편집자로 참여한 프로젝트입니다.";

          fetchData();
        }
      );

      resultRoot.append(button);
    });

    const pagination = data.pagination;

    if (pagination.total_pages > 1) {
      const pages = el(
        "div",
        "tutor-student-pages"
      );

      for (
        let page = 1;
        page <= pagination.total_pages;
        page += 1
      ) {
        const button = el(
          "button",
          page === pagination.page
            ? "active"
            : "",
          String(page)
        );

        button.type = "button";
        button.addEventListener(
          "click",
          function () {
            searchTutorStudents(page);
          }
        );

        pages.append(button);
      }

      resultRoot.append(pages);
    }

    resultRoot.classList.remove("d-none");
  }

  async function searchTutorStudents(page) {
    const input = document.getElementById(
      "tutor-student-query"
    );
    const resultRoot = document.getElementById(
      "tutor-student-results"
    );
    const spinner = document.getElementById(
      "tutor-student-spinner"
    );
    const help = document.getElementById(
      "tutor-student-help"
    );

    const query = input.value.trim();

    if (query.length < 2) {
      resultRoot.classList.add("d-none");
      help.textContent =
        "이름을 2자 이상 입력해 주세요.";
      return;
    }

    const requestId = ++studentSearchRequest;

    spinner.classList.remove("d-none");
    help.textContent = "학생을 찾고 있습니다.";

    try {
      const params = new URLSearchParams({
        q: query,
        page: String(page || 1),
        page_size: "8"
      });

      if (state.roundScope !== "all") {
        params.append(
          "round_scope",
          state.roundScope
        );
      }

      if (state.projectScope !== "all") {
        params.append(
          "project_scope",
          state.projectScope
        );
      }

      const data = await requestJson(
        root.dataset.tutorStudentsApiUrl +
          "?" +
          params,
        null,
        "학생을 검색하지 못했습니다."
      );

      if (
        requestId !== studentSearchRequest ||
        input.value.trim() !== query
      ) {
        return;
      }

      renderStudentResults(data);
      help.textContent =
        data.pagination.total_items +
        "명의 학생을 찾았습니다.";
    } catch (error) {
      if (requestId !== studentSearchRequest) {
        return;
      }

      resultRoot.replaceChildren(
        el(
          "div",
          "tutor-student-empty text-danger",
          error.message
        )
      );

      resultRoot.classList.remove("d-none");
      help.textContent =
        "검색 중 문제가 발생했습니다.";
    } finally {
      if (requestId === studentSearchRequest) {
        spinner.classList.add("d-none");
      }
    }
  }

  function renderPages(pagination) {
    const rootPages = document.getElementById(
      "home-pagination"
    );

    rootPages.replaceChildren();

    for (
      let page = 1;
      page <= pagination.total_pages;
      page += 1
    ) {
      const item = el(
        "li",
        "page-item" +
          (page === pagination.page
            ? " active"
            : "")
      );

      const button = el(
        "button",
        "page-link",
        String(page)
      );

      button.addEventListener(
        "click",
        function () {
          state.page = page;
          fetchData();
        }
      );

      item.append(button);
      rootPages.append(item);
    }
  }

  async function fetchRecentActivity(page) {
    const modalList = document.getElementById(
      "recent-activity-modal-list"
    );
    const modalLoading = document.getElementById(
      "recent-activity-modal-loading"
    );
    const modalAlert = document.getElementById(
      "recent-activity-modal-alert"
    );

    if (
      !modalList ||
      !root.dataset.recentActivityApiUrl
    ) {
      return;
    }

    modalLoading.classList.remove("d-none");
    modalAlert.classList.add("d-none");
    modalList.replaceChildren();

    try {
      const query = new URLSearchParams({
        page: String(page),
        page_size: "8",
        dashboard_view: state.dashboardView
      });

      const data = await requestJson(
        root.dataset.recentActivityApiUrl +
          "?" +
          query,
        null,
        "최근 활동을 불러오지 못했습니다."
      );

      renderRecentList(
        modalList,
        data.items
      );
      renderRecentPages(
        data.pagination
      );
    } catch (error) {
      modalAlert.textContent = error.message;
      modalAlert.classList.remove("d-none");
    } finally {
      modalLoading.classList.add("d-none");
    }
  }

  function renderRecentPages(pagination) {
    const paginationRoot = document.getElementById(
      "recent-activity-pagination"
    );

    paginationRoot.replaceChildren();

    for (
      let page = 1;
      page <= pagination.total_pages;
      page += 1
    ) {
      const item = el(
        "li",
        "page-item" +
          (page === pagination.page
            ? " active"
            : "")
      );

      const button = el(
        "button",
        "page-link",
        String(page)
      );

      button.type = "button";
      button.setAttribute(
        "aria-label",
        "최근 활동 " + page + "페이지"
      );

      button.addEventListener(
        "click",
        function () {
          fetchRecentActivity(page);
        }
      );

      item.append(button);
      paginationRoot.append(item);
    }
  }

  async function loadTrash() {
    const trashList = document.getElementById(
      "prd-trash-list"
    );
    const trashLoading = document.getElementById(
      "prd-trash-loading"
    );
    const trashAlert = document.getElementById(
      "prd-trash-alert"
    );

    trashLoading.classList.remove("d-none");
    trashAlert.classList.add("d-none");
    trashList.replaceChildren();

    try {
      const data = await requestJson(
        root.dataset.trashApiUrl +
          "?page_size=50",
        null,
        "휴지통을 불러오지 못했습니다."
      );

      renderTrash(data.items);
    } catch (error) {
      trashAlert.textContent = error.message;
      trashAlert.classList.remove("d-none");
    } finally {
      trashLoading.classList.add("d-none");
    }
  }

  function renderTrash(items) {
    const trashList = document.getElementById(
      "prd-trash-list"
    );

    trashList.replaceChildren();

    if (!items.length) {
      const emptyState = el("div", "trash-empty idea-empty-compact");
      const icon = el("span", "idea-empty-icon");
      icon.append(el("i", "idea-icon idea-icon-trash3"));
      emptyState.append(
        icon,
        el("strong", "", "휴지통이 비어 있습니다."),
        el("span", "", "삭제한 PRD가 생기면 30일 동안 이곳에서 복구할 수 있어요.")
      );
      trashList.append(emptyState);
      return;
    }

    items.forEach(function (item) {
      const row = el(
        "article",
        "trash-item"
      );

      const copy = el(
        "div",
        "trash-item-copy"
      );

      const description = el(
        "p",
        "",
        item.description ||
          "한 줄 소개가 없습니다."
      );

      const meta = el(
        "div",
        "trash-item-meta"
      );

      const complete =
        item.state === "deleted_complete";

      meta.append(
        el(
          "span",
          "trash-state" +
            (complete
              ? " complete"
              : ""),
          complete
            ? "삭제 완료"
            : "복구 가능"
        ),
        el(
          "span",
          "",
          complete
            ? "30일 보관 후 자동 삭제"
            : "영구 삭제까지 " +
              item.days_remaining +
              "일"
        )
      );

      copy.append(
        el("strong", "", item.title),
        description,
        meta
      );

      const actions = el(
        "div",
        "trash-item-actions"
      );

      if (!complete) {
        const restore = el(
          "button",
          "btn btn-sm btn-outline-primary",
          "복구"
        );

        const remove = el(
          "button",
          "btn btn-sm btn-outline-danger",
          "삭제"
        );

        restore.type =
          remove.type =
            "button";

        restore.addEventListener(
          "click",
          async function () {
            restore.disabled =
              remove.disabled =
                true;

            try {
              await mutation(
                root.dataset.trashApiUrl +
                  item.id +
                  "/restore/",
                {
                  version: item.version
                }
              );

              await loadTrash();
              await fetchData();
            } catch (error) {
              restore.disabled =
                remove.disabled =
                  false;

              await window.IdeaUI.alert({title: "요청을 처리하지 못했습니다", message: error.message, tone: "danger"});
            }
          }
        );

        remove.addEventListener(
          "click",
          async function () {
            const confirmed = await window.IdeaUI.confirm({
              title: "삭제 완료로 처리할까요?",
              message: "데이터는 최초 삭제일로부터 30일 뒤 영구 삭제됩니다.",
              confirmText: "삭제 완료",
              cancelText: "취소",
              tone: "danger"
            });
            if (!confirmed) return;

            restore.disabled =
              remove.disabled =
                true;

            try {
              await mutation(
                root.dataset.trashApiUrl +
                  item.id +
                  "/delete/",
                {
                  version: item.version
                }
              );

              await loadTrash();
            } catch (error) {
              restore.disabled =
                remove.disabled =
                  false;

              await window.IdeaUI.alert({title: "요청을 처리하지 못했습니다", message: error.message, tone: "danger"});
            }
          }
        );

        actions.append(
          restore,
          remove
        );
      } else {
        actions.append(
          el(
            "span",
            "small text-secondary",
            "삭제 완료"
          )
        );
      }

      row.append(copy, actions);
      trashList.append(row);
    });
  }

  document
    .querySelectorAll(".home-scope-tab")
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          state.scope =
            button.dataset.scope;
          state.page = 1;

          document
            .querySelectorAll(".home-scope-tab")
            .forEach(function (item) {
              const active =
                item === button;

              item.classList.toggle(
                "active",
                active
              );

              item.setAttribute(
                "aria-selected",
                String(active)
              );
            });

          document
            .getElementById("home-scope-description")
            .textContent =
              state.scope === "viewer"
                ? "읽기 권한으로 참여한 PRD를 모아봅니다."
                : "작성하거나 편집에 참여하는 PRD입니다.";

          fetchData();
        }
      );
    });

  document
    .querySelectorAll(".home-tab")
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          state.tab =
            button.dataset.tab;
          state.page = 1;

          document
            .querySelectorAll(".home-tab")
            .forEach(function (item) {
              item.className =
                "btn " +
                (
                  item === button
                    ? "btn-primary"
                    : "btn-outline-primary"
                ) +
                " home-tab";
            });

          fetchData();
        }
      );
    });

  document
    .getElementById("home-status")
    .addEventListener(
      "change",
      function (event) {
        state.status =
          event.target.value;
        state.page = 1;
        fetchData();
      }
    );

  document
    .getElementById("home-sort")
    .addEventListener(
      "change",
      function (event) {
        state.sort =
          event.target.value;
        state.page = 1;
        fetchData();
      }
    );

  document
    .getElementById("home-round-filter")
    .addEventListener(
      "change",
      function (event) {
        state.roundScope =
          event.target.value;
        state.page = 1;
        fetchData();
      }
    );

  document
    .getElementById("home-project-scope")
    .addEventListener(
      "change",
      function (event) {
        state.projectScope =
          event.target.value;
        state.page = 1;
        fetchData();
      }
    );

  document
    .querySelectorAll(".tutor-dashboard-tab")
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          state.dashboardView =
            button.dataset.dashboardView;
          state.scope = "mine";
          state.tab = "all";
          state.page = 1;

          if (state.dashboardView === "editing") {
            const hadStudentFilter =
              state.participantUserId !== null;

            clearTutorStudentFilter();

            if (!hadStudentFilter) {
              fetchData();
            }
          } else {
            fetchData();
          }
        }
      );
    });

  document
    .querySelectorAll(".home-kpi[data-status]")
    .forEach(function (button) {
      button.addEventListener(
        "click",
        function () {
          state.status =
            button.dataset.status;

          const statusSelect =
            document.getElementById("home-status");

          statusSelect.value =
            state.status;

          window.StudioControls
            ?.syncSelect(statusSelect);

          state.page = 1;
          fetchData();
        }
      );
    });

  document
    .getElementById("tutor-student-query")
    .addEventListener(
      "input",
      function () {
        window.clearTimeout(
          studentSearchTimer
        );

        if (!this.value.trim()) {
          clearTutorStudentFilter();
          return;
        }

        studentSearchTimer =
          window.setTimeout(
            function () {
              searchTutorStudents(1);
            },
            280
          );
      }
    );

  document
    .getElementById("tutor-student-query")
    .addEventListener(
      "keydown",
      function (event) {
        if (event.key !== "Enter") {
          return;
        }

        event.preventDefault();
        window.clearTimeout(
          studentSearchTimer
        );
        searchTutorStudents(1);
      }
    );

  document
    .getElementById("recent-activity-modal")
    ?.addEventListener(
      "show.bs.modal",
      function () {
        fetchRecentActivity(1);
      }
    );

  document
    .getElementById("prd-trash-modal")
    ?.addEventListener(
      "show.bs.modal",
      loadTrash
    );

  deleteConfirmButton.addEventListener(
    "click",
    async function () {
      if (!pendingDeletion) return;

      deleteConfirmButton.disabled =
        true;
      deleteError.classList.add(
        "d-none"
      );

      try {
        await requestJson(
          deleteUrl(pendingDeletion.id),
          {
            method: "DELETE",
            headers: {
              "Content-Type":
                "application/json",
              "X-CSRFToken":
                csrfToken
            },
            body: JSON.stringify({
              version:
                pendingDeletion.version
            })
          },
          "PRD를 삭제하지 못했습니다."
        );

        pendingDeletion = null;
        deleteConfirmModal.hide();
        await fetchData();
      } catch (error) {
        deleteError.textContent =
          error.message;
        deleteError.classList.remove(
          "d-none"
        );
        deleteConfirmButton.disabled =
          false;
      }
    }
  );

  fetchData().then(function () {
    const url = new URL(
      window.location.href
    );

    if (
      url.searchParams.get("deleted") !== "1"
    ) {
      return;
    }

    alertBox.className =
      "alert alert-success";

    alertBox.textContent =
      "PRD를 휴지통으로 이동했습니다. 30일 동안 복구할 수 있습니다.";

    url.searchParams.delete(
      "deleted"
    );

    window.history.replaceState(
      {},
      "",
      url.pathname +
        url.search +
        url.hash
    );
  });
}());
