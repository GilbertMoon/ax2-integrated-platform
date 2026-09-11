(() => {
  const panel = document.getElementById('teamLmsPanel');
  if (!panel) return;
  const el = id => document.getElementById(id);
  const selected = new Map();
  const initial = JSON.parse(document.getElementById('teams-initial-data').textContent);
  const names = new Map([...(initial.teams || []).flatMap(t=>t.members), ...(initial.unassigned_members || [])].map(p=>[String(p.participant_id),p.display_name]));
  let page = 1, pages = 1, loaded = false, requestNumber = 0;
  function selection() {
    return {enabled:el('teamLmsEnabled').checked, weight:Number(el('teamLmsWeight').value), items:[...selected.values()].sort((a,b)=>a.assignment_id-b.assignment_id)};
  }
  function count() { el('teamLmsCount').textContent = `선택 ${selected.size}개 (중복 과제는 한 번만 계산)`; }
  function controls() {
    el('teamLmsOptions').hidden = !el('teamLmsEnabled').checked;
    const w = Number(el('teamLmsWeight').value);
    el('teamLmsWeightLabel').textContent = `${w}%`;
    el('teamLmsBaseLabel').textContent = `기존 평가 기준 점수 ${100-w}% / LMS ${w}%`;
  }
  function showEvidence(evidence) {
    const students = evidence.students || {};
    const rows = Object.entries(evidence.seed_scores || {}).map(([pid, score]) => {
      const s = students[pid];
      const name = names.get(pid) || `참가자 ${pid}`;
      const missing = s ? s.details.filter(d=>d.submission_id === null).length : 0;
      const excluded = s ? s.details.filter(d=>d.status === 'not_in_historical_team').length : 0;
      return s ? `${name}: 기존 ${s.base ?? 'N/A'}, LMS ${s.lms_total ?? 'N/A'}/100 → 편성 ${score ?? 'N/A'} (미제출 ${missing}개, 당시 팀 소속 없음 ${excluded}개)` : `${name}: ${score ?? 'N/A'}`;
    });
    el('teamLmsEvidence').textContent = `계산 시각: ${evidence.calculated_at}\n${rows.join('\n')}\nN/A는 0점이 아니라 기준 점수 없는 참가자로 처리됩니다.`;
  }
  function params() { return new URLSearchParams({source_round:el('teamLmsRound').value,q:el('teamLmsQuery').value,page}); }
  async function load() {
    const number = ++requestNumber;
    try {
      const response = await fetch(`${panel.dataset.catalog}?${params()}`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.error?.message || '목록 조회 실패');
      if (number !== requestNumber) return;
      if (!loaded) {
        body.rounds.forEach(r => { const o=document.createElement('option'); o.value=r.id;o.textContent=`${r.title} (#${r.id})`;el('teamLmsRound').append(o); });
        loaded=true;controls();count();
      }
      el('teamLmsList').replaceChildren();
      body.items.forEach(a => {
        const label=document.createElement('label');label.className='d-block mb-1';
        const box=document.createElement('input');box.type='checkbox';box.checked=selected.has(a.id);
        box.disabled=initial.is_read_only || (a.is_team && !el('teamLmsRound').value);
        box.addEventListener('change',()=>{if(box.checked) selected.set(a.id,{assignment_id:a.id,round_id:Number(el('teamLmsRound').value)||null});else selected.delete(a.id);count();});
        label.append(box,document.createTextNode(` ${a.title} (#${a.id}) · ${a.is_team?'팀':'개인'} · ${a.due_at}`));el('teamLmsList').append(label);
      });
      page=body.page;pages=body.pages;el('teamLmsPage').textContent=`${page}/${pages} · ${body.total}개`;
      el('teamLmsPrev').disabled=initial.is_read_only || page<=1;el('teamLmsNext').disabled=initial.is_read_only || page>=pages;
      el('teamLmsMessage').textContent='설정을 바꾼 뒤 점수 계산 또는 자동 배치를 실행하세요. 팀 저장 시 계산 근거를 함께 보관합니다.';
    } catch(error) { el('teamLmsMessage').textContent=error.message; }
  }
  el('teamLmsEnabled').addEventListener('change',controls);el('teamLmsWeight').addEventListener('input',controls);
  el('teamLmsSearch').onclick=()=>{page=1;load();};el('teamLmsRound').onchange=()=>{page=1;load();};
  el('teamLmsPrev').onclick=()=>{page--;load();};el('teamLmsNext').onclick=()=>{page++;load();};
  el('teamLmsClear').onclick=()=>{selected.clear();count();load();};
  el('teamLmsAll').onclick=async()=>{
    if(!el('teamLmsRound').value){el('teamLmsMessage').textContent='전체 선택은 귀속 회차를 먼저 선택해 주세요.';return;}
    const sourceRound=Number(el('teamLmsRound').value), p=params();p.set('all_ids','1');
    try { const res=await fetch(`${panel.dataset.catalog}?${p}`);const body=await res.json();if(!res.ok)throw new Error(body.error?.message||'조회 실패');body.ids.forEach(id=>selected.set(id,{assignment_id:id,round_id:sourceRound}));count();load(); }
    catch(e){el('teamLmsMessage').textContent=e.message;}
  };
  window.TEAM_LMS={selection, showEvidence};
  if (initial.formation_evidence) {
    const s=initial.formation_evidence.selection;
    el('teamLmsEnabled').checked=s.enabled;el('teamLmsWeight').value=s.weight || 30;
    s.items.forEach(i=>selected.set(i.assignment_id,i));showEvidence(initial.formation_evidence);
  }
  controls();count();
  if (initial.is_read_only) panel.querySelectorAll('input,select,button').forEach(e=>e.disabled=true);
  load();
})();
