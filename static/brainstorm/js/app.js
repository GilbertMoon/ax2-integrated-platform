(function () {
  "use strict";

  var root = document.getElementById("brainstorm-root");
  if (!root) return;
  if (!window.React || !window.ReactDOM) {
    root.innerHTML = '<div class="alert alert-danger m-4">React CDN을 불러오지 못했습니다. 네트워크와 CSP 설정을 확인해 주세요.</div>';
    return;
  }

  var h = window.React.createElement;
  var apiBase = root.dataset.apiBase;
  var prdTitle = root.dataset.prdTitle || "PRD";
  var brandMarkUrl = root.dataset.brandMarkUrl || "";
  var firstPageIllustration = root.dataset.firstPageIllustration || "";
  var ideaDocumentIllustration = root.dataset.ideaDocumentIllustration || "";
  var interval = Math.min(5000, Math.max(2000, Number(root.dataset.pollingIntervalMs || 2000)));
  function nextPollDelay() {
    // Slack 링크처럼 여러 사용자가 동시에 들어와도 폴링 요청이 한 시각에 몰리지 않게 한다.
    return Math.min(5000, Math.max(2000, interval + Math.floor(Math.random() * 1001)));
  }
  var csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  var activeCanvasId = null;
  var DEFAULT_CANVAS_ZOOM = .62;
  var layout = window.BrainstormLayout;
  var apiClientFactory = window.BrainstormApiClient;
  if (!layout || !apiClientFactory) {
    root.innerHTML = '<div class="alert alert-danger m-4">브레인스토밍 모듈을 불러오지 못했습니다. 정적 파일 설정을 확인해 주세요.</div>';
    return;
  }
  var NODE_W = layout.NODE_W;
  var NODE_H = layout.NODE_H;
  var CANVAS_W = layout.CANVAS_W;
  var CANVAS_H = layout.CANVAS_H;
  var BOARD = layout.BOARD;
  var resizeBoard = layout.resizeBoard;
  var trayBox = layout.trayBox;
  var setRegionWeights = layout.setRegionWeights;
  var regionPath = layout.regionPath;
  var regionBounds = layout.regionBounds;
  var regionCenter = layout.regionCenter;
  var fitBoardView = layout.fitBoardView;
  var canvasContentSize = layout.canvasContentSize;
  var hitContext = layout.hitContext;
  var laneColors = layout.laneColors;
  var apiClient = apiClientFactory.create({
    csrf: csrf,
    getActiveCanvasId: function () { return activeCanvasId; }
  });
  var key = apiClient.key;
  var request = apiClient.request;

  function BrainstormApp() {
    var statePair = window.React.useState(null), state = statePair[0], setState = statePair[1];
    var syncPair = window.React.useState("loading"), sync = syncPair[0], setSync = syncPair[1];
    var filterPair = window.React.useState("all"), filter = filterPair[0], setFilter = filterPair[1];
    var toolPair = window.React.useState("select"), tool = toolPair[0], setTool = toolPair[1];
    var boardPair = window.React.useState("canvas"), boardView = boardPair[0], setBoardView = boardPair[1];
    var sourcePair = window.React.useState(null), source = sourcePair[0], setSource = sourcePair[1];
    var sourceDirectionPair = window.React.useState(null), sourceDirection = sourceDirectionPair[0], setSourceDirection = sourceDirectionPair[1];
    var focusPair = window.React.useState(null), focused = focusPair[0], setFocused = focusPair[1];
    var selectedPair = window.React.useState([]), selected = selectedPair[0], setSelected = selectedPair[1];
    // 연결선이 많아지면 서로 어지럽게 교차한다. 메모를 가리키거나 고른 동안만
    // 그 메모로 이어진 선을 도드라지게 하고 나머지는 옅게 깔아 둔다.
    var hoverPair = window.React.useState(null), hoveredNode = hoverPair[0], setHoveredNode = hoverPair[1];
    var viewPair = window.React.useState({x: 0, y: 0, zoom: 1}), view = viewPair[0], setView = viewPair[1];
    var noticePair = window.React.useState(null), notice = noticePair[0], setNotice = noticePair[1];
    var busyPair = window.React.useState(false), busy = busyPair[0], setBusy = busyPair[1];
    var jobPair = window.React.useState(null), jobId = jobPair[0], setJobId = jobPair[1];
    var aiPair = window.React.useState(null), aiPanel = aiPair[0], setAiPanel = aiPair[1];
    // PRD 반영 미리보기에서 펼쳐 둔 질문. 답변이 길어 전부 펼쳐 두면 읽기 어렵다.
    var openAnswersPair = window.React.useState({}), openAnswers = openAnswersPair[0], setOpenAnswers = openAnswersPair[1];
    var editorPair = window.React.useState(null), editor = editorPair[0], setEditor = editorPair[1];
    var assigneeMenuPair = window.React.useState(null), assigneeMenu = assigneeMenuPair[0], setAssigneeMenu = assigneeMenuPair[1];
    var heldExpandedPair = window.React.useState(false), heldExpanded = heldExpandedPair[0], setHeldExpanded = heldExpandedPair[1];
    var versionsOpenPair = window.React.useState(true), versionsOpen = versionsOpenPair[0], setVersionsOpen = versionsOpenPair[1];
    var questionsOpenPair = window.React.useState(false), questionsOpen = questionsOpenPair[0], setQuestionsOpen = questionsOpenPair[1];
    var questionSearchPair = window.React.useState(""), questionSearch = questionSearchPair[0], setQuestionSearch = questionSearchPair[1];
    var openQuestionSectionsPair = window.React.useState({}), openQuestionSections = openQuestionSectionsPair[0], setOpenQuestionSections = openQuestionSectionsPair[1];
    var timerRef = window.React.useRef(null);
    var cursorRef = window.React.useRef(null);
    var initialViewport = window.React.useRef(false);
    var viewportSaveRef = window.React.useRef(null);
    // 지금 끌고 있는 메모. 이 메모만은 자리 정리에서 빼 손을 그대로 따라오게 한다.
    var draggingRef = window.React.useRef(null);
    // 자유 캔버스 밖(보류 구역 포함)으로 드래그할 때는 도화지 전체가 올라오지 않도록
    // 메모 하나만 body 위 fixed preview로 보여 준다.
    var dragPreviewPair = window.React.useState(null),
      dragPreview = dragPreviewPair[0],
      setDragPreview = dragPreviewPair[1];

    // 섹션 보드의 HTML5 drag는 자유 캔버스의 custom dragPreview를 사용하지 않는다.
    // 두 화면 모두 같은 보류 drop-target 피드백을 쓰도록 별도 상태를 둔다.
    var boardDragHeldPair = window.React.useState(false),
      boardDragHeld = boardDragHeldPair[0],
      setBoardDragHeld = boardDragHeldPair[1];

    // 섹션 보드에서 메모를 다른 칸으로 드래그할 때
    // 현재 drop 대상 칸 전체를 시각적으로 강조한다.
    var boardDropTargetPair = window.React.useState(null),
      boardDropTarget = boardDropTargetPair[0],
      setBoardDropTarget = boardDropTargetPair[1];

    var unclassifiedPair = window.React.useState(false),
      unclassifiedExpanded = unclassifiedPair[0],
      setUnclassifiedExpanded = unclassifiedPair[1];

    var connectPointerPair = window.React.useState(null),
      connectPointer = connectPointerPair[0],
      setConnectPointer = connectPointerPair[1];
    // 이번에 그린 연결선 곡선 위의 점들. 조작 막대가 선을 덮지 않게 할 때 쓴다.
    // 선을 먼저 그리므로 메모를 그릴 때는 이미 채워져 있다.
    var curveSamplesRef = window.React.useRef([]);
    // 첫 그림에는 이름표 글자가 아직 없어 자리를 어림잡을 수밖에 없다.
    // 글자가 생긴 다음 한 번 더 그려서 잰 크기로 자리를 확정한다.
    var measuredPair = window.React.useState(false), measured = measuredPair[0], setMeasured = measuredPair[1];
    window.React.useEffect(function () {
      if (!measured && state) setMeasured(true);
    });
    window.React.useEffect(function () {
      function clearFocusedNode(event) {
        var target = event.target;
        if (target && target.closest && target.closest(".brain-note, .brain-note-actions, .brain-board-card, .brain-board-card-toolbar, .brain-floating-toolbar, .brain-assignee-menu")) return;
        setFocused(null); setSelected([]);
      }
      document.addEventListener("mousedown", clearFocusedNode);
      return function () { document.removeEventListener("mousedown", clearFocusedNode); };
    }, []);
    var fullSyncGenerationRef = window.React.useRef(0);

    function fullSync(canvasId) {
      if (canvasId !== undefined && canvasId !== null) {
        activeCanvasId = canvasId;
        initialViewport.current = false;
      }
      var generation = ++fullSyncGenerationRef.current;
      setSync("loading");
      return request(apiBase + "canvas/", {headers: {"Idempotency-Key": key()}})
        .then(function (data) {
          if (generation !== fullSyncGenerationRef.current) return;
          activeCanvasId = data.canvas.id;
          cursorRef.current = data.cursor; setState(data); setSync("connected");
          if (!initialViewport.current) {
            var opened = (data.nodes || []).filter(function (n) { return n.node_type === "note" && n.status !== "held"; });
            var openedPerSection = (data.sections || []).map(function (section) {
              return opened.filter(function (n) { return n.section_id === section.id; }).length;
            });
            resizeBoard(opened.length, openedPerSection.length ? Math.max.apply(null, openedPerSection) : 0);
            // 페이지를 열 때는 언제나 도화지 전체가 한눈에 들어오게 맞춘다.
            // 지난번에 확대해 둔 배율을 그대로 복원하면 들어오자마자 축소해야 한다.
            setView(fitBoardView(DEFAULT_CANVAS_ZOOM, DEFAULT_CANVAS_ZOOM));
            initialViewport.current = true;
            // 첫 계산은 무대가 아직 그려지기 전일 수 있어 한 번 더 맞춘다.
            window.requestAnimationFrame(function () {
              window.requestAnimationFrame(function () {
                setView(fitBoardView(DEFAULT_CANVAS_ZOOM, DEFAULT_CANVAS_ZOOM));
              });
            });
          }
        }).catch(function (error) {
          if (generation !== fullSyncGenerationRef.current) return;
          setSync("disconnected"); setNotice({kind: "warning", text: error.message});
        });
    }

    function applyConfirmedNode(snapshot) {
      if (!snapshot || !snapshot.id) return false;
      setState(function (previous) {
        if (!previous) return previous;
        var nodes = previous.nodes.filter(function (item) { return item.id !== snapshot.id; });
        var heldNodes = previous.held_nodes.filter(function (item) { return item.id !== snapshot.id; });
        var connections = previous.connections;
        if (snapshot.is_deleted || snapshot.status === "held") {
          connections = connections.filter(function (line) {
            return line.node_a_id !== snapshot.id && line.node_b_id !== snapshot.id;
          });
        }
        if (!snapshot.is_deleted) {
          if (snapshot.status === "held") heldNodes.push(snapshot);
          else nodes.push(snapshot);
        }
        var regularNotes = nodes.filter(function (item) { return item.node_type === "note"; });
        return Object.assign({}, previous, {
          nodes: nodes,
          held_nodes: heldNodes,
          connections: connections,
          counts: {
            total: regularNotes.length,
            unclassified: regularNotes.filter(function (item) { return !item.section_id; }).length,
            accepted: regularNotes.filter(function (item) { return !!item.section_id; }).length,
            held: heldNodes.length
          }
        });
      });
      return true;
    }

    function applyEventBatch(data) {
      if (!data.events || !data.events.length) return true;
      // 여러 노드가 한꺼번에 움직이는 작업은 개별 snapshot이 없으므로 전체 상태가 필요하다.
      if (data.events.some(function (event) { return event.target_type === "canvas"; })) return false;
      setState(function (previous) {
        if (!previous) return previous;
        var nodes = previous.nodes.slice();
        var heldNodes = previous.held_nodes.slice();
        var connections = previous.connections.slice();
        data.events.forEach(function (event) {
          if (event.target_type === "node" && event.snapshot) {
            var snapshot = event.snapshot;
            nodes = nodes.filter(function (item) { return item.id !== snapshot.id; });
            heldNodes = heldNodes.filter(function (item) { return item.id !== snapshot.id; });
            connections = connections.filter(function (line) {
              return line.node_a_id !== snapshot.id && line.node_b_id !== snapshot.id;
            });
            if (!snapshot.is_deleted) {
              if (snapshot.status === "held") heldNodes.push(snapshot);
              else nodes.push(snapshot);
              (event.related_connections || []).forEach(function (line) {
                connections = connections.filter(function (item) { return item.id !== line.id; });
                connections.push(line);
              });
            }
          } else if (event.target_type === "connection") {
            connections = connections.filter(function (item) { return item.id !== event.target_id; });
            if (event.action !== "connection_deleted" && event.snapshot) {
              connections.push(event.snapshot);
            }
          }
        });
        return Object.assign({}, previous, {
          nodes: nodes,
          held_nodes: heldNodes,
          connections: connections,
          counts: data.counts || previous.counts
        });
      });
      return true;
    }

    function poll() {
      if (cursorRef.current === null || !navigator.onLine) return fullSync();
      return request(apiBase + "events/?cursor=" + encodeURIComponent(cursorRef.current)).then(function (data) {
        cursorRef.current = data.cursor;
        if (data.reset_required || !applyEventBatch(data)) return fullSync();
        setSync("connected");
        if (data.has_more) return poll();
      }).catch(function (error) {
        if (error.code === "validation_error") {
          activeCanvasId = null; cursorRef.current = null;
          return fullSync();
        }
        setSync("disconnected");
      });
    }

    window.React.useEffect(function () {
      var stopped = false;
      function cycle() { if (stopped) return; poll().finally(function () { timerRef.current = window.setTimeout(cycle, nextPollDelay()); }); }
      function reconnect() { cursorRef.current = null; fullSync(); }
      fullSync().finally(function () { timerRef.current = window.setTimeout(cycle, nextPollDelay()); });
      window.addEventListener("online", reconnect);
      return function () { stopped = true; clearTimeout(timerRef.current); window.removeEventListener("online", reconnect); };
    }, []);

    function refresh(promise, success) {
      setBusy(true); setNotice(null);
      return promise.then(function (data) {
        if (success) success(data);
        // POST/PATCH/DELETE가 확정한 단일 메모는 곧바로 반영한다. 임시 메모가 아니며
        // 다음 polling 때 같은 event가 와도 ID 기준 upsert라 중복되지 않는다.
        if (data && data.node_type && applyConfirmedNode(data)) {
          setSync("connected");
          return data;
        }
        cursorRef.current = null;
        return fullSync();
      })
        .catch(function (error) { setNotice({kind: error.code === "version_conflict" ? "warning" : "danger", text: error.message}); cursorRef.current = null; return fullSync(); })
        .finally(function () { setBusy(false); });
    }

    function historyAction(path, completedMessage) {
      if (busy || !state?.permissions?.can_edit) return;
      setBusy(true); setNotice(null);
      request(apiBase + path, {method: "POST", body: "{}"})
        .then(function () { cursorRef.current = null; return fullSync(); })
        .then(function () { setNotice({kind: "info", text: completedMessage}); })
        .catch(function (error) {
          setNotice({kind: error.code === "version_conflict" ? "warning" : "danger", text: error.message});
          cursorRef.current = null;
          return fullSync();
        })
        .finally(function () { setBusy(false); });
    }

    async function closeEditorWithConfirmation() {
      if (!editor) return true;
      var original = editor.node ? editor.node.content : "";
      if ((editor.content || "") !== original) {
        var confirmed = await window.IdeaUI.confirm({
          title: "작성 중인 내용을 닫을까요?",
          message: "저장하지 않은 변경 내용은 사라집니다.",
          confirmText: "닫기",
          cancelText: "계속 작성",
          tone: "danger"
        });
        if (!confirmed) return false;
      }
      setEditor(null);
      return true;
    }

    window.React.useEffect(function () {
      function keyboard(event) {
        var target = event.target;
        var isTextInput = target && (target.matches?.("input, textarea") || target.isContentEditable);
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
          event.preventDefault();
          if (editor && (editor.content || "").trim()) saveEditor();
          return;
        }
        if ((event.ctrlKey || event.metaKey) && !isTextInput && event.key.toLowerCase() === "z") {
          event.preventDefault(); historyAction("undo/", "마지막 작업을 취소했습니다."); return;
        }
        if ((event.ctrlKey || event.metaKey) && !isTextInput && event.key.toLowerCase() === "y") {
          event.preventDefault(); historyAction("redo/", "취소한 작업을 다시 실행했습니다."); return;
        }
        if (!isTextInput && (event.key === "Delete" || event.key === "Backspace") && focused && !editor) {
          var focusedNode = state?.nodes?.find(function (item) { return item.id === focused; });
          if (focusedNode && state?.permissions?.can_edit && !state?.permissions?.is_completed) {
            event.preventDefault();
            deleteNode(focusedNode);
          }
          return;
        }
        if (event.key !== "Escape") return;
        if (assigneeMenu) { setAssigneeMenu(null); return; }
        if (editor) { closeEditorWithConfirmation(); return; }
        if (questionsOpen) { setQuestionsOpen(false); return; }
        if (tool === "connect" || source) { setTool("select"); setSource(null); setSourceDirection(null); setConnectPointer(null); return; }
        setSelected([]); setFocused(null);
      }
      document.addEventListener("keydown", keyboard);
      return function () { document.removeEventListener("keydown", keyboard); };
    });

    function createNote(section) {
      setEditor({
        node: null,
        content: "",
        color: "yellow",
        targetSectionId: section ? section.id : null
      });
    }

    function editNode(node) {
      setEditor({node: node, content: node.content, color: node.color || "yellow"});
    }

    function startConnection(node, direction) {
      setFocused(node.id);
      setSelected([]);
      setTool("connect");
      setSource(node);
      setSourceDirection(direction || null);
      setConnectPointer(null);
    }

    function createAdjacentNote(node, direction) {
      var origin = positions[node.id] || displayPosition(node);
      var gap = 44;
      var x = origin.x, y = origin.y;
      if (direction === "left") x -= NODE_W + gap;
      if (direction === "right") x += NODE_W + gap;
      if (direction === "top") y -= NODE_H + gap;
      if (direction === "bottom") y += NODE_H + gap;
      x = Math.max(20, Math.min(CANVAS_W - NODE_W - 20, x));
      y = Math.max(20, Math.min(CANVAS_H - NODE_H - 20, y));
      var sectionId = node.section_id || sectionAt(x, y);
      var spot = {x: x, y: y};
      if (sectionId) {
        var targetIndex = laneIndex(sectionId);
        spot = settleInRegion(targetIndex, x, y, takenSpots(sectionId, node.id)) || spot;
      } else {
        spot = nearestFreeNotePosition(x, y);
      }
      setEditor({
        node: null,
        content: "",
        color: node.color || "yellow",
        targetSectionId: sectionId || null,
        targetPosition: {x: Math.round(spot.x), y: Math.round(spot.y)},
        connectFromNodeId: node.id
      });
    }

    function nearestFreeNotePosition(wantX, wantY) {
      var gap = 20;
      var stepX = NODE_W + gap, stepY = NODE_H + gap;
      var occupied = state.nodes.filter(function (node) {
        return node.status !== "held";
      }).map(function (node) {
        return positions[node.id] || displayPosition(node);
      });
      function fits(x, y) {
        if (x < 20 || y < 20 || x > CANVAS_W - NODE_W || y > CANVAS_H - NODE_H) {
          return false;
        }
        // 미분류 공간에서 시작한 메모가 빈자리를 찾다가 섹션으로 들어가 분류되지 않게 한다.
        if (sectionAt(x, y) !== null) return false;
        return !occupied.some(function (spot) {
          return overlaps(
            x, y, NODE_W, NODE_H,
            spot.x - gap, spot.y - gap, NODE_W + gap * 2, NODE_H + gap * 2
          );
        });
      }
      var originX = Math.round(wantX), originY = Math.round(wantY);
      if (fits(originX, originY)) return {x: originX, y: originY};
      // 화면 중앙에서 오른쪽·아래·왼쪽·위 순으로 원을 넓힌다. 기존 메모는 움직이지 않는다.
      var directions = [[1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]];
      for (var ring = 1; ring <= 24; ring += 1) {
        for (var index = 0; index < directions.length; index += 1) {
          var x = Math.round(originX + directions[index][0] * stepX * ring);
          var y = Math.round(originY + directions[index][1] * stepY * ring);
          if (fits(x, y)) return {x: x, y: y};
        }
      }
      return {x: originX, y: originY};
    }

    function saveEditor() {
      var content = (editor?.content || "").trim();
      if (!content) return;
      if (editor.node) {
        refresh(request(apiBase + "nodes/" + editor.node.id + "/content/", {method: "PATCH", body: JSON.stringify({content: content, version: editor.node.version})}));
      } else {
        // 배율로 나눈 좌표는 소수점이 길게 남는다. 서버가 자릿수를 12개로 제한하므로 반올림한다.
        var x = editor.targetPosition
          ? Number(editor.targetPosition.x)
          : Math.round(Math.max(20, Math.min(CANVAS_W - NODE_W, (window.innerWidth / 2 - view.x) / view.zoom - NODE_W / 2)));
        var y = editor.targetPosition
          ? Number(editor.targetPosition.y)
          : Math.round(Math.max(20, Math.min(CANVAS_H - NODE_H, ((window.innerHeight - 190) / 2 - view.y) / view.zoom - NODE_H / 2)));
        // targetSectionId가 명시되어 있으면 null도 의미가 있다.
        // 일반 "메모 추가"는 null = 미분류로 만들고, 섹션 안의 + 버튼만 해당 섹션으로 들어간다.
        var hasTargetSection = Object.prototype.hasOwnProperty.call(editor, "targetSectionId");
        var sectionId = hasTargetSection ? editor.targetSectionId : sectionAt(x, y), spot = {x: x, y: y};
        if (!editor.targetPosition) {
          if (sectionId) {
            var targetIndex = laneIndex(sectionId);
            var targetTaken = takenSpots(sectionId);
            spot = editor.targetSectionId
              ? slotInRegion(targetIndex, targetTaken.length, targetTaken)
              : settleInRegion(targetIndex, x, y, targetTaken) || spot;
          } else {
            spot = nearestFreeNotePosition(x, y);
          }
        }
        var connectFromNodeId = editor.connectFromNodeId;
        refresh(
          request(apiBase + "nodes/", {
            method: "POST",
            headers: {"Idempotency-Key": key()},
            body: JSON.stringify({content: content, color: editor.color, x: Math.round(spot.x), y: Math.round(spot.y), section_id: sectionId})
          }),
          function (created) {
            setFocused(created.id);
            if (connectFromNodeId) {
              var fromNode = state.nodes.find(function (item) { return item.id === connectFromNodeId; });
              if (fromNode && created.id !== fromNode.id) createConnection(fromNode, created);
            }
          }
        );
      }
      setEditor(null);
    }

    function statusNode(node, status) {
      var payload = {status: status, version: node.version};
      if (status === "held") payload.connection_versions = state.connections.filter(function (line) { return line.node_a_id === node.id || line.node_b_id === node.id; }).map(function (line) { return {id: line.id, version: line.version}; });
      // Invalidate a canvas request that began before this mutation.  Applying
      // that older response after the hold succeeds would draw the note once
      // more until the next click/render.
      fullSyncGenerationRef.current += 1;
      setBusy(true); setNotice(null);
      request(apiBase + "nodes/" + node.id + "/status/", {method: "PATCH", body: JSON.stringify(payload)})
        .then(function (updated) {
          setFocused(function (current) { return current === updated.id ? null : current; });
          setState(function (previous) {
            var nodes = previous.nodes.filter(function (item) { return item.id !== updated.id; });
            var heldNodes = previous.held_nodes.filter(function (item) { return item.id !== updated.id; });
            var connections = previous.connections;
            if (updated.status === "held") {
              heldNodes.push(updated);
              connections = connections.filter(function (line) { return line.node_a_id !== updated.id && line.node_b_id !== updated.id; });
            } else {
              nodes.push(updated);
            }
            var regularNotes = nodes.filter(function (item) { return item.node_type === "note"; });
            var counts = {
              total: regularNotes.length,
              unclassified: regularNotes.filter(function (item) { return !item.section_id; }).length,
              accepted: regularNotes.filter(function (item) { return !!item.section_id; }).length,
              held: heldNodes.length
            };
            return Object.assign({}, previous, {nodes: nodes, held_nodes: heldNodes, connections: connections, counts: counts});
          });
          setSync("connected");
        })
        .catch(function (error) {
          setNotice({kind: error.code === "version_conflict" ? "warning" : "danger", text: error.message});
          cursorRef.current = null;
          return fullSync();
        })
        .finally(function () { setBusy(false); });
    }

    function assignNode(node, assigneeId) {
      refresh(request(apiBase + "nodes/" + node.id + "/assignee/", {
        method: "PATCH",
        body: JSON.stringify({assignee_id: Number(assigneeId), version: node.version})
      }));
    }

    async function deleteNode(node) {
      var confirmed = await window.IdeaUI.confirm({
        title: "메모를 삭제할까요?",
        message: "삭제된 메모는 일반 화면에서 복원할 수 없습니다.",
        confirmText: "삭제",
        cancelText: "취소",
        tone: "danger"
      });
      if (!confirmed) return;
      refresh(request(apiBase + "nodes/" + node.id + "/", {method: "DELETE", body: JSON.stringify({version: node.version})}));
    }

    function moveNode(node, x, y, sectionId) {
      // 배율로 나눈 좌표는 소수점이 길게 남는다. 서버가 자릿수를 12개로 제한하므로 반올림한다.
      x = Math.round(x); y = Math.round(y);
      // 서버 응답을 기다리지 않고 화면에 먼저 반영한다.
      // 영역 크기가 메모 수를 따라가므로 놓는 즉시 땅이 넓어지는 것이 보여야 한다.
      setState(function (current) {
        if (!current) return current;
        return Object.assign({}, current, {
          nodes: current.nodes.map(function (item) {
            return item.id === node.id
              ? Object.assign({}, item, {x: x, y: y, section_id: sectionId})
              : item;
          })
        });
      });
      refresh(request(apiBase + "nodes/" + node.id + "/position/", {method: "PATCH", body: JSON.stringify({version: node.version, x: x, y: y, section_id: sectionId})}));
    }

    function moveNodes(nodes, destinations) {
      refresh(request(apiBase + "nodes/batch-position/", {
        method: "POST",
        body: JSON.stringify({nodes: nodes.map(function (node) {
          var destination = destinations[node.id];
          return {
            id: node.id,
            version: node.version,
            x: Math.round(destination.x),
            y: Math.round(destination.y),
            section_id: destination.section_id
          };
        })})
      }), function () { setSelected([]); setFocused(null); });
    }

    function holdNode(node) {
      statusNode(node, "held");
    }

    function canvasWidth() { return CANVAS_W; }
    function laneIndex(sectionId) { return state.sections.findIndex(function (section) { return section.id === sectionId; }); }
    // 이름표가 차지하는 띠의 높이. 번호·제목·개수 세 줄이 여기에 들어간다.
    var LABEL_BAND = 118;
    // 그리는 위치는 저장된 좌표 그대로다.
    // 끌고 다니는 동안 밀어내면 메모가 손을 따라오지 않아 어디에 놓이는지 알 수 없다.
    // 자리 정리는 손을 뗀 뒤 settleInRegion이 한 번만 한다.
    function displayPosition(node) {
      return {x: Number(node.x), y: Number(node.y)};
    }
    function overlaps(ax, ay, aw, ah, bx, by, bw, bh) {
      return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;
    }
    // 이름표가 놓인 자리. 메모가 조금이라도 겹치면 안 된다.
    // 번호·제목·개수의 실제 글자 크기를 재서 쓴다. 제목 길이가 영역마다 달라
    // 어림잡은 폭으로는 긴 제목의 끝을 가리게 된다.
    function labelBox(index) {
      var box = regionCenter(index);
      var group = document.querySelectorAll(".brain-region")[index];
      var texts = group ? group.querySelectorAll("text") : [];
      var pad = 14;
      var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (var i = 0; i < texts.length; i += 1) {
        try {
          var b = texts[i].getBBox();
          minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x + b.width);
          minY = Math.min(minY, b.y); maxY = Math.max(maxY, b.y + b.height);
        } catch (error) { /* 아직 그려지지 않은 글자는 건너뛴다 */ }
      }
      if (minX < maxX) {
        return {x: minX - pad, y: minY - pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2};
      }
      // 화면에 없으면 이름표가 차지할 자리를 어림잡는다.
      var half = Math.min(260, Math.max(120, box.w / 2 - 20));
      return {x: box.x - half, y: box.top + 18, w: half * 2, h: LABEL_BAND};
    }
    // 미분류는 칸이 아니라 그냥 빈 여백이라 이름표가 상단 한 줄뿐이다.
    // 실제 글자 크기를 재서 그 자리에 메모가 걸리면 아래로 비켜 준다.
    function trayLabelBox() {
      var tray = trayBox();
      var title = document.querySelector(".brain-tray-title");
      var hint = document.querySelector(".brain-tray-hint");
      var pad = 14, minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      [title, hint].forEach(function (el) {
        if (!el) return;
        try {
          var b = el.getBBox();
          minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x + b.width);
          minY = Math.min(minY, b.y); maxY = Math.max(maxY, b.y + b.height);
        } catch (error) { /* 아직 그려지지 않은 글자는 건너뛴다 */ }
      });
      if (minX < maxX) {
        return {x: minX - pad, y: minY - pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2, bottom: maxY + pad};
      }
      return {x: tray.x, y: tray.y, w: tray.w, h: 92, bottom: tray.y + 92};
    }
    // 놓은 자리를 영역 안의 빈 곳으로 옮겨 준다.
    // 네 모서리가 모두 영역 안에 들어가야 하므로 곡선 밖으로 삐져나오지 않는다.
    // taken은 이미 자리를 차지한 메모들의 좌표다.
    function settleInRegion(index, wantX, wantY, taken) {
      var path = new Path2D(regionPath(index));
      var bounds = regionBounds(index);
      var label = labelBox(index);
      var GAP = 10;
      // 경계선에 딱 붙으면 어느 영역 것인지 헷갈린다. 이만큼은 안쪽으로 들여 놓는다.
      var PAD = 24;
      // 네 모서리에 각 변의 가운데까지 본다.
      // 곡선이 안쪽으로 부풀면 모서리만으로는 선을 넘은 것을 놓친다.
      function inside(x, y, pad) {
        var left = x - pad, top = y - pad;
        var right = x + NODE_W + pad, bottom = y + NODE_H + pad;
        var midX = (left + right) / 2, midY = (top + bottom) / 2;
        var probes = [
          [left, top], [right, top], [left, bottom], [right, bottom],
          [midX, top], [midX, bottom], [left, midY], [right, midY]
        ];
        return probes.every(function (point) {
          return hitContext.isPointInPath(path, point[0], point[1]);
        });
      }
      // level 0: 여백·이름표·이웃을 모두 지킨다.
      // level 1: 이웃과의 겹침만 눈감는다. 좁은 영역에 메모가 몰린 경우다.
      // level 2: 안쪽 여백까지 포기한다. 그래도 영역 밖과 이름표는 끝까지 지킨다.
      function fits(x, y, level) {
        if (!inside(x, y, level >= 2 ? 0 : PAD)) return false;
        if (overlaps(x, y, NODE_W, NODE_H, label.x, label.y, label.w, label.h)) return false;
        if (level >= 1) return true;
        return !taken.some(function (spot) {
          return overlaps(x, y, NODE_W, NODE_H, spot.x - GAP, spot.y - GAP, NODE_W + GAP * 2, NODE_H + GAP * 2);
        });
      }
      // 놓은 자리가 이미 멀쩡하면 그대로 둔다.
      if (fits(wantX, wantY, 0)) return {x: wantX, y: wantY};
      function nearest(level) {
        var step = 14, best = null, bestDistance = Infinity;
        for (var y = bounds.y; y <= bounds.y + bounds.h - NODE_H; y += step) {
          for (var x = bounds.x; x <= bounds.x + bounds.w - NODE_W; x += step) {
            var distance = (x - wantX) * (x - wantX) + (y - wantY) * (y - wantY);
            if (distance >= bestDistance || !fits(x, y, level)) continue;
            best = {x: x, y: y}; bestDistance = distance;
          }
        }
        return best;
      }
      return nearest(0) || nearest(1) || nearest(2);
    }
    // 화면에 그릴 자리를 한 번에 정한다.
    // 영역의 넓이가 메모 수를 따라 움직이는 탓에, 메모 하나를 옮기면 다른 영역의
    // 경계까지 밀려서 잘 놓여 있던 메모가 선을 넘거나 이름표를 덮는다.
    // 그래서 그릴 때마다 어긋난 것만 안쪽으로 들인다. 저장된 좌표는 건드리지 않으므로
    // 서버에 다시 쓰지 않고, 함께 편집 중인 사람과 부딪히지도 않는다.
    function layoutPositions(nodes) {
      var placed = {};
      var dragging = draggingRef.current;
      function isDraggingNode(nodeId) {
        return Array.isArray(dragging) ? dragging.includes(nodeId) : dragging === nodeId;
      }
      nodes.forEach(function (node) { placed[node.id] = {x: Number(node.x), y: Number(node.y)}; });
      state.sections.forEach(function (section, index) {
        var taken = [];
        nodes.forEach(function (node) {
          if (node.node_type === "title" || node.section_id !== section.id) return;
          // 끌고 있는 메모는 손을 따라와야 한다. 자리만 차지한 것으로 친다.
          if (isDraggingNode(node.id)) return taken.push(placed[node.id]);
          var spot = settleInRegion(index, placed[node.id].x, placed[node.id].y, taken);
          if (!spot) {
            // 자리를 못 찾아도 항목 밖에 그리면 분류된 메모가 미분류처럼 보인다.
            // 이름표 아래 가운데로 들여놓아 적어도 제 항목 안에는 있게 한다.
            var box = regionCenter(index);
            spot = {x: box.x - NODE_W / 2, y: box.top + LABEL_BAND + 8};
          }
          placed[node.id] = spot;
          taken.push(spot);
        });
      });
      // 미분류 메모는 6200×3600 자유 캔버스 어디에나 둘 수 있다. 새 메모와 자동 정렬의
      // 시작 위치로만 오른쪽 tray를 사용하고, 사용자가 직접 옮긴 좌표를 렌더링 단계에서
      // tray 안으로 되돌리지 않는다.
      return placed;
    }
    // 메모를 고르면 뜨는 조작 막대의 자리를 정한다.
    // 그대로 두면 항목 경계를 넘거나 다른 메모·이름표·연결선을 덮는다.
    // 후보를 넉넉히 두고 가린 넓이를 재서 가장 덜 가리는 자리를 고른다.
    // 딱 맞는 자리가 없을 때 첫 후보로 되돌아가면 결국 무언가를 덮게 된다.
    // 실제로 그려지는 막대 크기와 맞춰야 겹침 계산이 어긋나지 않는다.
    var ACTIONS_W = 272, ACTIONS_H = 50, ACTIONS_GAP = 7;
    function overlapArea(ax, ay, aw, ah, bx, by, bw, bh) {
      var w = Math.min(ax + aw, bx + bw) - Math.max(ax, bx);
      var h = Math.min(ay + ah, by + bh) - Math.max(ay, by);
      return w > 0 && h > 0 ? w * h : 0;
    }
    function actionsOffset(node, spot) {
      var index = node.section_id ? laneIndex(node.section_id) : -1;
      var path = index >= 0 ? new Path2D(regionPath(index)) : null;
      var others = visible.filter(function (row) {
        return row.id !== node.id && row.node_type !== "title" && positions[row.id];
      }).map(function (row) { return positions[row.id]; });
      var labels = state.sections.map(function (section, i) { return labelBox(i); });
      // 연결선은 장애물을 피해 휘므로 직선으로 어림잡으면 실제로 덮는 곳을 놓친다.
      // 선을 그릴 때 남겨 둔 곡선 위의 점을 그대로 쓴다.
      var linePoints = curveSamplesRef.current;
      var candidates = [];
      // 아래·위로는 가로 위치를 바꿔 가며, 옆으로는 세로 위치를 바꿔 가며 찾는다.
      // 붙는 자리가 막히면 한 칸 더 떨어진 자리까지 시도해야 도망갈 곳이 생긴다.
      [1, 2].forEach(function (step) {
        var below = NODE_H + ACTIONS_GAP + (step - 1) * (ACTIONS_H + ACTIONS_GAP);
        var above = -(ACTIONS_H + ACTIONS_GAP) - (step - 1) * (ACTIONS_H + ACTIONS_GAP);
        var right = NODE_W + ACTIONS_GAP + (step - 1) * (ACTIONS_W / 2);
        var left = -(ACTIONS_W + ACTIONS_GAP) - (step - 1) * (ACTIONS_W / 2);
        [0, NODE_W - ACTIONS_W, (NODE_W - ACTIONS_W) / 2].forEach(function (dx) {
          candidates.push({dx: dx, dy: below});
          candidates.push({dx: dx, dy: above});
        });
        [0, (NODE_H - ACTIONS_H) / 2, NODE_H - ACTIONS_H].forEach(function (dy) {
          candidates.push({dx: right, dy: dy});
          candidates.push({dx: left, dy: dy});
        });
      });
      var best = null, bestScore = Infinity;
      candidates.forEach(function (candidate) {
        var x = spot.x + candidate.dx, y = spot.y + candidate.dy;
        var score = 0;
        // 항목 경계를 넘는 것도 흠이지만, 메모나 연결선을 덮는 쪽이 더 나쁘다.
        // 경계를 조금 벗어난 떠 있는 막대는 읽는 데 방해가 되지 않는다.
        if (path) {
          var corners = [[x, y], [x + ACTIONS_W, y], [x, y + ACTIONS_H], [x + ACTIONS_W, y + ACTIONS_H]];
          corners.forEach(function (p) {
            if (!hitContext.isPointInPath(path, p[0], p[1])) score += 2200;
          });
        }
        // 이름표를 가리는 것이 메모를 가리는 것보다 나쁘다.
        labels.forEach(function (box) {
          score += overlapArea(x, y, ACTIONS_W, ACTIONS_H, box.x, box.y, box.w, box.h) * 3;
        });
        others.forEach(function (row) {
          score += overlapArea(x, y, ACTIONS_W, ACTIONS_H, row.x, row.y, NODE_W, NODE_H);
        });
        linePoints.forEach(function (p) {
          if (p[0] > x && p[0] < x + ACTIONS_W && p[1] > y && p[1] < y + ACTIONS_H) score += 400;
        });
        if (score < bestScore) { bestScore = score; best = candidate; }
      });
      return best || candidates[0];
    }
    // 같은 영역에 이미 놓인 메모들의 좌표.
    function takenSpots(sectionId, exceptId) {
      return state.nodes.filter(function (item) {
        return item.id !== exceptId && item.section_id === sectionId
          && item.node_type === "note" && item.status !== "held";
      }).map(function (item) { return {x: Number(item.x), y: Number(item.y)}; });
    }
    function sectionAt(x, y) {
      var centerX = x + NODE_W / 2, centerY = y + NODE_H / 2;
      for (var index = 0; index < state.sections.length; index += 1) {
        if (hitContext.isPointInPath(new Path2D(regionPath(index)), centerX, centerY)) {
          return state.sections[index].id;
        }
      }
      // 어느 영역에도 닿지 않으면 도화지의 빈 공간이므로 분류하지 않은 상태로 둔다.
      return null;
    }
    // 영역 안에서 메모가 겹치지 않게 놓을 자리를 고른다.
    // 격자로 어림잡은 뒤 settleInRegion에 맡겨 곡선 밖과 이름표를 피하게 한다.
    function slotInRegion(index, order, taken) {
      var box = regionCenter(index);
      var perRow = Math.max(1, Math.floor((box.w * 0.78) / (NODE_W * 0.62)));
      var column = order % perRow, row = Math.floor(order / perRow);
      var guessX = box.x - (perRow * NODE_W * 0.62) / 2 + column * NODE_W * 0.62;
      var guessY = box.top + LABEL_BAND + 8 + row * NODE_H * 0.72;
      return settleInRegion(index, guessX, guessY, taken || []) || {x: guessX, y: guessY};
    }

    function createConnection(nodeA, nodeB) {
      var optimisticId = "pending-" + key();
      var optimisticConnection = {
        id: optimisticId,
        node_a_id: nodeA.id,
        node_b_id: nodeB.id,
        version: 0,
        pending: true
      };
      function showOptimisticConnection() {
        setState(function (previous) {
          return Object.assign({}, previous, {
            connections: previous.connections.concat([optimisticConnection])
          });
        });
      }
      if (window.ReactDOM.flushSync) {
        window.ReactDOM.flushSync(showOptimisticConnection);
      } else {
        showOptimisticConnection();
      }
      fullSyncGenerationRef.current += 1;
      setBusy(true); setNotice(null);
      request(apiBase + "connections/", {
        method: "POST",
        headers: {"Idempotency-Key": key()},
        body: JSON.stringify({node_a_id: nodeA.id, node_b_id: nodeB.id, node_a_version: nodeA.version, node_b_version: nodeB.version})
      }).then(function (result) {
        var connection = result.connection;
        setState(function (previous) {
          var connections = previous.connections.filter(function (item) { return item.id !== optimisticId && item.id !== connection.id; });
          connections.push(connection);
          return Object.assign({}, previous, {connections: connections});
        });
        setSync("connected");
      }).catch(function (error) {
        setState(function (previous) {
          return Object.assign({}, previous, {connections: previous.connections.filter(function (item) { return item.id !== optimisticId; })});
        });
        setNotice({kind: error.code === "version_conflict" ? "warning" : "danger", text: error.message});
        cursorRef.current = null;
        return fullSync();
      }).finally(function () { setBusy(false); });
    }

    function deleteConnection(connection) {
      fullSyncGenerationRef.current += 1;
      setBusy(true); setNotice(null);
      request(apiBase + "connections/" + connection.id + "/", {method: "DELETE", body: JSON.stringify({version: connection.version})})
        .then(function () {
          setState(function (previous) {
            return Object.assign({}, previous, {connections: previous.connections.filter(function (item) { return item.id !== connection.id; })});
          });
          setSync("connected");
        }).catch(function (error) {
          setNotice({kind: error.code === "version_conflict" ? "warning" : "danger", text: error.message});
          cursorRef.current = null;
          return fullSync();
        }).finally(function () { setBusy(false); });
    }

    function beginMove(event, node) {
      event.stopPropagation(); setFocused(node.id);
      if (tool === "connect") {
        setFocused(node.id);
        return;
      }
      if (event.shiftKey) {
        setSelected(function (current) {
          var next = current.slice();
          if (!next.length && focused && focused !== node.id) next.push(focused);
          var index = next.indexOf(node.id);
          if (index >= 0) next.splice(index, 1); else next.push(node.id);
          return next;
        });
        return;
      }
      if (!state.permissions.can_edit || state.permissions.is_completed || event.button !== 0) return;

      var movingIds = selected.length > 1 && selected.includes(node.id) ? selected.slice() : [node.id];
      if (movingIds.length === 1) setSelected([]);
      var movingNodes = state.nodes.filter(function (item) { return movingIds.includes(item.id); });
      var starts = {};
      movingNodes.forEach(function (item) { starts[item.id] = positions[item.id] || displayPosition(item); });
      var start = starts[node.id];
      var sx = event.clientX, sy = event.clientY, moved = false;
      var sourceElement = event.currentTarget;
      var sourceRect = sourceElement && sourceElement.getBoundingClientRect
        ? sourceElement.getBoundingClientRect()
        : null;
      var previewOffsetX = sourceRect ? sx - sourceRect.left : 20;
      var previewOffsetY = sourceRect ? sy - sourceRect.top : 20;

      function boundedDelta(rawX, rawY) {
        var minX = Math.min.apply(null, movingNodes.map(function (item) { return starts[item.id].x; }));
        var maxX = Math.max.apply(null, movingNodes.map(function (item) { return starts[item.id].x; }));
        var minY = Math.min.apply(null, movingNodes.map(function (item) { return starts[item.id].y; }));
        var maxY = Math.max.apply(null, movingNodes.map(function (item) { return starts[item.id].y; }));
        return {
          x: Math.max(10 - minX, Math.min(canvasWidth() - NODE_W - maxX, rawX)),
          y: Math.max(10 - minY, Math.min(CANVAS_H - NODE_H - maxY, rawY))
        };
      }

      function heldBoundsAt(clientX, clientY) {
        var heldArea = document.querySelector(".brain-held");
        var bounds = heldArea ? heldArea.getBoundingClientRect() : null;
        return Boolean(
          bounds &&
          clientX >= bounds.left &&
          clientX <= bounds.right &&
          clientY >= bounds.top &&
          clientY <= bounds.bottom
        );
      }

      function moving(moveEvent) {
        var deltaX = moveEvent.clientX - sx, deltaY = moveEvent.clientY - sy;
        if (!moved && Math.abs(deltaX) + Math.abs(deltaY) < 5) return;
        moved = true;
        draggingRef.current = movingIds;

        // 단일 메모는 원래 도화지 DOM을 움직이지 않고 fixed preview만 포인터를 따른다.
        // 이 방식이면 보류 구역 위에서도 섹션 도화지 전체가 같이 올라오지 않는다.
        if (movingIds.length === 1) {
          setDragPreview({
            node: node,
            source: "canvas",
            x: moveEvent.clientX - previewOffsetX,
            y: moveEvent.clientY - previewOffsetY,
            width: sourceRect ? sourceRect.width : NODE_W,
            height: sourceRect ? sourceRect.height : NODE_H,
            scale: sourceRect ? Math.max(0.35, Math.min(1.25, sourceRect.width / NODE_W)) : 1,
            overHeld: heldBoundsAt(moveEvent.clientX, moveEvent.clientY)
          });
          return;
        }

        // 다중 선택 이동은 기존 동작을 유지한다.
        var delta = boundedDelta(deltaX / view.zoom, deltaY / view.zoom);
        setState(function (previous) { return Object.assign({}, previous, {nodes: previous.nodes.map(function (item) {
          return movingIds.includes(item.id)
            ? Object.assign({}, item, {x: starts[item.id].x + delta.x, y: starts[item.id].y + delta.y})
            : item;
        })}); });
      }

      function done(upEvent) {
        window.removeEventListener("mousemove", moving);
        window.removeEventListener("mouseup", done);
        draggingRef.current = null;
        setDragPreview(null);
        if (!moved) return;

        var droppedOnHeld = heldBoundsAt(upEvent.clientX, upEvent.clientY);
        if (droppedOnHeld) {
          if (movingNodes.length > 1) {
            setNotice({kind: "warning", text: "여러 메모는 한 번에 보류할 수 없습니다."});
            cursorRef.current = null; fullSync();
            return;
          }
          holdNode(node);
          return;
        }

        var finalDelta = boundedDelta((upEvent.clientX - sx) / view.zoom, (upEvent.clientY - sy) / view.zoom);
        if (movingNodes.length > 1) {
          var destinations = {};
          movingNodes.forEach(function (item) {
            var x = starts[item.id].x + finalDelta.x, y = starts[item.id].y + finalDelta.y;
            destinations[item.id] = {x: x, y: y, section_id: sectionAt(x, y)};
          });
          moveNodes(movingNodes, destinations);
          return;
        }

        var x = start.x + finalDelta.x, y = start.y + finalDelta.y;
        var sectionId = sectionAt(x, y), spot = {x: x, y: y}, index = sectionId ? laneIndex(sectionId) : -1;
        if (index >= 0) spot = settleInRegion(index, x, y, takenSpots(sectionId, node.id)) || spot;
        moveNode(node, spot.x, spot.y, sectionId);
      }

      window.addEventListener("mousemove", moving);
      window.addEventListener("mouseup", done);
    }

    function clampView(next) {
      var stage = document.querySelector(".brain-stage");
      if (!stage || !canvasContentSize) return next;

      // 자유 캔버스 가장자리에도 메모를 둘 수 있도록 패닝 여백을 넉넉히 둔다.
      // 저장 좌표/노드 좌표는 건드리지 않고 viewport 이동 가능 범위만 확장한다.
      var safe = 240;
      var size = canvasContentSize();
      var scaledW = size.w * next.zoom;
      var scaledH = size.h * next.zoom;
      var width = stage.clientWidth;
      var height = stage.clientHeight;

      var x;
      if (scaledW <= width - safe * 2) {
        x = (width - scaledW) / 2;
      } else {
        var minX = width - scaledW - safe;
        var maxX = safe;
        x = Math.max(minX, Math.min(maxX, next.x));
      }

      var y;
      if (scaledH <= height - safe * 2) {
        y = (height - scaledH) / 2;
      } else {
        var minY = height - scaledH - safe;
        var maxY = safe;
        y = Math.max(minY, Math.min(maxY, next.y));
      }

      return {x: x, y: y, zoom: next.zoom};
    }

    function pan(event) {
      if (![0, 1].includes(event.button) || (event.button === 0 && event.target.closest("[data-node],button,a,input,textarea"))) return;
      event.preventDefault();
      var sx = event.clientX, sy = event.clientY, ox = view.x, oy = view.y;
      function moving(moveEvent) {
        setView(clampView({
          x: ox + moveEvent.clientX - sx,
          y: oy + moveEvent.clientY - sy,
          zoom: view.zoom
        }));
      }
      function done(upEvent) {
        window.removeEventListener("mousemove", moving);
        window.removeEventListener("mouseup", done);
        var next = clampView({
          x: ox + upEvent.clientX - sx,
          y: oy + upEvent.clientY - sy,
          zoom: view.zoom
        });
        setView(next);
        saveView(next);
      }
      window.addEventListener("mousemove", moving);
      window.addEventListener("mouseup", done);
    }
    function panBoard(event) {
      if (tool !== "pan" || event.button !== 0) return;
      if (event.target.closest("button,a,input,textarea,select,.brain-board-card-toolbar")) return;
      var viewport = event.currentTarget;
      event.preventDefault();
      setFocused(null);
      setSelected([]);
      var startX = event.clientX;
      var startY = event.clientY;
      var startLeft = viewport.scrollLeft;
      var startTop = viewport.scrollTop;
      viewport.classList.add("is-panning");

      function moving(moveEvent) {
        viewport.scrollLeft = startLeft - (moveEvent.clientX - startX);
        viewport.scrollTop = startTop - (moveEvent.clientY - startY);
      }
      function done() {
        viewport.classList.remove("is-panning");
        window.removeEventListener("mousemove", moving);
        window.removeEventListener("mouseup", done);
      }
      window.addEventListener("mousemove", moving);
      window.addEventListener("mouseup", done);
    }

    function saveView(next) {
      // DecimalField는 viewport x/y 소수 3자리, zoom 소수 2자리까지만 허용한다.
      // 확대/패닝 계산값을 그대로 보내면 긴 부동소수점 때문에 400이 반복될 수 있다.
      var x = Number(next && next.x), y = Number(next && next.y), zoomValue = Number(next && next.zoom);
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(zoomValue)) return;
      var payload = {
        viewport_x: Math.round(x * 1000) / 1000,
        viewport_y: Math.round(y * 1000) / 1000,
        zoom_level: Math.round(Math.max(.3, Math.min(2, zoomValue)) * 100) / 100
      };
      request(apiBase + "viewport/", {method: "PUT", body: JSON.stringify(payload)}).catch(function () {});
    }
    function saveViewSoon(next) { clearTimeout(viewportSaveRef.current); viewportSaveRef.current = setTimeout(function () { saveView(next); }, 250); }
    function zoom(amount, anchorX, anchorY) {
      var nextZoom = Math.max(.3, Math.min(2, Math.round((view.zoom + amount) * 100) / 100));
      var stage = document.querySelector(".brain-stage");
      var px = anchorX === undefined
        ? (stage ? stage.clientWidth / 2 : window.innerWidth / 2)
        : anchorX;
      var py = anchorY === undefined
        ? (stage ? stage.clientHeight / 2 : window.innerHeight / 2)
        : anchorY;
      var worldX = (px - view.x) / view.zoom, worldY = (py - view.y) / view.zoom;
      var next = clampView({x: px - worldX * nextZoom, y: py - worldY * nextZoom, zoom: nextZoom});
      setView(next); saveViewSoon(next);
    }
    function wheelCanvas(event) {
      event.preventDefault();
      if (event.ctrlKey || event.metaKey) {
        var rect = event.currentTarget.getBoundingClientRect();
        zoom(event.deltaY < 0 ? .05 : -.05, event.clientX - rect.left, event.clientY - rect.top);
        return;
      }
      var next = clampView({x: view.x - event.deltaX, y: view.y - event.deltaY, zoom: view.zoom});
      setView(next); saveViewSoon(next);
    }

    function autoLayout() {
      var counters = {}, placed = {};
      var nodes = state.nodes.filter(function (node) { return node.node_type === "note" && node.status !== "held"; }).map(function (node) {
        var keyName = node.section_id ? String(node.section_id) : "none", order = counters[keyName] || 0; counters[keyName] = order + 1;
        // 분류하지 않은 메모는 오른쪽 여백에 두 줄로 늘어놓는다.
        if (!node.section_id) {
          var tray = trayBox();
          return {id: node.id, version: node.version, section_id: null, x: tray.x + 24 + (order % 2) * (NODE_W + 20), y: tray.y + 92 + Math.floor(order / 2) * (NODE_H + 18)};
        }
        // 같은 영역에 앞서 배치한 자리를 넘겨야 서로 겹치지 않는다.
        var taken = placed[keyName] || (placed[keyName] = []);
        var slot = slotInRegion(laneIndex(node.section_id), order, taken);
        taken.push(slot);
        return {id: node.id, version: node.version, section_id: node.section_id, x: Math.round(slot.x), y: Math.round(slot.y)};
      });
      if (nodes.length) refresh(request(apiBase + "auto-layout/", {method: "POST", body: JSON.stringify({nodes: nodes})}));
    }

    function pollJob(id, completed) {
      setJobId(id);
      function check() { request(apiBase + "ai/jobs/" + id + "/").then(function (job) { if (["queued", "running", "retry_wait", "cancel_requested"].includes(job.status)) return setTimeout(check, 1500); setBusy(false); setJobId(null); if (job.status === "succeeded") completed(job); else setNotice({kind: "warning", text: job.error?.message || "AI 작업이 실패했습니다."}); }).catch(function (error) { setBusy(false); setNotice({kind: "danger", text: error.message}); }); }
      check();
    }
    function loadClassificationResult() {
      setBusy(true); setNotice(null);
      setQuestionsOpen(false);
      request(apiBase + "canvas/", {headers: {"Idempotency-Key": key()}})
        .then(function (serverState) {
          var result = {
            counts: {
              total: serverState.counts.total,
              classified: serverState.counts.accepted,
              unclassified: serverState.counts.unclassified,
              held: serverState.counts.held
            },
            sections: serverState.sections.map(function (section) {
              return Object.assign({}, section, {
                note_count: serverState.nodes.filter(function (node) {
                  return node.node_type === "note" && node.section_id === section.id;
                }).length
              });
            })
          };
          setAiPanel({type: "classification_result", result: result});
        })
        .catch(function (error) { setNotice({kind: "danger", text: error.message}); })
        .finally(function () { setBusy(false); });
    }
    function previewPrd() {
      setQuestionsOpen(false);
      var selectedDefaults = [];
      // 성공 응답은 작업 필드가 최상위에 그대로 펼쳐져 있어 job이라는 키가 없다.
      // 반영할 메모가 없을 때만 서버가 {job: null, message: "..."}를 따로 보낸다.
      // result.job으로 나누면 성공 응답도 매번 이 없음 판정에 걸려 결과를 못 받았다.
      setBusy(true); request(apiBase + "ai/prd-apply/preview/", {method: "POST", headers: {"Idempotency-Key": key()}, body: JSON.stringify({selected_default_nodes: selectedDefaults})}).then(function (result) { if (!result.id) { setBusy(false); return setNotice({kind: "info", text: result.message}); } pollJob(result.id, function (job) { setAiPanel({type: "prd", job: job}); }); }).catch(function (error) { setBusy(false); setNotice({kind: "danger", text: error.message}); });
    }
    function applyPrd() {
      var job = aiPanel.job;
      refresh(request(apiBase + "ai/prd-apply/apply/", {method: "POST", headers: {"Idempotency-Key": key()}, body: JSON.stringify({preview_request_id: job.id, node_versions: job.preview.node_versions, approved_questions: (job.output.answers || []).map(function (row) { return {question_id: row.question_id, version: row.question_version}; })})}), function () { setAiPanel(null); });
    }

    if (!state) return h("div", {className: "brain-loading"}, h("span", {className: "spinner-border text-primary"}), h("p", null, "아이디어 캔버스를 불러오는 중입니다."));
    var canEdit = state.permissions.can_edit && !state.permissions.is_completed;
    var canCreateNote = state.permissions.can_create_note && !state.permissions.is_completed;
    var visible = state.nodes.filter(function (node) { return node.node_type === "title" || filter === "all" || node.status === filter; });
    var positions = layoutPositions(visible);

    function toolButton(value, icon, label) { return h("button", {type: "button", className: "brain-tool " + (tool === value ? "active" : ""), onClick: function () { setTool(value); if (value !== "connect") { setSource(null); setSourceDirection(null); setConnectPointer(null); } }}, h("i", {className: icon}), label); }
    // 연결선이 상관없는 메모 위를 지나가면 그 메모까지 이어진 것처럼 보이고,
    // 항목 이름 위를 지나가면 글자를 읽기 어렵다. 둘 다 피해서 잇는다.
    // 조종점 두 개를 따로 밀 수 있어야 한쪽 끝에 가까이 붙은 것도 비켜 갈 수 있다.
    // blockers는 {x, y, w, h, margin} 꼴의 사각형들이다.
    function routeConnection(x1, y1, x2, y2, blockers) {
      var dx = x2 - x1, dy = y2 - y1;
      var length = Math.sqrt(dx * dx + dy * dy) || 1;
      var awayX = -dy / length, awayY = dx / length;
      function control(first, second) {
        return {
          ax: x1 + dx / 3 + awayX * first, ay: y1 + dy / 3 + awayY * first,
          bx: x1 + dx * 2 / 3 + awayX * second, by: y1 + dy * 2 / 3 + awayY * second
        };
      }
      // 곡선이 벗어나면 안 되는 도화지 범위. 항목 네모와 미분류 여백을 합친 만큼만 허용하고,
      // 그 바깥(빈 여백)으로 크게 휘어 나가는 것도 막힌 것으로 친다.
      var tray = trayBox();
      var boundsLeft = Math.min(BOARD.x, tray.x) - 30;
      var boundsRight = Math.max(BOARD.x + BOARD.w, tray.x + tray.w) + 30;
      var boundsTop = BOARD.y - 30;
      var boundsBottom = BOARD.y + BOARD.h + 30;
      // 막힌 샘플 지점 개수를 센다. 0이면 완전히 안 걸리는 곡선이다.
      function blockedCount(c) {
        var count = 0;
        for (var step = 1; step <= 47; step += 1) {
          var t = step / 48, u = 1 - t;
          var px = u * u * u * x1 + 3 * u * u * t * c.ax + 3 * u * t * t * c.bx + t * t * t * x2;
          var py = u * u * u * y1 + 3 * u * u * t * c.ay + 3 * u * t * t * c.by + t * t * t * y2;
          if (px < boundsLeft || px > boundsRight || py < boundsTop || py > boundsBottom) {
            count += 1;
            continue;
          }
          var blocked = blockers.some(function (spot) {
            var edge = spot.margin;
            return px > spot.x - edge && px < spot.x + spot.w + edge
              && py > spot.y - edge && py < spot.y + spot.h + edge;
          });
          if (blocked) count += 1;
        }
        return count;
      }
      // 0은 곧은 선. 그다음부터 양쪽을 함께, 앞쪽만, 뒤쪽만, S자 순서로 점점 크게 넓혀 간다.
      // 후보를 넉넉히 둬야 메모·이름표가 빽빽한 보드에서도 안 걸리는 곡선을 찾을 확률이 높다.
      var steps = [90, 170, 260, 360, 470, 600, 750, 920];
      var shapes = [control(0, 0)];
      steps.forEach(function (amount) {
        [amount, -amount].forEach(function (signed) {
          shapes.push(control(signed, signed));
          shapes.push(control(signed, 0));
          shapes.push(control(0, signed));
          shapes.push(control(signed, -signed));
        });
      });
      for (var i = 0; i < shapes.length; i += 1) {
        if (blockedCount(shapes[i]) === 0) return shapes[i];
      }
      // 어느 후보도 완전히 못 비키면, 그나마 가장 덜 가리는 곡선을 쓴다.
      // 예전엔 이럴 때 무조건 곧게 이어서 메모·이름표를 정면으로 가로질렀다.
      var best = shapes[0], bestScore = blockedCount(shapes[0]);
      for (var j = 1; j < shapes.length; j += 1) {
        var score = blockedCount(shapes[j]);
        if (score < bestScore) { best = shapes[j]; bestScore = score; }
      }
      return best;
    }
    // 한 메모에 여러 선이 붙으면 모두 같은 중심에서 출발해 겹쳐 보인다.
    // 강조 중인 메모에서는 선들을 테두리에 부챗살처럼 나눠 붙여 서로 떨어뜨린다.
    function spreadAnchor(spotlight, connection, cx, cy, towardX, towardY) {
      if (!spotlight) return {x: cx, y: cy};
      var siblings = state.connections.filter(function (row) {
        return row.node_a_id === spotlight || row.node_b_id === spotlight;
      });
      if (siblings.length < 2) return {x: cx, y: cy};
      // 상대 메모의 방향 순서대로 줄을 세워야 선끼리 꼬이지 않는다.
      var ordered = siblings.map(function (row) {
        var otherId = row.node_a_id === spotlight ? row.node_b_id : row.node_a_id;
        var other = positions[otherId];
        return {id: row.id, angle: other ? Math.atan2(other.y - cy, other.x - cx) : 0};
      }).sort(function (left, right) { return left.angle - right.angle; });
      var slot = ordered.findIndex(function (row) { return row.id === connection.id; });
      if (slot < 0) return {x: cx, y: cy};
      // 상대 쪽을 향한 방향을 기준으로 좌우로 고르게 벌린다.
      var base = Math.atan2(towardY - cy, towardX - cx);
      var spread = Math.min(1.1, 0.34 * (ordered.length - 1));
      var offset = ordered.length < 2 ? 0 : -spread / 2 + spread * (slot / (ordered.length - 1));
      var angle = base + offset;
      var radiusX = NODE_W / 2 - 6, radiusY = NODE_H / 2 - 6;
      return {x: cx + Math.cos(angle) * radiusX, y: cy + Math.sin(angle) * radiusY};
    }
    function line(connection) {
      var nodeA = visible.find(function (node) { return node.id === connection.node_a_id; });
      var nodeB = visible.find(function (node) { return node.id === connection.node_b_id; });
      if (!nodeA || !nodeB) return null;
      // 가리키거나 고른 메모에 닿는 선인지. 부챗살 계산과 강조 표시가 함께 쓴다.
      var spotlightId = hoveredNode || focused;
      var touches = spotlightId && (connection.node_a_id === spotlightId || connection.node_b_id === spotlightId);
      // 둘 다 미분류면 항상 흐리게 보여 준다. 한쪽이라도 섹션에 들어가면 선이 섹션 위를
      // 가로질러 어지러우므로, 그 메모를 가리키거나 골랐을 때만 드러낸다.
      var bothUnclassified = nodeA.section_id === null && nodeB.section_id === null;
      if (!bothUnclassified && !touches) return null;
      var a = positions[connection.node_a_id], b = positions[connection.node_b_id]; if (!a || !b) return null;
      var x1 = a.x + NODE_W / 2, y1 = a.y + NODE_H / 2, x2 = b.x + NODE_W / 2, y2 = b.y + NODE_H / 2;
      // 강조 중인 메모 쪽 끝만 부챗살로 벌려 선끼리 겹치지 않게 한다.
      if (spotlightId === connection.node_a_id) {
        var fanA = spreadAnchor(spotlightId, connection, x1, y1, x2, y2);
        x1 = fanA.x; y1 = fanA.y;
      } else if (spotlightId === connection.node_b_id) {
        var fanB = spreadAnchor(spotlightId, connection, x2, y2, x1, y1);
        x2 = fanB.x; y2 = fanB.y;
      }
      var blockers = visible.filter(function (node) {
        return node.node_type !== "title" && node.id !== connection.node_a_id && node.id !== connection.node_b_id;
      }).map(function (node) {
        var spot = positions[node.id];
        return spot ? {x: spot.x, y: spot.y, w: NODE_W, h: NODE_H, margin: 12} : null;
      }).filter(Boolean);
      // 항목 이름표도 피해야 한다. labelBox가 이미 여유를 두고 재므로 조금만 더 준다.
      state.sections.forEach(function (section, index) {
        var box = labelBox(index);
        blockers.push({x: box.x, y: box.y, w: box.w, h: box.h, margin: 4});
      });
      var bend = routeConnection(x1, y1, x2, y2, blockers);
      // 곡선의 한가운데. 삭제 단추를 여기에 둔다.
      var handleX = (x1 + 3 * bend.ax + 3 * bend.bx + x2) / 8;
      var handleY = (y1 + 3 * bend.ay + 3 * bend.by + y2) / 8;
      var curve = "M " + x1 + " " + y1 + " C " + bend.ax.toFixed(1) + " " + bend.ay.toFixed(1)
        + ", " + bend.bx.toFixed(1) + " " + bend.by.toFixed(1) + ", " + x2 + " " + y2;
      // 조작 막대가 이 선을 덮지 않도록 지나가는 자리를 남겨 둔다.
      for (var s = 0; s <= 40; s += 1) {
        var t = s / 40, u = 1 - t;
        curveSamplesRef.current.push([
          u * u * u * x1 + 3 * u * u * t * bend.ax + 3 * u * t * t * bend.bx + t * t * t * x2,
          u * u * u * y1 + 3 * u * u * t * bend.ay + 3 * u * t * t * bend.by + t * t * t * y2
        ]);
      }
      // unclassified 클래스가 평소 흐리게 보이는 상태를 만든다. 분류된 메모가 낀 선은
      // 이 클래스를 빼서 기본 opacity:0으로 두고 highlighted 때만 드러나게 한다.
      var emphasis = touches ? " highlighted" : "";
      return h("g", {key: connection.id},
        h("path", {d: curve, className: "brain-connection" + (bothUnclassified ? " unclassified" : "") + emphasis + (connection.pending ? " pending" : "")}),
        canEdit && !connection.pending ? h("circle", {cx: handleX, cy: handleY, r: 9, className: "brain-connection-delete" + emphasis, onClick: function () { deleteConnection(connection); }}) : null);
    }
    function note(node) {
      var p = positions[node.id], isFocused = focused === node.id, isMultiSelected = selected.includes(node.id), connect = source?.id === node.id;
      var dragging = draggingRef.current;
      var isDragging = Array.isArray(dragging)
        ? dragging.includes(node.id)
        : dragging === node.id;
      var assignee = (state.participants || []).find(function (participant) { return participant.user_id === node.assignee_id; });
      var connectTarget = tool === "connect" && source && source.id !== node.id && hoveredNode === node.id;
      function handle(direction) {
        var connecting = tool === "connect" && source;
        var isSourceHandle = connecting && source.id === node.id && sourceDirection === direction;
        return h("button", {
          type: "button",
          className: "brain-note-handle " + direction + (isSourceHandle ? " active" : ""),
          "aria-label": connecting
            ? (source.id === node.id ? "연결 시작점 변경" : "이 메모와 연결")
            : "이 지점에서 연결 시작",
          onMouseDown: function (event) { event.preventDefault(); event.stopPropagation(); },
          onClick: function (event) {
            event.preventDefault(); event.stopPropagation();
            if (!canEdit) return;
            if (!source) {
              startConnection(node, direction);
              return;
            }
            if (source.id === node.id) {
              setSourceDirection(direction);
              return;
            }
            createConnection(source, node);
            setSource(null);
            setSourceDirection(null);
            setConnectPointer(null);
            setTool("select");
          }
        }, h("span", {"aria-hidden": "true"}));
      }
      return h("article", {
        key: node.id,
        "data-node": "true",
        "data-node-id": node.id,
        "data-color": node.color,
        className: "brain-note " + (isFocused ? "selected " : "") + (isMultiSelected ? "multi-selected " : "") + (connect ? "connect-source " : "") + (connectTarget ? "connect-target " : ""),
        style: {left: p.x, top: p.y},
        onMouseDown: function (event) { beginMove(event, node); },
        onMouseEnter: function () { setHoveredNode(node.id); },
        onMouseLeave: function () { setHoveredNode(function (current) { return current === node.id ? null : current; }); },
        onDoubleClick: function (event) { event.stopPropagation(); if (canEdit) editNode(node); }
      },
        h("div", {className: "brain-note-top"},
          h("span", {className: "brain-note-status " + node.status}, node.status === "accepted" ? "채택" : "아이디어")
        ),
        h("p", {title: node.content}, node.content),
        h("footer", null,
          h("span", null, "ver." + node.introduced_in_version),
          h("span", {title: assignee ? "담당자 " + assignee.display_name : "담당자 없음"}, assignee ? "담당 " + assignee.display_name : "담당자 없음")
        ),
        (isFocused || tool === "connect") && canEdit && !isDragging ? h(window.React.Fragment, null, handle("top"), handle("right"), handle("bottom"), handle("left")) : null
      );
    }

    function member(userId) {
      return (state.participants || []).find(function (participant) { return participant.user_id === userId; });
    }

    function initials(name) {
      var compact = Array.from(
        String(name || "?").trim().replace(/\s+/g, "")
      );
      return compact.slice(-2).join("") || "?";
    }

    function avatarColorIndex(user) {
      var rawId = Number(user?.user_id);
      if (Number.isSafeInteger(rawId)) {
        return (Math.imul(rawId, -1640531527) >>> 0) % 8;
      }
      var name = String(user?.display_name || "?");
      var hash = 0;
      for (var i = 0; i < name.length; i += 1) {
        hash = ((hash * 31) + name.charCodeAt(i)) >>> 0;
      }
      return hash % 8;
    }

    function participantAvatarStyle(user) {
      if (user && Number(user.user_id) === Number(state.current_user_id)) {
        return {
          color: "var(--idea-avatar-current-fg)",
          background: "var(--idea-avatar-current-bg)"
        };
      }
      var index = avatarColorIndex(user);
      return {
        color: "var(--idea-avatar-" + index + "-fg)",
        background: "var(--idea-avatar-" + index + "-bg)"
      };
    }

    function roleLabel(role) {
      return {owner: "소유자", editor: "편집자", tutor: "튜터", viewer: "조회자"}[role] || role || "참여자";
    }

    function openAssigneeMenu(event, node) {
      event.preventDefault(); event.stopPropagation();
      var rect = event.currentTarget.getBoundingClientRect();
      // 담당자 선택은 modal이 아니라 trigger에 붙는 compact dropdown이다.
      var width = 264;
      var height = Math.min(336, 40 + (state.participants || []).length * 48);
      var left = Math.max(10, Math.min(rect.left, window.innerWidth - width - 10));
      var above = rect.bottom + height > window.innerHeight - 12 && rect.top > height + 12;
      setAssigneeMenu({node: node, left: left, top: above ? null : rect.bottom + 8, bottom: above ? window.innerHeight - rect.top + 8 : null});
    }

    function assigneeButton(node) {
      var assigned = member(node.assignee_id);
      return h("button", {type: "button", className: "brain-assignee-trigger", onMouseDown: function (event) { event.stopPropagation(); }, onClick: function (event) { openAssigneeMenu(event, node); }, "aria-label": "담당자 변경"},
        h("b", {style: participantAvatarStyle(assigned)}, initials(assigned?.display_name)),
        h("span", null, h("small", null, "담당자"), h("strong", null, assigned?.display_name || "담당자 없음")),
        h("i", {className: "idea-icon idea-icon-chevron-down"})
      );
    }

    function renderAssigneeMenu() {
      if (!assigneeMenu) return null;
      var node = assigneeMenu.node;
      return window.ReactDOM.createPortal(h(window.React.Fragment, null,
        h("button", {type: "button", className: "brain-assignee-dismiss", onMouseDown: function () { setAssigneeMenu(null); }, "aria-label": "담당자 메뉴 닫기"}),
        h("aside", {className: "brain-assignee-menu brain-assignee-dropdown", role: "listbox", "aria-label": "담당자 선택", style: {left: assigneeMenu.left, top: assigneeMenu.top, bottom: assigneeMenu.bottom}, onMouseDown: function (event) { event.stopPropagation(); }},
          h("div", {className: "brain-assignee-dropdown-label"}, "담당자 선택"),
          h("div", {className: "brain-assignee-options"}, (state.participants || []).map(function (participant) {
            var selected = participant.user_id === node.assignee_id;
            return h("button", {key: participant.user_id, type: "button", role: "option", "aria-selected": selected ? "true" : "false", className: selected ? "selected" : "", onClick: function () { setAssigneeMenu(null); assignNode(node, participant.user_id); }},
              h("b", {style: participantAvatarStyle(participant)}, initials(participant.display_name)),
              h("span", null, h("strong", null, participant.display_name), h("small", null, roleLabel(participant.role))),
              selected ? h("i", {className: "idea-icon idea-icon-check-lg"}) : null
            );
          }))
        )
      ), document.body);
    }

    function moveToSection(node, sectionId) {
      var sectionNodes = state.nodes.filter(function (item) { return item.node_type === "note" && item.section_id === sectionId && item.status !== "held" && item.id !== node.id; });
      if (sectionId === null) {
        moveNode(node, trayBox().x + 24 + (sectionNodes.length % 2) * 252, trayBox().y + 92 + Math.floor(sectionNodes.length / 2) * 162, null);
        return;
      }
      var slot = slotInRegion(laneIndex(sectionId), sectionNodes.length, takenSpots(sectionId, node.id));
      moveNode(node, slot.x, slot.y, sectionId);
    }

    function finishBoardDragVisuals() {
      setBoardDragHeld(false);
      setBoardDropTarget(null);
      setDragPreview(null);
      Array.prototype.forEach.call(document.querySelectorAll(".brain-board-card.is-dragging-source"), function (element) {
        element.classList.remove("is-dragging-source");
      });
    }

    function dropNode(event, sectionId) {
      event.preventDefault();
      event.stopPropagation();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
      var nodeId = event.dataTransfer.getData("text/brain-node");
      var node = state.nodes.find(function (item) { return item.id === nodeId; });
      // Drop 순간에 preview/source 상태를 먼저 종료해, 포인터를 한 번 더 움직여야
      // 드래그가 끝난 것처럼 보이는 잔상 상태를 만들지 않는다.
      finishBoardDragVisuals();
      if (node && canEdit) {
        setFocused(node.id);
        moveToSection(node, sectionId);
      }
    }

    function dropHeld(event) {
      event.preventDefault();
      event.stopPropagation();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
      var nodeId = event.dataTransfer.getData("text/brain-node");
      var node = state.nodes.find(function (item) { return item.id === nodeId; });
      finishBoardDragVisuals();
      if (node && canEdit) {
        setFocused(node.id);
        holdNode(node);
      }
    }

    function compactCard(node) {
      var owner = member(node.author_id), assignee = member(node.assignee_id);
      var isFocused = focused === node.id;
      var isBoardDragging = !!(dragPreview && dragPreview.source === "board" && dragPreview.node && dragPreview.node.id === node.id);
      return h("article", {
        key: node.id,
        className: "brain-board-card" + (isFocused ? " selected" : "") + (isBoardDragging ? " is-dragging-source" : ""),
        "data-color": node.color,
        draggable: canEdit && tool !== "pan",
        tabIndex: 0,
        onClick: function (event) { if (tool === "pan") return; event.stopPropagation(); setFocused(node.id); setSelected([]); },
        onDoubleClick: function (event) { if (tool === "pan") return; event.stopPropagation(); if (canEdit) editNode(node); },
        onDragStart: function (event) {
          // Mark the source as visually suppressed without removing it from layout.
          // The CSS uses opacity only; visibility:hidden would cancel native drag in Chromium.
          event.currentTarget.classList.add("is-dragging-source");
          setFocused(node.id);
          setBoardDragHeld(false);
          setBoardDropTarget(null);
          event.dataTransfer.setData("text/brain-node", node.id);
          event.dataTransfer.effectAllowed = "move";

          // 브라우저 기본 drag ghost는 강제로 반투명해져 Dark 카드가 흐릿하게 보인다.
          // native ghost는 1px 투명 이미지로 숨기고, 자유 캔버스와 같은 fixed preview를 사용한다.
          var rect = event.currentTarget.getBoundingClientRect();
          var offsetX = event.clientX - rect.left;
          var offsetY = event.clientY - rect.top;
          var ghost = document.createElement("canvas");
          ghost.width = 1; ghost.height = 1;
          ghost.style.position = "fixed";
          ghost.style.left = "-10px";
          ghost.style.top = "-10px";
          document.body.appendChild(ghost);
          try { event.dataTransfer.setDragImage(ghost, 0, 0); } catch (_) {}
          setTimeout(function () { if (ghost.parentNode) ghost.parentNode.removeChild(ghost); }, 0);
          setDragPreview({
            node: node,
            source: "board",
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height,
            scale: 1,
            offsetX: offsetX,
            offsetY: offsetY,
            overHeld: false
          });
        },
        onDrag: function (event) {
          if (!event.clientX && !event.clientY) return;
          setDragPreview(function (current) {
            if (!current || current.source !== "board" || current.node.id !== node.id) return current;
            return Object.assign({}, current, {
              x: event.clientX - (current.offsetX || 20),
              y: event.clientY - (current.offsetY || 20)
            });
          });
        },
        onDragEnd: function (event) {
          if (event && event.currentTarget) event.currentTarget.classList.remove("is-dragging-source");
          setBoardDragHeld(false);
          setBoardDropTarget(null);
          setDragPreview(null);
        }
      },
      h("div", {className: "brain-board-card-head"},
        h("span", {className: "brain-note-status " + node.status}, node.status === "accepted" ? "✓ 채택" : "아이디어")
      ),
      h("p", {title: node.content}, node.content),
      h("div", {className: "brain-card-people"},
        h("span", {className: "brain-person", title: "작성자 " + (owner?.display_name || "알 수 없음")}, h("b", {style: participantAvatarStyle(owner)}, initials(owner?.display_name)), h("small", null, owner?.display_name || "작성자")),
        h("span", {className: "brain-person assignee", title: "담당자 " + (assignee?.display_name || "없음")}, h("i", null, "→"), h("b", {style: participantAvatarStyle(assignee)}, initials(assignee?.display_name)), h("small", null, assignee?.display_name || "담당자 없음"))
      ),
      isFocused && canEdit && !(dragPreview && dragPreview.source === "board" && dragPreview.node && dragPreview.node.id === node.id) ? h("div", {className: "brain-board-card-toolbar brain-action-toolbar", onClick: function (event) { event.stopPropagation(); }},
        h("button", {type: "button", onClick: function () { editNode(node); }, "aria-label": "메모 수정"}, h("i", {className: "idea-icon idea-icon-pencil-square"}), h("span", null, "수정")),
        assigneeButton(node),
        h("button", {type: "button", onClick: function () { statusNode(node, "held"); }, "aria-label": "메모 보류"}, h("i", {className: "idea-icon idea-icon-pause-circle"}), h("span", null, "보류")),
        h("span", {className: "brain-floating-divider"}),
        h("button", {type: "button", className: "danger", onClick: function () { deleteNode(node); }, "aria-label": "메모 삭제"}, h("i", {className: "idea-icon idea-icon-trash3"}), h("span", null, "삭제"))
      ) : null);
    }

    function boardColumn(section, index) {
      var color = laneColors[index % laneColors.length];
      var nodes = visible.filter(function (node) { return node.node_type === "note" && node.section_id === section.id; });
      return h("section", {
        key: section.id,
        className:
          "brain-board-column brain-lane-index-" + (index % laneColors.length) +
          (boardDropTarget === section.id ? " is-drop-target" : ""),
        style: {
          "--lane-bg": color[0],
          "--lane-border": color[1],
          "--lane-accent": color[2]
        },
        onDragEnter: function (event) {
          if (!canEdit) return;
          event.preventDefault();
          setBoardDragHeld(false);
          setBoardDropTarget(section.id);
        },
        onDragOver: function (event) {
          if (!canEdit) return;
          event.preventDefault();
          if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
          if (boardDropTarget !== section.id) {
            setBoardDropTarget(section.id);
          }
        },
        onDragLeave: function (event) {
          if (
            event.relatedTarget &&
            event.currentTarget.contains(event.relatedTarget)
          ) return;
          if (boardDropTarget === section.id) {
            setBoardDropTarget(null);
          }
        },
        onDrop: function (event) {
          dropNode(event, section.id);
        }
      },
        h("header", null,
          h("span", null, String(index + 1).padStart(2, "0")),
          h("div", null, h("strong", null, section.title), h("small", null, nodes.length + "개 아이디어")),
          state.permissions.can_apply_ai && !state.permissions.is_completed ? h("button", {type: "button", onClick: previewPrd}, "✦ AI PRD 적용") : null
        ),
        h("div", {className: "brain-board-stack"}, nodes.length ? nodes.map(compactCard) : h("div", {className: "brain-column-empty"}, h("i", {className: "idea-icon idea-icon-lightbulb"}), h("span", null, "아이디어를 이 칸으로 끌어오세요")))
      );
    }

    function renderBoard() {
      var unclassified = visible.filter(function (node) { return node.node_type === "note" && !node.section_id; });
      return h("main", {
        className: "brain-board-view" + (tool === "pan" ? " is-pan-mode" : ""),
        onMouseDown: panBoard
      },
        h("section", {
          className:
            "brain-unclassified-strip" +
            (boardDropTarget === "__unclassified__" ? " is-drop-target" : ""),
          onDragEnter: function (event) {
            if (!canEdit) return;
            event.preventDefault();
            setBoardDragHeld(false);
            setBoardDropTarget("__unclassified__");
          },
          onDragOver: function (event) {
            if (!canEdit) return;
            event.preventDefault();
            if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
            if (boardDropTarget !== "__unclassified__") {
              setBoardDropTarget("__unclassified__");
            }
          },
          onDragLeave: function (event) {
            if (
              event.relatedTarget &&
              event.currentTarget.contains(event.relatedTarget)
            ) return;
            if (boardDropTarget === "__unclassified__") {
              setBoardDropTarget(null);
            }
          },
          onDrop: function (event) {
            dropNode(event, null);
          }
        },
          h("header", null,
            h("div", null, h("strong", null, "미분류 아이디어"), h("span", null, unclassified.length), h("p", null, "AI 분류 전이거나 직접 옮길 메모입니다.")),
            h("button", {type: "button", className: "brain-unclassified-toggle brain-held-toggle", "aria-expanded": unclassifiedExpanded, onClick: function (event) { event.stopPropagation(); setUnclassifiedExpanded(function (value) { return !value; }); }},
              h("span", null, unclassifiedExpanded ? "접기" : "펼치기"), h("i", {className: "idea-icon " + (unclassifiedExpanded ? "idea-icon-chevron-up" : "idea-icon-chevron-down")})
            )
          ),
          h("div", {className: "brain-unclassified-list" + (unclassifiedExpanded ? " expanded" : " collapsed")}, unclassified.length ? unclassified.map(compactCard) : h("div", {className: "brain-strip-empty"}, h("i", {className: "idea-icon idea-icon-lightbulb"}), h("span", null, "미분류 메모가 없습니다.")))
        ),
        h("div", {
          className: "brain-board-columns",
          style: {"--section-count": Math.max(1, state.sections.length)}
        }, state.sections.map(boardColumn))
      );
    }

    function renderList() {
      var groups = [{id: null, title: "미분류"}].concat(state.sections);
      var listNotes = visible.filter(function (node) { return node.node_type === "note"; });
      return h("main", {className: "brain-list-view"}, h("div", {className: "brain-list-wrap"},
        h("header", {className: "brain-list-heading"}, h("div", null, h("span", null, "IDEA INVENTORY"), h("h2", null, "전체 아이디어 목록")), h("strong", null, listNotes.length + "개")),
        !listNotes.length ? h("section", {className: "brain-inventory-empty"},
          firstPageIllustration ? h("img", {src: firstPageIllustration, alt: ""}) : null,
          h("span", null, "IDEA INVENTORY"),
          h("strong", null, "아직 모아둔 아이디어가 없습니다."),
          h("p", null, "브레인스토밍에서 메모를 추가하면 섹션과 상태별로 이곳에 정리됩니다.")
        ) : groups.map(function (group, index) {
          var nodes = listNotes.filter(function (node) { return node.section_id === group.id; });
          return h("section", {key: group.id || "none", className: "brain-list-group"},
            h("header", null, h("i", {style: {background: laneColors[index % laneColors.length][2]}}), h("strong", null, group.title), h("span", null, nodes.length)),
            nodes.length ? h("div", null, nodes.map(function (node) { var assigned = member(node.assignee_id); return h("article", {key: node.id}, h("span", {className: "brain-note-status " + node.status}, node.status === "accepted" ? "채택" : "기본"), h("p", {title: node.content}, node.content), h("small", null, "담당 " + (assigned?.display_name || "없음")), canEdit ? h("button", {type: "button", onClick: function () { editNode(node); }}, "열기") : null); })) : h("p", {className: "brain-list-empty"}, "등록된 아이디어가 없습니다."));
        })
      ));
    }

    function renderCanvas() {
      // 그리기 전에 도화지 크기와 영역 배분을 메모 수에 맞춰 다시 계산한다.
      // 선을 다시 그리므로 지난번에 남긴 곡선 자리는 버린다.
      curveSamplesRef.current = [];
      var perSection = state.sections.map(function (section) {
        return visible.filter(function (node) { return node.section_id === section.id; }).length;
      });
      resizeBoard(visible.length, perSection.length ? Math.max.apply(null, perSection) : 0);
      setRegionWeights(perSection);
      return h("main", {
        className: "brain-stage" + (draggingRef.current ? " dragging-note" : ""),
        onMouseDown: pan,
        onWheel: wheelCanvas,
        onMouseMove: function (event) {
          if (tool !== "connect" || !source) return;
          var rect = event.currentTarget.getBoundingClientRect();
          setConnectPointer({
            x: (event.clientX - rect.left - view.x) / view.zoom,
            y: (event.clientY - rect.top - view.y) / view.zoom
          });
        },
        onMouseLeave: function () { if (tool === "connect") setConnectPointer(null); }
      },
        h("div", {className: "brain-canvas-hint"}, h("i", {className: "idea-icon idea-icon-arrows-move"}), " 빈 공간을 드래그해 이동 · 휠로 패닝 · Ctrl+휠로 확대/축소"),
        h("div", {className: "brain-zoom"},
          h("button", {type: "button", "aria-label": "확대", onClick: function () { zoom(.05); }}, h("i", {className: "idea-icon idea-icon-plus-lg", "aria-hidden": "true"})),
          h("span", null, Math.round(view.zoom * 100) + "%"),
          h("button", {type: "button", "aria-label": "축소", onClick: function () { zoom(-.05); }}, h("span", {className: "brain-zoom-minus", "aria-hidden": "true"}, "−")),
          h("button", {type: "button", "aria-label": "도화지 전체 보기", onClick: function () { var next = clampView(fitBoardView()); setView(next); saveView(next); }}, h("i", {className: "idea-icon idea-icon-house-door", "aria-hidden": "true"}))
        ),
        h("div", {className: "brain-canvas", style: {width: canvasWidth(), height: CANVAS_H, transform: "translate(" + view.x + "px," + view.y + "px) scale(" + view.zoom + ")"}},
          h("svg", {className: "brain-regions", width: CANVAS_W, height: CANVAS_H},
            h("rect", {className: "brain-board", x: BOARD.x, y: BOARD.y, width: BOARD.w, height: BOARD.h, rx: 26}),
            // 미분류는 칸을 가진 영역이 아니라 그냥 빈 여백이다. 테두리 없이 이름만 위쪽에 둔다.
            h("text", {className: "brain-tray-title", x: trayBox().x + trayBox().w / 2, y: trayBox().y + 42}, "미분류"),
            h("text", {className: "brain-tray-hint", x: trayBox().x + trayBox().w / 2, y: trayBox().y + 68},
              state.counts.unclassified + "개 · 네모 밖에 두면 분류되지 않습니다"),
            state.sections.map(function (section, index) {
              var color = laneColors[index % laneColors.length];
              return h("path", {key: section.id, className: "brain-region-path brain-lane-index-" + (index % laneColors.length), d: regionPath(index), fill: color[0], stroke: color[1]});
            })),
          h("svg", {className: "brain-lines", width: canvasWidth(), height: CANVAS_H},
            state.connections.map(line),
            tool === "connect" && source && connectPointer ? (function () {
              var sourceSpot = positions[source.id] || displayPosition(source);
              var targetNode = hoveredNode ? state.nodes.find(function (item) { return item.id === hoveredNode && item.id !== source.id; }) : null;
              var targetSpot = targetNode ? (positions[targetNode.id] || displayPosition(targetNode)) : null;
              var x1 = sourceSpot.x + NODE_W / 2, y1 = sourceSpot.y + NODE_H / 2;
              if (sourceDirection === "left") x1 = sourceSpot.x;
              if (sourceDirection === "right") x1 = sourceSpot.x + NODE_W;
              if (sourceDirection === "top") y1 = sourceSpot.y;
              if (sourceDirection === "bottom") y1 = sourceSpot.y + NODE_H;
              var x2 = targetSpot ? targetSpot.x + NODE_W / 2 : connectPointer.x;
              var y2 = targetSpot ? targetSpot.y + NODE_H / 2 : connectPointer.y;
              return h("path", {className: "brain-connection-preview" + (targetNode ? " is-target" : ""), d: "M " + x1 + " " + y1 + " L " + x2 + " " + y2});
            })() : null
          ),
          // 이름표는 연결선보다 위에 그린다. 강조된 연결선이 항목 이름을 가로질러도
          // 글자가 항상 또렷하게 읽히도록 하기 위해서다.
          h("svg", {className: "brain-region-labels", width: CANVAS_W, height: CANVAS_H},
            state.sections.map(function (section, index) {
              var color = laneColors[index % laneColors.length];
              var box = regionCenter(index);
              var count = visible.filter(function (node) { return node.section_id === section.id; }).length;
              return h("g", {key: section.id, className: "brain-region brain-lane-index-" + (index % laneColors.length)},
                h("text", {className: "brain-region-index", x: box.x, y: box.top + 46, fill: color[2]}, String(index + 1).padStart(2, "0")),
                h("text", {className: "brain-region-title", x: box.x, y: box.top + 76, fill: color[2]}, section.title),
                h("text", {className: "brain-region-count", x: box.x, y: box.top + 98, fill: color[2]}, count + "개 아이디어")
              );
            })),
          visible.map(note)));
    }

    function renderSelectedToolbar() {
      if (boardView !== "canvas" || !focused || !canEdit || editor || draggingRef.current) return null;
      var node = state.nodes.find(function (item) { return item.id === focused; });
      var p = node ? positions[node.id] : null;
      if (!node || !p) return null;
      var stage = document.querySelector(".brain-stage");
      if (!stage) return null;
      var noteElement = stage.querySelector('[data-node-id="' + node.id + '"]');
      var stageRect = stage.getBoundingClientRect();
      var noteRect = noteElement ? noteElement.getBoundingClientRect() : null;
      var noteLeft = noteRect ? noteRect.left : stageRect.left + view.x + p.x * view.zoom;
      var noteTop = noteRect ? noteRect.top : stageRect.top + view.y + p.y * view.zoom;
      var noteBottom = noteRect ? noteRect.bottom : stageRect.top + view.y + (p.y + NODE_H) * view.zoom;
      // 선택 툴바는 캔버스 좌표가 아니라 실제 메모 DOM의 viewport 좌표를 기준으로 둔다.
      // 직전 렌더의 툴바가 있으면 실제 크기를 재사용해 긴 담당자 이름에서도 메모를 덮지 않는다.
      var previousToolbar = document.querySelector('.brain-floating-toolbar[data-owner-node-id="' + node.id + '"]');
      var previousRect = previousToolbar ? previousToolbar.getBoundingClientRect() : null;
      var toolbarWidth = previousRect && previousRect.width ? previousRect.width : 432;
      var toolbarHeight = previousRect && previousRect.height ? previousRect.height : 52;
      var gap = 14;
      var viewportWidth = document.documentElement.clientWidth || window.innerWidth;
      var viewportHeight = document.documentElement.clientHeight || window.innerHeight;
      var left = Math.max(12, Math.min(noteLeft, viewportWidth - toolbarWidth - 12));
      var belowTop = noteBottom + gap;
      var spaceBelow = viewportHeight - belowTop - 12;
      var spaceAbove = noteTop - gap - 12;
      // 아래쪽에 다른 메모가 바로 붙어 있으면 툴바를 위로 올린다.
      // 단순 viewport 여백만 보던 이전 방식은 메모가 조밀할 때 툴바가 다음 메모를 덮었다.
      var belowRect = {left: left, top: belowTop, right: left + toolbarWidth, bottom: belowTop + toolbarHeight};
      var overlapsBelow = Array.prototype.some.call(stage.querySelectorAll('.brain-note[data-node-id]'), function (candidate) {
        if (candidate === noteElement) return false;
        var rect = candidate.getBoundingClientRect();
        return belowRect.left < rect.right && belowRect.right > rect.left && belowRect.top < rect.bottom && belowRect.bottom > rect.top;
      });
      // 기본 위치는 항상 선택 메모 아래쪽이다. 아래에 다른 메모가 있어도 높은 z-index로
      // 그 위에 표시하고, 실제 viewport 하단 공간이 부족할 때만 위쪽으로 전환한다.
      var placeAbove = spaceBelow < toolbarHeight && spaceAbove >= toolbarHeight;
      // 아래 배치는 top으로, 위 배치는 bottom으로 고정한다. 위쪽 배치에서 툴바의 실제 높이가
      // 예상보다 커져도 메모 방향이 아니라 위쪽으로만 자라므로 선택 메모를 덮지 않는다.
      var toolbarStyle = placeAbove
        ? {left: left, bottom: Math.max(12, viewportHeight - noteTop + gap)}
        : {left: left, top: Math.max(noteBottom + gap, 12)};
      return window.ReactDOM.createPortal(
        h("div", {className: "brain-floating-toolbar brain-action-toolbar " + (placeAbove ? "is-above" : "is-below"), "data-owner-node-id": node.id, style: toolbarStyle, onMouseDown: function (event) { event.stopPropagation(); }},
          h("button", {type: "button", onClick: function () { editNode(node); }, "aria-label": "메모 수정"}, h("i", {className: "idea-icon idea-icon-pencil-square"}), h("span", null, "수정")),
          assigneeButton(node),
          h("button", {type: "button", onClick: function () { statusNode(node, "held"); }, "aria-label": "메모 보류"}, h("i", {className: "idea-icon idea-icon-pause-circle"}), h("span", null, "보류")),
          h("span", {className: "brain-floating-divider"}),
          h("button", {type: "button", className: "danger", onClick: function () { deleteNode(node); }, "aria-label": "메모 삭제"}, h("i", {className: "idea-icon idea-icon-trash3"}), h("span", null, "삭제"))
        ),
        document.body
      );
    }

    function renderDragPreview() {
      if (!dragPreview || !dragPreview.node) return null;
      var previewNode = dragPreview.node;

      // Section-board drag preview should be visually identical to the source
      // board card instead of falling back to the free-canvas sticky-note skin.
      if (dragPreview.source === "board") {
        var previewOwner = member(previewNode.author_id);
        var previewAssignee = member(previewNode.assignee_id);
        return window.ReactDOM.createPortal(
          h("article", {
            className: "idea-dev idea-dev--brainstorm brain-drag-preview brain-board-drag-preview" + (dragPreview.overHeld ? " is-over-held" : ""),
            "data-color": previewNode.color || "yellow",
            style: {
              left: dragPreview.x,
              top: dragPreview.y,
              width: dragPreview.width,
              height: dragPreview.height
            },
            "aria-hidden": "true"
          },
            h("div", {className: "brain-board-card-head"},
              h("span", {className: "brain-note-status " + previewNode.status}, previewNode.status === "accepted" ? "✓ 채택" : "아이디어")
            ),
            h("p", {title: previewNode.content}, previewNode.content),
            h("div", {className: "brain-card-people"},
              h("span", {className: "brain-person"},
                h("b", {style: participantAvatarStyle(previewOwner)}, initials(previewOwner?.display_name)),
                h("small", null, previewOwner?.display_name || "작성자")
              ),
              h("span", {className: "brain-person assignee"},
                h("i", null, "→"),
                h("b", {style: participantAvatarStyle(previewAssignee)}, initials(previewAssignee?.display_name)),
                h("small", null, previewAssignee?.display_name || "담당자 없음")
              )
            )
          ),
          document.body
        );
      }

      return window.ReactDOM.createPortal(
        h("div", {
          className: "idea-dev idea-dev--brainstorm brain-drag-preview is-canvas-source" + (dragPreview.overHeld ? " is-over-held" : ""),
          "data-color": previewNode.color || "yellow",
          style: {
            left: dragPreview.x,
            top: dragPreview.y,
            width: NODE_W,
            height: NODE_H,
            transform: "scale(" + (dragPreview.scale || 1) + ")",
            transformOrigin: "top left"
          },
          "aria-hidden": "true"
        },
          h("div", {className: "brain-note-top"},
            h("span", {className: "brain-note-status " + previewNode.status},
              previewNode.status === "accepted" ? "채택" : "아이디어"
            )
          ),
          h("p", null, previewNode.content),
          h("footer", null,
            h("span", null, "ver." + previewNode.introduced_in_version),
            h("span", null, "담당 " + (member(previewNode.assignee_id)?.display_name || "없음"))
          )
        ),
        document.body
      );
    }

    function renderEditor() {
      if (!editor) return null;
      var colorOptions = ["yellow", "blue", "pink", "green", "orange", "purple"];
      var current = member(editor.node ? editor.node.author_id : state.current_user_id);
      return window.ReactDOM.createPortal(h("div", {className: "brain-editor-backdrop", onMouseDown: function (event) { if (event.target === event.currentTarget) closeEditorWithConfirmation(); }},
        h("section", {className: "brain-editor-modal", role: "dialog", "aria-modal": "true", "aria-labelledby": "brain-editor-title"},
          h("header", null, h("div", null, h("span", null, editor.node ? "EDIT IDEA" : "NEW IDEA"), h("h2", {id: "brain-editor-title"}, editor.node ? "아이디어 수정" : "새 메모 추가")), h("button", {type: "button", onClick: function () { closeEditorWithConfirmation(); }, "aria-label": "닫기"}, "×")),
          h("div", {className: "brain-editor-body"},
            !editor.node ? h("div", {className: "brain-color-picker"}, colorOptions.map(function (color) { return h("button", {key: color, type: "button", "data-color": color, className: editor.color === color ? "active" : "", onClick: function () { setEditor(Object.assign({}, editor, {color: color})); }, "aria-label": color + " 색상"}); })) : null,
            h("textarea", {autoFocus: true, rows: 5, maxLength: 2000, value: editor.content, placeholder: "아이디어를 자유롭게 적어보세요…", onChange: function (event) { setEditor(Object.assign({}, editor, {content: event.target.value})); }}),
            h("div", {className: "brain-editor-author"}, h("span", null, "작성자"), h("b", {style: participantAvatarStyle(current)}, initials(current?.display_name)), h("strong", null, current?.display_name || "로그인 사용자"), h("small", null, "작성자는 변경할 수 없습니다."))
          ),
          h("footer", null, h("button", {type: "button", className: "btn btn-light", onClick: function () { closeEditorWithConfirmation(); }}, "취소"), h("button", {type: "button", className: "btn btn-primary", disabled: !(editor.content || "").trim(), onClick: saveEditor}, editor.node ? "수정 저장" : "메모 추가"))
        )), document.body);
    }

    function renderAiPanel() {
      if (!aiPanel) return null;
      var body;
      if (aiPanel.type === "classification_result") {
        var result = aiPanel.result, counts = result.counts;
        body = h("div", null,
          h("p", {className: "lead"}, "활성 메모 " + counts.total + "개 중 " + counts.classified + "개가 섹션에 분류되어 있습니다."),
          h("div", {className: "brain-result-counts"},
            h("span", null, "분류됨 ", h("strong", null, counts.classified)),
            h("span", null, "미분류 ", h("strong", null, counts.unclassified)),
            h("span", null, "보류 ", h("strong", null, counts.held))
          ),
          h("h3", null, "섹션별 분류 결과"),
          h("ul", null, result.sections.map(function (row) {
            return h("li", {key: row.id}, h("span", null, String(row.position).padStart(2, "0") + " " + row.title), h("strong", null, row.note_count + "개"));
          }))
        );
      } else {
        // 질문을 전부 펼쳐 두면 패널이 글로 가득 차 무엇을 저장하는지 훑기 어렵다.
        // PRD 구조 화면처럼 큰 주제(섹션)만 먼저 보이고, 펼쳐야 그 안의 질문이 나오게 한다.
        var answers = aiPanel.job.output.answers || [];
        var groups = [], groupById = {};
        answers.forEach(function (row) {
          var sectionKey = String(row.section_id);
          if (!groupById[sectionKey]) {
            groupById[sectionKey] = {sectionId: row.section_id, rows: []};
            groups.push(groupById[sectionKey]);
          }
          groupById[sectionKey].rows.push(row);
        });
        // 보드에 보이는 섹션 차례대로 세운다. 답변이 온 순서는 그 차례와 다를 수 있다.
        var sectionOrder = {};
        (state.sections || []).forEach(function (section, index) { sectionOrder[String(section.id)] = index; });
        groups.sort(function (left, right) {
          var leftAt = sectionOrder[String(left.sectionId)], rightAt = sectionOrder[String(right.sectionId)];
          return (leftAt === undefined ? 999 : leftAt) - (rightAt === undefined ? 999 : rightAt);
        });
        var allOpen = groups.length > 0 && groups.every(function (group) { return openAnswers[group.sectionId]; });
        body = h("div", null,
          h("div", {className: "brain-ai-preview-toolbar"},
            h("span", null, "항목 " + groups.length + "개 · 질문 " + answers.length + "개"),
            h("button", {type: "button", onClick: function () {
              var next = {};
              if (!allOpen) groups.forEach(function (group) { next[group.sectionId] = true; });
              setOpenAnswers(next);
            }}, allOpen ? "모두 접기" : "모두 펼치기")
          ),
          groups.map(function (group, index) {
            var open = Boolean(openAnswers[group.sectionId]);
            var section = (state.sections || []).find(function (item) { return item.id === group.sectionId; });
            return h("article", {key: group.sectionId, className: "brain-ai-section" + (open ? " open" : "")},
              h("button", {type: "button", className: "brain-ai-section-head", onClick: function () {
                setOpenAnswers(function (current) {
                  var next = Object.assign({}, current);
                  if (next[group.sectionId]) delete next[group.sectionId];
                  else next[group.sectionId] = true;
                  return next;
                });
              }},
                h("span", {className: "brain-ai-section-index"}, String(index + 1).padStart(2, "0")),
                h("strong", null, section ? section.title : "섹션 " + group.sectionId),
                h("span", {className: "brain-ai-section-count"}, group.rows.length + "개 질문"),
                h("i", {className: "idea-icon idea-icon-chevron-down"})
              ),
              open ? h("div", {className: "brain-ai-section-body"}, group.rows.map(function (row) {
                return h("div", {key: row.question_id, className: "brain-ai-answer-row"},
                  h("strong", null, row.question_prompt || "질문 " + row.question_id),
                  h("p", null, row.draft)
                );
              })) : null
            );
          }),
          h("button", {className: "btn btn-primary w-100", onClick: applyPrd}, "질문별 통합 답변 저장")
        );
      }
      return h("aside", {className: "brain-ai-panel" + (aiPanel.type === "classification_result" ? " brain-classification-panel" : "")},
        h("header", null,
          h("div", null, h("span", null, aiPanel.type === "classification_result" ? "CLASSIFICATION RESULT" : "AI RESULT"), h("h2", null, aiPanel.type === "classification_result" ? "분류 결과" : "PRD 반영 미리보기")),
          h("button", {type: "button", onClick: function () { setAiPanel(null); }}, "×")
        ),
        h("div", {className: "brain-ai-body"}, body)
      );
    }

    function renderQuestionPanel() {
      if (!questionsOpen) return null;
      var term = questionSearch.trim().toLowerCase();
      var total = state.sections.reduce(function (sum, section) { return sum + (section.questions || []).length; }, 0);
      var visibleSections = state.sections.map(function (section) {
        var questions = (section.questions || []).filter(function (question) {
          return !term || section.title.toLowerCase().includes(term) || question.prompt.toLowerCase().includes(term) || (question.answer || "").toLowerCase().includes(term);
        });
        return {section: section, questions: questions};
      }).filter(function (group) { return group.questions.length; });
      var hasExplicitOpenState = Object.keys(openQuestionSections).length > 0;
      return h("aside", {className: "brain-question-panel", role: "dialog", "aria-modal": "false", "aria-labelledby": "brain-question-panel-title"},
        h("header", null,
          h("div", null, h("span", null, "PRD REFERENCE"), h("h2", {id: "brain-question-panel-title"}, "PRD 질문"), h("small", null, total + "개 질문")),
          h("button", {type: "button", onClick: function () { setQuestionsOpen(false); }, "aria-label": "질문 목록 닫기"}, "×")
        ),
        h("div", {className: "brain-question-search"}, h("i", {className: "idea-icon idea-icon-search"}), h("input", {type: "search", value: questionSearch, placeholder: "질문 또는 답변 검색", onChange: function (event) { setQuestionSearch(event.target.value); }})),
        h("div", {className: "brain-question-body"},
          visibleSections.length ? visibleSections.map(function (group, index) {
            var section = group.section;
            var open = term || (hasExplicitOpenState ? !!openQuestionSections[section.id] : index === 0);
            var completed = group.questions.filter(function (question) { return question.is_completed && !question.is_held; }).length;
            return h("section", {key: section.id, className: "brain-question-section" + (open ? " open" : "")},
              h("div", {className: "brain-question-section-head"},
                h("button", {type: "button", className: "brain-question-section-title", onClick: function () { setOpenQuestionSections(function (current) { var next = Object.assign({}, current); next[section.id] = !open; return next; }); }},
                  h("span", {className: "brain-question-section-index"}, String(section.position).padStart(2, "0")),
                  h("strong", null, section.title)
                ),
                canCreateNote ? h("button", {type: "button", className: "brain-question-section-add", "aria-label": section.title + "에 메모 추가", onClick: function () { createNote(section); }},
                  h("i", {className: "idea-icon idea-icon-plus-lg", "aria-hidden": "true"})
                ) : null,
                h("small", null, completed + "/" + group.questions.filter(function (question) { return !question.is_held; }).length),
                h("button", {type: "button", className: "brain-question-section-toggle", onClick: function () { setOpenQuestionSections(function (current) { var next = Object.assign({}, current); next[section.id] = !open; return next; }); }, "aria-label": section.title + (open ? " 접기" : " 펼치기")},
                  h("i", {className: "idea-icon idea-icon-chevron-down"})
                )
              ),
              open ? h("div", {className: "brain-question-items"},
                group.questions.map(function (question) {
                  var answered = !!(question.answer || "").trim();
                  var statusClass = question.is_held ? " held" : answered || question.is_completed ? " done" : "";
                  return h("article", {key: question.id, className: "brain-question-item" + statusClass},
                    h("div", {className: "brain-question-copy"},
                      h("span", null, question.is_held ? "보류" : answered || question.is_completed ? "작성됨" : "미작성"),
                      h("strong", null, question.prompt),
                      answered ? h("p", {title: question.answer}, question.answer) : null
                    )
                  );
                })
              ) : null
            );
          }) : h("div", {className: "brain-question-empty"}, h("i", {className: "idea-icon idea-icon-card-checklist"}), h("strong", null, term ? "검색 결과가 없습니다." : "등록된 질문이 없습니다."), h("span", null, term ? "다른 검색어로 다시 찾아보세요." : "PRD 질문이 준비되면 이곳에서 바로 확인할 수 있어요."))
        )
      );
    }

    function changeBoard(value) {
      setBoardView(value); setSource(null); setTool("select");
    }

    function switchCanvas(canvasId) {
      if (busy || canvasId === state.canvas.id) return;
      setSource(null); setFocused(null); setAssigneeMenu(null); setAiPanel(null);
      cursorRef.current = null;
      fullSync(canvasId);
    }

    function createCanvasVersion() {
      if (busy) return;
      setBusy(true); setNotice(null);
      request(apiBase + "boards/", {
        method: "POST",
        headers: {"Idempotency-Key": key()},
        body: JSON.stringify({source_canvas_id: state.canvas.id})
      }).then(function (created) {
        cursorRef.current = null;
        return fullSync(created.id);
      }).catch(function (error) {
        setNotice({kind: "danger", text: error.message});
      }).finally(function () { setBusy(false); });
    }

    function reorderCanvasVersions(canvasIds, openCanvasId) {
      if (busy) return;
      setBusy(true); setNotice(null);
      request(apiBase + "boards/order/", {
        method: "PATCH",
        body: JSON.stringify({canvas_ids: canvasIds})
      }).then(function (result) {
        cursorRef.current = null;
        return fullSync(openCanvasId || result.latest_canvas_id);
      }).catch(function (error) {
        setNotice({kind: "danger", text: error.message});
      }).finally(function () { setBusy(false); });
    }

    function moveCanvasVersion(row, direction) {
      var versions = state.versions || [];
      var index = versions.findIndex(function (item) { return item.id === row.id; });
      var target = index + direction;
      if (index < 0 || target < 0 || target >= versions.length) return;
      var reordered = versions.slice();
      var moved = reordered.splice(index, 1)[0];
      reordered.splice(target, 0, moved);
      reorderCanvasVersions(reordered.map(function (item) { return item.id; }), row.id);
    }

    function designateLatestCanvas(row) {
      var reordered = (state.versions || []).filter(function (item) { return item.id !== row.id; });
      reordered.unshift(row);
      reorderCanvasVersions(reordered.map(function (item) { return item.id; }), row.id);
    }

    async function deleteLatestCanvas(row) {
      if (busy || !row.is_latest) return;
      var confirmed = await window.IdeaUI.confirm({
        title: "최신 보드를 삭제할까요?",
        message: "바로 이전 보드가 최신 보드로 전환됩니다.",
        confirmText: "삭제",
        cancelText: "취소",
        tone: "danger"
      });
      if (!confirmed) return;
      setBusy(true); setNotice(null);
      request(apiBase + "boards/" + row.id + "/", {method: "DELETE"})
        .then(function (result) {
          activeCanvasId = result.latest_canvas_id;
          cursorRef.current = null;
          return fullSync(result.latest_canvas_id);
        }).catch(function (error) {
          setNotice({kind: "danger", text: error.message});
        }).finally(function () { setBusy(false); });
    }

    function renderVersionSidebar() {
      var versions = state.versions || [];
      return h("aside", {className: "brain-version-sidebar" + (versionsOpen ? "" : " collapsed")},
        h("header", null,
          versionsOpen ? h("span", null, "VERSION") : null,
          h("button", {type: "button", onClick: function () { setVersionsOpen(function (value) { return !value; }); }, "aria-label": versionsOpen ? "버전 목록 접기" : "버전 목록 펼치기"}, h("i", {className: "idea-icon " + (versionsOpen ? "idea-icon-chevron-left" : "idea-icon-chevron-right")}))
        ),
        versionsOpen && state.permissions.can_manage_versions ? h("button", {type: "button", className: "brain-version-add", disabled: busy, onClick: createCanvasVersion, "aria-label": "새 캔버스 버전 만들기"}, h("i", {className: "idea-icon idea-icon-plus-lg"}), h("span", null, "새 보드")) : null,
        versionsOpen ? h("nav", {"aria-label": "캔버스 버전"}, versions.map(function (row, index) {
          return h("div", {key: row.id, className: "brain-version-row" + (row.id === state.canvas.id ? " active" : "")},
            h("button", {type: "button", className: "brain-version-select", onClick: function () { switchCanvas(row.id); }},
              h("span", null, "ver." + row.version_number),
              row.is_latest ? h("small", null, "최신") : null
            ),
            state.permissions.can_manage_versions ? h("div", {className: "brain-version-controls"},
              !row.is_latest ? h("button", {type: "button", disabled: busy, "aria-label": "ver." + row.version_number + " 최신 지정", onClick: function () { designateLatestCanvas(row); }}, h("i", {className: "idea-icon idea-icon-pin-angle"})) : null,
              index > 0 ? h("button", {type: "button", disabled: busy, "aria-label": "ver." + row.version_number + " 위로 이동", onClick: function () { moveCanvasVersion(row, -1); }}, h("i", {className: "idea-icon idea-icon-chevron-up"})) : null,
              index < versions.length - 1 ? h("button", {type: "button", disabled: busy, "aria-label": "ver." + row.version_number + " 아래로 이동", onClick: function () { moveCanvasVersion(row, 1); }}, h("i", {className: "idea-icon idea-icon-chevron-down"})) : null,
              row.is_latest && versions.length > 1 ? h("button", {type: "button", className: "danger", disabled: busy, "aria-label": "ver." + row.version_number + " 삭제", onClick: function () { deleteLatestCanvas(row); }}, h("i", {className: "idea-icon idea-icon-trash3"})) : null
            ) : null
          );
        })) : null
      );
    }

    return h("div", {className: "brain-react-shell"},
      h("header", {className: "brain-topbar"},
        h("div", {className: "brain-project"}, h("a", {href: "/ideas/prds/" + root.dataset.prdId + "/write/", className: "brain-back"}, h("i", {className: "idea-icon idea-icon-arrow-left"}), " PRD로 돌아가기"), h("span", {className: "brain-divider"}), brandMarkUrl ? h("img", {className: "brain-brand-mark", src: brandMarkUrl, alt: "", "aria-hidden": "true"}) : null, h("div", null, h("strong", {className: "brain-title"}, prdTitle), h("small", null, "Idea Developer · 브레인스토밍 보드"))),
        h("nav", {className: "brain-view-tabs", "aria-label": "브레인스토밍 보기 방식"}, [
          ["board", "idea-icon idea-icon-kanban", "섹션 보드"], ["canvas", "idea-icon idea-icon-bounding-box", "자유 캔버스"], ["list", "idea-icon idea-icon-list-ul", "아이디어 목록"]
        ].map(function (item) { return h("button", {key: item[0], type: "button", className: boardView === item[0] ? "active" : "", onClick: function () { changeBoard(item[0]); }}, h("i", {className: item[1]}), item[2]); })),
        h("div", {className: "brain-top-actions"}, h("span", {className: "brain-sync " + sync}, sync === "connected" ? "● 동기화됨" : "● 재연결 중"), state.permissions.can_apply_ai && canEdit ? h("button", {type: "button", className: "btn btn-sm btn-outline-primary", disabled: busy, onClick: previewPrd}, "PRD에 반영") : null)
      ),
      h("div", {className: "brain-toolbar"},
        h("div", {className: "brain-counts"}, h("span", null, state.counts.total + "개 메모"), h("span", {className: "warn"}, "미분류 " + state.counts.unclassified), h("span", {className: "good"}, "✓ " + state.counts.accepted + "개 채택")),
        boardView === "board" ? h("div", {className: "brain-tools"}, toolButton("select", "idea-icon idea-icon-cursor", "선택"), toolButton("pan", "idea-icon idea-icon-hand", "손 이동")) :
          boardView === "canvas" ? h("div", {className: "brain-tools"}, toolButton("select", "idea-icon idea-icon-cursor", "선택"), toolButton("connect", "idea-icon idea-icon-bezier2", "연결")) : null,
        canCreateNote ? h("button", {type: "button", className: "brain-add", onClick: function () { createNote(); }}, h("i", {className: "idea-icon idea-icon-plus-lg"}), " 메모 추가") : null,
        h("div", {className: "brain-filter"}, ["all", "accepted", "default"].map(function (value) { return h("button", {key: value, type: "button", className: filter === value ? "active" : "", onClick: function () { setFilter(value); }}, {all: "전체", accepted: "채택됨", default: "미분류"}[value]); })),
        boardView === "canvas" && canEdit ? h("button", {type: "button", className: "btn btn-sm brain-auto", disabled: busy, onClick: autoLayout}, h("i", {className: "idea-icon idea-icon-grid-3x3-gap"}), " 자동 정렬") : null,
        h("div", {className: "brain-ai-actions"},
          h("button", {type: "button", className: "brain-question-trigger" + (questionsOpen ? " active" : ""), "aria-expanded": questionsOpen, onClick: function () { var next = !questionsOpen; setQuestionsOpen(next); if (next) setAiPanel(null); }}, h("i", {className: "idea-icon idea-icon-card-checklist"}), " 질문 보기"),
          h("button", {type: "button", className: "brain-classification-trigger", disabled: busy, onClick: loadClassificationResult}, h("i", {className: "idea-icon idea-icon-diagram-3"}), " 분류 결과")
        )
      ),
      h("div", {className: "brain-workspace"},
        renderVersionSidebar(),
        h("div", {className: "brain-version-content"},
          !state.permissions.is_latest_canvas ? h("div", {className: "brain-readonly-banner"}, h("i", {className: "idea-icon idea-icon-lock"}), " 이전 버전은 조회 전용입니다. 최신 보드에서만 편집할 수 있습니다.") : null,
          boardView === "canvas" && tool === "connect" ? h("div", {className: "brain-connect-banner"}, source ? "다른 메모의 연결 점을 선택해 주세요" : "메모 가장자리의 연결 점을 선택해 주세요", h("button", {onClick: function () { setTool("select"); setSource(null); setSourceDirection(null); setConnectPointer(null); }}, "취소")) : null,
          boardView === "canvas" && selected.length > 1 && tool !== "connect" ? h("div", {className: "brain-multi-banner"}, selected.length + "개 메모 선택됨", h("button", {type: "button", onClick: function () { setSelected([]); setFocused(null); }}, "선택 해제")) : null,
          notice ? h("div", {className: "brain-notice alert alert-" + notice.kind}, notice.text, h("button", {type: "button", className: "btn-close", onClick: function () { setNotice(null); }})) : null,
          boardView === "board" ? renderBoard() : boardView === "canvas" ? renderCanvas() : renderList(),
          h("section", {
            className:
              "brain-held" +
              (heldExpanded ? "" : " collapsed") +
              ((dragPreview?.overHeld || boardDragHeld) ? " is-drop-target" : ""),
            onDragEnter: function (event) {
              if (!canEdit) return;
              event.preventDefault();
              setBoardDropTarget(null);
              setBoardDragHeld(true);
            },
            onDragOver: function (event) {
              if (!canEdit) return;
              event.preventDefault();
              setBoardDropTarget(null);
              if (!boardDragHeld) setBoardDragHeld(true);
            },
            onDragLeave: function (event) {
              if (
                event.relatedTarget &&
                event.currentTarget.contains(event.relatedTarget)
              ) return;
              setBoardDragHeld(false);
            },
            onDrop: dropHeld
          },
            h("header", null,
              h("strong", null, "⏸ 보류 구역"),
              h("span", null, state.held_nodes.length),
              h("small", null, "메모를 이곳으로 끌어오거나 보류 버튼을 누르면 보류됩니다"),
              h("button", {type: "button", className: "brain-held-toggle", "aria-expanded": heldExpanded, onClick: function () { setHeldExpanded(function (current) { return !current; }); }},
                h("span", null, heldExpanded ? "접기" : "펼치기"),
                h("i", {className: "idea-icon " + (heldExpanded ? "idea-icon-chevron-down" : "idea-icon-chevron-up"), "aria-hidden": "true"})
              )
            ),
            h("div", {className: "brain-held-list"}, state.held_nodes.map(function (node) {
              return h("article", {key: node.id, className: "brain-held-card", "data-color": node.color},
                h("span", {className: "brain-note-status held"}, "보류"),
                h("p", {title: node.content}, node.content),
                canEdit ? h("footer", null, h("button", {type: "button", onClick: function () { statusNode(node, "default"); }}, "보류 해제")) : null
              );
            }))
          )
        )
      ),
      renderEditor(), renderAssigneeMenu(), renderAiPanel(), renderQuestionPanel(), renderSelectedToolbar(), renderDragPreview(),
      busy ? h("div", {className: "brain-busy"}, h("span", {className: "spinner-border spinner-border-sm"}), jobId ? " AI 작업 처리 중" : " 저장 중") : null);
  }

  window.ReactDOM.createRoot(root).render(h(BrainstormApp));
}());
