(function () {
  "use strict";

  const root = document.getElementById("prd-write-app");
  if (!root) return;

  const detailApi = root.dataset.detailApi;
  const exportApi = root.dataset.exportApi;
  const participantsApi = root.dataset.participantsApi;
  const participantSearchApi = root.dataset.participantSearchApi;
  const participantTeamApi = root.dataset.participantTeamApi;
  const commentsApi = root.dataset.commentsApi;
  const contributionsApi = root.dataset.contributionsApi;
  const aiBase = root.dataset.aiApiBase;
  const sharedThinkingIllustration = root.dataset.illustrationSharedThinking || "";
  const focusedReviewIllustration = root.dataset.illustrationFocusedReview || "";
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const sectionsRoot = document.getElementById("prd-sections");
  const sectionBackToTop = document.getElementById("section-back-to-top");
  const writeBodyViewport = root.querySelector(".write-body-viewport");
  const scope = document.getElementById("coach-scope");
  const messagesRoot = document.getElementById("coach-messages");
  const form = document.getElementById("coach-form");
  const input = document.getElementById("coach-input");
  const submit = document.getElementById("coach-submit");
  const cancel = document.getElementById("coach-cancel");
  const alertBox = document.getElementById("prd-alert");
  const commentForm = document.getElementById("comment-form");
  const commentTarget = document.getElementById("comment-target");
  const saveAllButton = document.getElementById("save-all-answers");
  const expandAllSectionsButton = document.getElementById("expand-all-sections");
  const collapseAllSectionsButton = document.getElementById("collapse-all-sections");
  const statusPicker = document.getElementById("prd-status-picker");
  const statusControl = document.getElementById("prd-status-control");
  const statusControlLabel = document.getElementById("prd-status-control-label");
  const statusOptions = Array.from(document.querySelectorAll("[data-prd-status-option]"));
  const deadlineInput = document.getElementById("write-deadline-input");
  const deadlineWarning = document.getElementById("write-deadline-warning");
  const evaluationButton = document.getElementById("run-evaluation");
  const evaluationCancel = document.getElementById("cancel-evaluation");
  const evaluationAlert = document.getElementById("evaluation-alert");
  const perspectiveDraftButton = document.getElementById("run-perspective-draft");
  const perspectiveDraftAlert = document.getElementById("perspective-draft-alert");
  const perspectiveDraftModalElement = document.getElementById("perspective-draft-modal");
  const perspectiveDraftModalPersona = document.getElementById("perspective-draft-modal-persona");
  const perspectiveDraftList = document.getElementById("perspective-draft-list");
  const perspectiveDraftToggleAll = document.getElementById("perspective-draft-toggle-all");
  const perspectiveDraftSelectedCount = document.getElementById("perspective-draft-selected-count");
  const perspectiveDraftApplyButton = document.getElementById("perspective-draft-apply");
  const perspectiveDraftAvailable = Boolean(
    perspectiveDraftButton && perspectiveDraftAlert && perspectiveDraftModalElement &&
    perspectiveDraftModalPersona && perspectiveDraftList && perspectiveDraftToggleAll &&
    perspectiveDraftSelectedCount && perspectiveDraftApplyButton
  );
  const perspectiveDraftModal = perspectiveDraftAvailable
    ? bootstrap.Modal.getOrCreateInstance(perspectiveDraftModalElement)
    : null;
  let perspectiveDraftJob = null;
  const exportModalElement = document.getElementById("export-modal");
  const exportPreview = document.getElementById("export-preview");
  const exportPreviewState = document.getElementById("export-preview-state");
  const copyMarkdownButton = document.getElementById("copy-prd-markdown");
  const downloadMarkdownLink = document.getElementById("download-prd-markdown");
  const settingsButton = document.getElementById("prd-settings-button");
  const settingsModalElement = document.getElementById("prd-settings-modal");
  const settingsModal = bootstrap.Modal.getOrCreateInstance(settingsModalElement);
  const settingsEditSection = document.getElementById("prd-settings-edit-section");
  const settingsDangerSection = document.getElementById("prd-settings-danger-section");
  const createdDateOutput = document.getElementById("prd-created-date");
  const summaryForm = document.getElementById("prd-summary-form");
  const summaryTitleField = document.getElementById("prd-summary-title-field");
  const summaryDescriptionField = document.getElementById("prd-summary-description-field");
  const summaryDeadlineField = document.getElementById("prd-summary-deadline-field");
  const summaryTitleInput = document.getElementById("prd-summary-title");
  const summaryDescriptionInput = document.getElementById("prd-summary-description");
  const summaryDeadlineInput = document.getElementById("prd-summary-deadline");
  const summarySaveButton = document.getElementById("prd-summary-save");
  const summaryError = document.getElementById("prd-summary-error");
  const deletePrdButton = document.getElementById("delete-prd");
  const deleteConfirmElement = document.getElementById("write-delete-confirm-modal");
  const deleteConfirmModal = bootstrap.Modal.getOrCreateInstance(deleteConfirmElement);
  const confirmDeletePrdButton = document.getElementById("confirm-delete-prd");
  const deleteError = document.getElementById("write-delete-error");
  const answerConflictElement = document.getElementById("answer-conflict-modal");
  const answerConflictModal = bootstrap.Modal.getOrCreateInstance(answerConflictElement);
  const answerConflictLatest = document.getElementById("answer-conflict-latest");
  const answerConflictLocal = document.getElementById("answer-conflict-local");
  const answerHeldConflictElement = document.getElementById("answer-held-conflict-modal");
  const answerHeldConflictModal = bootstrap.Modal.getOrCreateInstance(answerHeldConflictElement);
  const answerHeldConflictLocal = document.getElementById("answer-held-conflict-local");
  const answerHeldConflictCopy = document.getElementById("answer-held-conflict-copy");
  let answerConflictQuestionId = null;
  let detail = null;
  let activeJobId = null;
  // undefined means the initial render; null means the user collapsed every section.
  let activeSectionId = undefined;
  const expandedSectionIds = new Set();
  let authorMode = "guided";
  let writeView = "write";
  let activeQuestionId = null;
  if (sectionBackToTop && writeBodyViewport) {
    sectionBackToTop.addEventListener("click", function () { writeBodyViewport.scrollTo({top: 0, behavior: "smooth"}); });
    writeBodyViewport.addEventListener("scroll", syncSectionBackToTop, {passive: true});
  }
  const guidedSchema = window.IdeaGuidedSchema || window.IdeaGuidedSchemaV34 || Object.freeze({
    getConfig: function () { return null; },
    getDependencies: function () { return []; },
    getSectionShort: function (_prdType, _position) { return ""; },
    emptyState: function () { return {}; },
    compose: function () { return ""; },
    hydrate: function (answer) { return {mode: "raw", raw: answer || ""}; },
    parse: function (answer) { return {mode: "raw", raw: answer || ""}; }
  });
  const uiDemo = window.IdeaPrdUiDemoV18 || window.IdeaPrdUiDemoV17 || window.IdeaPrdUiDemoV16 || window.IdeaPrdUiDemoV15 || window.IdeaPrdUiDemoV14 || window.IdeaPrdUiDemoV13 || window.IdeaPrdUiDemoV12 || window.IdeaPrdUiDemoV11 || {enabled:false};
  const uiDemoMode = Boolean(uiDemo.enabled);
  const demoAnswerStorageKey = "idea-prd-demo-answers:" + root.dataset.prdId;
  function readDemoAnswerOverrides() {
    if (!uiDemoMode) return {};
    try { return JSON.parse(window.localStorage.getItem(demoAnswerStorageKey) || "{}"); }
    catch (error) { return {}; }
  }
  function writeDemoAnswerOverride(questionId, content) {
    if (!uiDemoMode) return;
    const current = readDemoAnswerOverrides();
    current[String(questionId)] = String(content || "");
    try { window.localStorage.setItem(demoAnswerStorageKey, JSON.stringify(current)); } catch (error) {}
  }
  const structuredTransferPrefix = "idea-prd-structured-state:" + root.dataset.prdId + ":";
  function readStructuredTransfer(questionId, backend) {
    try {
      const key = structuredTransferPrefix + String(questionId);
      const payload = JSON.parse(window.localStorage.getItem(key) || "null");
      if (!payload || payload.composedAnswer !== String(backend || "") || !payload.state) {
        if (payload) window.localStorage.removeItem(key);
        return null;
      }
      return {composedAnswer: payload.composedAnswer, state: payload.state};
    } catch (error) { return null; }
  }
  function writeStructuredTransfer(questionId, composedAnswer, state) {
    if (!state || !composedAnswer) return;
    try {
      window.localStorage.setItem(structuredTransferPrefix + String(questionId), JSON.stringify({
        composedAnswer:String(composedAnswer), state:state, savedAt:Date.now()
      }));
    } catch (error) {}
  }
  function clearStructuredTransfer(questionId) {
    try { window.localStorage.removeItem(structuredTransferPrefix + String(questionId)); } catch (error) {}
  }
  const guidedCache = new Map();
  const liveGuidedStates = new Map();
  const answerRequests = new Map();
  let autosaveTimer;
  let flushPromise;
  let navigationBusy = false;
  let sectionScrollTicking = false;
  let sectionSnapshotCollapsed = true;
  let canManageParticipants = false;
  let canCreateComments = false;
  let canEditSummaryMetadata = false;
  let canEditDeadlineMetadata = false;
  const pendingAnswers = new Map();
  let savingAllAnswers = false;
  const statusLabels = {in_progress: "진행 중", completed: "완료", held: "보류", dropped: "드랍"};
  const evaluationPersonas = ["pm", "engineering", "investor"];
  let evaluationResults = {};
  let synthesisResult = null;
  let synthesisRequestInFlight = false;
  let evaluationJobIds = [];
  let evaluationCancelRequested = false;
  let evaluationRunController = null;
  let exportedMarkdown = "";
  let alertTimer = null;
  let canRequestAi = false;
  let conversationToken = 0;
  const pollIntervalMs = 1500;
  const pollTimeoutMs = 120000;
  const pollNetworkRetryLimit = 3;

  function localDateKey(date) {
    return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
  }

  function isPastDeadline(prd) {
    return Boolean(prd.deadline && prd.deadline < localDateKey(new Date()));
  }

  function renderDeadlineState(prd) {
    const control = deadlineInput.closest(".write-deadline");
    const today = localDateKey(new Date());
    const isOpen = !["completed", "dropped"].includes(prd.status);
    const overdue = isOpen && Boolean(prd.deadline && prd.deadline < today);
    const dueToday = isOpen && prd.deadline === today;
    const unset = isOpen && !prd.deadline;
    control.classList.toggle("is-overdue", overdue);
    control.classList.toggle("is-today", dueToday);
    control.classList.toggle("is-unset", unset);
    deadlineWarning.classList.toggle("d-none", !overdue && !dueToday);
    deadlineWarning.textContent = overdue ? "마감 지남" : dueToday ? "오늘 마감" : "";
    control.setAttribute(
      "aria-label",
      overdue ? "마감 기한이 지났습니다." : dueToday ? "오늘이 마감일입니다." : unset ? "마감일이 설정되지 않았습니다." : "목표 마감일"
    );
  }

  function decodeSafeText(value) {
    const area = document.createElement("textarea");
    area.innerHTML = value || "";
    return area.value;
  }

  function firstErrorDetail(value) {
    if (!value) return "";
    if (typeof value === "string") return value.trim();
    if (Array.isArray(value)) {
      for (const item of value) {
        const message = firstErrorDetail(item);
        if (message) return message;
      }
      return "";
    }
    if (typeof value === "object") {
      for (const item of Object.values(value)) {
        const message = firstErrorDetail(item);
        if (message) return message;
      }
    }
    return "";
  }

  async function api(url, options) {
    let response;
    try {
      response = await fetch(url, {
        credentials: "same-origin",
        cache: "no-store",
        ...options,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
          ...(options?.headers || {})
        }
      });
    } catch (networkError) {
      if (networkError && networkError.name === "AbortError") {
        const aborted = new Error("요청이 취소되었습니다.");
        aborted.name = "AbortError";
        throw aborted;
      }
      throw new Error("서버에 연결하지 못했습니다. 네트워크 상태를 확인해 주세요.");
    }
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      throw new Error(response.status === 401 || response.redirected
        ? "로그인 상태가 만료되었습니다. 페이지를 새로고침해 주세요."
        : response.ok
        ? "서버 응답 형식을 확인하지 못했습니다. 다시 시도해 주세요."
        : "서버에서 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.");
    }
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      const error = new Error(
        firstErrorDetail(payload.error?.details) ||
        payload.error?.message ||
        "요청을 처리하지 못했습니다."
      );
      error.code = payload.error?.code;
      error.details = payload.error?.details;
      throw error;
    }
    return payload.data;
  }

  function showAlert(message, kind) {
    if (alertTimer) window.clearTimeout(alertTimer);
    alertBox.className = "alert write-alert alert-" + (kind || "danger");
    alertBox.textContent = message;
    alertTimer = window.setTimeout(clearAlert, kind === "success" ? 3000 : 5000);
  }

  function clearAlert() {
    if (alertTimer) window.clearTimeout(alertTimer);
    alertTimer = null;
    alertBox.className = "alert write-alert d-none";
    alertBox.textContent = "";
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function sectionRate(section) {
    const activeQuestions = section.questions.filter(function (question) { return !question.is_held; });
    if (!activeQuestions.length) return 0;
    return Math.round(activeQuestions.filter(function (question) { return question.is_completed; }).length * 100 / activeQuestions.length);
  }

  function renderProgress(data) {
    const rate = data.prd.completion_rate;
    document.getElementById("write-completion-label").textContent = rate + "%";
    document.getElementById("write-step-progress-bar").style.width = rate + "%";
    const progressRoot = document.getElementById("write-section-progress");
    if (!progressRoot) return;
    progressRoot.replaceChildren();
    data.sections.forEach(function (section) {
      const value = sectionRate(section);
      const row = element("div", "score-row");
      const bar = element("i"); bar.append(element("b")); bar.firstChild.style.width = value + "%";
      row.append(element("span", "", section.title), bar, element("strong", "", value + "%"));
      progressRoot.append(row);
    });
  }


  function queueAutosave() {
    if (uiDemoMode) return;
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(flushAnswers, 1350);
  }
  async function flushAnswers() {
    clearTimeout(autosaveTimer);
    if (uiDemoMode) return true;
    if (flushPromise) return flushPromise;
    flushPromise = (async function () {
      try {
        for (const key of Array.from(pendingAnswers.keys())) {
          if (!findQuestion(key)?.is_held) await persistPendingAnswer(key);
        }
        if (detail) refreshAnswerProgress();
        updateSaveAllButton();
        return pendingAnswers.size === 0;
      } catch (error) {
        await handleAnswerSaveError(error);
        return false;
      }
    }());
    try { return await flushPromise; } finally { flushPromise = null; }
  }
  async function navigateWriting(change) {
    if (navigationBusy || !detail) return;
    navigationBusy = true;
    try {
      if (!await flushAnswers()) return;
      change();
      document.querySelector(".v34-mode")?.removeAttribute("open");
      renderDetail(detail);
    } finally { navigationBusy = false; }
  }
  function action(label, fn, className) {
    const button = element("button", className || "btn btn-sm btn-outline-secondary", label);
    button.type = "button";
    button.addEventListener("click", fn);
    return button;
  }

  function updateSectionSnapshot(sectionId) {
    if (!detail || authorMode !== "direct") return;
    const snapshot = root.querySelector("[data-section-snapshot]");
    if (!snapshot) return;
    const section = detail.sections.find(function (item) { return String(item.id) === String(sectionId); });
    if (!section) return;
    const activeQuestions = section.questions.filter(function (question) { return !question.is_held; });
    const answered = activeQuestions.filter(function (question) { return question.is_completed; }).length;
    const held = section.questions.filter(function (question) { return question.is_held; }).length;
    const title = snapshot.querySelector("[data-snapshot-title]");
    const guide = snapshot.querySelector("[data-snapshot-guide]");
    if (title) title.textContent = section.title;
    if (guide) guide.textContent = section.guide || "이 섹션의 질문을 함께 보며 답변을 정리해요.";
    const values = {
      answered: answered,
      unanswered: Math.max(activeQuestions.length - answered, 0),
      held: held
    };
    Object.keys(values).forEach(function (key) {
      const target = snapshot.querySelector('[data-snapshot-stat="' + key + '"] b');
      if (target) target.textContent = String(values[key]);
    });
  }

  function syncActiveSectionVisual(sectionId) {
    const key = String(sectionId);
    root.querySelectorAll(".write-step[data-section-id]").forEach(function (button) {
      button.classList.toggle("active", button.dataset.sectionId === key);
    });
    root.querySelectorAll(".write-section[data-section-id]").forEach(function (card) {
      card.classList.toggle("active", card.dataset.sectionId === key);
    });
    updateSectionSnapshot(sectionId);
  }

  function scrollToSection(sectionId, behavior) {
    const target = root.querySelector('.write-section[data-section-id="' + CSS.escape(String(sectionId)) + '"]');
    if (!target) return;
    target.scrollIntoView({behavior: behavior || "smooth", block: "start", inline: "nearest"});
  }

  function syncSectionBackToTop() {
    if (!writeBodyViewport || !sectionBackToTop) return;
    const visible = writeView === "write" && authorMode === "direct" && writeBodyViewport.scrollTop > 360;
    sectionBackToTop.classList.toggle("is-visible", visible);
    sectionBackToTop.setAttribute("aria-hidden", String(!visible));
    sectionBackToTop.tabIndex = visible ? 0 : -1;
  }

  function syncActiveSectionFromScroll() {
    if (sectionScrollTicking || writeView !== "write" || authorMode !== "direct") return;
    const viewport = root.querySelector(".write-body-viewport");
    if (!viewport) return;
    sectionScrollTicking = true;
    requestAnimationFrame(function () {
      sectionScrollTicking = false;
      const cards = Array.from(root.querySelectorAll(".write-section[data-section-id]"));
      if (!cards.length) return;
      const viewportRect = viewport.getBoundingClientRect();
      const guideLine = viewportRect.top + Math.min(170, viewport.clientHeight * 0.28);
      let best = null;
      let bestDistance = Infinity;
      cards.forEach(function (card) {
        const rect = card.getBoundingClientRect();
        if (rect.bottom < viewportRect.top + 24 || rect.top > viewportRect.bottom - 24) return;
        const distance = Math.abs(rect.top - guideLine);
        if (distance < bestDistance) { best = card; bestDistance = distance; }
      });
      if (!best) return;
      const nextSectionId = best.dataset.sectionId;
      if (String(activeSectionId) === String(nextSectionId)) return;
      activeSectionId = nextSectionId;
      activeQuestionId = null;
      syncActiveSectionVisual(nextSectionId);
      renderContext();
    });
  }
  function structuredEditor(block, question, section) {
    const editor = block.querySelector(".question-editor");
    if (!editor) return;
    const config = guidedSchema.getConfig(detail.prd.prd_type, section.position, question.position);
    if (!config) return;
    const key = String(question.id), backend = question.answer?.content || "";
    if (uiDemoMode && question.__ui_demo_guided_state) {
      guidedCache.set(key, {state: structuredClone(question.__ui_demo_guided_state), composedAnswer: backend});
    }
    const cache = guidedCache.get(key) || readStructuredTransfer(key, backend);
    const validCache = cache?.composedAnswer === backend ? cache : null;
    let state = guidedSchema.hydrate(backend, config, validCache);
    const live = liveGuidedStates.get(key);
    if (pendingAnswers.has(key) && live?.composedAnswer === pendingAnswers.get(key)) state = structuredClone(live.state);
    if (state.mode === "raw" || (pendingAnswers.has(key) && !live)) {
      editor.before(element("p", "text-secondary", config.purpose || ""), element("p", "small text-secondary", "기존 작성 내용을 그대로 편집할 수 있어요."));
      return;
    }
    editor.classList.add("d-none");
    const region = element("div", "v34-fields v34-pattern-" + config.pattern);
    const purpose = element("p", "text-secondary", config.purpose || "");
    const preview = element("pre", "v34-preview");
    const previewWrap = element("div", "v34-preview-wrap");
    previewWrap.append(element("strong", "small", "이 답변은 이렇게 정리돼요"), preview);
    function changed() {
      const composed = guidedSchema.compose(state, config);
      preview.textContent = composed;
      previewWrap.hidden = !composed.trim();
      liveGuidedStates.set(key, {state: structuredClone(state), composedAnswer: composed});
      if (!composed && backend) {
        preview.textContent = "기존 작성 내용은 보관돼요. 전체 삭제는 직접 편집에서 할 수 있어요.";
        pendingAnswers.delete(key);
        editor.value = backend;
        updateSaveAllButton();
        return;
      }
      editor.value = composed;
      editor.dispatchEvent(new Event("input", {bubbles: true}));
    }
    function field(label, placeholder, value, onChange, wide) {
      const wrap = element("label", "v34-field" + (wide ? " v34-field-wide" : ""));
      wrap.append(element("span", "small fw-semibold", label));
      // Guided fields are deliberately single-line: the structured UI should scan like a form,
      // while the hidden raw answer remains the single backend Answer value.
      const control = element("input", "form-control");
      control.type = "text";
      control.value = value || "";
      control.placeholder = placeholder || "";
      control.maxLength = 12000;
      control.addEventListener("input", function () { onChange(control.value); changed(); });
      wrap.append(control);
      return wrap;
    }
    function draw() {
      region.replaceChildren();
      if (config.kind === "metric") {
        const table = element("div", "v34-metric");
        state.rows.forEach(function (row, index) {
          const line = element("div", "v34-metric-row");
          ["metric", "current", "target", "period"].forEach(function (key, column) {
            line.append(field(config.tableHeaders[column], config.fields[column]?.placeholder || config.fields[0]?.placeholder, row[key], value => { row[key] = value; }, false));
          });
          const controls = element("div", "v34-metric-actions");
          const addMetric = action("", function () {
            state.rows.splice(index + 1, 0, {metric:"",current:"",target:"",period:""});
            changed(); draw();
          }, "v34-metric-square v34-metric-plus");
          addMetric.setAttribute("aria-label", "지표 추가");
          addMetric.title = "지표 추가";
          addMetric.append(element("i", "idea-icon idea-icon-plus-lg"));
          const removeMetric = action("", function () {
            if (state.rows.length <= 1) return;
            state.rows.splice(index, 1); changed(); draw();
          }, "v34-metric-square v34-metric-minus");
          removeMetric.setAttribute("aria-label", "지표 삭제");
          removeMetric.title = state.rows.length <= 1 ? "지표는 한 줄 이상 필요해요" : "지표 삭제";
          removeMetric.disabled = state.rows.length <= 1;
          removeMetric.append(element("span", "v34-minus-glyph", "−"));
          controls.append(addMetric, removeMetric);
          line.append(controls);
          table.append(line);
        });
        region.append(table);
      } else if (config.kind === "steps") {
        const ordered = element("ol", "v34-flow");
        state.steps.forEach(function (step, index) {
          const row = element("li");
          row.append(field(config.fields[index]?.label || String(index + 1), config.fields[index]?.placeholder || "", step, value => { state.steps[index] = value; }, true));
          ordered.append(row);
        });
        region.append(ordered);
      } else {
        config.fields.forEach(function (spec, index) {
          const wide = !["user", "target", "period", "metric", "value"].includes(spec.key) && config.fields.length === 1;
          region.append(field(spec.label, spec.placeholder, state.fields[index], value => { state.fields[index] = value; }, wide));
        });
      }
    }
    draw();
    editor.before(purpose, region);
    if (config.preview !== false) { preview.textContent = guidedSchema.compose(state, config); previewWrap.hidden = !preview.textContent.trim(); block.querySelector(".write-answer-footer").after(previewWrap); }
    const help = element("aside", "v34-help");
    help.append(element("strong", "v34-help-title", "생각해볼 점"));
    const helpList = element("ul", "v34-help-list");
    (config.prompts || []).slice(0, 3).forEach(text => helpList.append(element("li", "", text)));
    (config.checks || []).slice(0, 2).forEach(text => helpList.append(element("li", "", text)));
    if (!helpList.children.length) helpList.append(element("li", "", "질문의 핵심만 먼저 한 문장으로 정리해 보세요."));
    help.append(helpList);
    block.classList.add("has-guided-help");
    block.append(help);
  }
  function renderContext() {
    const rail = document.getElementById("v34-context-body");
    rail.replaceChildren();
    const section = detail.sections.find(s => String(s.id) === String(activeSectionId));
    const question = section?.questions.find(q => String(q.id) === String(activeQuestionId)) || section?.questions[0];
    if (!section || !question) return;

    const contextHeading = document.getElementById("v34-context-heading");
    if (contextHeading) contextHeading.textContent = "참고 정보";

    const related = guidedSchema.getDependencies(detail.prd.prd_type, section.position).map(function (pair) {
      return detail.sections.find(s => Number(s.position) === Number(pair[0]))?.questions.find(q => Number(q.position) === Number(pair[1]));
    }).filter(q => q && !q.is_held && q.answer?.content).slice(0, 2);
    document.getElementById("v34-context-toggle").textContent = "앞에서 쓴 내용 " + related.length + "개";

    const previous = element("details", "v34-context-disclosure");
    previous.append(element("summary", "", "앞에서 쓴 내용 · " + related.length));
    const previousBody = element("div", "v34-context-disclosure-body");
    related.forEach(function (q) {
      const item = element("section", "v34-context-answer");
      item.append(element("strong", "small", q.prompt), element("p", "v34-answer", q.answer.content));
      previousBody.append(item);
    });
    if (!related.length) previousBody.append(element("p", "small text-secondary", "현재 질문과 연결된 이전 답변이 아직 없어요."));
    previous.append(previousBody); rail.append(previous);

    const demoMemos = uiDemoMode && typeof uiDemo.memosFor === "function" ? uiDemo.memosFor(question, section) : [];
    const notes = element("details", "v34-context-disclosure v34-context-notes");
    if (uiDemoMode) notes.open = true;
    notes.append(element("summary", "", "관련 메모" + (demoMemos.length ? " · " + demoMemos.length : "")));
    const notesBody = element("div", "v34-context-disclosure-body");
    if (demoMemos.length) {
      demoMemos.forEach(function (memo) {
        const item = element("section", "v34-context-answer v34-demo-memo");
        item.append(element("strong", "small", memo.title), element("p", "v34-answer", memo.body));
        notesBody.append(item);
      });
    } else {
      notesBody.append(element("p", "v34-context-note-copy", "현재 질문과 연결된 메모는 브레인스토밍에서 확인할 수 있어요."));
    }
    const notesLink = element("a", "idea-inline-link v34-context-link", "메모 전체 보기");
    notesLink.href = root.querySelector(".brainstorm-launch").href;
    notesLink.append(element("i", "idea-icon idea-icon-chevron-right"));
    notesBody.append(notesLink); notes.append(notesBody); rail.append(notes);

    const contextComments = authorMode === "direct"
      ? section.questions.flatMap(function (sectionQuestion) {
          return (commentController.getItemsForQuestion ? commentController.getItemsForQuestion(sectionQuestion.id) : []).map(function (comment) {
            return Object.assign({}, comment, {__questionPrompt: sectionQuestion.prompt});
          });
        })
      : (commentController.getItemsForQuestion ? commentController.getItemsForQuestion(question.id) : []);
    const commentDisclosure = element("details", "v34-context-disclosure");
    commentDisclosure.open = contextComments.length > 0;
    commentDisclosure.append(element("summary", "", (authorMode === "direct" ? "이 섹션의 댓글 · " : "댓글 · ") + contextComments.length));
    const commentBody = element("div", "v34-context-disclosure-body");
    if (contextComments.length) {
      const contextTypeLabels = {general:"일반", guidance:"지도", review:"리뷰", post_completion_review:"완료 후 리뷰"};
      const contextRoleLabels = {owner:"소유자", editor:"편집자", tutor:"튜터", viewer:"뷰어"};
      contextComments.slice(0, 4).forEach(function (comment) {
        const item = element("article", "v20-context-comment");
        const heading = element("div", "v20-context-comment-head");
        const tags = element("div", "v26-context-comment-tags");
        const typeKey = comment.comment_type || "general";
        tags.append(element("span", "comment-kind comment-kind--" + typeKey, contextTypeLabels[typeKey] || typeKey));
        const roleKey = comment.author?.role_at_created || comment.author?.role || "";
        if (roleKey) tags.append(element("span", "comment-role comment-role--" + roleKey, contextRoleLabels[roleKey] || roleKey));
        heading.append(element("strong", "", comment.author?.display_name || "팀원"), tags);
        item.append(heading, element("p", "", comment.content || ""));
        commentBody.append(item);
      });
    } else {
      commentBody.append(element("p", "small text-secondary", authorMode === "direct" ? "현재 섹션에 등록된 댓글이 없어요." : "현재 질문에 등록된 댓글이 없어요."));
    }
    const comments = action("전체 댓글 보기", function () {
      if (authorMode === "guided") commentTarget.value = String(question.id);
      else commentTarget.value = "";
      commentTarget.dispatchEvent(new Event("change", {bubbles:true}));
      document.getElementById("comment-toggle").click();
    }, "v20-comment-all");
    comments.append(element("i", "idea-icon idea-icon-chevron-right"));
    commentBody.append(comments);
    commentDisclosure.append(commentBody);

    const coach = action("질문하기", async function () {
      scope.value = String(section.id);
      window.StudioControls?.syncSelect(scope);
      await loadConversation();
      bootstrap.Offcanvas.getOrCreateInstance(document.getElementById("write-support-panel")).show();
    });
    coach.disabled = !canRequestAi;
    coach.className = "btn btn-sm btn-outline-primary";
    const coachSection = element("section", "v34-context-coach");
    coachSection.append(element("h3", "h6", "AI 코치"), element("p", "small text-secondary", "현재 질문이 막힐 때만 사용"), coach);
    rail.append(commentDisclosure, coachSection);
  }
  function renderFullAnswerContent(content, emptyText) {
    const text = String(content || "").trim();
    const host = element("div", "v34-answer" + (text ? "" : " text-secondary"));
    if (!text) { host.textContent = emptyText || "아직 작성하지 않았어요."; return host; }
    const rows = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    const isTable = rows.length >= 3 && /^\|.*\|$/.test(rows[0]) && /^\|.*\|$/.test(rows[1]);
    if (isTable) {
      const splitRow = line => line.slice(1, -1).split("|").map(cell => cell.trim());
      const headers = splitRow(rows[0]);
      const divider = splitRow(rows[1]);
      const validDivider = divider.length === headers.length && divider.every(cell => /^:?-{3,}:?$/.test(cell));
      const bodyRows = rows.slice(2).map(splitRow);
      if (validDivider && bodyRows.every(row => row.length === headers.length)) {
        const wrap = element("div", "v20-answer-table-wrap");
        const table = element("table", "v20-answer-table");
        const thead = document.createElement("thead"), headRow = document.createElement("tr");
        headers.forEach(label => { const th = document.createElement("th"); th.textContent = label; headRow.append(th); });
        thead.append(headRow); table.append(thead);
        const tbody = document.createElement("tbody");
        bodyRows.forEach(row => {
          const tr = document.createElement("tr");
          row.forEach(value => { const td = document.createElement("td"); td.textContent = value; tr.append(td); });
          tbody.append(tr);
        });
        table.append(tbody); wrap.append(table); host.append(wrap); return host;
      }
    }
    host.textContent = text;
    return host;
  }

  function renderFullView() {
    const full = document.getElementById("v34-full"); full.replaceChildren();
    const heading = element("header", "v34-review-heading v9-page-heading");
    const copy = element("div");
    copy.append(
      element("small", "v9-page-eyebrow", "FULL PRD"),
      element("h2", "v9-page-title", "전체 내용 보기"),
      element("p", "v9-page-subtitle", "PRD를 문서처럼 읽어보고 필요한 곳만 다시 수정해요.")
    );
    const actions = element("div", "v34-review-actions");
    actions.append(action("작성으로 돌아가기", () => navigateWriting(() => { writeView = "write"; })), action("점검·공유", () => navigateWriting(() => { writeView = "report"; })));
    heading.append(copy, actions); full.append(heading);
    const layout = element("div", "v34-document-layout"), main = element("div", "v34-document-main"), summary = element("aside", "v34-document-summary");
    detail.sections.forEach(function (section,index) {
      const group = element("section", "v34-document-section"), head = element("header", "v34-document-head"), title = element("div");
      title.append(element("small", "text-secondary", "SECTION " + (index + 1)), element("h3", "h5", section.title));
      head.append(title, action(detail.permissions.can_edit && detail.prd.status !== "completed" ? "섹션 수정" : "작성 화면 보기", function () {
        navigateWriting(function () { writeView = "write"; authorMode = "direct"; activeSectionId = section.id; activeQuestionId = null; expandedSectionIds.add(String(section.id)); });
      })); group.append(head);
      section.questions.forEach(function (q,index) {
        const part = element("section", "v34-document-question");
        const questionHead = element("header", "v34-document-question-head");
        const questionState = element("span", "v34-question-state", q.is_held ? "제외" : q.is_completed ? "작성됨" : "미작성");
        questionState.dataset.state = q.is_held ? "held" : q.is_completed ? "completed" : "empty";
        questionHead.append(element("h4", "h6", "Q" + (index + 1) + ". " + q.prompt), questionState);
        const content = q.answer?.content || "";
        part.append(questionHead, renderFullAnswerContent(
          content,
          q.is_held ? "이번 PRD에서 제외한 질문이에요." : "아직 작성하지 않았어요."
        ));
        group.append(part);
      }); main.append(group);
    });
    const questions = detail.sections.flatMap(section => section.questions), active = questions.filter(q => !q.is_held), completed = active.filter(q => q.is_completed).length;
    summary.append(element("h3", "h6", "현재 버전"), element("p", "small text-secondary", detail.prd.version != null ? String(detail.prd.version) : "현재 작성본"));
    const stats = element("dl", "v34-document-stats");
    [["작성",completed + " / " + active.length],["미작성",active.length-completed],["제외",questions.length-active.length]].forEach(([label,value]) => stats.append(element("dt","",label),element("dd","",String(value))));
    summary.append(stats);
    const reviewStatus = element("section", "v34-document-review-status");
    reviewStatus.append(element("strong", "", "점검 상태"));
    if (synthesisResult?.job?.status === "succeeded") {
      const statusLine = element("div", "v34-document-review-line");
      const reviewChip = element("b", "v34-document-review-chip", synthesisResult.isCurrent ? "최신 결과" : "업데이트 필요");
      reviewChip.dataset.state = synthesisResult.isCurrent ? "current" : "stale";
      statusLine.append(element("span", "", "최근 점검"), reviewChip);
      reviewStatus.append(statusLine, element("p", "small text-secondary", "전체 품질 · " + (qualityScore(synthesisResult.job.output?.overall_score) ?? "—") + "점"));
    } else {
      const statusLine = element("div", "v34-document-review-line");
      const reviewChip = element("b", "v34-document-review-chip", "진단 전");
      reviewChip.dataset.state = "empty";
      statusLine.append(element("span", "", "최근 점검"), reviewChip);
      reviewStatus.append(statusLine, element("p", "small text-secondary", "작성 내용을 채운 뒤 세 관점에서 보완할 곳을 확인할 수 있어요."));
    }
    summary.append(reviewStatus, action("점검·공유로 이동", () => navigateWriting(() => { writeView = "report"; }), "btn btn-primary btn-sm"));
    layout.append(main,summary); full.append(layout);
  }
  function applyWriteView() {
    document.body.classList.toggle("idea-prd-focus", writeView === "full" || writeView === "report");
    root.dataset.writeView = writeView;
    root.dataset.authorMode = authorMode;
    const modeLabel = document.getElementById("v34-mode-label");
    if (modeLabel) modeLabel.textContent = authorMode === "guided" ? "단계별 작성" : "섹션별 작성";
    const guidedTab = document.getElementById("structure-view");
    const sectionTab = document.getElementById("question-view");
    if (guidedTab) { guidedTab.classList.toggle("active", authorMode === "guided"); guidedTab.setAttribute("aria-pressed", String(authorMode === "guided")); }
    if (sectionTab) { sectionTab.classList.toggle("active", authorMode === "direct"); sectionTab.setAttribute("aria-pressed", String(authorMode === "direct")); }
    if (expandAllSectionsButton) expandAllSectionsButton.disabled = authorMode !== "direct" || !detail?.sections?.length || detail.sections.every(function (section) { return expandedSectionIds.has(String(section.id)); });
    if (collapseAllSectionsButton) {
      const activeKey = activeSectionId === undefined || activeSectionId === null ? null : String(activeSectionId);
      collapseAllSectionsButton.disabled = authorMode !== "direct" || !activeKey || (expandedSectionIds.size === 1 && expandedSectionIds.has(activeKey));
    }
    root.querySelectorAll("[data-write-view]").forEach(button => {
      if (button === root) return;
      button.setAttribute("aria-pressed", String(button.dataset.writeView === writeView));
    });
    if (writeView === "full") renderFullView();
    renderContext();
  }

  function renderSteps(data) {
    const steps = document.getElementById("write-steps");
    steps.replaceChildren();
    data.sections.forEach(function (section, index) {
      const rate = sectionRate(section);
      const answered = section.questions.filter(function (question) {
        return !question.is_held && question.is_completed;
      }).length;
      const total = section.questions.length;
      const button = element("button", "write-step" + (rate === 100 ? " done" : "") + (String(section.id) === String(activeSectionId) ? " active" : ""));
      button.type = "button";
      button.dataset.sectionId = String(section.id);
      button.title = section.title + " · " + answered + "/" + total + " 작성";
      // 완료 상태에서도 번호를 유지한다. 완료 여부는 우측 작성 수와 색상으로만 표현한다.
      const label = element("span", "write-step-label", guidedSchema.getSectionShort(data.prd.prd_type, section.position) || section.title);
      const count = element("small", "write-step-count", answered + "/" + total);
      button.append(element("b", "", String(index + 1)), label, count);
      button.addEventListener("click", function () {
        const shouldScroll = authorMode === "direct";
        navigateWriting(function () {
          activeSectionId = section.id;
          activeQuestionId = null;
          if (authorMode === "direct") expandedSectionIds.add(String(section.id));
        }).then(function () {
          if (shouldScroll && authorMode === "direct") requestAnimationFrame(function () { scrollToSection(section.id); });
        });
      });
      steps.append(button);
    });
  }

  function renderDetail(data) {
    detail = data;
    if (activeSectionId === undefined && data.sections.length) activeSectionId = data.sections[0].id;
    document.getElementById("prd-heading").textContent = data.prd.title;
    document.getElementById("prd-description").textContent = data.prd.description || "한 줄 소개가 없습니다.";
    const roleBadge = document.getElementById("prd-my-role");
    const roleKey = data.permissions.is_creator ? "owner" : data.permissions.role;
    const roleLabels = {owner: "소유자", editor: "편집자", viewer: "뷰어", tutor: "튜터"};
    roleBadge.textContent = roleLabels[roleKey] || "";
    roleBadge.className = "write-role-badge" + (roleLabels[roleKey] ? " " + roleKey : " d-none");
    document.title = data.prd.title + " | Idea Developer";
    const status = document.getElementById("prd-status");
    status.textContent = statusLabels[data.prd.status] || data.prd.status;
    status.dataset.status = data.prd.status;
    statusControl.dataset.status = data.prd.status;
    statusControlLabel.textContent = statusLabels[data.prd.status] || data.prd.status;
    statusOptions.forEach(function (option) {
      const value = option.dataset.prdStatusOption;
      option.disabled = (data.prd.status === "completed" && !["completed", "in_progress"].includes(value))
        || (value === "completed" && !["in_progress", "completed"].includes(data.prd.status));
      option.classList.toggle("active", value === data.prd.status);
    });
    statusPicker.classList.toggle("d-none", !data.permissions.can_change_status);
    status.classList.toggle("d-none", Boolean(data.permissions.can_change_status));
    deadlineInput.value = data.prd.deadline || "";
    deadlineInput.disabled = !data.permissions.can_edit_deadline;
    deadlineInput.min = data.prd.auto_completed ? localDateKey(new Date()) : "";
    const canEditSummary = data.permissions.can_edit && data.prd.status !== "completed";
    canEditSummaryMetadata = canEditSummary;
    canEditDeadlineMetadata = Boolean(data.permissions.can_edit_deadline);
    settingsButton.classList.remove("d-none");
    settingsEditSection.classList.toggle("d-none", !canEditSummaryMetadata && !canEditDeadlineMetadata);
    summaryTitleField.classList.toggle("d-none", !canEditSummaryMetadata);
    summaryDescriptionField.classList.toggle("d-none", !canEditSummaryMetadata);
    summaryDeadlineField.classList.toggle("d-none", !canEditDeadlineMetadata);
    settingsDangerSection.classList.toggle("d-none", !data.permissions.can_delete);
    createdDateOutput.textContent = data.prd.created_at
      ? localDateKey(new Date(data.prd.created_at))
      : "확인할 수 없음";
    document.getElementById("write-deadline-label").textContent = data.prd.deadline || (!["completed", "dropped"].includes(data.prd.status) ? "마감 미설정" : "마감 없음");
    renderDeadlineState(data.prd);
    document.getElementById("active-section-count").textContent = data.sections.length + "개 활성 섹션";
    document.getElementById("reopen-prd").classList.toggle("d-none", !data.permissions.can_reopen || data.prd.status !== "completed");
    document.getElementById("contribution-toggle").classList.toggle("d-none", !data.permissions.can_view_contributions);
    canManageParticipants = Boolean(data.permissions.can_manage_participants) && data.prd.status !== "completed";
    document.getElementById("manage-participants").classList.toggle("d-none", !canManageParticipants);
    document.getElementById("participant-add-section").classList.toggle("d-none", !canManageParticipants);
    canCreateComments = Boolean(data.permissions.can_comment || data.permissions.can_review_comment);
    commentForm.classList.toggle("d-none", !canCreateComments);
    if (data.prd.status === "completed" && data.permissions.can_review_comment) {
      document.getElementById("comment-permission-hint").textContent = "선택한 위치에 완료 후 튜터 리뷰 코멘트로 등록됩니다.";
    } else {
      document.getElementById("comment-permission-hint").textContent = "PRD 전체 또는 질문을 선택해 의견을 남길 수 있습니다.";
    }
    renderProgress(data);
    renderSteps(data);
    sectionsRoot.replaceChildren();
    scope.replaceChildren(new Option("전체 PRD", ""));
    const previousCommentTarget = commentTarget.value;
    commentTarget.replaceChildren(new Option("PRD 전체", ""));
    canRequestAi = !uiDemoMode && data.permissions.can_request_ai && data.prd.status !== "completed";
    const canEditAnswers = uiDemoMode || (data.permissions.can_edit && data.prd.status !== "completed");
    saveAllButton.classList.toggle("d-none", !canEditAnswers);
    input.disabled = !canRequestAi;
    submit.disabled = !canRequestAi;
    evaluationButton.disabled = !canRequestAi;
    perspectiveDraftButton.disabled = !canRequestAi;
    if (!canRequestAi) input.placeholder = "현재 권한 또는 PRD 상태에서는 AI를 요청할 수 없습니다.";

    function buildQuestionBlock(question, section, extraClass) {
      const block = element("div", "write-question" + (question.is_held ? " is-held" : "") + (extraClass ? " " + extraClass : ""));
      const top = element("div", "write-question-head");
      const stateChip = element("span", "v34-question-state", question.is_held ? "보류" : question.is_completed ? "작성됨" : "미작성");
      stateChip.dataset.state = question.is_held ? "held" : question.is_completed ? "completed" : "empty";
      top.append(element("h3", "", question.prompt), stateChip);
      if (canEditAnswers) {
        const hold = element("button", "question-hold-button" + (question.is_held ? " active" : ""), question.is_held ? "다시 포함" : "이번 PRD에서 제외");
        hold.type = "button";
        hold.setAttribute("aria-pressed", String(question.is_held));
        hold.addEventListener("click", function () { toggleQuestionHold(question, hold); });
        top.append(hold);
      }
      block.append(top);
      if (question.is_held) {
        const held = element("div", "question-held-panel");
        held.append(
          element("strong", "", "이번 PRD에서는 작성하지 않는 질문이에요."),
          element("p", "", "다시 포함하면 작성할 수 있어요.")
        );
        block.append(held);
        return block;
      }
      if (canEditAnswers) {
        const editor = element("textarea", "form-control question-editor");
        editor.rows = 4;
        editor.maxLength = 12000;
        const savedContent = question.answer?.content || "";
        editor.value = pendingAnswers.has(String(question.id)) ? pendingAnswers.get(String(question.id)) : savedContent;
        editor.placeholder = "이 질문에 대한 팀의 답변을 작성해 주세요.";
        editor.dataset.questionId = question.id;
        editor.dataset.version = question.version;
        editor.dataset.savedContent = savedContent;
        const save = element("button", "btn btn-outline-primary btn-sm question-save-button", "저장");
        save.type = "button";
        save.disabled = !pendingAnswers.has(String(question.id));
        editor.addEventListener("input", function () {
          if (editor.value === editor.dataset.savedContent) pendingAnswers.delete(String(question.id));
          else pendingAnswers.set(String(question.id), editor.value);
          save.disabled = !pendingAnswers.has(String(question.id));
          updateSaveAllButton();
          queueAutosave();
        });
        const footer = element("div", "write-answer-footer");
        const saved = element("small", "", question.answer ? "저장된 답변" : "아직 저장되지 않았습니다.");
        const actions = element("span", "write-answer-actions");
        actions.append(save);
        save.addEventListener("click", function () { saveOneAnswer(String(question.id), save); });
        if (authorMode === "guided") {
          const nextTarget = findNextQuestionTarget(String(question.id));
          if (nextTarget) {
            const next = element("button", "btn btn-primary btn-sm question-next-button", "다음 질문");
            next.type = "button";
            next.addEventListener("click", async function () {
              if (navigationBusy) return;
              next.disabled = true;
              try {
                if (pendingAnswers.has(String(question.id))) {
                  const savedOk = await saveOneAnswer(String(question.id), save);
                  if (!savedOk) return;
                }
                await navigateWriting(function () {
                  authorMode = "guided";
                  activeSectionId = nextTarget.sectionId;
                  activeQuestionId = nextTarget.questionId;
                });
              } finally {
                next.disabled = false;
              }
            });
            actions.append(next);
          }
        }
        footer.append(saved, actions);
        block.append(editor, footer);
        editor.addEventListener("focus", function () { activeSectionId = section.id; activeQuestionId = question.id; renderContext(); });
        if (authorMode === "guided") structuredEditor(block, question, section);
      } else {
        const answer = element("div", "question-answer", question.answer?.content || "아직 답변이 없습니다.");
        answer.dataset.questionId = question.id;
        block.append(answer);
      }
      return block;
    }

    if (authorMode === "direct") {
      const activeSection = data.sections.find(function (item) { return String(item.id) === String(activeSectionId); }) || data.sections[0];
      const sectionIntro = element("section", "v9-section-mode-intro");
      const introCopy = element("div", "v9-section-mode-copy");
      introCopy.append(
        element("span", "v9-section-mode-eyebrow", "SECTION WRITE"),
        element("h2", "", "섹션별 작성"),
        element("p", "", "이어지는 질문을 한 섹션 안에서 함께 보고 바로 수정해요.")
      );
      sectionIntro.append(introCopy);
      let sectionSnapshot = null;
      if (activeSection) {
        const activeQuestions = activeSection.questions.filter(function (q) { return !q.is_held; });
        const answered = activeQuestions.filter(function (q) { return q.is_completed; }).length;
        const held = activeSection.questions.filter(function (q) { return q.is_held; }).length;
        const snapshot = element("section", "v9-section-snapshot" + (sectionSnapshotCollapsed ? " is-collapsed" : ""));
        snapshot.dataset.sectionSnapshot = "true";
        const snapshotMain = element("div", "v9-section-snapshot-main");
        const snapshotCopy = element("div", "v9-section-snapshot-copy");
        const snapshotTitle = element("strong", "", activeSection.title);
        snapshotTitle.dataset.snapshotTitle = "true";
        const snapshotGuide = element("small", "", activeSection.guide || "이 섹션의 질문을 함께 보며 답변을 정리해요.");
        snapshotGuide.dataset.snapshotGuide = "true";
        snapshotCopy.append(element("span", "", "현재 섹션"), snapshotTitle, snapshotGuide);
        const snapshotStats = element("div", "v9-section-snapshot-stats");
        [["answered", "작성", answered], ["unanswered", "미작성", Math.max(activeQuestions.length - answered, 0)], ["held", "보류", held]].forEach(function (item) {
          const stat = element("span", "");
          stat.dataset.snapshotStat = item[0];
          stat.append(element("b", "", String(item[2])), document.createTextNode(item[1]));
          snapshotStats.append(stat);
        });
        const snapshotToggle = element("button", "v9-section-snapshot-toggle");
        snapshotToggle.type = "button";
        snapshotToggle.setAttribute("aria-expanded", String(!sectionSnapshotCollapsed));
        snapshotToggle.setAttribute("aria-label", sectionSnapshotCollapsed ? "현재 섹션 펼치기" : "현재 섹션 접기");
        snapshotToggle.append(
          element("span", "", sectionSnapshotCollapsed ? "펼치기" : "접기"),
          element("i", "idea-icon " + (sectionSnapshotCollapsed ? "idea-icon-chevron-down" : "idea-icon-chevron-up"))
        );
        snapshotToggle.addEventListener("click", function () {
          sectionSnapshotCollapsed = !sectionSnapshotCollapsed;
          snapshot.classList.toggle("is-collapsed", sectionSnapshotCollapsed);
          snapshotToggle.setAttribute("aria-expanded", String(!sectionSnapshotCollapsed));
          snapshotToggle.setAttribute("aria-label", sectionSnapshotCollapsed ? "현재 섹션 펼치기" : "현재 섹션 접기");
          snapshotToggle.querySelector("span").textContent = sectionSnapshotCollapsed ? "펼치기" : "접기";
          const icon = snapshotToggle.querySelector("i");
          if (icon) icon.className = "idea-icon " + (sectionSnapshotCollapsed ? "idea-icon-chevron-down" : "idea-icon-chevron-up");
        });
        snapshotMain.append(snapshotCopy, snapshotStats, snapshotToggle);
        snapshot.append(snapshotMain);
        sectionSnapshot = snapshot;
      }
      sectionsRoot.append(sectionIntro);
      if (sectionSnapshot) sectionsRoot.append(sectionSnapshot);
    }

    data.sections.forEach(function (section, index) {
      scope.add(new Option(section.title, String(section.id)));
      section.questions.forEach(function (question) {
        commentTarget.add(new Option(section.title + " · " + question.prompt + (question.is_held ? " (제외됨)" : ""), String(question.id)));
      });
      const rate = sectionRate(section);
      if (authorMode === "guided") {
        if (String(section.id) !== String(activeSectionId)) return;
        const current = section.questions.find(q => String(q.id) === String(activeQuestionId)) || section.questions[0];
        if (!current) return;
        activeQuestionId = current.id;
        const group = element("section", "v34-guided-section"); group.dataset.sectionId = section.id;
        group.append(element("p", "small text-secondary", String(index + 1) + " / " + data.sections.length + " · " + guidedSchema.getSectionShort(data.prd.prd_type, section.position)), element("h2", "h5", section.title));
        const siblings = element("details", "v34-siblings v32-guided-question-disclosure");
        siblings.setAttribute("aria-label", section.title + " 질문 바로가기");
        const currentIndex = Math.max(0, section.questions.findIndex(function (q) { return String(q.id) === String(current.id); }));
        const siblingSummary = element("summary", "v32-guided-question-summary");
        siblingSummary.append(
          element("span", "v32-guided-question-summary-title", "이 섹션의 질문"),
          element("span", "v32-guided-question-current", "현재 " + String(currentIndex + 1) + " / " + section.questions.length),
          element("i", "idea-icon idea-icon-chevron-down v32-guided-question-chevron")
        );
        siblings.append(siblingSummary);
        const siblingList = element("div", "v32-guided-question-list");
        section.questions.forEach(function (q, qIndex) {
          const choice = action("", function () { navigateWriting(function () { activeQuestionId = q.id; }); }, "v34-sibling v32-guided-question-item btn text-start");
          choice.setAttribute("aria-current", String(q.id === current.id));
          choice.append(
            element("b", "v32-guided-question-no", String(qIndex + 1)),
            element("span", "v32-guided-question-copy", q.prompt),
            element("small", "", q.is_held ? "제외" : q.is_completed ? "작성됨" : "미작성")
          );
          siblingList.append(choice);
        });
        siblings.append(siblingList);
        group.append(siblings, buildQuestionBlock(current, section));
        sectionsRoot.append(group); return;
      }

      const sectionKey = String(section.id);
      const isOpen = expandedSectionIds.has(sectionKey);
      const card = element("article", "write-section" + (String(section.id) === String(activeSectionId) ? " active" : "") + (isOpen ? " open" : ""));
      card.dataset.sectionId = section.id;
      const toggle = element("button", "write-section-toggle"); toggle.type = "button";
      toggle.setAttribute("aria-expanded", String(isOpen));
      const copy = element("span", "write-section-title"); copy.append(element("strong", "", section.title), element("small", "", section.guide || "작성 가이드를 확인해 주세요."));
      toggle.append(element("span", "write-section-index", String(index + 1)), copy, element("span", "write-section-badge" + (rate === 100 ? " done" : ""), rate === 100 ? "완료" : rate ? "작성 중" : "시작 전"), element("i", "idea-icon idea-icon-chevron-down write-section-chevron"));
      toggle.addEventListener("click", function () {
        activeSectionId = section.id;
        activeQuestionId = null;
        if (expandedSectionIds.has(sectionKey)) expandedSectionIds.delete(sectionKey);
        else expandedSectionIds.add(sectionKey);
        renderDetail(detail);
      });
      card.append(toggle);
      const body = element("div", "write-section-body");
      body.id = "write-section-body-" + section.id;
      toggle.setAttribute("aria-controls", body.id);
      section.questions.forEach(function (question) { body.append(buildQuestionBlock(question, section)); });
      card.append(body); sectionsRoot.append(card);
    });
    if (Array.from(commentTarget.options).some(function (option) { return option.value === previousCommentTarget; })) commentTarget.value = previousCommentTarget;
    updateSaveAllButton();
    applyWriteView();
  }

  function setExportTab(name) {
    const preview = name === "preview";
    document.getElementById("export-check-tab").classList.toggle("active", !preview);
    document.getElementById("export-preview-tab").classList.toggle("active", preview);
    document.getElementById("export-check-tab").setAttribute("aria-selected", String(!preview));
    document.getElementById("export-preview-tab").setAttribute("aria-selected", String(preview));
    document.getElementById("export-check-panel").classList.toggle("d-none", preview);
    document.getElementById("export-preview-panel").classList.toggle("d-none", !preview);
  }

  function renderExportCheck() {
    if (!detail) return;
    document.getElementById("export-prd-title").textContent = detail.prd.title;
    document.getElementById("export-progress-value").textContent = detail.prd.completion_rate + "%";
    document.querySelector(".export-progress-ring").style.setProperty("--export-score", detail.prd.completion_rate + "%");
    const list = document.getElementById("export-section-list");
    list.replaceChildren();
    detail.sections.forEach(function (section) {
      const active = section.questions.filter(function (question) { return !question.is_held; });
      const answered = active.filter(function (question) { return question.is_completed; }).length;
      const rate = sectionRate(section);
      const row = element("div", "export-section-row");
      const copy = element("div", "export-section-copy");
      copy.append(element("strong", "", section.title), element("small", "", answered + "/" + active.length + "개 질문 작성"));
      const progress = element("span", "export-section-bar");
      progress.append(element("i"));
      progress.firstChild.style.width = rate + "%";
      row.append(copy, progress, element("b", "", rate + "%"));
      list.append(row);
    });
  }

  async function loadMarkdownPreview() {
    exportedMarkdown = "";
    copyMarkdownButton.disabled = true;
    exportPreview.classList.add("d-none");
    exportPreviewState.className = "export-preview-state";
    exportPreviewState.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> 미리보기를 준비하고 있습니다.';
    try {
      const response = await fetch(exportApi, {credentials: "same-origin"});
      const contentType = response.headers.get("content-type") || "";
      if (response.redirected || contentType.includes("text/html")) throw new Error("로그인 상태를 확인한 뒤 다시 시도해 주세요.");
      if (!response.ok) throw new Error("PRD 내보내기 내용을 불러오지 못했습니다.");
      exportedMarkdown = await response.text();
      exportPreview.textContent = exportedMarkdown;
      exportPreview.classList.remove("d-none");
      exportPreviewState.classList.add("d-none");
      copyMarkdownButton.disabled = false;
    } catch (error) {
      exportPreviewState.className = "export-preview-state danger";
      exportPreviewState.textContent = error.message;
    }
  }

  function updateSaveAllButton() {
    const count = pendingAnswers.size;
    saveAllButton.disabled = savingAllAnswers || count === 0;
    saveAllButton.innerHTML = savingAllAnswers
      ? '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> 저장 중…'
      : '<i class="idea-icon idea-icon-cloud-check"></i> 전체 저장' + (count ? ' <span class="save-count">' + count + '</span>' : '');
  }

  function findQuestion(questionId) {
    return detail.sections.flatMap(function (section) { return section.questions; })
      .find(function (question) { return String(question.id) === String(questionId); });
  }

  function findNextQuestionTarget(questionId) {
    if (!detail) return null;
    const ordered = [];
    detail.sections.forEach(function (section) {
      section.questions.forEach(function (question) {
        if (!question.is_held) ordered.push({sectionId: section.id, questionId: question.id});
      });
    });
    const index = ordered.findIndex(function (item) { return String(item.questionId) === String(questionId); });
    return index >= 0 && index + 1 < ordered.length ? ordered[index + 1] : null;
  }

  function refreshAnswerProgress() {
    const completed = detail.sections.flatMap(function (section) { return section.questions; })
      .filter(function (item) { return !item.is_held && item.is_completed; }).length;
    const total = detail.sections.reduce(function (count, section) {
      return count + section.questions.filter(function (item) { return !item.is_held; }).length;
    }, 0);
    detail.prd.completion_rate = total ? Math.round(completed * 100 / total) : 0;
    renderProgress(detail);
    renderSteps(detail);
    sectionsRoot.querySelectorAll(".write-question").forEach(function (block) {
      const editor = block.querySelector("[data-question-id]");
      const question = editor && findQuestion(editor.dataset.questionId);
      const label = block.querySelector(".v34-question-state");
      if (question && label) label.textContent = question.is_held ? "보류" : question.is_completed ? "작성됨" : "미작성";
    });
  }

  async function toggleQuestionHold(question, button) {
    const key = String(question.id);
    const nextHeld = !question.is_held;
    if (nextHeld && !await flushAnswers()) return;
    if (uiDemoMode) {
      question.is_held = nextHeld;
      if (nextHeld) question.is_completed = false;
      refreshAnswerProgress();
      renderDetail(detail);
      showAlert(nextHeld ? "데모에서 이번 PRD 제외 상태를 적용했어요." : "데모에서 질문을 다시 포함했어요.", "success");
      return;
    }
    button.disabled = true;
    try {
      const data = await api(detailApi + "questions/" + question.id + "/hold/", {
        method: "PATCH",
        body: JSON.stringify({is_held: nextHeld, version: question.version})
      });
      question.is_held = data.question.is_held;
      question.version = data.question.version;
      question.is_completed = data.question.is_completed;
      question.answer = data.question.answer;
      detail.prd.completion_rate = data.completion_rate;
      if (nextHeld) pendingAnswers.delete(key);
      renderDetail(detail);
      markEvaluationStale();
      showAlert(nextHeld ? "이번 PRD에서 제외했어요." : "질문을 다시 포함했어요.", "success");
    } catch (error) {
      if (error.code === "version_conflict") {
        pendingAnswers.delete(key);
        renderDetail(await api(detailApi));
        showAlert("다른 사용자가 먼저 질문을 변경했습니다. 최신 내용을 다시 불러왔습니다.", "warning");
      } else showAlert(error.message);
    } finally {
      button.disabled = false;
    }
  }

  async function persistPendingAnswer(questionId) {
    if (answerRequests.has(questionId)) await answerRequests.get(questionId);
    if (!pendingAnswers.has(questionId) || findQuestion(questionId)?.is_held) return false;
    const request = persistAnswerRequest(questionId);
    answerRequests.set(questionId, request);
    try { return await request; } finally { if (answerRequests.get(questionId) === request) answerRequests.delete(questionId); }
  }
  async function persistAnswerRequest(questionId) {
    const editor = sectionsRoot.querySelector('.question-editor[data-question-id="' + questionId + '"]');
    const question = findQuestion(questionId);
    if (!question || question.is_held || !pendingAnswers.has(questionId)) return false;
    const submittedContent = pendingAnswers.get(questionId);
    if (uiDemoMode) {
      writeDemoAnswerOverride(question.id, submittedContent);
      question.answer = Object.assign({}, question.answer || {}, {content: submittedContent});
      question.is_completed = Boolean(submittedContent.trim());
      if (editor) editor.dataset.savedContent = submittedContent;
      if (pendingAnswers.get(questionId) === submittedContent) pendingAnswers.delete(questionId);
      const savedState = editor?.closest(".write-question")?.querySelector(".write-answer-footer small");
      if (savedState) { savedState.textContent = "데모에 반영됨"; savedState.className = "small text-success"; }
      const live = liveGuidedStates.get(String(questionId)) || liveGuidedStates.get(questionId);
      if (live?.composedAnswer === submittedContent) {
        guidedCache.set(String(questionId), structuredClone(live));
        writeStructuredTransfer(question.id, submittedContent, live.state);
      } else {
        clearStructuredTransfer(question.id);
      }
      const questionSave = editor?.closest(".write-question")?.querySelector(".question-save-button");
      if (questionSave) questionSave.disabled = !pendingAnswers.has(questionId);
      refreshAnswerProgress();
      markEvaluationStale();
      return true;
    }
    const data = await api(detailApi + "questions/" + question.id + "/answer/", {
      method: "PATCH",
      body: JSON.stringify({content: submittedContent, version: Number(editor?.dataset.version ?? question.version)})
    });
    if (editor) { editor.dataset.version = data.version; editor.dataset.savedContent = data.answer?.content || ""; }
    question.version = data.version;
    question.answer = data.answer;
    const live = liveGuidedStates.get(questionId) || liveGuidedStates.get(String(questionId));
    if (live?.composedAnswer === (data.answer?.content || "")) {
      guidedCache.set(String(questionId), structuredClone(live));
      writeStructuredTransfer(question.id, data.answer?.content || "", live.state);
    } else {
      clearStructuredTransfer(question.id);
    }
    question.is_completed = data.is_completed;
    if (pendingAnswers.get(questionId) === submittedContent) pendingAnswers.delete(questionId);
    else queueAutosave();
    markEvaluationStale();
    const savedState = editor?.closest(".write-question")?.querySelector(".write-answer-footer small");
    if (savedState) {
      savedState.textContent = "방금 저장됨";
      savedState.className = "small text-success";
    }
    const questionSave = editor?.closest(".write-question")?.querySelector(".question-save-button");
    if (questionSave) questionSave.disabled = !pendingAnswers.has(questionId);
    return true;
  }

  async function handleAnswerSaveError(error) {
    if (error.code === "version_conflict") {
      const latestQuestion = error.details?.latest;
      const questionId = latestQuestion ? String(latestQuestion.id) : null;
      const localContent = questionId ? pendingAnswers.get(questionId) : null;
      const latest = await api(detailApi);
      renderDetail(latest);
      if (questionId && localContent !== undefined) {
        if (latestQuestion.is_held) {
          pendingAnswers.delete(questionId);
          answerHeldConflictLocal.value = localContent;
          answerHeldConflictModal.show();
          updateSaveAllButton();
          showAlert(
            "다른 사용자가 이 질문을 제외했어요. 작성 중인 내용은 복사할 수 있어요.",
            "warning"
          );
          return;
        }
        answerConflictQuestionId = questionId;
        answerConflictLatest.value = latestQuestion.answer?.content || "";
        answerConflictLocal.value = localContent;
        answerConflictModal.show();
      }
      showAlert("다른 사용자가 먼저 답변을 수정했습니다. 작성 중인 내용은 보존했습니다.", "warning");
    } else {
      showAlert(error.message);
    }
  }

  document.getElementById("answer-conflict-use-latest").addEventListener("click", function () {
    if (answerConflictQuestionId) pendingAnswers.delete(answerConflictQuestionId);
    answerConflictModal.hide();
    answerConflictQuestionId = null;
    renderDetail(detail);
    updateSaveAllButton();
  });

  document.getElementById("answer-conflict-keep-local").addEventListener("click", function () {
    answerConflictModal.hide();
    const editor = answerConflictQuestionId
      ? sectionsRoot.querySelector('.question-editor[data-question-id="' + answerConflictQuestionId + '"]')
      : null;
    if (editor) {
      editor.value = answerConflictLocal.value;
      pendingAnswers.set(answerConflictQuestionId, answerConflictLocal.value);
      editor.focus();
    }
    answerConflictQuestionId = null;
    updateSaveAllButton();
  });

  answerHeldConflictCopy.addEventListener("click", async function () {
    const original = answerHeldConflictCopy.innerHTML;
    try {
      await navigator.clipboard.writeText(answerHeldConflictLocal.value);
      answerHeldConflictCopy.innerHTML = '<i class="idea-icon idea-icon-check2"></i> 복사됨';
      window.setTimeout(function () { answerHeldConflictCopy.innerHTML = original; }, 1800);
    } catch (error) {
      answerHeldConflictLocal.focus();
      answerHeldConflictLocal.select();
      showAlert("내용을 선택했습니다. Ctrl+C로 복사해 주세요.", "warning");
    }
  });

  async function saveOneAnswer(questionId, button) {
    if (!pendingAnswers.has(questionId)) return true;
    clearAlert();
    button.disabled = true;
    button.textContent = "저장 중…";
    try {
      const saved = await persistPendingAnswer(questionId);
      refreshAnswerProgress();
      showAlert(uiDemoMode ? "데모 답변을 반영했습니다." : "답변을 저장했습니다.", "success");
      return saved !== false;
    } catch (error) {
      await handleAnswerSaveError(error);
      return false;
    } finally {
      button.textContent = "저장";
      button.disabled = !pendingAnswers.has(questionId);
      updateSaveAllButton();
    }
  }

  async function saveAllAnswers() {
    if (uiDemoMode) { showAlert("UI 데모에서는 서버에 저장하지 않습니다.", "warning"); return; }
    if (savingAllAnswers || !pendingAnswers.size) return;
    clearAlert();
    savingAllAnswers = true;
    updateSaveAllButton();
    let savedCount = 0;
    try {
      const questionIds = Array.from(pendingAnswers.keys());
      for (const questionId of questionIds) {
        if (await persistPendingAnswer(questionId)) savedCount += 1;
      }
      refreshAnswerProgress();
      showAlert(savedCount + "개 답변을 저장했습니다.", "success");
    } catch (error) {
      await handleAnswerSaveError(error);
    } finally {
      savingAllAnswers = false;
      updateSaveAllButton();
    }
  }

  // 코치가 특정 질문의 답변 수정을 제안했을 때, 사용자가 승인해야만 반영되는 카드.
  function buildProposalCard(message) {
    const proposal = message.proposal;
    const card = element("div", "coach-proposal");

    const head = element("div", "coach-proposal-head");
    head.append(element("i", "idea-icon idea-icon-pencil-square"), element("strong", "", "이 답변을 고칠까요?"));
    card.append(head);

    const target = element("div", "coach-proposal-target");
    target.append(
      element("span", "coach-proposal-section", decodeSafeText(proposal.section_title || "")),
      element("span", "coach-proposal-question", decodeSafeText(proposal.question_prompt || ""))
    );
    card.append(target);

    if (proposal.reason) {
      card.append(element("p", "coach-proposal-reason", decodeSafeText(proposal.reason)));
    }

    card.append(element("div", "coach-proposal-preview", decodeSafeText(proposal.content || "")));

    const actions = element("div", "coach-proposal-actions");
    const yes = element("button", "btn btn-primary btn-sm", "네, 반영할게요");
    const no = element("button", "btn btn-outline-secondary btn-sm", "아니오");
    yes.type = "button";
    no.type = "button";
    if (!canRequestAi) {
      yes.disabled = true;
    }
    yes.addEventListener("click", function () {
      applyProposal(message.job.id, proposal, yes, no, card);
    });
    no.addEventListener("click", function () {
      declineProposal(message.job.id, yes, no, card);
    });
    actions.append(no, yes);
    card.append(actions);
    return card;
  }

  async function declineProposal(jobId, yes, no, card) {
    yes.disabled = true;
    no.disabled = true;
    no.textContent = "처리 중…";
    try {
      // 서버에 남겨야 새로고침해도 되살아나지 않고, 다음 요청에서 같은 제안을 막을 수 있다.
      await api(aiBase + "chat/" + jobId + "/decline/", {method: "POST", body: "{}"});
      card.replaceChildren(element("p", "coach-proposal-declined", "제안을 반영하지 않았습니다."));
    } catch (error) {
      yes.disabled = !canRequestAi;
      no.disabled = false;
      no.textContent = "아니오";
      showAlert(error.message);
    }
  }

  async function applyProposal(jobId, proposal, yes, no, card) {
    yes.disabled = true;
    no.disabled = true;
    yes.textContent = "반영 중…";
    try {
      const data = await api(aiBase + "chat/" + jobId + "/apply/", {
        method: "POST",
        body: JSON.stringify({
          question_version: proposal.question_version,
          content: proposal.content
        })
      });
      const editor = sectionsRoot.querySelector('[data-question-id="' + data.question_id + '"]');
      if (editor && editor.tagName === "TEXTAREA") {
        editor.value = data.answer.content;
        editor.dataset.version = data.question_version;
      } else if (editor) {
        editor.textContent = data.answer.content;
      }
      const target = detail?.sections
        .flatMap(function (section) { return section.questions; })
        .find(function (question) { return question.id === data.question_id; });
      if (target) {
        target.version = data.question_version;
        target.answer = {content: data.answer.content};
      }
      card.replaceChildren(element("p", "coach-proposal-applied", "이 답변에 반영했습니다."));
      showAlert("코치 제안을 PRD 답변에 반영했습니다.", "success");
      refreshAnswerProgress();
    } catch (error) {
      yes.disabled = false;
      no.disabled = false;
      yes.textContent = "네, 반영할게요";
      showAlert(
        error.code === "version_conflict"
          ? "그 사이 답변이 바뀌었습니다. 대화를 새로고침한 뒤 다시 시도해 주세요."
          : error.message
      );
    }
  }

  async function loadConversation() {
    const token = ++conversationToken;
    messagesRoot.replaceChildren(element("p", "text-secondary", "대화를 불러오는 중입니다."));
    try {
      const query = scope.value ? "?section_id=" + encodeURIComponent(scope.value) : "";
      const data = await api(aiBase + "conversation/" + query);
      if (token !== conversationToken) return;
      messagesRoot.replaceChildren();
      if (!data.messages.length) {
        messagesRoot.append(element("p", "text-secondary", "이 범위에서 AI 코치와 나눈 대화가 없습니다."));
      }
      data.messages.forEach(function (message) {
        const wrap = element("div", "mb-2");
        const bubble = element(
          "div",
          "coach-message coach-message-" + message.role,
          message.content
        );
        wrap.append(bubble);
        if (message.role === "assistant" && message.proposal && message.job?.id) {
          wrap.append(buildProposalCard(message));
        }
        const failedStates = ["failed", "timed_out", "cancelled"];
        const pendingStates = ["queued", "running", "retry_wait"];
        if (message.role === "user" && canRequestAi && failedStates.includes(message.job?.status)) {
          const retry = element("button", "btn btn-link btn-sm float-end", "다시 시도");
          retry.type = "button";
          retry.addEventListener("click", function () { retryJob(message.job.id); });
          wrap.append(retry);
        } else if (message.role === "user" && pendingStates.includes(message.job?.status)) {
          wrap.append(element("small", "text-secondary d-block mt-1", "AI가 답변을 준비하고 있습니다…"));
        }
        messagesRoot.append(wrap);
      });
      messagesRoot.scrollTop = messagesRoot.scrollHeight;
    } catch (error) {
      if (token !== conversationToken) return;
      messagesRoot.replaceChildren(element("p", "text-danger", error.message));
    }
  }

  function setBusy(busy, jobId) {
    // 권한이 없으면 작업이 끝나도 입력창을 다시 열지 않는다.
    submit.disabled = busy || !canRequestAi;
    input.disabled = busy || !canRequestAi;
    activeJobId = jobId || null;
    cancel.classList.toggle("d-none", !busy || !jobId);
  }

  async function pollJob(jobId, onSuccess) {
    const pending = ["queued", "running", "retry_wait", "cancel_requested"];
    const deadline = Date.now() + pollTimeoutMs;
    let networkFailures = 0;
    for (;;) {
      await new Promise(function (resolve) { setTimeout(resolve, pollIntervalMs); });

      let job;
      try {
        job = await api(aiBase + "jobs/" + jobId + "/");
        networkFailures = 0;
      } catch (error) {
        // 일시적인 통신 오류로 폴링을 끝내지 않는다. 서버에서는 작업이 계속 진행 중일 수 있다.
        networkFailures += 1;
        if (networkFailures >= pollNetworkRetryLimit) {
          showAlert("서버와 연결이 끊겼습니다. 잠시 후 대화를 새로고침해 결과를 확인해 주세요.");
          return null;
        }
        continue;
      }

      if (!pending.includes(job.status)) {
        if (job.status === "succeeded") onSuccess(job);
        else if (job.status === "cancelled") showAlert("AI 요청을 취소했습니다.", "secondary");
        else showAlert(job.error?.message || "AI 요청이 완료되지 않았습니다.");
        return job;
      }

      if (Date.now() > deadline) {
        showAlert(
          "AI 응답이 오지 않아 대기를 멈췄습니다. 작업 처리기(run_job_worker)가 실행 중인지 확인해 주세요."
        );
        return job;
      }
    }
  }

  function evaluationStateLabel(score) {
    if (score >= 80) return "충분";
    if (score >= 60) return "기본 충족";
    return "보완 필요";
  }

  function evaluationStatusLabel(status) {
    return {good: "충족", needs_improvement: "보완 필요", missing: "근거 부족"}[status] || "확인 필요";
  }

  function setEvaluationNotice(message, kind) {
    evaluationAlert.textContent = message;
    evaluationAlert.className = "evaluation-alert" + (kind ? " " + kind : "");
  }


  function qualityScore(value) {
    if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return null;
    return Math.max(0, Math.min(100, Number(value)));
  }
  function qualityState(score) { return score === null ? "neutral" : score >= 80 ? "success" : score >= 60 ? "warning" : "danger"; }
  function qualityLabel(score) { return score === null ? "진단 전" : evaluationStateLabel(score); }

  function setScoreState(label, state) {
    const node = document.getElementById("score-state");
    if (!node) return;
    node.textContent = label;
    node.dataset.state = state || "empty";
  }
  const reportPersonaLabels = {pm: "PM", engineering: "Engineering", investor: "Business"};
  let selectedDiagnosisId = null;
  function personaSection(persona, sectionId) {
    const result = evaluationResults[persona];
    if (result?.job?.status !== "succeeded") return null;
    return result.job.output?.sections?.find(row => String(row.section_id) === String(sectionId)) || null;
  }
  function renderPersonaSummary() {
    const target = document.getElementById("v34-persona-summary");
    target.replaceChildren();
    const hasResults = synthesisResult?.job?.status === "succeeded" || evaluationPersonas.some(persona => evaluationResults[persona]?.job?.status === "succeeded");
    root.dataset.evaluationEmpty = String(!hasResults);
    let passed = 0;
    evaluationPersonas.forEach(function (persona) {
      const result = evaluationResults[persona];
      const score = result?.job?.status === "succeeded" ? qualityScore(result.job.output?.overall_score) : null;
      if (score !== null && score >= 80) passed++;
      const line = element("p", "v34-quality", reportPersonaLabels[persona] + (score === null ? " · 진단 전" : " · " + score + " · " + qualityLabel(score)));
      line.dataset.quality = qualityState(score);
      const track = element("span", "v34-mini-track"); const fill = element("i");
      fill.style.width = (score ?? 0) + "%"; track.append(fill); track.setAttribute("aria-hidden", "true");
      if (score !== null) line.append(track); target.append(line);
    });
    if (hasResults) target.prepend(element("strong", "", passed + " / " + evaluationPersonas.length + " 기준 충족"));
    const passLabel = document.getElementById("v34-perspective-pass");
    if (passLabel) passLabel.textContent = passed + " / " + evaluationPersonas.length + " 충족";
    evaluationPersonas.forEach(function (persona) {
      const card = document.querySelector('[data-guide-persona="' + persona + '"]');
      if (!card) return;
      const result = evaluationResults[persona];
      const output = result?.job?.status === "succeeded" ? (result.job.output || {}) : null;
      const score = output ? qualityScore(output.overall_score) : null;
      const scoreEl = card.querySelector("[data-persona-score]");
      const gapEl = card.querySelector("[data-persona-gap]");
      if (scoreEl) { scoreEl.textContent = score ?? "—"; scoreEl.dataset.quality = qualityState(score); }
      if (!gapEl) return;
      const weakest = (output?.sections || []).filter(function (row) { return qualityScore(row.score) !== null; }).slice().sort(function (a,b) { return qualityScore(a.score) - qualityScore(b.score); })[0];
      const section = weakest ? detail?.sections?.find(function (s) { return String(s.id) === String(weakest.section_id); }) : null;
      gapEl.textContent = section ? section.title : score === null ? "진단 전" : "세부 결과 확인";
    });
  }
  function renderDiagnosisDetail(row, section, isCurrent) {
    const target = document.getElementById("v34-diagnosis-detail");
    target.replaceChildren(); target.hidden = false; selectedDiagnosisId = section.id;
    const score = qualityScore(row?.score);

    const head = element("header", "v13-diagnosis-detail-head");
    const headCopy = element("div");
    headCopy.append(element("small", "", "SECTION DIAGNOSIS"), element("h3", "", section.title));
    const scoreChip = element("strong", "v13-diagnosis-score", (score ?? "—") + " · " + qualityLabel(score));
    scoreChip.dataset.quality = qualityState(score);
    head.append(headCopy, scoreChip);

    const feedback = element("p", "v13-diagnosis-feedback", decodeSafeText(row?.feedback || "아직 이 영역의 진단 결과가 없어요."));
    const perspectives = element("div", "v13-diagnosis-perspectives");
    evaluationPersonas.forEach(function (persona) {
      const entry = personaSection(persona, section.id), value = qualityScore(entry?.score);
      if (value === null) return;
      const item = element("div", "v13-diagnosis-perspective");
      item.dataset.quality = qualityState(value);
      item.append(element("span", "", reportPersonaLabels[persona]), element("b", "", value + " · " + qualityLabel(value)));
      perspectives.append(item);
    });

    const actions = element("div", "v13-diagnosis-actions");
    const coach = action("AI에게 보완 방법 묻기", function () {
      if (synthesisResult?.isCurrent && canRequestAi && row) startSectionCoaching(section, row);
    });
    coach.classList.add("diagnosis-coach-button"); coach.disabled = !isCurrent || !synthesisResult?.isCurrent || !canRequestAi || !row;
    const edit = action("직접 수정", function () {
      navigateWriting(function () { writeView = "write"; activeSectionId = section.id; activeQuestionId = null; });
    });
    actions.append(coach, edit);
    target.append(head, feedback);
    if (perspectives.childElementCount) target.append(perspectives);
    target.append(actions);
  }
  function renderPersonaRing(persona, result) {
    const card = document.querySelector('.write-score-persona[data-persona="' + persona + '"]');
    if (!card) return;
    const ring = card.querySelector(".write-score-persona-ring");
    const progress = card.querySelector(".write-score-persona-progress");
    const value = card.querySelector(".write-score-persona-value");
    const feedback = card.querySelector(".write-score-persona-feedback");
    const job = result?.job;
    if (!job || job.status !== "succeeded") {
      ring.classList.add("is-pending");
      progress.style.strokeDashoffset = "100";
      value.textContent = "—";
      feedback.textContent = job && ["failed", "cancelled"].includes(job.status) ? "진단을 완료하지 못했어요. 다시 진단해 주세요." : job ? "작성한 내용을 세 관점에서 확인하고 있어요." : "아직 품질 진단을 하지 않았어요.";
      card.dataset.quality = "neutral";
      card.querySelector(".v23-persona-priority")?.remove();
      card.querySelector(".v34-persona-status")?.remove();
      const coach = card.querySelector(".v34-persona-coach");
      if (coach) coach.disabled = true;
      renderPersonaSummary();
      return;
    }
    const output = job.output || {};
    const score = qualityScore(output.overall_score);
    ring.classList.toggle("is-pending", score === null);
    progress.style.strokeDashoffset = String(100 - Math.max(0, Math.min(100, score)));
    value.textContent = score ?? "—";
    feedback.textContent = decodeSafeText(output.summary || "진단 결과를 확인해 주세요.");
    card.dataset.quality = qualityState(score);
    card.querySelector(".v23-persona-priority")?.remove();
    const lowest = (output.sections || []).filter(row => qualityScore(row.score) !== null && row.feedback).slice().sort((a,b) => qualityScore(a.score) - qualityScore(b.score))[0];
    if (lowest) {
      const priority = element("div", "v23-persona-priority");
      priority.append(element("strong", "small", qualityScore(lowest.score) >= 80 ? "더 다듬어 볼 곳" : "가장 먼저 보완할 점"),element("p", "small", decodeSafeText(lowest.feedback)));
      feedback.after(priority);
    }
    card.querySelector(".v34-persona-status")?.remove();
    feedback.before(element("p", "v34-persona-status", qualityLabel(score) + (result.isCurrent ? "" : " · 업데이트 필요")));
    if (!card.querySelector(".v34-persona-coach")) {
      const coach = action("보완하기", async function () {
        if (!canRequestAi || !evaluationResults[persona]?.isCurrent) return;
        scope.value = ""; window.StudioControls?.syncSelect(scope); await loadConversation();
        input.value = reportPersonaLabels[persona] + " 관점의 진단을 바탕으로 보완 방법을 알려 주세요.\n" + decodeSafeText(evaluationResults[persona]?.job?.output?.summary || "");
        bootstrap.Offcanvas.getOrCreateInstance(document.getElementById("write-support-panel")).show();
      });
      coach.classList.add("v34-persona-coach", "diagnosis-coach-button"); card.append(coach);
    }
    card.querySelector(".v34-persona-coach").disabled = !canRequestAi || !result.isCurrent;
    renderPersonaSummary();
  }

  function renderSynthesisEmpty(message) {
    document.getElementById("write-score-value").textContent = "—";
    document.getElementById("write-score-progress").style.strokeDashoffset = "100";
    document.getElementById("write-score-ring").classList.add("is-pending");
    setScoreState("진단 전", "empty");
    document.getElementById("write-score-label").textContent = "아직 품질 진단을 하지 않았어요.";
    const executiveTitle = document.getElementById("v34-executive-title");
    const executiveDescription = document.getElementById("v34-executive-description");
    if (executiveTitle) executiveTitle.textContent = "아직 품질 진단 전입니다.";
    if (executiveDescription) executiveDescription.textContent = "AI 진단 후 현재 상태, 가장 큰 리스크, 다음에 확인할 내용을 실제 결과 기준으로 보여줘요.";
    if (document.getElementById("v34-signal-state")) document.getElementById("v34-signal-state").textContent = "진단 전";
    if (document.getElementById("v34-signal-risk")) document.getElementById("v34-signal-risk").textContent = "—";
    if (document.getElementById("v34-signal-next")) document.getElementById("v34-signal-next").textContent = "—";
    document.getElementById("write-score-feedback").textContent = message || "작성한 내용을 기준으로 세 관점의 품질과 보완할 곳을 확인할 수 있어요.";
    document.getElementById("write-score-ring").dataset.quality = "neutral";
    document.getElementById("write-score-label").dataset.quality = "neutral";
    document.getElementById("v34-priorities").replaceChildren();
    document.getElementById("v34-diagnosis-detail").replaceChildren();
    renderPersonaSummary();
    const diagnosticsEmpty = element("div", "evaluation-empty evaluation-empty--review");
    if (focusedReviewIllustration) {
      const image = document.createElement("img");
      image.src = focusedReviewIllustration;
      image.alt = "";
      diagnosticsEmpty.append(image);
    }
    const emptyCopy = element("div");
    emptyCopy.append(
      element("strong", "", "아직 AI 진단 전입니다."),
      element("span", "", "작성한 내용을 기준으로 세 관점의 품질과 보완할 곳을 확인할 수 있어요.")
    );
    diagnosticsEmpty.append(emptyCopy);
    document.getElementById("write-section-diagnostics").replaceChildren(diagnosticsEmpty);
  }

  function renderEvaluationEmpty() {
    renderSynthesisEmpty();
    evaluationAlert.className = "evaluation-alert d-none";
    evaluationPersonas.forEach(function (persona) { renderPersonaRing(persona, null); });
  }

  function renderSynthesisResult(job, isCurrent) {
    const output = job.output || {}, score = qualityScore(output.overall_score);
    const ring = document.getElementById("write-score-ring");
    ring.classList.toggle("is-pending", score === null); ring.dataset.quality = qualityState(score);
    document.getElementById("write-score-progress").style.strokeDashoffset = String(100 - (score ?? 0));
    document.getElementById("write-score-value").textContent = score ?? "—";
    setScoreState(isCurrent ? "진단 완료" : "업데이트 필요", isCurrent ? "current" : "stale");
    document.getElementById("write-score-label").textContent = qualityLabel(score);
    document.getElementById("write-score-label").dataset.quality = qualityState(score);
    document.getElementById("write-score-feedback").textContent = decodeSafeText(output.summary || "진단 결과를 확인해 주세요.");
    const executiveTitle = document.getElementById("v34-executive-title");
    const executiveDescription = document.getElementById("v34-executive-description");
    if (executiveTitle) executiveTitle.textContent = qualityLabel(score) + (score === null ? "" : " · " + score + "점");
    if (executiveDescription) executiveDescription.textContent = decodeSafeText(output.summary || "진단 결과를 확인해 주세요.");
    if (document.getElementById("v34-signal-state")) document.getElementById("v34-signal-state").textContent = qualityLabel(score) + (score === null ? "" : " · " + score + "점");
    if (!isCurrent) setEvaluationNotice("작성 내용이 바뀌었어요. 최신 내용으로 다시 진단해 주세요.", "warning");
    else evaluationAlert.className = "evaluation-alert d-none";
    evaluationButton.textContent = "다시 진단하기";
    renderPersonaSummary();
    const rows = (output.sections || []).filter(row => detail.sections.some(s => String(s.id) === String(row.section_id)));
    const scored = rows.filter(row => qualityScore(row.score) !== null).slice().sort((a,b) => qualityScore(a.score) - qualityScore(b.score));
    document.getElementById("v34-priority-heading").textContent = !scored.length ? "보완 우선순위" : scored.some(row => qualityScore(row.score) < 80) ? "먼저 보완하면 좋은 곳" : "더 다듬어 볼 곳";
    const weakestRow = scored[0];
    const weakestSection = weakestRow ? detail.sections.find(function (s) { return String(s.id) === String(weakestRow.section_id); }) : null;
    if (document.getElementById("v34-signal-risk")) document.getElementById("v34-signal-risk").textContent = weakestSection ? weakestSection.title + " · " + qualityScore(weakestRow.score) + "점" : "—";
    if (document.getElementById("v34-signal-next")) document.getElementById("v34-signal-next").textContent = weakestRow?.feedback ? decodeSafeText(weakestRow.feedback) : "상세 진단 확인";
    const priorities = document.getElementById("v34-priorities"); priorities.replaceChildren();
    scored.slice(0,3).forEach(function (row, index) {
      const section = detail.sections.find(s => String(s.id) === String(row.section_id));
      if (!section) return;
      const button = action("", function () { renderDiagnosisDetail(row, section, isCurrent); }, "v34-priority-item");
      const copy = element("span", "v34-priority-copy");
      copy.append(element("strong", "", section.title), element("small", "", decodeSafeText(row.feedback || "상세 진단을 확인해 주세요.")));
      const scoreChip = element("b", "v34-priority-score", qualityScore(row.score) + "점");
      scoreChip.dataset.quality = qualityState(qualityScore(row.score));
      button.append(element("span", "v34-priority-index", String(index + 1)), copy, scoreChip);
      priorities.append(button);
    });
    const list = element("div", "v34-quality-list");
    detail.sections.forEach(function (section, index) {
      const row = rows.find(r => String(r.section_id) === String(section.id));
      const value = qualityScore(row?.score);
      const item = action("", function () { renderDiagnosisDetail(row, section, isCurrent); }, "v34-quality-row");
      item.dataset.quality = qualityState(value);
      item.append(
        element("span", "v34-quality-index", String(index + 1)),
        element("strong", "v34-quality-title", section.title),
        element("span", "v34-quality-state", qualityLabel(value)),
        element("b", "v34-quality-score", value ?? "—"),
        element("span", "v34-quality-feedback", decodeSafeText(row?.feedback || "아직 이 영역의 진단 결과가 없어요.")),
        element("span", "v34-quality-link", "상세 진단 ›")
      );
      list.append(item);
    });
    document.getElementById("write-section-diagnostics").replaceChildren(list);
    const selected = detail.sections.find(s => String(s.id) === String(selectedDiagnosisId));
    if (selected) renderDiagnosisDetail(rows.find(r => String(r.section_id) === String(selected.id)),selected,isCurrent);
    else document.getElementById("v34-diagnosis-detail").hidden = true;
  }

  // 진단이 지적한 내용을 그대로 들고 코치 대화로 넘어간다.
  // 문구만 채워 두고 전송은 사용자에게 맡긴다. 버튼만 눌러도 AI가 호출되면
  // 실수로 사용량을 쓰게 되고, 사용자가 질문을 다듬을 기회도 사라진다.
  async function startSectionCoaching(section, row) {
    clearAlert();
    scope.value = String(section.id);
    window.StudioControls?.syncSelect(scope);
    await loadConversation();
    input.value = [
      "AI 진단에서 “" + section.title + "” 섹션이 “" + evaluationStatusLabel(row.status)
        + "”(" + row.score + "점)으로 나왔습니다.",
      "지적된 내용: " + decodeSafeText(row.feedback),
      "이 섹션을 채우려면 어떤 질문부터 어떻게 답해야 할지 하나씩 짚어 주세요."
    ].join("\n");
    const panel = document.getElementById("write-support-panel");
    if (panel.classList.contains("show")) {
      input.focus();
      return;
    }
    panel.addEventListener("shown.bs.offcanvas", function focusOnce() {
      panel.removeEventListener("shown.bs.offcanvas", focusOnce);
      input.focus();
    });
    bootstrap.Offcanvas.getOrCreateInstance(panel).show();
  }

  function setEvaluationBusy(busy, jobIds, label) {
    if (busy && jobIds !== undefined) {
      evaluationJobIds = Array.isArray(jobIds) ? jobIds : (jobIds ? [jobIds] : []);
    } else if (!busy) {
      evaluationJobIds = [];
      evaluationCancelRequested = false;
      evaluationRunController = null;
    }
    evaluationButton.disabled = busy || !detail?.permissions.can_request_ai || detail?.prd.status === "completed";
    evaluationButton.innerHTML = busy
      ? '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>' + (label || "세 관점 진단 중…") + '</span>'
      : '<i class="idea-icon idea-icon-stars"></i><span>' + (Object.keys(evaluationResults).length ? "다시 진단하기" : "AI 관점 진단") + '</span>';
    evaluationCancel.classList.toggle("d-none", !busy);
    evaluationCancel.disabled = !busy || evaluationCancelRequested;
    if (busy) setScoreState(evaluationCancelRequested ? "취소 요청됨" : "진단 중", "running");
    else if (!Object.keys(evaluationResults).length && !synthesisResult?.job) setScoreState("진단 전", "empty");
  }

  // AI 진단하기는 PM/엔지니어링/투자자 세 관점을 각각 진단한 뒤, 세 결과가 모두
  // 최신 상태로 갖춰지면 이어서 종합 의견을 만든다. 새로고침으로 다시 들어왔을
  // 때도 세 관점은 있는데 종합만 없거나 낡은 경우 여기서 자동으로 채운다.
  async function loadEvaluation() {
    try {
      if (uiDemoMode && typeof uiDemo.evaluationFor === "function") {
        const demo = uiDemo.evaluationFor(detail);
        evaluationResults = demo.personas || {};
        evaluationPersonas.forEach(function (persona) { renderPersonaRing(persona, evaluationResults[persona]); });
        synthesisResult = demo.synthesis || null;
        if (synthesisResult?.job?.status === "succeeded") renderSynthesisResult(synthesisResult.job, true);
        else renderEvaluationEmpty();
        evaluationButton.disabled = true;
        evaluationButton.title = "UI 데모에서는 실제 AI를 호출하지 않습니다.";
        return;
      }
      const data = await api(aiBase + "evaluation/");
      evaluationResults = {};
      evaluationPersonas.forEach(function (persona) {
        const job = data.jobs?.[persona];
        if (job) evaluationResults[persona] = {
          job: job,
          isCurrent: Boolean(data.is_current_by_persona?.[persona])
        };
      });
      evaluationPersonas.forEach(function (persona) { renderPersonaRing(persona, evaluationResults[persona]); });

      if (!Object.keys(evaluationResults).length) {
        renderEvaluationEmpty();
        return;
      }

      const activeJobs = Object.values(evaluationResults).map(function (item) { return item.job; })
        .filter(function (job) { return ["queued", "running", "retry_wait", "cancel_requested"].includes(job.status); });
      if (activeJobs.length) {
        setEvaluationNotice("PM·Engineering·Business 관점 진단을 진행하고 있습니다.", "working");
        setEvaluationBusy(true, activeJobs.map(function (job) { return job.id; }), "세 관점 진단 중…");
        await Promise.allSettled(activeJobs.map(function (job) { return pollJob(job.id, function () {}); }));
        setEvaluationBusy(false);
        await loadEvaluation();
        return;
      }

      const allSucceededAndCurrent = evaluationPersonas.every(function (persona) {
        const result = evaluationResults[persona];
        return result?.job?.status === "succeeded" && result.isCurrent;
      });

      let synthesisJob = data.synthesis;
      let synthesisIsCurrent = Boolean(data.synthesis_is_current);

      if (
        allSucceededAndCurrent
        && (!synthesisJob || synthesisJob.status !== "succeeded" || !synthesisIsCurrent)
        && !synthesisRequestInFlight
      ) {
        synthesisRequestInFlight = true;
        setEvaluationNotice("세 관점 진단을 종합하고 있습니다.", "working");
        try {
          const job = await api(aiBase + "evaluation/synthesis/run/", {
            method: "POST",
            headers: {"Idempotency-Key": crypto.randomUUID()},
            body: JSON.stringify({})
          });
          setEvaluationBusy(true, [job.id], "종합 의견 생성 중…");
          const finished = await pollJob(job.id, function () {});
          setEvaluationBusy(false);
          if (finished?.status === "succeeded") {
            synthesisJob = finished;
            synthesisIsCurrent = true;
          }
        } catch (error) {
          setEvaluationBusy(false);
        } finally {
          synthesisRequestInFlight = false;
        }
      }

      synthesisResult = synthesisJob ? {job: synthesisJob, isCurrent: synthesisIsCurrent} : null;
      if (synthesisJob?.status === "succeeded") {
        renderSynthesisResult(synthesisJob, synthesisIsCurrent);
      } else if (!allSucceededAndCurrent) {
        renderSynthesisEmpty("PM·Engineering·Business 진단을 모두 완료하면 종합 의견을 확인할 수 있습니다.");
      } else {
        renderSynthesisEmpty("종합 의견을 준비하지 못했습니다. 다시 시도해 주세요.");
      }
    } catch (error) {
      setEvaluationNotice(error.message, "danger");
    }
  }

  function markEvaluationStale() {
    Object.values(evaluationResults).forEach(function (result) { result.isCurrent = false; });
    if (synthesisResult) synthesisResult.isCurrent = false;
    root.querySelectorAll(".diagnosis-coach-button").forEach(button => { button.disabled = true; });
    if (document.getElementById("write-score-value").textContent !== "—") {
      setScoreState("업데이트 필요", "stale");
      setEvaluationNotice("작성 내용이 바뀌었어요. 최신 내용으로 다시 진단해 주세요.", "warning");
    }
  }

  evaluationButton.addEventListener("click", async function () {
    clearAlert();
    evaluationCancelRequested = false;
    evaluationRunController = new AbortController();
    setEvaluationBusy(true);
    setEvaluationNotice("세 관점의 AI 진단 요청을 등록하고 있습니다.", "working");
    try {
      const batchKey = crypto.randomUUID();
      const requests = await Promise.allSettled(evaluationPersonas.map(function (persona) {
        return api(aiBase + "evaluation/run/", {
          method: "POST",
          headers: {"Idempotency-Key": batchKey + "-" + persona},
          body: JSON.stringify({persona: persona}),
          signal: evaluationRunController?.signal
        });
      }));
      const jobs = requests.filter(function (result) { return result.status === "fulfilled"; })
        .map(function (result) { return result.value; });
      if (evaluationCancelRequested) {
        if (jobs.length) {
          await Promise.allSettled(jobs.map(function (job) {
            return api(aiBase + "jobs/" + job.id + "/cancel/", {method: "POST", body: "{}"});
          }));
        }
        setEvaluationNotice("진단 요청을 취소했습니다.", "warning");
        return;
      }
      if (!jobs.length) {
        const rejected = requests.find(function (result) { return result.status === "rejected"; });
        if (rejected?.reason?.name === "AbortError") {
          setEvaluationNotice("진단 요청을 취소했습니다.", "warning");
          return;
        }
        throw rejected?.reason || new Error("AI 진단 요청을 시작하지 못했습니다.");
      }
      setEvaluationBusy(true, jobs.map(function (job) { return job.id; }));
      await Promise.allSettled(jobs.map(function (job) { return pollJob(job.id, function () {}); }));
      if (!evaluationCancelRequested) {
        await loadEvaluation();
        if (jobs.length < evaluationPersonas.length) {
          setEvaluationNotice("일부 관점의 진단만 완료했습니다. 다시 진단하면 부족한 결과를 보완할 수 있어요.", "warning");
        }
      }
    } catch (error) {
      if (error?.name === "AbortError" || evaluationCancelRequested) {
        setEvaluationNotice("진단 요청을 취소했습니다.", "warning");
      } else {
        setEvaluationNotice(error.message, "danger");
      }
    } finally {
      setEvaluationBusy(false);
    }
  });

  evaluationCancel.addEventListener("click", async function () {
    if (evaluationCancel.classList.contains("d-none") || evaluationCancel.disabled) return;
    evaluationCancelRequested = true;
    evaluationCancel.disabled = true;
    setScoreState("취소 요청됨", "running");
    setEvaluationNotice("진단 요청을 취소하고 있습니다.", "warning");
    try {
      evaluationRunController?.abort();
      if (evaluationJobIds.length) {
        await Promise.allSettled(evaluationJobIds.map(function (jobId) {
          return api(aiBase + "jobs/" + jobId + "/cancel/", {method: "POST", body: "{}"});
        }));
      }
      setEvaluationNotice("진단 요청을 취소했습니다.", "warning");
    } catch (error) {
      if (error?.name !== "AbortError") setEvaluationNotice(error.message, "danger");
    }
  });

  async function retryJob(jobId) {
    clearAlert();
    try {
      const job = await api(aiBase + "jobs/" + jobId + "/retry/", {method: "POST", body: "{}"});
      setBusy(true, job.id);
      await pollJob(job.id, loadConversation);
      await loadConversation();
    } catch (error) {
      showAlert(error.message);
    } finally {
      setBusy(false);
    }
  }

  scope.addEventListener("change", loadConversation);

  async function updateMetadata(changes) {
    const data = await api(detailApi + "metadata/", {
      method: "PATCH",
      body: JSON.stringify({...changes, version: detail.prd.version})
    });
    detail.prd.title = data.title;
    detail.prd.description = data.description;
    detail.prd.status = data.status;
    detail.prd.deadline = data.deadline;
    detail.prd.version = data.version;
    renderDetail(detail);
    return data;
  }

  settingsModalElement.addEventListener("show.bs.modal", function () {
    summaryTitleInput.value = detail?.prd.title || "";
    summaryDescriptionInput.value = detail?.prd.description || "";
    summaryDeadlineInput.value = detail?.prd.deadline || "";
    summaryDeadlineInput.min = deadlineInput.min;
    summaryError.classList.add("d-none");
    summaryError.textContent = "";
    summaryForm.classList.remove("was-validated");
  });

  summaryForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (!summaryForm.checkValidity()) {
      summaryForm.classList.add("was-validated");
      return;
    }
    summarySaveButton.disabled = true;
    summaryError.classList.add("d-none");
    try {
      const changes = {};
      if (canEditSummaryMetadata) {
        changes.title = summaryTitleInput.value.trim();
        changes.description = summaryDescriptionInput.value.trim();
      }
      if (canEditDeadlineMetadata) changes.deadline = summaryDeadlineInput.value || null;
      await updateMetadata(changes);
      settingsModal.hide();
      showAlert("PRD 기본 정보를 수정했습니다.", "success");
    } catch (error) {
      if (error.code === "version_conflict") {
        const latest = await api(detailApi);
        renderDetail(latest);
        summaryTitleInput.value = latest.prd.title;
        summaryDescriptionInput.value = latest.prd.description || "";
        summaryDeadlineInput.value = latest.prd.deadline || "";
        summaryError.textContent = "다른 사용자가 먼저 수정했습니다. 최신 기본 정보를 불러왔습니다.";
      } else summaryError.textContent = error.message;
      summaryError.classList.remove("d-none");
    } finally {
      summarySaveButton.disabled = false;
    }
  });

  function showAfterHidden(currentElement, nextModal) {
    currentElement.addEventListener("hidden.bs.modal", function showNext() {
      currentElement.removeEventListener("hidden.bs.modal", showNext);
      nextModal.show();
    });
    bootstrap.Modal.getOrCreateInstance(currentElement).hide();
  }

  deletePrdButton.addEventListener("click", function () {
    document.getElementById("write-delete-prd-title").textContent = detail.prd.title;
    deleteError.classList.add("d-none");
    deleteError.textContent = "";
    confirmDeletePrdButton.disabled = false;
    showAfterHidden(settingsModalElement, deleteConfirmModal);
  });

  confirmDeletePrdButton.addEventListener("click", async function () {
    confirmDeletePrdButton.disabled = true;
    deleteError.classList.add("d-none");
    try {
      await api(detailApi + "delete/", {
        method: "DELETE",
        body: JSON.stringify({version: detail.prd.version})
      });
      window.location.href = "/ideas/?deleted=1";
    } catch (error) {
      confirmDeletePrdButton.disabled = false;
      deleteError.textContent = error.message;
      deleteError.classList.remove("d-none");
    }
  });

  async function changePrdStatus(requested) {
    const previous = detail.prd.status;
    statusControl.disabled = true;
    try {
      if (requested === "completed") {
        const completeConfirmed = await window.IdeaUI.confirm({
          title: "PRD를 완료할까요?",
          message: "완료하면 일반 편집이 잠깁니다.",
          confirmText: "완료",
          cancelText: "취소"
        });
        if (!completeConfirmed) return;
        try {
          await api(detailApi + "complete/", {method: "POST", body: JSON.stringify({confirm_incomplete: false})});
        } catch (error) {
          const needsConfirmation = error.details && error.details.confirm_incomplete;
          if (!needsConfirmation) throw error;
          const incompleteConfirmed = await window.IdeaUI.confirm({
            title: "미답변 질문이 있습니다",
            message: "아직 답변하지 않은 질문이 있습니다. 그래도 완료하시겠습니까?",
            confirmText: "그래도 완료",
            cancelText: "돌아가기"
          });
          if (!incompleteConfirmed) return;
          await api(detailApi + "complete/", {method: "POST", body: JSON.stringify({confirm_incomplete: true})});
        }
        renderDetail(await api(detailApi));
        showAlert("PRD를 완료했습니다.", "success");
      } else if (previous === "completed") {
        if (requested !== "in_progress") throw new Error("완료된 PRD는 먼저 진행 중으로 다시 열어 주세요.");
        if (detail.prd.auto_completed && isPastDeadline(detail.prd)) {
          showAlert("자동 완료된 PRD입니다. 먼저 마감 기한을 오늘 이후로 변경해 주세요.", "warning");
          deadlineInput.focus();
          return;
        }
        const reason = await window.IdeaUI.prompt({
          title: "PRD 다시 열기",
          message: "다시 여는 이유를 입력해 주세요.",
          placeholder: "예: 추가 수정이 필요합니다.",
          confirmText: "다시 열기",
          cancelText: "취소",
          required: true
        });
        if (!reason || !reason.trim()) return;
        await api(detailApi + "reopen/", {method: "POST", body: JSON.stringify({reason: reason.trim()})});
        renderDetail(await api(detailApi));
        showAlert("PRD를 다시 열었습니다.", "success");
      } else {
        await updateMetadata({status: requested});
        showAlert("PRD 상태를 변경했습니다.", "success");
      }
    } catch (error) {
      if (error.code === "version_conflict") {
        renderDetail(await api(detailApi));
        showAlert("다른 사용자가 먼저 PRD를 변경했습니다. 최신 상태를 불러왔습니다.", "warning");
      } else showAlert(error.message);
    } finally {
      statusControl.disabled = false;
      if (detail) {
        statusControl.dataset.status = detail.prd.status;
        statusControlLabel.textContent = statusLabels[detail.prd.status] || detail.prd.status;
      } else {
        statusControl.dataset.status = previous;
      }
    }
  }

  statusOptions.forEach(function (option) {
    option.addEventListener("click", function () {
      if (!option.disabled && option.dataset.prdStatusOption !== detail.prd.status) {
        changePrdStatus(option.dataset.prdStatusOption);
      }
    });
  });

  deadlineInput.addEventListener("change", async function () {
    const previous = detail.prd.deadline || "";
    deadlineInput.disabled = true;
    try {
      await updateMetadata({deadline: deadlineInput.value || null});
      showAlert(deadlineInput.value ? "목표 마감일을 변경했습니다." : "목표 마감일을 삭제했습니다.", "success");
    } catch (error) {
      if (error.code === "version_conflict") {
        renderDetail(await api(detailApi));
        showAlert("다른 사용자가 먼저 PRD를 변경했습니다. 최신 마감일을 불러왔습니다.", "warning");
      } else {
        deadlineInput.value = previous;
        showAlert(error.message);
      }
    } finally {
      deadlineInput.disabled = !detail.permissions.can_edit_deadline;
    }
  });

  document.getElementById("reopen-prd").addEventListener("click", async function (event) {
    if (detail.prd.auto_completed && isPastDeadline(detail.prd)) {
      showAlert("자동 완료된 PRD입니다. 먼저 마감 기한을 오늘 이후로 변경해 주세요.", "warning");
      deadlineInput.focus();
      return;
    }
    const reason = await window.IdeaUI.prompt({
      title: "PRD 다시 열기",
      message: "다시 여는 이유를 입력해 주세요.",
      placeholder: "예: 추가 수정이 필요합니다.",
      confirmText: "다시 열기",
      cancelText: "취소",
      required: true
    });
    if (!reason || !reason.trim()) return;
    const button = event.currentTarget;
    button.disabled = true;
    try {
      await api(detailApi + "reopen/", {method: "POST", body: JSON.stringify({reason: reason.trim()})});
      renderDetail(await api(detailApi));
      showAlert("PRD를 다시 열었습니다.", "success");
    } catch (error) {
      showAlert(error.message);
    } finally {
      button.disabled = false;
    }
  });

  function fallbackParticipantAvatar(participant, className) {
    const avatar = element("span", className || "participant-person-avatar");
    const name = String(participant?.display_name || "?").trim();
    avatar.textContent = name.length > 2 ? name.slice(-2) : name || "?";
    avatar.setAttribute("aria-hidden", "true");
    return avatar;
  }

  let participantController = {
    load: function () { return Promise.resolve(); },
    avatar: fallbackParticipantAvatar
  };
  if (window.PrdWriteParticipants && typeof window.PrdWriteParticipants.create === "function") {
    try {
      participantController = window.PrdWriteParticipants.create({
        api: api,
        element: element,
        participantsApi: participantsApi,
        participantSearchApi: participantSearchApi,
        participantTeamApi: participantTeamApi,
        canManageParticipants: function () { return canManageParticipants; }
      });
    } catch (error) {
      console.error("[Idea Write] participant module init failed", error);
    }
  } else {
    console.error("[Idea Write] write-participants.js did not load.");
  }

  let commentController = {
    load: function () { return Promise.resolve(); },
    getItemsForQuestion: function () { return []; },
    getCountForQuestion: function () { return 0; },
    getTotalCount: function () { return 0; }
  };
  if (window.PrdWriteComments && typeof window.PrdWriteComments.create === "function") {
    try {
      commentController = window.PrdWriteComments.create({
        api: api,
        element: element,
        participantAvatar: participantController.avatar || fallbackParticipantAvatar,
        commentsApi: commentsApi,
        emptyIllustration: sharedThinkingIllustration,
        getDetail: function () { return detail; }
      });
    } catch (error) {
      console.error("[Idea Write] comment module init failed", error);
    }
  } else {
    console.error("[Idea Write] write-comments.js did not load.");
  }
  document.addEventListener("prd:comments-loaded", function () {
    if (detail && writeView === "write") renderContext();
  });

  let contributionController = {load: function () { return Promise.resolve(); }};
  if (window.PrdWriteContributions && typeof window.PrdWriteContributions.create === "function") {
    try {
      contributionController = window.PrdWriteContributions.create({
        api: api,
        element: element,
        contributionsApi: contributionsApi,
        getDetail: function () { return detail; }
      });
    } catch (error) {
      console.error("[Idea Write] contribution module init failed", error);
    }
  } else {
    console.error("[Idea Write] write-contributions.js did not load.");
  }
  saveAllButton.addEventListener("click", saveAllAnswers);

  exportModalElement.addEventListener("show.bs.modal", function () {
    setExportTab("check");
    renderExportCheck();
    downloadMarkdownLink.href = exportApi;
    loadMarkdownPreview();
  });
  document.getElementById("export-check-tab").addEventListener("click", function () {
    setExportTab("check");
  });
  document.getElementById("export-preview-tab").addEventListener("click", function () {
    setExportTab("preview");
  });
  copyMarkdownButton.addEventListener("click", async function () {
    if (!exportedMarkdown) return;
    try {
      await navigator.clipboard.writeText(exportedMarkdown);
      copyMarkdownButton.innerHTML = '<i class="idea-icon idea-icon-check2"></i> 복사됨';
      window.setTimeout(function () {
        copyMarkdownButton.innerHTML = '<i class="idea-icon idea-icon-clipboard"></i> 복사';
      }, 1800);
    } catch (_error) {
      showAlert("클립보드에 복사하지 못했습니다. 미리보기 내용을 직접 복사해 주세요.");
    }
  });

  if (expandAllSectionsButton) {
    expandAllSectionsButton.addEventListener("click", function () {
      if (!detail || authorMode !== "direct") return;
      detail.sections.forEach(function (section) { expandedSectionIds.add(String(section.id)); });
      renderDetail(detail);
    });
  }
  if (collapseAllSectionsButton) {
    collapseAllSectionsButton.addEventListener("click", function () {
      if (!detail || authorMode !== "direct") return;
      expandedSectionIds.clear();
      if (activeSectionId !== undefined && activeSectionId !== null) expandedSectionIds.add(String(activeSectionId));
      renderDetail(detail);
      if (activeSectionId !== undefined && activeSectionId !== null) requestAnimationFrame(function () { scrollToSection(activeSectionId); });
    });
  }

  document.getElementById("structure-view").addEventListener("click", function () {
    navigateWriting(function () { authorMode = "guided"; });
  });
  document.getElementById("question-view").addEventListener("click", function () {
    navigateWriting(function () {
      authorMode = "direct";
      if (activeSectionId !== undefined && activeSectionId !== null) expandedSectionIds.add(String(activeSectionId));
    });
  });
  root.querySelectorAll("[data-write-view]").forEach(function (button) {
    button.addEventListener("click", function () { navigateWriting(function () { writeView = button.dataset.writeView; }); });
  });
  const projectActions = element("div", "v34-project-actions");
  projectActions.append(document.getElementById("contribution-toggle"), document.getElementById("reopen-prd"));
  root.querySelector(".write-toolbar").append(projectActions);
  root.querySelector(".v34-views").append(root.querySelector(".write-actions"));
  root.querySelector(".write-workspace").prepend(root.querySelector(".write-stepper"));
  root.dataset.writeView = "write";
  root.querySelector(".write-body-viewport")?.addEventListener("scroll", syncActiveSectionFromScroll, {passive:true});
  window.addEventListener("pagehide", function () { flushAnswers(); });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
  });

  if (uiDemoMode && typeof uiDemo.decorate === "function") uiDemo.decorate(root);
  if (uiDemoMode) {
    const brainstormLink = root.querySelector(".brainstorm-launch");
    if (brainstormLink) {
      try {
        const url = new URL(brainstormLink.href, window.location.origin);
        url.searchParams.set("ui_demo", "1");
        brainstormLink.href = url.pathname + url.search;
      } catch (_error) {}
    }
  }

  api(detailApi)
    .then(function (data) {
      if (uiDemoMode && typeof uiDemo.prepareDetail === "function") {
        data = uiDemo.prepareDetail(data, guidedSchema);
        const demoFocus = data.sections.flatMap(function (section) {
          return (section.questions || []).map(function (question) {
            return {section:section, question:question, config:guidedSchema.getConfig(data.prd.prd_type, section.position, question.position)};
          });
        }).find(function (item) { return item.config?.kind === "steps"; });
        if (demoFocus) {
          activeSectionId = demoFocus.section.id;
          activeQuestionId = demoFocus.question.id;
        }
      }
      if (data.current_user_id !== undefined && data.current_user_id !== null) {
        root.dataset.currentUserId = String(data.current_user_id);
      }
      if (participantController.setCurrentUserIdentity) {
        participantController.setCurrentUserIdentity(
          data.current_user_id,
          root.dataset.currentUserName,
          Boolean(data.permissions?.is_creator)
        );
      }
      renderDetail(data);
      Promise.resolve(participantController.load()).catch(function (error) {
        console.error("[Idea Write] participants load failed", error);
      });
      Promise.resolve(commentController.load()).catch(function (error) {
        console.error("[Idea Write] comments load failed", error);
      });
      loadEvaluation();
      return loadConversation();
    })
    .catch(function (error) { showAlert(error.message); });
}());
