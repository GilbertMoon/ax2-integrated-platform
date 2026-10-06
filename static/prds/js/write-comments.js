(function () {
  "use strict";

  window.PrdWriteComments = {
    create: function (options) {
      var api = options.api;
      var element = options.element;
      var participantAvatar = options.participantAvatar;
      var commentsApi = options.commentsApi;
      var getDetail = options.getDetail;
      var emptyIllustration = options.emptyIllustration || "";
      var commentList = document.getElementById("comment-list");
      var commentForm = document.getElementById("comment-form");
      var commentInput = document.getElementById("comment-input");
      var commentTarget = document.getElementById("comment-target");
      var commentSubmit = document.getElementById("comment-submit");
      var commentPanelAlert = document.getElementById("comment-panel-alert");
      var commentPagination = document.getElementById("comment-pagination");
      var commentPage = 1;
      var commentPageSize = 10;
      var demoMode = new URLSearchParams(window.location.search).get("ui_demo") === "1";
      var latestItems = [];

      function demoCommentData() {
        var detail = getDetail();
        var questions = detail ? detail.sections.reduce(function (acc, section) {
          return acc.concat(section.questions.map(function (question) { return {section: section, question: question}; }));
        }, []) : [];
        var first = questions.find(function (row) { return row.section.position === 2; }) || questions[0];
        var second = questions.find(function (row) { return row.section.position === 6; }) || questions[1] || first;
        var now = new Date();
        function iso(minusMinutes) { return new Date(now.getTime() - minusMinutes * 60000).toISOString(); }
        var items = [];
        if (first) items.push({
          id: "demo-comment-1", version: 1, section_question_id: first.question.id,
          content: "목표 수치가 어떤 기준에서 나온 것인지 한 줄만 더 적어두면 공유할 때 이해가 더 빠를 것 같아요.",
          comment_type: "general", created_at: iso(38), can_modify: false,
          author: {user_id: "demo-junho", display_name: "준호", role_at_created: "editor"}
        });
        if (second) items.push({
          id: "demo-comment-2", version: 1, section_question_id: second.question.id,
          content: "핵심 흐름뿐 아니라 중간 이탈이나 예외 상황도 같이 적어두면 구현 범위 확인에 도움이 될 것 같아요.",
          comment_type: "review", created_at: iso(12), can_modify: false,
          author: {user_id: "demo-seoyeon", display_name: "서연", role_at_created: "editor"}
        });
        return {items: items, pagination: {page: 1, page_size: 10, total_items: items.length, total_pages: 1}};
      }


      function commentEmpty(title, copy) {
        var state = element("div", "comment-empty");
        if (emptyIllustration) {
          var image = document.createElement("img");
          image.src = emptyIllustration;
          image.alt = "";
          state.append(image);
        }
        state.append(
          element("strong", "", title),
          element("span", "", copy)
        );
        return state;
      }

      function showCommentAlert(message, kind) {
        commentPanelAlert.className = "alert alert-" + (kind || "danger") + " comment-panel-alert";
        commentPanelAlert.textContent = message;
      }

      function clearCommentAlert() {
        commentPanelAlert.className = "alert d-none comment-panel-alert";
        commentPanelAlert.textContent = "";
      }

      function commentDate(value) {
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return "";
        return new Intl.DateTimeFormat("ko-KR", {month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit"}).format(parsed);
      }

      function questionContext(questionId) {
        if (!getDetail() || !questionId) return {section: "PRD 전체", question: "전체 문서에 남긴 코멘트"};
        for (const section of getDetail().sections) {
          const question = section.questions.find(function (item) { return item.id === questionId; });
          if (question) return {section: section.title, question: question.prompt};
        }
        return {section: "PRD", question: "질문 코멘트"};
      }

      function renderCommentPagination(pagination) {
        commentPagination.replaceChildren();
        commentPagination.classList.toggle("d-none", pagination.total_pages <= 1);
        if (pagination.total_pages <= 1) return;
        const previous = element("button", "btn btn-sm btn-outline-secondary", "이전");
        const next = element("button", "btn btn-sm btn-outline-secondary", "다음");
        previous.type = next.type = "button";
        previous.disabled = pagination.page <= 1;
        next.disabled = pagination.page >= pagination.total_pages;
        previous.addEventListener("click", function () { loadComments(pagination.page - 1); });
        next.addEventListener("click", function () { loadComments(pagination.page + 1); });
        commentPagination.append(previous, element("span", "", pagination.page + " / " + pagination.total_pages), next);
      }

      function editComment(card, comment) {
        const content = card.querySelector(".comment-content");
        const actions = card.querySelector(".comment-actions");
        const editor = element("textarea", "form-control comment-edit-input");
        editor.maxLength = 4000;
        editor.value = comment.content;
        const editActions = element("div", "comment-edit-actions");
        const cancelEdit = element("button", "btn btn-sm btn-light", "취소");
        const saveEdit = element("button", "btn btn-sm btn-primary", "저장");
        cancelEdit.type = saveEdit.type = "button";
        cancelEdit.addEventListener("click", function () { editor.remove(); editActions.remove(); content.classList.remove("d-none"); actions.classList.remove("d-none"); });
        saveEdit.addEventListener("click", async function () {
          if (!editor.value.trim()) return showCommentAlert("코멘트 내용을 입력해 주세요.", "warning");
          saveEdit.disabled = true;
          try {
            const localContent = editor.value.trim();
            await api(commentsApi + comment.id + "/", {
              method: "PATCH",
              body: JSON.stringify({content: localContent, version: comment.version})
            });
            showCommentAlert("코멘트를 수정했습니다.", "success");
            await loadComments(commentPage);
          } catch (error) {
            if (error.code === "version_conflict") {
              const latestContent = error.details?.latest?.content || "";
              if (error.details?.latest?.version) comment.version = error.details.latest.version;
              const preview = latestContent.length > 120 ? latestContent.slice(0, 120) + "…" : latestContent;
              showCommentAlert("다른 사용자가 먼저 수정했습니다. 최신 내용: “" + preview + "” 작성 중인 내용은 입력창에 유지했습니다.", "warning");
            } else showCommentAlert(error.message);
            saveEdit.disabled = false;
          }
        });
        editActions.append(cancelEdit, saveEdit);
        content.classList.add("d-none"); actions.classList.add("d-none");
        content.after(editor, editActions);
        editor.focus();
      }

      async function deleteComment(comment) {
        const confirmed = await window.IdeaUI.confirm({
          title: "코멘트를 삭제할까요?",
          message: "삭제한 코멘트는 현재 화면에서 복원할 수 없습니다.",
          confirmText: "삭제",
          cancelText: "취소",
          tone: "danger"
        });
        if (!confirmed) return;
        try {
          await api(commentsApi + comment.id + "/", {
            method: "DELETE",
            body: JSON.stringify({version: comment.version})
          });
          showCommentAlert("코멘트를 삭제했습니다.", "success");
          await loadComments(commentPage);
        } catch (error) {
          if (error.code === "version_conflict") {
            await loadComments(commentPage);
            showCommentAlert("다른 사용자가 먼저 코멘트를 변경했습니다. 최신 목록을 불러왔습니다.", "warning");
          } else showCommentAlert(error.message);
        }
      }

      function renderComments(data) {
        latestItems = Array.isArray(data.items) ? data.items.slice() : [];
        const count = document.getElementById("comment-count");
        count.textContent = data.pagination.total_items;
        count.classList.toggle("d-none", data.pagination.total_items === 0);
        commentList.replaceChildren();
        if (!data.items.length) {
          commentList.append(commentEmpty("아직 등록된 코멘트가 없습니다.", "PRD 전체나 질문을 선택해 팀과 첫 의견을 나눠보세요."));
          renderCommentPagination(data.pagination);
          return;
        }
        const typeLabels = {general: "일반", guidance: "지도", review: "리뷰", post_completion_review: "완료 후 리뷰"};
        const roleLabels = {owner: "소유자", editor: "편집자", tutor: "튜터", viewer: "뷰어"};
        data.items.forEach(function (comment) {
          const card = element("article", "comment-card");
          const head = element("div", "comment-card-head");
          const author = element("div", "comment-author");
          author.append(
            element("strong", "", comment.author.display_name),
            element("small", "", commentDate(comment.created_at))
          );
          const kind = element("span", "comment-kind comment-kind--" + (comment.comment_type || "general"), typeLabels[comment.comment_type] || comment.comment_type);
          const roleKind = element("span", "comment-role comment-role--" + (comment.author.role_at_created || "viewer"), roleLabels[comment.author.role_at_created] || comment.author.role_at_created);
          const metaTags = element("div", "comment-meta-tags");
          metaTags.append(roleKind, kind);
          head.append(
            participantAvatar({user_id: comment.author.user_id, display_name: comment.author.display_name, role: comment.author.role_at_created}, "participant-person-avatar"),
            author,
            metaTags
          );
          card.append(head);
          const context = questionContext(comment.section_question_id);
          const contextBlock = element("div", "comment-context");
          const sectionRow = element("div", "comment-context-section");
          sectionRow.append(element("span", "comment-section-tag", "섹션"), element("strong", "", context.section));
          contextBlock.append(sectionRow, element("p", "comment-question", context.question));
          card.append(contextBlock);
          card.append(
            element(
              "p",
              "comment-content",
              comment.content
            )
          );
          if (comment.can_modify) {
            const actions = element("div", "comment-actions");
            const edit = element("button", "btn btn-sm btn-light", "수정");
            const remove = element("button", "btn btn-sm btn-link text-danger", "삭제");
            edit.type = remove.type = "button";
            edit.addEventListener("click", function () { editComment(card, comment); });
            remove.addEventListener("click", function () { deleteComment(comment); });
            actions.append(edit, remove);
            card.append(actions);
          }
          commentList.append(card);
        });
        renderCommentPagination(data.pagination);
        document.dispatchEvent(new CustomEvent("prd:comments-loaded", {detail: {total: latestItems.length}}));
      }

      async function loadComments(page) {
        if (demoMode) {
          commentPage = 1;
          renderComments(demoCommentData());
          return;
        }
        if (!commentsApi) return;
        commentPage = Math.max(1, Number(page || commentPage || 1));
        try {
          let data = await api(commentsApi + "?page=" + commentPage + "&page_size=" + commentPageSize);
          if (!data.items.length && commentPage > 1) {
            commentPage -= 1;
            data = await api(commentsApi + "?page=" + commentPage + "&page_size=" + commentPageSize);
          }
          renderComments(data);
        } catch (error) {
          commentList.replaceChildren(commentEmpty("코멘트를 불러오지 못했습니다.", "잠시 후 다시 열어 최신 코멘트를 확인해 주세요."));
          showCommentAlert(error.message);
        }
      }

      commentForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        clearCommentAlert();
        if (demoMode) {
          showCommentAlert("데모 모드에서는 예시 코멘트를 확인할 수 있고 실제 등록은 하지 않습니다.", "info");
          return;
        }
        const content = commentInput.value.trim();
        if (!content) {
          showCommentAlert("코멘트 내용을 입력해 주세요.", "warning");
          return;
        }
        commentSubmit.disabled = true;
        try {
          const selectedQuestionId = commentTarget.value ? Number(commentTarget.value) : null;
          const body = {content: content, section_question_id: selectedQuestionId};
          if (getDetail().prd.status === "completed" && getDetail().permissions.can_review_comment) body.comment_type = "post_completion_review";
          await api(commentsApi, {method: "POST", body: JSON.stringify(body)});
          commentInput.value = "";
          commentPage = 1;
          showCommentAlert("코멘트를 등록했습니다.", "success");
          await loadComments(1);
        } catch (error) {
          showCommentAlert(error.message);
        } finally {
          commentSubmit.disabled = false;
        }
      });

      document.getElementById("write-comments-panel").addEventListener("show.bs.offcanvas", function () {
        loadComments(commentPage);
      });


      return {
        load: loadComments,
        getItemsForQuestion: function (questionId) {
          if (questionId === null || questionId === undefined || questionId === "") return latestItems.slice();
          return latestItems.filter(function (item) { return String(item.section_question_id) === String(questionId); });
        },
        getCountForQuestion: function (questionId) {
          return latestItems.filter(function (item) { return String(item.section_question_id) === String(questionId); }).length;
        },
        getTotalCount: function () { return latestItems.length; }
      };
    }
  };
}());
