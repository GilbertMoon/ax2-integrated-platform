// LMS 알림 종 - 배지·패널. Core static/js/notifications.js와 동일 구조,
// LMS 전용 엔드포인트(lms_modules.notifications)만 바라본다.
// 종 아이콘 자체(HTML)는 이 스크립트 밖(topbar.html)에서 만든다 - id="axNotificationBell"만 있으면 된다.
(() => {
  const POLL_INTERVAL_MS = 20000;
  const SUMMARY_URL = "/lms/notifications/summary/";
  const MARK_ALL_READ_URL = "/lms/notifications/mark-all-read/";
  const DELETE_ALL_URL = "/lms/notifications/delete-all/";
  const markReadUrl = (id) => `/lms/notifications/${id}/read/`;
  const deleteUrl = (id) => `/lms/notifications/${id}/delete/`;

  function csrfToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  }

  function timeAgo(isoString) {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const minutes = Math.floor(diffMs / 60000);
    if (minutes < 1) return "방금 전";
    if (minutes < 60) return `${minutes}분 전`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // 알림 종류별 아이콘·색상. LMS 쪽엔 아직 카테고리가 없어 전부 기본값(회색 종)으로 뜬다 —
  // 앞으로 LMS 이벤트가 알림을 만들 때 쓸 카테고리가 정해지면 여기 채워 넣는다.
  const CATEGORY_ICONS = {};
  const DEFAULT_CATEGORY_ICON = { icon: "bi-bell-fill", variant: "muted" };
  const categoryIcon = (category) => CATEGORY_ICONS[category] || DEFAULT_CATEGORY_ICON;

  class NotificationCenter {
    constructor(bell) {
      this.bell = bell;
      this.isOpen = false;
      this.hasBaseline = false;
      this.lastSeenId = 0;

      // 배지가 종 위에 겹쳐 뜨려면 종 쪽이 position:relative여야 한다.
      if (!this.bell.style.position) {
        this.bell.style.position = "relative";
      }
      this.badge = document.createElement("span");
      this.badge.className = "ax-notification-badge d-none";
      this.badge.setAttribute("aria-hidden", "true");
      this.bell.appendChild(this.badge);

      this.panel = this._buildPanel();
      document.body.appendChild(this.panel);

      this.bell.addEventListener("click", (event) => {
        event.stopPropagation();
        this.toggle();
      });
      document.addEventListener("click", (event) => {
        if (this.isOpen && !this.panel.contains(event.target) && event.target !== this.bell) {
          this.close();
        }
      });
      window.addEventListener("resize", () => {
        if (this.isOpen) this._position();
      });
    }

    _buildPanel() {
      const panel = document.createElement("div");
      panel.className = "ax-notification-panel";
      panel.id = "axNotificationPanel";
      panel.innerHTML = `
        <div class="ax-notification-panel-header">
          <span class="fw-semibold small">알림</span>
          <div class="d-flex align-items-center gap-2">
            <button type="button" class="btn btn-sm btn-link p-0 small" id="axNotificationMarkAllRead">모두 읽음</button>
            <span class="text-muted small">·</span>
            <button type="button" class="btn btn-sm btn-link p-0 small text-danger" id="axNotificationDeleteAll">전체 삭제</button>
          </div>
        </div>
        <div class="ax-notification-panel-body" id="axNotificationList">
          <p class="ax-notification-empty">알림이 없습니다.</p>
        </div>
      `;
      panel
        .querySelector("#axNotificationMarkAllRead")
        .addEventListener("click", () => this.markAllRead());
      panel
        .querySelector("#axNotificationDeleteAll")
        .addEventListener("click", () => this.deleteAll());
      return panel;
    }

    _position() {
      const rect = this.bell.getBoundingClientRect();
      this.panel.style.top = `${rect.bottom + 8}px`;
      this.panel.style.right = `${Math.max(16, window.innerWidth - rect.right)}px`;
    }

    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    }

    open() {
      this._position();
      this.panel.classList.add("show");
      this.isOpen = true;
      this.refresh();
    }

    close() {
      this.panel.classList.remove("show");
      this.isOpen = false;
    }

    async refresh() {
      const data = await this._fetchSummary();
      if (!data) return;
      this._renderList(data.items);
      this._renderBadge(data.unread_count);
    }

    _renderBadge(count) {
      if (count > 0) {
        this.badge.textContent = count > 99 ? "99+" : String(count);
        this.badge.classList.remove("d-none");
      } else {
        this.badge.classList.add("d-none");
      }
    }

    _renderList(items) {
      const list = this.panel.querySelector("#axNotificationList");
      if (!items.length) {
        list.innerHTML = '<p class="ax-notification-empty">알림이 없습니다.</p>';
        return;
      }
      list.innerHTML = "";
      items.forEach((item) => {
        const { icon, variant } = categoryIcon(item.category);
        // 바깥은 button이 아니라 div다 - 안에 "본문(클릭 시 이동)"과 "삭제" 두 개의
        // 별도 버튼이 들어가서, button 안에 button을 못 넣는 제약을 피한다.
        const row = document.createElement("div");
        row.className = `ax-notification-item${item.is_read ? "" : " unread"}`;
        row.innerHTML = `
          <button type="button" class="ax-notification-item-body-btn">
            <div class="ax-notification-item-icon ax-notification-icon--${variant}"><i class="bi ${icon}"></i></div>
            <div class="ax-notification-item-body">
              <div class="ax-notification-item-title">${escapeHtml(item.title)}</div>
              ${item.message ? `<div class="ax-notification-item-message">${escapeHtml(item.message)}</div>` : ""}
              <div class="ax-notification-item-time">${timeAgo(item.created_at)}</div>
            </div>
          </button>
          <button type="button" class="ax-notification-item-delete" aria-label="알림 삭제">
            <i class="bi bi-x-lg"></i>
          </button>
        `;
        row.querySelector(".ax-notification-item-body-btn").addEventListener("click", () => this._openItem(item));
        row.querySelector(".ax-notification-item-delete").addEventListener("click", (event) => {
          event.stopPropagation();
          this.deleteItem(item.id);
        });
        list.appendChild(row);
      });
    }

    async _openItem(item) {
      if (!item.is_read) {
        await fetch(markReadUrl(item.id), {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken() },
        });
      }
      if (item.link) {
        window.location.href = item.link;
        return;
      }
      this.refresh();
    }

    async markAllRead() {
      await fetch(MARK_ALL_READ_URL, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
      });
      this.refresh();
    }

    async deleteItem(id) {
      await fetch(deleteUrl(id), {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
      });
      this.refresh();
    }

    async deleteAll() {
      await fetch(DELETE_ALL_URL, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
      });
      this.refresh();
    }

    async _fetchSummary() {
      try {
        const response = await fetch(SUMMARY_URL, { headers: { Accept: "application/json" } });
        if (!response.ok) return null;
        return await response.json();
      } catch (error) {
        return null;
      }
    }

    // 폴링 - 배지는 항상 갱신하고, 새로 생긴 알림이 있으면 토스트를 한 번 띄운다.
    async poll() {
      const data = await this._fetchSummary();
      if (!data) return;
      this._renderBadge(data.unread_count);
      if (this.isOpen) this._renderList(data.items);

      const newestId = data.items.length ? data.items[0].id : 0;
      if (!this.hasBaseline) {
        // 첫 로드 때는 과거 미확인 알림까지 전부 토스트로 띄우면 시끄러우니 기준점만 잡는다.
        this.lastSeenId = newestId;
        this.hasBaseline = true;
        return;
      }
      const freshItems = data.items.filter((item) => item.id > this.lastSeenId);
      if (freshItems.length === 1 && window.showToast) {
        window.showToast(escapeHtml(freshItems[0].title));
      } else if (freshItems.length > 1 && window.showToast) {
        window.showToast(`새 알림 ${freshItems.length}개가 있습니다.`);
      }
      if (newestId) this.lastSeenId = newestId;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    const bell = document.getElementById("axNotificationBell");
    if (!bell) return;
    const center = new NotificationCenter(bell);
    center.poll();
    setInterval(() => center.poll(), POLL_INTERVAL_MS);
    window.AXNotifications = {
      refresh: () => center.refresh(),
      toggle: () => center.toggle(),
    };
  });
})();
