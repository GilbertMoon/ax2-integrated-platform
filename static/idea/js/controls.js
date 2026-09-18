(function () {
  "use strict";

  /* =========================
     Shared Select
     ========================= */

  function selectedOption(select) {
    return (
      select.options[select.selectedIndex] ||
      select.options[0] ||
      null
    );
  }

  function enhanceSelect(select) {
    if (
      !(select instanceof HTMLSelectElement) ||
      select.dataset.studioEnhanced === "true"
    ) {
      return;
    }

    if (
      !select.classList.contains("form-select") ||
      select.dataset.nativeSelect === "true"
    ) {
      return;
    }

    const shell = document.createElement("div");
    shell.className = "studio-select-shell dropdown";

    select.parentNode.insertBefore(shell, select);
    shell.append(select);

    select.dataset.studioEnhanced = "true";
    select.classList.add("studio-native-select");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");

    const button = document.createElement("button");
    button.type = "button";
    button.className = "studio-select-button";
    button.dataset.bsToggle = "dropdown";
    button.setAttribute("aria-expanded", "false");

    const label = document.createElement("span");
    label.className = "text-truncate";

    const chevron = document.createElement("i");
    chevron.className =
      "bi bi-chevron-down studio-select-chevron";

    button.append(label, chevron);

    const menu = document.createElement("div");
    menu.className =
      "dropdown-menu studio-select-menu";

    shell.append(button, menu);

    function sync() {
      const option =
        selectedOption(select);

      label.textContent =
        option
          ? option.textContent.trim()
          : "선택";

      button.disabled = select.disabled;

      button.setAttribute(
        "aria-label",
        select.getAttribute("aria-label") ||
          label.textContent
      );

      menu
        .querySelectorAll(
          "[data-studio-option]"
        )
        .forEach(function (item) {
          const active =
            item.dataset.studioOption ===
            select.value;

          item.classList.toggle(
            "is-selected",
            active
          );

          item.setAttribute(
            "aria-selected",
            String(active)
          );
        });
    }

    function rebuild() {
      menu.replaceChildren();

      Array.from(select.options)
        .forEach(function (option) {
          const item =
            document.createElement("button");

          item.type = "button";
          item.className =
            "studio-select-option";

          item.dataset.studioOption =
            option.value;

          item.disabled =
            option.disabled;

          item.setAttribute(
            "role",
            "option"
          );

          const copy =
            document.createElement("span");

          copy.className =
            "text-truncate";

          copy.textContent =
            option.textContent.trim();

          const check =
            document.createElement("i");

          check.className =
            "bi bi-check-lg";

          item.append(copy, check);

          item.addEventListener(
            "click",
            function () {
              if (option.disabled) return;

              select.value =
                option.value;

              select.dispatchEvent(
                new Event("change", {
                  bubbles: true
                })
              );

              sync();

              if (
                window.bootstrap?.Dropdown
              ) {
                window.bootstrap.Dropdown
                  .getOrCreateInstance(
                    button
                  )
                  .hide();
              }
            }
          );

          menu.append(item);
        });

      sync();
    }

    select.addEventListener(
      "change",
      sync
    );

    new MutationObserver(
      rebuild
    ).observe(select, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: [
        "disabled",
        "selected",
        "label"
      ]
    });

    select._studioSelectSync =
      sync;

    rebuild();
  }

  /* =========================
     Shared Date Picker
     ========================= */

  let activeDatePicker = null;

  function ensureDateStyles() {
    if (
      document.getElementById(
        "idea-date-runtime-style"
      )
    ) {
      return;
    }

    const style =
      document.createElement("style");

    style.id =
      "idea-date-runtime-style";

    style.textContent = `
.idea-date-field{position:relative;display:block}
.idea-date-native{position:absolute!important;width:1px!important;height:1px!important;margin:-1px!important;padding:0!important;overflow:hidden!important;clip:rect(0 0 0 0)!important;white-space:nowrap!important;border:0!important;opacity:0!important;pointer-events:none!important}
.idea-date-trigger{display:flex;width:100%;min-height:46px;align-items:center;gap:10px;justify-content:space-between;padding:0 13px;border:1px solid var(--idea-border-default,#e2e8f0);border-radius:12px;color:var(--idea-text-secondary,#334155);background:var(--idea-neutral-25,#fbfcfe);cursor:pointer;font:500 14px/1 var(--idea-font-family,Pretendard,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif)}
.idea-date-trigger:hover{border-color:var(--idea-indigo-200,#c7d2fe);background:#fff}
.idea-date-trigger[aria-expanded="true"],.idea-date-trigger:focus-visible{border-color:var(--idea-border-focus,#818cf8);outline:0;background:#fff;box-shadow:var(--idea-focus-ring,0 0 0 3px rgba(99,102,241,.12))}
.idea-date-trigger:disabled{cursor:not-allowed;opacity:.55}
.idea-date-value{min-width:0;flex:1;overflow:hidden;text-align:left;text-overflow:ellipsis;white-space:nowrap}
.idea-date-value.is-placeholder{color:var(--idea-text-disabled,#94a3b8)}
.idea-date-trigger i{color:var(--idea-color-primary,#4f46e5)}
.idea-date-popover{position:fixed;z-index:2200;width:min(312px,calc(100vw - 24px));padding:12px;border:1px solid var(--idea-border-default,#e2e8f0);border-radius:16px;color:var(--idea-text-secondary,#334155);background:#fff;box-shadow:0 22px 60px rgba(15,23,42,.22);font-family:var(--idea-font-family,Pretendard,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif)}
.idea-date-popover[hidden]{display:none!important}
.idea-date-head{display:grid;grid-template-columns:34px minmax(0,1fr) 34px;align-items:center;gap:7px}
.idea-date-nav,.idea-date-period,.idea-date-action,.idea-date-month-button{border:0;color:var(--idea-text-secondary,#334155);background:transparent}
.idea-date-nav{display:grid;width:34px;height:34px;place-items:center;border-radius:9px;color:var(--idea-text-muted,#64748b)}
.idea-date-nav:hover{color:var(--idea-color-primary,#4f46e5);background:var(--idea-color-primary-soft,#eef2ff)}
.idea-date-period{display:flex;min-height:34px;align-items:center;justify-content:center;gap:7px;border-radius:9px;font-size:13px;font-weight:700}
.idea-date-period:hover,.idea-date-period[aria-expanded="true"]{color:var(--idea-color-primary-hover,#4338ca);background:var(--idea-color-primary-soft,#eef2ff)}
.idea-date-month-panel{margin-top:9px;padding:10px;border:1px solid var(--idea-border-default,#e2e8f0);border-radius:12px;background:var(--idea-surface-subtle,#f8fafc)}
.idea-date-year-head{display:grid;grid-template-columns:30px 1fr 30px;align-items:center;gap:6px;margin-bottom:9px}
.idea-date-year-head strong{text-align:center;font-size:13px}
.idea-date-month-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.idea-date-month-button{min-height:34px;border-radius:8px;font-size:12px}
.idea-date-month-button:hover{color:var(--idea-color-primary,#4f46e5);background:#fff}
.idea-date-month-button.is-selected{color:#fff;background:var(--idea-color-primary,#4f46e5)}
.idea-date-weekdays,.idea-date-days{display:grid;grid-template-columns:repeat(7,1fr)}
.idea-date-weekdays{margin-top:10px;padding:0 2px}
.idea-date-weekdays span{display:grid;height:25px;place-items:center;color:var(--idea-text-disabled,#94a3b8);font-size:10px;font-weight:600}
.idea-date-days{gap:3px;margin-top:2px}
.idea-date-day{display:grid;aspect-ratio:1/1;place-items:center;padding:0;border:0;border-radius:9px;color:var(--idea-text-secondary,#334155);background:transparent;font-size:12px}
.idea-date-day:hover:not(:disabled){color:var(--idea-color-primary,#4f46e5);background:var(--idea-color-primary-soft,#eef2ff)}
.idea-date-day.is-outside{color:#cbd5e1}
.idea-date-day.is-today{box-shadow:inset 0 0 0 1px var(--idea-indigo-300,#a5b4fc);color:var(--idea-color-primary,#4f46e5);font-weight:700}
.idea-date-day.is-selected{color:#fff;background:var(--idea-color-primary,#4f46e5);font-weight:700;box-shadow:none}
.idea-date-day:disabled{cursor:not-allowed;opacity:.32}
.idea-date-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:10px;padding-top:10px;border-top:1px solid var(--idea-border-default,#e2e8f0)}
.idea-date-action{min-height:32px;padding:0 10px;border-radius:8px;font-size:11px;font-weight:600}
.idea-date-action:hover{background:var(--idea-surface-muted,#f1f5f9)}
.idea-date-action.is-primary{color:var(--idea-color-primary,#4f46e5);background:var(--idea-color-primary-soft,#eef2ff)}
.idea-date-action.is-primary:hover{color:#fff;background:var(--idea-color-primary,#4f46e5)}
@media(max-width:480px){.idea-date-popover{width:calc(100vw - 20px)!important}}
`;

    document.head.append(style);
  }

  function parseDate(value) {
    const match =
      /^(\d{4})-(\d{2})-(\d{2})$/.exec(
        String(value || "")
      );

    if (!match) return null;

    const date =
      new Date(
        Number(match[1]),
        Number(match[2]) - 1,
        Number(match[3])
      );

    return Number.isNaN(
      date.getTime()
    )
      ? null
      : date;
  }

  function dateValue(date) {
    const year =
      date.getFullYear();

    const month =
      String(
        date.getMonth() + 1
      ).padStart(2, "0");

    const day =
      String(
        date.getDate()
      ).padStart(2, "0");

    return (
      year +
      "-" +
      month +
      "-" +
      day
    );
  }

  function displayDate(value) {
    const date =
      parseDate(value);

    if (!date) return "";

    return (
      date.getFullYear() +
      ". " +
      String(
        date.getMonth() + 1
      ).padStart(2, "0") +
      ". " +
      String(
        date.getDate()
      ).padStart(2, "0") +
      "."
    );
  }

  function sameDay(a, b) {
    return Boolean(
      a &&
      b &&
      a.getFullYear() ===
        b.getFullYear() &&
      a.getMonth() ===
        b.getMonth() &&
      a.getDate() ===
        b.getDate()
    );
  }

  function enhanceDate(input) {
    if (
      !(input instanceof HTMLInputElement) ||
      input.type !== "date" ||
      input.dataset.ideaDateEnhanced === "true" ||
      input.dataset.nativeDate === "true" ||
      !input.closest(".idea-dev, .idea-dev-modal")
    ) {
      return;
    }

    ensureDateStyles();

    input.dataset.ideaDateEnhanced =
      "true";

    const field =
      document.createElement("div");

    field.className =
      "idea-date-field";

    input.parentNode.insertBefore(
      field,
      input
    );

    field.append(input);

    input.classList.add(
      "idea-date-native"
    );

    input.tabIndex = -1;

    const trigger =
      document.createElement("button");

    trigger.type = "button";
    trigger.className =
      "idea-date-trigger";

    trigger.setAttribute(
      "aria-haspopup",
      "dialog"
    );

    trigger.setAttribute(
      "aria-expanded",
      "false"
    );

    const value =
      document.createElement("span");

    value.className =
      "idea-date-value";

    const icon =
      document.createElement("i");

    icon.className =
      "bi bi-calendar3";

    trigger.append(
      value,
      icon
    );

    field.append(trigger);

    const popover =
      document.createElement("div");

    popover.className =
      "idea-date-popover";

    popover.hidden = true;

    popover.setAttribute(
      "role",
      "dialog"
    );

    popover.setAttribute(
      "aria-label",
      "날짜 선택"
    );

    document.body.append(popover);

    const head =
      document.createElement("div");

    head.className =
      "idea-date-head";

    const prev =
      document.createElement("button");

    prev.type = "button";
    prev.className =
      "idea-date-nav";

    prev.setAttribute(
      "aria-label",
      "이전 달"
    );

    prev.innerHTML =
      '<i class="bi bi-chevron-left"></i>';

    const period =
      document.createElement("button");

    period.type = "button";
    period.className =
      "idea-date-period";

    period.setAttribute(
      "aria-expanded",
      "false"
    );

    const next =
      document.createElement("button");

    next.type = "button";
    next.className =
      "idea-date-nav";

    next.setAttribute(
      "aria-label",
      "다음 달"
    );

    next.innerHTML =
      '<i class="bi bi-chevron-right"></i>';

    head.append(
      prev,
      period,
      next
    );

    const monthPanel =
      document.createElement("div");

    monthPanel.className =
      "idea-date-month-panel";

    monthPanel.hidden = true;

    const yearHead =
      document.createElement("div");

    yearHead.className =
      "idea-date-year-head";

    const prevYear =
      document.createElement("button");

    prevYear.type = "button";
    prevYear.className =
      "idea-date-nav";

    prevYear.innerHTML =
      '<i class="bi bi-chevron-left"></i>';

    const yearLabel =
      document.createElement("strong");

    const nextYear =
      document.createElement("button");

    nextYear.type = "button";
    nextYear.className =
      "idea-date-nav";

    nextYear.innerHTML =
      '<i class="bi bi-chevron-right"></i>';

    yearHead.append(
      prevYear,
      yearLabel,
      nextYear
    );

    const monthGrid =
      document.createElement("div");

    monthGrid.className =
      "idea-date-month-grid";

    monthPanel.append(
      yearHead,
      monthGrid
    );

    const weekdays =
      document.createElement("div");

    weekdays.className =
      "idea-date-weekdays";

    [
      "일",
      "월",
      "화",
      "수",
      "목",
      "금",
      "토"
    ].forEach(function (text) {
      const item =
        document.createElement("span");

      item.textContent = text;
      weekdays.append(item);
    });

    const days =
      document.createElement("div");

    days.className =
      "idea-date-days";

    const foot =
      document.createElement("div");

    foot.className =
      "idea-date-foot";

    const clear =
      document.createElement("button");

    clear.type = "button";
    clear.className =
      "idea-date-action";

    clear.textContent = "지우기";

    const today =
      document.createElement("button");

    today.type = "button";
    today.className =
      "idea-date-action is-primary";

    today.textContent = "오늘";

    foot.append(
      clear,
      today
    );

    popover.append(
      head,
      monthPanel,
      weekdays,
      days,
      foot
    );

    let viewDate =
      parseDate(input.value) ||
      new Date();

    viewDate =
      new Date(
        viewDate.getFullYear(),
        viewDate.getMonth(),
        1
      );

    let monthSelectYear =
      viewDate.getFullYear();

    function syncTrigger() {
      const text =
        displayDate(input.value);

      value.textContent =
        text || "날짜를 선택해 주세요";

      value.classList.toggle(
        "is-placeholder",
        !text
      );

      trigger.disabled =
        input.disabled;
    }

    /*
     * write.js처럼 API 데이터를 받은 뒤 input.value를 직접 대입하는 경우,
     * native input 값은 바뀌지만 커스텀 trigger 텍스트는 change 이벤트 없이
     * 갱신되지 않는다. 해당 date input 인스턴스의 value setter만 감싸서
     * 프로그램에서 값을 넣어도 화면 표시를 즉시 동기화한다.
     */
    const nativeValueDescriptor =
      Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype,
        "value"
      );

    if (
      nativeValueDescriptor &&
      nativeValueDescriptor.get &&
      nativeValueDescriptor.set &&
      !Object.prototype.hasOwnProperty.call(
        input,
        "value"
      )
    ) {
      Object.defineProperty(
        input,
        "value",
        {
          configurable: true,
          enumerable:
            nativeValueDescriptor.enumerable,

          get: function () {
            return nativeValueDescriptor.get.call(
              input
            );
          },

          set: function (nextValue) {
            nativeValueDescriptor.set.call(
              input,
              nextValue
            );

            window.queueMicrotask(function () {
              const selected =
                parseDate(input.value);

              if (selected) {
                viewDate =
                  new Date(
                    selected.getFullYear(),
                    selected.getMonth(),
                    1
                  );

                monthSelectYear =
                  selected.getFullYear();
              }

              syncTrigger();

              if (!popover.hidden) {
                render();
                position();
              }
            });
          }
        }
      );
    }

    function renderMonthPanel() {
      yearLabel.textContent =
        monthSelectYear + "년";

      monthGrid.replaceChildren();

      for (
        let month = 0;
        month < 12;
        month += 1
      ) {
        const button =
          document.createElement("button");

        button.type = "button";
        button.className =
          "idea-date-month-button";

        button.textContent =
          month + 1 + "월";

        if (
          viewDate.getFullYear() ===
            monthSelectYear &&
          viewDate.getMonth() ===
            month
        ) {
          button.classList.add(
            "is-selected"
          );
        }

        button.addEventListener(
          "click",
          function () {
            viewDate =
              new Date(
                monthSelectYear,
                month,
                1
              );

            monthPanel.hidden = true;
            weekdays.hidden = false;
            days.hidden = false;
            foot.hidden = false;

            period.setAttribute(
              "aria-expanded",
              "false"
            );

            render();
            position();
          }
        );

        monthGrid.append(button);
      }
    }

    function render() {
      period.innerHTML =
        "<strong>" +
        viewDate.getFullYear() +
        "년 " +
        (viewDate.getMonth() + 1) +
        "월</strong>" +
        '<i class="bi bi-chevron-down"></i>';

      const first =
        new Date(
          viewDate.getFullYear(),
          viewDate.getMonth(),
          1
        );

      const start =
        new Date(
          first.getFullYear(),
          first.getMonth(),
          1 - first.getDay()
        );

      const selected =
        parseDate(input.value);

      const now =
        new Date();

      days.replaceChildren();

      for (
        let index = 0;
        index < 42;
        index += 1
      ) {
        const date =
          new Date(
            start.getFullYear(),
            start.getMonth(),
            start.getDate() + index
          );

        const button =
          document.createElement("button");

        button.type = "button";
        button.className =
          "idea-date-day";

        button.textContent =
          String(date.getDate());

        if (
          date.getMonth() !==
          viewDate.getMonth()
        ) {
          button.classList.add(
            "is-outside"
          );
        }

        if (
          sameDay(date, now)
        ) {
          button.classList.add(
            "is-today"
          );
        }

        if (
          sameDay(
            date,
            selected
          )
        ) {
          button.classList.add(
            "is-selected"
          );
        }

        button.addEventListener(
          "click",
          function () {
            input.value =
              dateValue(date);

            input.dispatchEvent(
              new Event("input", {
                bubbles: true
              })
            );

            input.dispatchEvent(
              new Event("change", {
                bubbles: true
              })
            );

            syncTrigger();
            close();
          }
        );

        days.append(button);
      }

      renderMonthPanel();
    }

    function position() {
      if (popover.hidden) return;

      const rect =
        trigger.getBoundingClientRect();

      const margin = 10;

      const width =
        Math.min(
          312,
          window.innerWidth -
            margin * 2
        );

      popover.style.width =
        width + "px";

      const height =
        popover.offsetHeight;

      const spaceBelow =
        window.innerHeight -
        rect.bottom -
        margin;

      const spaceAbove =
        rect.top -
        margin;

      const openUp =
        spaceBelow < height &&
        spaceAbove > spaceBelow;

      let top =
        openUp
          ? rect.top -
            height -
            8
          : rect.bottom + 8;

      top = Math.max(
        margin,
        Math.min(
          top,
          window.innerHeight -
            height -
            margin
        )
      );

      let left =
        rect.left;

      left = Math.max(
        margin,
        Math.min(
          left,
          window.innerWidth -
            width -
            margin
        )
      );

      popover.style.top =
        top + "px";

      popover.style.left =
        left + "px";

      popover.classList.toggle(
        "is-top",
        openUp
      );
    }

    function open() {
      if (trigger.disabled) return;

      syncTrigger();

      if (
        activeDatePicker &&
        activeDatePicker.close !==
          close
      ) {
        activeDatePicker.close();
      }

      const selected =
        parseDate(input.value);

      if (selected) {
        viewDate =
          new Date(
            selected.getFullYear(),
            selected.getMonth(),
            1
          );

        monthSelectYear =
          selected.getFullYear();
      }

      monthPanel.hidden = true;
      weekdays.hidden = false;
      days.hidden = false;
      foot.hidden = false;

      period.setAttribute(
        "aria-expanded",
        "false"
      );

      render();

      popover.hidden = false;

      trigger.setAttribute(
        "aria-expanded",
        "true"
      );

      activeDatePicker = {
        trigger: trigger,
        popover: popover,
        close: close,
        position: position
      };

      requestAnimationFrame(
        position
      );
    }

    function close() {
      popover.hidden = true;

      trigger.setAttribute(
        "aria-expanded",
        "false"
      );

      monthPanel.hidden = true;
      weekdays.hidden = false;
      days.hidden = false;
      foot.hidden = false;

      period.setAttribute(
        "aria-expanded",
        "false"
      );

      if (
        activeDatePicker &&
        activeDatePicker.trigger ===
          trigger
      ) {
        activeDatePicker = null;
      }
    }

    trigger.addEventListener(
      "click",
      function () {
        if (popover.hidden) {
          open();
        } else {
          close();
        }
      }
    );

    prev.addEventListener(
      "click",
      function () {
        viewDate =
          new Date(
            viewDate.getFullYear(),
            viewDate.getMonth() - 1,
            1
          );

        monthSelectYear =
          viewDate.getFullYear();

        render();
        position();
      }
    );

    next.addEventListener(
      "click",
      function () {
        viewDate =
          new Date(
            viewDate.getFullYear(),
            viewDate.getMonth() + 1,
            1
          );

        monthSelectYear =
          viewDate.getFullYear();

        render();
        position();
      }
    );

    function syncCalendarView() {
      var choosingMonth = !monthPanel.hidden;
      weekdays.hidden = choosingMonth;
      days.hidden = choosingMonth;
      foot.hidden = choosingMonth;
      period.setAttribute(
        "aria-expanded",
        String(choosingMonth)
      );
    }

    period.addEventListener(
      "click",
      function () {
        monthPanel.hidden =
          !monthPanel.hidden;

        renderMonthPanel();
        syncCalendarView();
        position();
      }
    );

    prevYear.addEventListener(
      "click",
      function () {
        monthSelectYear -= 1;
        renderMonthPanel();
        position();
      }
    );

    nextYear.addEventListener(
      "click",
      function () {
        monthSelectYear += 1;
        renderMonthPanel();
        position();
      }
    );

    clear.addEventListener(
      "click",
      function () {
        input.value = "";

        input.dispatchEvent(
          new Event("input", {
            bubbles: true
          })
        );

        input.dispatchEvent(
          new Event("change", {
            bubbles: true
          })
        );

        syncTrigger();
        close();
      }
    );

    today.addEventListener(
      "click",
      function () {
        const now =
          new Date();

        input.value =
          dateValue(now);

        input.dispatchEvent(
          new Event("input", {
            bubbles: true
          })
        );

        input.dispatchEvent(
          new Event("change", {
            bubbles: true
          })
        );

        syncTrigger();
        close();
      }
    );

    input.addEventListener(
      "change",
      syncTrigger
    );

    new MutationObserver(
      syncTrigger
    ).observe(input, {
      attributes: true,
      attributeFilter: [
        "disabled"
      ]
    });

    syncTrigger();
  }

  function scan(root) {
    if (
      root instanceof
      HTMLSelectElement
    ) {
      enhanceSelect(root);
    }

    if (
      root instanceof
        HTMLInputElement &&
      root.type === "date"
    ) {
      enhanceDate(root);
    }

    if (root.querySelectorAll) {
      root
        .querySelectorAll(
          "select.form-select"
        )
        .forEach(
          enhanceSelect
        );

      root
        .querySelectorAll(
          '.idea-dev input[type="date"], .idea-dev-modal input[type="date"]'
        )
        .forEach(
          enhanceDate
        );
    }
  }

  document.addEventListener(
    "pointerdown",
    function (event) {
      if (!activeDatePicker) return;

      if (
        activeDatePicker.popover.contains(
          event.target
        ) ||
        activeDatePicker.trigger.contains(
          event.target
        )
      ) {
        return;
      }

      activeDatePicker.close();
    }
  );

  document.addEventListener(
    "keydown",
    function (event) {
      if (
        event.key === "Escape" &&
        activeDatePicker
      ) {
        const trigger =
          activeDatePicker.trigger;

        activeDatePicker.close();
        trigger.focus();
      }
    }
  );

  function repositionDatePicker() {
    if (
      activeDatePicker
    ) {
      activeDatePicker.position();
    }
  }

  window.addEventListener(
    "resize",
    repositionDatePicker
  );

  window.addEventListener(
    "scroll",
    repositionDatePicker,
    true
  );

  function syncIdeaSidebarActive() {
    const ideaRoot =
      document.querySelector(
        ".idea-dev, #prd-home-app, #new-prd-app, #prd-write-app, #brainstorm-root"
      );

    if (!ideaRoot) return;

    const sidebar =
      document.getElementById(
        "sidebar"
      );

    if (!sidebar) return;

    sidebar
      .querySelectorAll(
        ".sidebar-nav-link"
      )
      .forEach(function (link) {
        link.classList.remove(
          "active"
        );

        link.removeAttribute(
          "aria-current"
        );
      });

    const ideaLink =
      sidebar.querySelector(
        '.sidebar-nav-link[title="아이디어 개발"]'
      );

    if (ideaLink) {
      ideaLink.classList.add(
        "active"
      );

      ideaLink.setAttribute(
        "aria-current",
        "page"
      );
    }
  }

  window.StudioControls = {
    enhanceSelect: enhanceSelect,
    enhanceDate: enhanceDate,
    syncSelect: function (select) {
      if (
        select &&
        typeof select._studioSelectSync ===
          "function"
      ) {
        select._studioSelectSync();
      }
    }
  };

  scan(document);
  syncIdeaSidebarActive();

  new MutationObserver(
    function (mutations) {
      mutations.forEach(
        function (mutation) {
          mutation.addedNodes.forEach(
            function (node) {
              if (
                node.nodeType ===
                Node.ELEMENT_NODE
              ) {
                scan(node);
              }
            }
          );
        }
      );
    }
  ).observe(document.body, {
    childList: true,
    subtree: true
  });
}());
