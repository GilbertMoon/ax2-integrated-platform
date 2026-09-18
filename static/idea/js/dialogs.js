(function () {
  "use strict";

  if (window.IdeaUI && window.IdeaUI.__v2) return;

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function firstErrorDetail(value) {
    if (!value) return "";
    if (typeof value === "string") return value.trim();

    if (Array.isArray(value)) {
      for (var i = 0; i < value.length; i += 1) {
        var arrayMessage = firstErrorDetail(value[i]);
        if (arrayMessage) return arrayMessage;
      }
      return "";
    }

    if (typeof value === "object") {
      var values = Object.values(value);
      for (var j = 0; j < values.length; j += 1) {
        var objectMessage = firstErrorDetail(values[j]);
        if (objectMessage) return objectMessage;
      }
    }

    return "";
  }

  function dialog(options) {
    options = options || {};

    var mode = options.mode || "confirm";
    var tone = options.tone || "primary";

    return new Promise(function (resolve) {
      var previousFocus = document.activeElement;

      var backdrop = element("div", "idea-ui-dialog-backdrop");
      var panel = element("section", "idea-ui-dialog");

      panel.setAttribute("role", "dialog");
      panel.setAttribute("aria-modal", "true");

      var header = element("header", "idea-ui-dialog__header");
      var heading = element("div");

      var eyebrow = element(
        "span",
        "idea-ui-dialog__eyebrow",
        options.eyebrow || "IDEA DEVELOPER"
      );

      var title = element(
        "h2",
        "idea-ui-dialog__title",
        options.title || "확인"
      );

      heading.append(eyebrow, title);

      var close = element("button", "idea-ui-dialog__close");
      close.type = "button";
      close.setAttribute("aria-label", "닫기");
      close.innerHTML = '<i class="bi bi-x-lg"></i>';

      header.append(heading, close);

      var body = element("div", "idea-ui-dialog__body");

      body.append(
        element(
          "p",
          "idea-ui-dialog__message",
          options.message || ""
        )
      );

      var input = null;
      var inputError = null;

      if (mode === "prompt") {
        input = element("input", "idea-ui-dialog__input");
        input.type = "text";
        input.value = options.value || "";
        input.placeholder = options.placeholder || "";
        input.maxLength = options.maxLength || 500;

        inputError = element("div", "idea-ui-dialog__error");
        inputError.hidden = true;

        body.append(input, inputError);
      }

      var footer = element("footer", "idea-ui-dialog__footer");

      var cancel = element(
        "button",
        "idea-ui-dialog__button",
        options.cancelText || "취소"
      );
      cancel.type = "button";

      var confirmClass =
        "idea-ui-dialog__button " +
        (
          tone === "danger"
            ? "idea-ui-dialog__button--danger"
            : "idea-ui-dialog__button--primary"
        );

      var confirm = element(
        "button",
        confirmClass,
        options.confirmText || "확인"
      );
      confirm.type = "button";

      if (mode === "alert") {
        footer.append(confirm);
      } else {
        footer.append(cancel, confirm);
      }

      panel.append(header, body, footer);
      backdrop.append(panel);
      document.body.append(backdrop);

      var settled = false;

      function finish(value) {
        if (settled) return;
        settled = true;

        document.removeEventListener("keydown", onKeydown, true);

        backdrop.remove();

        if (
          previousFocus &&
          previousFocus.focus &&
          document.contains(previousFocus)
        ) {
          previousFocus.focus();
        }

        resolve(value);
      }

      function submit() {
        if (mode === "prompt") {
          var value = input.value.trim();

          if (options.required && !value) {
            inputError.textContent =
              options.requiredMessage || "내용을 입력해 주세요.";

            inputError.hidden = false;
            input.focus();
            return;
          }

          finish(value);
          return;
        }

        finish(true);
      }

      function onKeydown(event) {
        if (event.key === "Escape") {
          event.preventDefault();
          finish(mode === "prompt" ? null : false);
          return;
        }

        if (
          event.key === "Enter" &&
          mode === "prompt" &&
          document.activeElement === input
        ) {
          event.preventDefault();
          submit();
        }
      }

      close.addEventListener("click", function () {
        finish(mode === "prompt" ? null : false);
      });

      cancel.addEventListener("click", function () {
        finish(mode === "prompt" ? null : false);
      });

      confirm.addEventListener("click", submit);

      backdrop.addEventListener("mousedown", function (event) {
        if (event.target === backdrop) {
          finish(mode === "prompt" ? null : false);
        }
      });

      document.addEventListener("keydown", onKeydown, true);

      window.setTimeout(function () {
        if (input) input.focus();
        else confirm.focus();
      }, 0);
    });
  }

  function toast(message, options) {
    options = options || {};

    var stack = document.querySelector(".idea-ui-toast-stack");

    if (!stack) {
      stack = element("div", "idea-ui-toast-stack");
      document.body.append(stack);
    }

    var tone = options.tone || "default";

    var item = element(
      "div",
      "idea-ui-toast" +
        (tone === "default" ? "" : " idea-ui-toast--" + tone),
      message
    );

    stack.append(item);

    window.setTimeout(function () {
      item.remove();
      if (!stack.childElementCount) stack.remove();
    }, options.duration || 2600);
  }

  window.IdeaUI = {
    __v2: true,

    confirm: function (options) {
      if (typeof options === "string") {
        options = {message: options};
      }

      return dialog(
        Object.assign(
          {mode: "confirm"},
          options || {}
        )
      );
    },

    prompt: function (options) {
      if (typeof options === "string") {
        options = {message: options};
      }

      return dialog(
        Object.assign(
          {mode: "prompt"},
          options || {}
        )
      );
    },

    alert: function (options) {
      if (typeof options === "string") {
        options = {message: options};
      }

      return dialog(
        Object.assign(
          {mode: "alert"},
          options || {}
        )
      );
    },

    toast: toast
  };

  /* ==========================================================
     Helpers used by the automatic compatibility bridge
     ========================================================== */

  var replayingClicks = new WeakSet();
  var replayingEscape = false;

  function isIdeaPage() {
    return Boolean(
      document.querySelector(
        ".idea-dev, #prd-home-app, #new-prd-app, #prd-write-app, #brainstorm-root"
      )
    );
  }

  function withNativeConfirm(result, callback) {
    var original = window.confirm;

    window.confirm = function () {
      return result;
    };

    try {
      return callback();
    } finally {
      window.confirm = original;
    }
  }

  function replayClick(target, nativeConfirmResult) {
    replayingClicks.add(target);

    return withNativeConfirm(
      nativeConfirmResult,
      function () {
        target.click();
      }
    );
  }

  function probeConfirm(target) {
    var asked = false;
    var message = "";

    var original = window.confirm;

    window.confirm = function (value) {
      asked = true;
      message = String(value || "");
      return false;
    };

    try {
      replayingClicks.add(target);
      target.click();
    } finally {
      window.confirm = original;
    }

    return {
      asked: asked,
      message: message
    };
  }

  function replayEscape(nativeConfirmResult) {
    replayingEscape = true;

    return withNativeConfirm(
      nativeConfirmResult,
      function () {
        document.dispatchEvent(
          new KeyboardEvent(
            "keydown",
            {
              key: "Escape",
              code: "Escape",
              bubbles: true,
              cancelable: true
            }
          )
        );
      }
    );
  }

  function probeEscapeConfirm() {
    var asked = false;
    var message = "";

    var original = window.confirm;

    window.confirm = function (value) {
      asked = true;
      message = String(value || "");
      return false;
    };

    try {
      replayingEscape = true;

      document.dispatchEvent(
        new KeyboardEvent(
          "keydown",
          {
            key: "Escape",
            code: "Escape",
            bubbles: true,
            cancelable: true
          }
        )
      );
    } finally {
      window.confirm = original;
    }

    return {
      asked: asked,
      message: message
    };
  }

  async function ideaRequest(url, options) {
    var response;

    try {
      response = await fetch(
        url,
        Object.assign(
          {
            credentials: "same-origin",
            cache: "no-store"
          },
          options || {},
          {
            headers: Object.assign(
              {
                "Content-Type": "application/json",
                "X-CSRFToken":
                  document.querySelector('meta[name="csrf-token"]')
                    ?.content || ""
              },
              options?.headers || {}
            )
          }
        )
      );
    } catch (_networkError) {
      throw new Error(
        "서버에 연결하지 못했습니다. 네트워크 상태를 확인해 주세요."
      );
    }

    var contentType =
      response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
      throw new Error(
        response.status === 401 || response.redirected
          ? "로그인 상태가 만료되었습니다. 새로고침 후 다시 로그인해 주세요."
          : "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
      );
    }

    var payload = await response.json();

    if (!response.ok || !payload.ok) {
      var error = new Error(
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

  async function completePrd(writeRoot) {
    var confirmed = await window.IdeaUI.confirm({
      title: "PRD를 완료할까요?",
      message: "완료하면 일반 편집이 잠깁니다.",
      confirmText: "완료",
      cancelText: "취소",
      tone: "primary"
    });

    if (!confirmed) return;

    var detailApi = writeRoot.dataset.detailApi;

    try {
      await ideaRequest(
        detailApi + "complete/",
        {
          method: "POST",
          body: JSON.stringify({
            confirm_incomplete: false
          })
        }
      );
    } catch (error) {
      var needsConfirmation =
        Boolean(
          error.details &&
          error.details.confirm_incomplete
        );

      if (!needsConfirmation) {
        await window.IdeaUI.alert({
          title: "완료하지 못했습니다",
          message: error.message,
          confirmText: "확인",
          tone: "danger"
        });
        return;
      }

      var incompleteConfirmed =
        await window.IdeaUI.confirm({
          title: "미답변 질문이 있습니다",
          message:
            "아직 답변하지 않은 질문이 있습니다.\n그래도 PRD를 완료하시겠습니까?",
          confirmText: "그래도 완료",
          cancelText: "돌아가기",
          tone: "primary"
        });

      if (!incompleteConfirmed) return;

      try {
        await ideaRequest(
          detailApi + "complete/",
          {
            method: "POST",
            body: JSON.stringify({
              confirm_incomplete: true
            })
          }
        );
      } catch (finalError) {
        await window.IdeaUI.alert({
          title: "완료하지 못했습니다",
          message: finalError.message,
          confirmText: "확인",
          tone: "danger"
        });
        return;
      }
    }

    window.location.reload();
  }

  async function reopenPrd(writeRoot) {
    var reason = await window.IdeaUI.prompt({
      title: "PRD 다시 열기",
      message: "다시 여는 이유를 입력해 주세요.",
      placeholder: "예: 요구사항 변경으로 추가 수정이 필요합니다.",
      confirmText: "다시 열기",
      cancelText: "취소",
      required: true,
      requiredMessage: "다시 여는 이유를 입력해 주세요."
    });

    if (!reason) return;

    try {
      await ideaRequest(
        writeRoot.dataset.detailApi + "reopen/",
        {
          method: "POST",
          body: JSON.stringify({
            reason: reason
          })
        }
      );

      window.location.reload();
    } catch (error) {
      await window.IdeaUI.alert({
        title: "다시 열 수 없습니다",
        message: error.message,
        confirmText: "확인",
        tone: "danger"
      });
    }
  }

  function hideStatusDropdown() {
    var control =
      document.getElementById("prd-status-control");

    if (
      control &&
      window.bootstrap?.Dropdown
    ) {
      window.bootstrap.Dropdown
        .getOrCreateInstance(control)
        .hide();
    }
  }

  async function handleSimpleNativeConfirm(
    target,
    options
  ) {
    var probe = probeConfirm(target);

    /*
     * No confirm was requested by the original handler.
     * In that case the probed replay already completed the original action.
     */
    if (!probe.asked) return;

    var confirmed =
      await window.IdeaUI.confirm({
        title: options.title,
        message:
          options.message ||
          probe.message ||
          "계속하시겠습니까?",
        confirmText:
          options.confirmText || "확인",
        cancelText:
          options.cancelText || "취소",
        tone:
          options.tone || "primary"
      });

    if (!confirmed) return;

    replayClick(target, true);
  }

  /* ==========================================================
     Automatic bridge for existing page JS
     No write.js / comments.js / participants.js replacement needed.
     ========================================================== */

  document.addEventListener(
    "click",
    function (event) {
      var target =
        event.target &&
        event.target.closest
          ? event.target.closest("button, a")
          : null;

      if (!target) return;

      if (replayingClicks.has(target)) {
        replayingClicks.delete(target);
        return;
      }

      var writeRoot =
        document.getElementById("prd-write-app");

      if (writeRoot) {
        var statusOption =
          target.closest(
            "[data-prd-status-option]"
          );

        if (statusOption) {
          var requested =
            statusOption.dataset.prdStatusOption;

          var current =
            document.getElementById(
              "prd-status-control"
            )?.dataset.status;

          if (
            requested === "completed" &&
            current !== "completed"
          ) {
            event.preventDefault();
            event.stopImmediatePropagation();

            hideStatusDropdown();
            completePrd(writeRoot);
            return;
          }

          if (
            requested === "in_progress" &&
            current === "completed"
          ) {
            event.preventDefault();
            event.stopImmediatePropagation();

            hideStatusDropdown();
            reopenPrd(writeRoot);
            return;
          }
        }

        if (target.id === "reopen-prd") {
          event.preventDefault();
          event.stopImmediatePropagation();

          reopenPrd(writeRoot);
          return;
        }

        if (
          target.matches(
            ".question-hold-button"
          )
        ) {
          event.preventDefault();
          event.stopImmediatePropagation();

          handleSimpleNativeConfirm(
            target,
            {
              title: "질문을 보류할까요?",
              message:
                "저장하지 않은 답변이 있다면 작성 중인 내용이 사라질 수 있습니다.",
              confirmText: "보류",
              cancelText: "계속 작성",
              tone: "danger"
            }
          );

          return;
        }

        if (
          target.matches(
            "#write-comments-panel .comment-actions .text-danger"
          )
        ) {
          event.preventDefault();
          event.stopImmediatePropagation();

          handleSimpleNativeConfirm(
            target,
            {
              title: "코멘트를 삭제할까요?",
              message:
                "삭제한 코멘트는 목록에서 제거됩니다.",
              confirmText: "삭제",
              cancelText: "취소",
              tone: "danger"
            }
          );

          return;
        }

        if (
          target.matches(
            "#participant-picker .participant-person-actions .btn-outline-danger"
          )
        ) {
          event.preventDefault();
          event.stopImmediatePropagation();

          var participantName =
            target
              .closest(".participant-person")
              ?.querySelector(
                ".participant-person-copy strong"
              )
              ?.textContent
              ?.trim();

          handleSimpleNativeConfirm(
            target,
            {
              title: "참여자를 제거할까요?",
              message:
                (participantName
                  ? participantName + "님을 "
                  : "이 사용자를 ") +
                "PRD 참여자에서 제거합니다.",
              confirmText: "제거",
              cancelText: "취소",
              tone: "danger"
            }
          );

          return;
        }
      }

      var homeRoot =
        document.getElementById("prd-home-app");

      if (
        homeRoot &&
        target.matches(
          "#prd-trash-list .trash-item-actions .btn-outline-danger"
        )
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();

        handleSimpleNativeConfirm(
          target,
          {
            title: "삭제 완료로 처리할까요?",
            message:
              "데이터는 최초 삭제일로부터 30일 뒤 영구 삭제됩니다.",
            confirmText: "삭제 처리",
            cancelText: "취소",
            tone: "danger"
          }
        );

        return;
      }

      /*
       * Brainstorm editor has a synchronous window.confirm internally.
       * Probe it first with confirm=false. If the editor is clean, the
       * original click simply closes it. If it is dirty, the editor stays
       * open and we show our custom dialog before replaying with confirm=true.
       */
      if (
        document.getElementById("brainstorm-root") &&
        target.matches(
          ".brain-editor-modal > header button, " +
          ".brain-editor-modal > footer .btn-light, " +
          ".brain-editor-modal > footer .btn-outline-secondary"
        )
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();

        handleSimpleNativeConfirm(
          target,
          {
            title: "작성 중인 내용을 버릴까요?",
            message:
              "저장하지 않은 메모 내용은 복구할 수 없습니다.",
            confirmText: "버리고 닫기",
            cancelText: "계속 작성",
            tone: "danger"
          }
        );
      }
    },
    true
  );

  /* Brainstorm editor ESC */
  document.addEventListener(
    "keydown",
    function (event) {
      if (replayingEscape) {
        replayingEscape = false;
        return;
      }

      if (
        event.key !== "Escape" ||
        !document.getElementById("brainstorm-root") ||
        !document.querySelector(".brain-editor-modal")
      ) {
        return;
      }

      event.preventDefault();
      event.stopImmediatePropagation();

      var probe =
        probeEscapeConfirm();

      if (!probe.asked) {
        return;
      }

      window.IdeaUI.confirm({
        title: "작성 중인 내용을 버릴까요?",
        message:
          "저장하지 않은 메모 내용은 복구할 수 없습니다.",
        confirmText: "버리고 닫기",
        cancelText: "계속 작성",
        tone: "danger"
      }).then(function (confirmed) {
        if (confirmed) {
          replayEscape(true);
        }
      });
    },
    true
  );

  /* ==========================================================
     Existing browser alert() can be safely replaced because
     callers do not depend on a synchronous return value.
     ========================================================== */

  var nativeAlert =
    window.alert.bind(window);

  window.alert = function (message) {
    if (!isIdeaPage()) {
      nativeAlert(message);
      return;
    }

    window.IdeaUI.alert({
      title: "알림",
      message: String(message || ""),
      confirmText: "확인"
    });
  };

  /* ==========================================================
     Feedback cleanup without touching existing write.js
     ========================================================== */

  function setupWriteFeedbackBridge() {
    var writeRoot =
      document.getElementById("prd-write-app");

    if (!writeRoot) return;

    var prdAlert =
      document.getElementById("prd-alert");

    if (prdAlert) {
      new MutationObserver(function () {
        var message =
          prdAlert.textContent.trim();

        if (
          message.startsWith(
            "질문을 보류했습니다"
          )
        ) {
          prdAlert.classList.remove(
            "alert-success"
          );

          prdAlert.classList.add(
            "alert-danger"
          );
        }
      }).observe(prdAlert, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class"]
      });
    }

    function autoDismissSuccess(node) {
      if (!node) return;

      var timer = null;

      new MutationObserver(function () {
        window.clearTimeout(timer);

        var visible =
          !node.classList.contains("d-none");

        var success =
          node.classList.contains("alert-success") ||
          node.classList.contains("success");

        if (!visible || !success) return;

        timer =
          window.setTimeout(
            function () {
              node.classList.add("d-none");
            },
            2200
          );
      }).observe(node, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class"]
      });
    }

    autoDismissSuccess(
      document.getElementById(
        "comment-panel-alert"
      )
    );

    autoDismissSuccess(
      document.getElementById(
        "participant-alert"
      )
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      setupWriteFeedbackBridge,
      {once: true}
    );
  } else {
    setupWriteFeedbackBridge();
  }

}());
