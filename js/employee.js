/* =====================================================================
 * SwachhLens — Employee dashboard
 * Group-assigned task list · Accept/reject assigned · Mark collected · Verify
 * ===================================================================== */
(function () {
  const me = Auth.require('EMPLOYEE');
  if (!me) return;

  const roster = Store.rosterForEmail(me.email);
  const MY_ID = roster.id;
  const MY_GROUP = Store.group(roster.groupId);
  const I_AM_LEAD = Store.isLead(MY_ID);

  document.getElementById('eName').textContent = roster.name;
  document.getElementById('eRole').textContent = roster.specialty + ' · ' + roster.name;
  document.getElementById('greetName').textContent = roster.name.split(' ')[0];
  document.getElementById('eAvatar').textContent = roster.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  document.getElementById('empBlurb').textContent = roster.name + ' (' + roster.specialty + ') · ' + (MY_GROUP ? MY_GROUP.name : t('emp.yourGroup')) + '. ' + t('emp.blurb') + (I_AM_LEAD ? ' ' + t('emp.blurbLead') : '');

  const leadSection = document.getElementById('leadVerification');
  if (I_AM_LEAD && leadSection) leadSection.style.display = '';
  else if (leadSection) leadSection.style.display = 'none';

  const dispatchSection = document.getElementById('leadDispatch');
  if (I_AM_LEAD && dispatchSection) dispatchSection.style.display = '';
  else if (dispatchSection) dispatchSection.style.display = 'none';

  const iconOf = (r) => (Store.WASTE_TYPES.find((w) => w.key === r.wasteType) || {}).icon || '🗑️';
  const sevColor = { Low: '#16a34a', Medium: '#f59e0b', High: '#ef4444' };

  function badgeFor(r) {
    if (r.status === 'RESOLVED') return '<span class="status-badge st-resolved">' + t('st.resolved') + '</span>';
    if (r.status === 'VERIFY') return '<span class="status-badge st-verify">' + t('st.verification') + '</span>';
    if (r.status === 'ASSIGNED') return '<span class="status-badge st-pending">' + t('st.assigned') + '</span>';
    return '<span class="status-badge st-progress">' + t('st.inProgress') + '</span>';
  }

  function taskCard(r, i) {
    var isAssigned = r.status === 'ASSIGNED';
    var isVerify = r.status === 'VERIFY';
    var actions = '';
    if (isAssigned) {
      actions = '<button class="btn btn-primary btn-small" data-accept="' + r.id + '" style="background:#16a34a;">✓ ' + t('app.acceptTask') + '</button> ' +
                '<button class="btn btn-outline btn-small" data-reject="' + r.id + '" style="border-color:#ef4444;color:#ef4444;">✕ ' + t('app.rejectTask') + '</button>';
    } else if (isVerify) {
      actions = '<span class="rc-tag" style="background:#ede9fe;color:#6d28d9;">' + t('app.verifyTag') + '</span>';
    } else {
      actions = '<button class="btn btn-primary btn-small" data-collect="' + r.id + '">' + t('app.collect') + '</button>';
    }
    return '<article class="report-card task-card reveal in" style="animation-delay:' + Math.min(i * 70, 420) + 'ms">' +
      '<div class="rc-body">' +
        '<div class="rc-top"><h4>' + iconOf(r) + ' ' + escapeHtml(r.wasteType) + (r.isBooking ? ' · 🗓️' : '') + '</h4>' + badgeFor(r) + '</div>' +
        '<div class="rc-meta">📍 ' + escapeHtml(r.location) + '</div>' +
        '<div class="rc-meta">' + escapeHtml(r.desc) + '</div>' +
        '<div class="rc-meta">' + t('emp.reportedBy', { name: escapeHtml(r.reporterName) }) + '</div>' +
        '<div class="detail-row"><span class="d-lbl">' + t('app.severityLbl') + '</span><span class="d-val"><b style="color:' + (sevColor[r.severity] || '#16a34a') + ';">' + r.severity + '</b> · ' + timeAgo(r.createdAt) + '</span></div>' +
        (r.photo ? '<img src="' + r.photo + '" alt="Site photo" style="border-radius:12px;height:120px;width:100%;object-fit:cover;" />' : '') +
        '<div class="tc-actions">' + actions + ' <span class="rc-tag" style="align-self:center;">' + r.id + '</span></div>' +
      '</div></article>';
  }

  function renderTasks() {
    var mine = Store.forEmployee(MY_ID);
    var assigned = mine.filter(r => r.status === 'ASSIGNED');
    var active = mine.filter(r => r.status === 'IN_PROGRESS');
    var verify = mine.filter(r => r.status === 'VERIFY');
    var done = mine.filter(r => r.status === 'RESOLVED');
    var taskEl = document.getElementById('taskGrid');
    var doneEl = document.getElementById('doneGrid');
    var assignedEl = document.getElementById('assignedGrid');

    if (assignedEl) {
      if (!assigned.length) {
        assignedEl.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><span class="e-ico">📭</span><b>' + t('app.noAssigned') + '</b><p>' + t('app.noAssignedSub') + '</p></div>';
      } else { assignedEl.innerHTML = assigned.map(taskCard).join(''); }
    }

    if (!active.length && !verify.length) {
      taskEl.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><span class="e-ico">🎉</span><b>' + t('app.allCaughtUp') + '</b>' + t('app.allCaughtUpSub') + '</div>';
    } else { taskEl.innerHTML = [...active, ...verify].map(taskCard).join(''); }

    doneEl.innerHTML = done.length ? done.map(taskCard).join('') : '<div class="empty-state" style="grid-column:1/-1;"><span class="e-ico">🌱</span><b>' + t('app.nothingDone') + '</b>' + t('app.nothingDoneSub') + '</div>';

    document.querySelectorAll('[data-accept]').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true; btn.innerHTML = '<span class="rp-spinner"></span> ';
      try { await Store.acceptTask(btn.dataset.accept); toast(t('emp.acceptedToast')); renderTasks(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; btn.innerHTML = '✓ ' + t('app.acceptTask'); }
    }));
    document.querySelectorAll('[data-reject]').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true; btn.innerHTML = '<span class="rp-spinner"></span> ';
      try { await Store.rejectTask(btn.dataset.reject); toast(t('emp.rejectedToast')); renderTasks(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; btn.innerHTML = '✕ ' + t('app.rejectTask'); }
    }));
    document.querySelectorAll('[data-collect]').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true; btn.innerHTML = '<span class="rp-spinner"></span> ' + t('app.updating');
      try { await Store.submitCollected(btn.dataset.collect); toast(t('emp.collectedToast')); renderTasks(); renderVerify(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; btn.innerHTML = t('app.collect'); }
    }));
  }

  function renderDispatch() {
    var el = document.getElementById('leadDispatchGrid');
    if (!el || !I_AM_LEAD) return;
    var list = Store.pending().filter(r => r.suggestedGroupId === roster.groupId);
    if (!list.length) {
      el.innerHTML = '<div class="empty-state"><span class="e-ico">🤖</span><b>' + t('app.noDispatch') + '</b>' + t('app.noDispatchSub') + '</div>';
      return;
    }
    el.innerHTML = list.map((r, i) => {
      var sugM = Store.member(r.suggestedMemberId);
      var memberOpts = Store.membersOf(roster.groupId).map(e =>
        '<option value="' + e.id + '"' + (e.id === r.suggestedMemberId ? ' selected' : '') + '>' + e.icon + ' ' + e.name + '</option>'
      ).join('');
      return '<div class="queue-row reveal in" style="animation-delay:' + Math.min(i * 60, 360) + 'ms">' +
        '<div class="qr-ico" style="background:#eef3ff;">🤖</div>' +
        '<div class="qr-main">' +
          '<div class="qr-title">' + iconOf(r) + ' ' + escapeHtml(r.wasteType) + ' · ' + escapeHtml(r.location) + '</div>' +
          '<div class="qr-meta"><span>' + t('emp.by', { name: escapeHtml(r.reporterName) }) + '</span><span>⚡ ' + r.severity + '</span><span>' + timeAgo(r.createdAt) + '</span></div>' +
          '<div class="qr-meta" style="margin-top:4px;"><span style="font-weight:800;color:var(--green-600);">🤖 ' + t('emp.aiSuggests') + '</span><span>' + (sugM ? sugM.icon + ' ' + sugM.name : t('emp.anyMember')) + '</span></div>' +
        '</div>' +
        '<div class="qr-actions"><select id="ldm-' + r.id + '">' + memberOpts + '</select>' +
          '<button class="btn btn-primary btn-small" data-lead-approve="' + r.id + '">' + t('emp.approveDispatch') + '</button></div>' +
      '</div>';
    }).join('');

    el.querySelectorAll('[data-lead-approve]').forEach(btn => btn.addEventListener('click', async () => {
      var id = btn.dataset.leadApprove;
      var memberId = document.getElementById('ldm-' + id).value;
      btn.disabled = true;
      try { await Store.approveAssign(id, { groupId: roster.groupId, memberId }); toast(t('emp.dispatched', { name: Store.member(memberId)?.name || t('emp.crew') })); renderDispatch(); renderReassign(); renderTasks(); }
      catch (e) { toast(e.message || 'Dispatch failed', true); btn.disabled = false; }
    }));
  }

  function renderReassign() {
    if (!I_AM_LEAD) return;
    var el = document.getElementById('leadDispatchGrid');
    if (!el) return;
    var assigned = Store.load().filter(r => r.status === 'ASSIGNED' && r.assignedGroupId === roster.groupId);
    if (!assigned.length) return;
    var rows = assigned.map((r, i) => {
      var m = Store.member(r.assignedTo);
      var opts = Store.membersOf(roster.groupId).map(e =>
        '<option value="' + e.id + '"' + (e.id === r.assignedTo ? ' selected' : '') + '>' + e.icon + ' ' + e.name + '</option>'
      ).join('');
      return '<div class="queue-row reveal in" style="border-left:3px solid #f59e0b;">' +
        '<div class="qr-ico" style="background:#fef3c7;">🔄</div>' +
        '<div class="qr-main">' +
          '<div class="qr-title">' + iconOf(r) + ' ' + escapeHtml(r.wasteType) + ' · ' + escapeHtml(r.location) + '</div>' +
          '<div class="qr-meta"><span>Assigned to: <b>' + (m ? m.icon + ' ' + m.name : '?') + '</b></span><span>⚡ ' + r.severity + '</span></div>' +
        '</div>' +
        '<div class="qr-actions"><select id="ram-' + r.id + '">' + opts + '</select>' +
          '<button class="btn btn-outline btn-small" data-lead-reassign="' + r.id + '">🔄 ' + t('emp.reassignBtn') + '</button></div>' +
      '</div>';
    }).join('');
    el.insertAdjacentHTML('beforeend', rows);
    el.querySelectorAll('[data-lead-reassign]').forEach(btn => btn.addEventListener('click', async () => {
      var id = btn.dataset.leadReassign;
      var memberId = document.getElementById('ram-' + id).value;
      btn.disabled = true;
      try { await Store.reassignTask(id, memberId); toast(t('emp.reassignedToast', { name: Store.member(memberId)?.name || '' })); renderDispatch(); renderReassign(); renderTasks(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; }
    }));
  }

  function renderVerify() {
    var el = document.getElementById('leadVerifyGrid');
    if (!el || !I_AM_LEAD) return;
    var list = Store.verification().filter(r => r.assignedGroupId === roster.groupId);
    if (!list.length) {
      el.innerHTML = '<div class="empty-state"><span class="e-ico">🔍</span><b>' + t('app.nothingVerify') + '</b>' + t('app.nothingVerifySub') + '</div>';
      return;
    }
    el.innerHTML = list.map((r, i) => {
      var m = Store.member(r.assignedTo);
      return '<div class="queue-row reveal in" style="animation-delay:' + Math.min(i * 60, 360) + 'ms">' +
        '<div class="qr-ico" style="background:#ede9fe;">🔍</div>' +
        '<div class="qr-main">' +
          '<div class="qr-title">' + iconOf(r) + ' ' + escapeHtml(r.wasteType) + ' · ' + escapeHtml(r.location) + '</div>' +
          '<div class="qr-meta"><span>' + t('emp.collectedBy', { name: m ? m.name : t('emp.crew') }) + '</span><span>⚡ ' + r.severity + '</span><span>' + timeAgo(r.createdAt) + '</span></div>' +
        '</div>' +
        '<div class="qr-actions">' +
          '<button class="btn btn-primary btn-small" data-lv-pass="' + r.id + '">' + t('emp.confirmResolve') + '</button> ' +
          '<button class="btn btn-outline btn-small" data-lv-reject="' + r.id + '">' + t('emp.sendBack') + '</button>' +
        '</div></div>';
    }).join('');

    el.querySelectorAll('[data-lv-pass]').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true;
      try { await Store.verifyPass(btn.dataset.lvPass, roster.name); toast(t('emp.verifiedToast')); renderTasks(); renderVerify(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; }
    }));
    el.querySelectorAll('[data-lv-reject]').forEach(btn => btn.addEventListener('click', async () => {
      btn.disabled = true;
      try { await Store.verifyReject(btn.dataset.lvReject, roster.name); toast(t('emp.sentBackToast')); renderTasks(); renderVerify(); }
      catch (e) { toast(e.message || 'Failed', true); btn.disabled = false; }
    }));
  }

  Store.onChange(() => { renderDispatch(); renderReassign(); renderTasks(); renderVerify(); });

  (async () => {
    await Store.init();
    renderDispatch(); renderReassign(); renderTasks(); renderVerify();
  })();
})();