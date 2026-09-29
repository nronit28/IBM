/**
 * IBM FINANCIAL SOLUTIONS // FRONTEND ENGINE
 * Interactive Terminal, Live REST API Client, Gemini 2.5 Flash AI Co-Pilot,
 * Custom Invoice Sandbox, Payment Rails Execution, and Mechanical Audio FX.
 */

class AudioFX {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx && typeof window.AudioContext !== 'undefined') {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  // Synthesize realistic mechanical keyboard click
  click() {
    if (!this.enabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(600, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(120, this.ctx.currentTime + 0.035);

      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.035);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.04);
    } catch (e) {
      // Audio fallback silent
    }
  }
}

const sfx = new AudioFX();

document.addEventListener('DOMContentLoaded', () => {
  initHeroAssetToggle();
  initLiveCrtTicker();
  initTerminalEngine();
  setupClickSounds();
  initModalHandlers();
  initGeminiSubtabs();
  initGeminiConfigModal();
  initCustomInvoiceModal();
  initDataLabModal();
  initLiveLedger();
});

// Setup click sounds for interactive elements
function setupClickSounds() {
  document.querySelectorAll('button, .scenario-btn, .toggle-btn, .nav-cta, .btn-primary, .btn-secondary').forEach(btn => {
    btn.addEventListener('click', () => sfx.click());
  });
}

// Toggle between Studio Photo and ASCII Art view
function initHeroAssetToggle() {
  const photoBtn = document.getElementById('btnPhotoView');
  const asciiBtn = document.getElementById('btnAsciiView');
  const photoWrapper = document.getElementById('computerPhotoWrapper');
  const asciiWrapper = document.getElementById('computerAsciiWrapper');

  if (!photoBtn || !asciiBtn) return;

  photoBtn.addEventListener('click', () => {
    photoBtn.classList.add('active');
    asciiBtn.classList.remove('active');
    photoWrapper.style.display = 'flex';
    asciiWrapper.classList.remove('active');
  });

  asciiBtn.addEventListener('click', () => {
    asciiBtn.classList.add('active');
    photoBtn.classList.remove('active');
    photoWrapper.style.display = 'none';
    asciiWrapper.classList.add('active');
    asciiWrapper.textContent = ASCII_IBM_PC;
  });
}

// Simulate tiny CRT phosphor terminal text on the hero computer screen
function initLiveCrtTicker() {
  const crtText = document.getElementById('crtScreenLiveText');
  if (!crtText) return;

  const messages = [
    "A> SAP_AP.EXE\n>> CONNECTED\n>> PO: 45009812\n>> RAG: ONLINE\n_ ",
    "A> GEMINI_2.5\n>> MODEL: FLASH\n>> REASONING: OK\n>> CITATION: OK\n_ ",
    "A> EXCEPTION\n>> TAX: +$8.50\n>> TOLERANCE: OK\n>> APPROVED\n_ ",
    "A> DISPUTE\n>> RATE: $195/H\n>> CAP: $170/H\n>> DRAFT SENT\n_ ",
    "A> NACHA_PAY\n>> ACH: GENERATED\n>> 94-COL: VALID\n>> CLEARED\n_ ",
    "A> ISO20022\n>> PAIN.001: OK\n>> SWIFT: CLEARED\n>> LEDGER: POST\n_ "
  ];

  let msgIdx = 0;
  setInterval(() => {
    crtText.textContent = messages[msgIdx];
    msgIdx = (msgIdx + 1) % messages.length;
  }, 3200);
}

// Active State Cache for Payloads and Modals
let ACTIVE_INVOICE_ID = "INV-2026-001";
let ACTIVE_DISBURSEMENT = null;
let ACTIVE_GEMINI_ANALYSIS = null;

// Terminal Engine for Scenario Simulation & Live API Execution
function initTerminalEngine() {
  const scenarioBtnsContainer = document.getElementById('scenarioPills');
  const logStream = document.getElementById('terminalLogStream');
  const dossierTitle = document.getElementById('dossierTitle');
  const dossierStatusPill = document.getElementById('dossierStatusPill');
  const dossierInfo = document.getElementById('dossierInfo');
  const dossierComm = document.getElementById('dossierCommunication');
  const liveDot = document.getElementById('terminalStatusDot');
  const actionButtons = document.getElementById('dossierActionButtons');
  const settlementCard = document.getElementById('settlementCard');

  if (!scenarioBtnsContainer || typeof SCENARIOS === 'undefined') return;

  // Check Backend Server Status
  fetch('/api/status')
    .then(r => r.json())
    .then(data => {
      const titleElem = document.querySelector('.terminal-title');
      if (titleElem && data.system) {
        titleElem.textContent = `${data.system} [${data.status}: SAP + GEMINI 2.5 + NACHA + ISO 20022]`;
      }
      const gemBtn = document.getElementById('btnGeminiConfig');
      if (gemBtn && data.gemini_live) {
        gemBtn.textContent = '✨ GEMINI 2.5 (LIVE CLOUD)';
      }
    })
    .catch(() => {
      // Backend offline, fallback client mode
    });

  // Render scenario selector buttons
  function renderButtons(selectInvoiceId) {
    scenarioBtnsContainer.innerHTML = '';
    SCENARIOS.forEach((scn, idx) => {
      const isSelected = selectInvoiceId ? scn.invoiceId === selectInvoiceId : idx === 0;
      const btn = document.createElement('button');
      btn.className = `scenario-btn ${isSelected ? 'active' : ''}`;
      btn.textContent = `[${scn.code}: ${scn.title.split('(')[0].trim()}]`;
      btn.dataset.id = scn.id;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        runScenario(scn);
      });
      scenarioBtnsContainer.appendChild(btn);
    });
  }

  window.renderScenarioButtons = renderButtons;
  window.runTerminalScenario = runScenario;

  // Automatically execute first scenario on load
  renderButtons();
  runScenario(SCENARIOS[0]);

  async function runScenario(scn) {
    ACTIVE_INVOICE_ID = scn.invoiceId;
    if (liveDot) liveDot.className = 't-dot yellow';
    if (settlementCard) settlementCard.style.display = 'none';

    // Clear logs
    logStream.innerHTML = `<div class="log-line log-highlight">> INITIATING LIVE 3-WAY MATCH ON ${scn.invoiceId}...</div>`;

    // Trigger live backend match API in parallel
    let liveMatchResult = null;
    try {
      const apiResp = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invoice_id: scn.invoiceId })
      });
      if (apiResp.ok) {
        const body = await apiResp.json();
        liveMatchResult = body.matching_result;
        ACTIVE_GEMINI_ANALYSIS = body.gemini_analysis;
        renderGeminiReasoning(ACTIVE_GEMINI_ANALYSIS);
      }
    } catch (e) {
      // Offline fallback
    }

    // Typewriter effect streaming agent logs
    scn.agentLogs.forEach((log, i) => {
      setTimeout(() => {
        const div = document.createElement('div');
        div.className = 'log-line';
        if (log.includes('CRITICAL') || log.includes('Excess') || log.includes('Overcharge')) {
          div.className += ' log-error';
        } else if (log.includes('Exception') || log.includes('Missing') || log.includes('Pending')) {
          div.className += ' log-warn';
        } else if (log.includes('Auto-posting') || log.includes('100% confidence') || log.includes('Auto-approved')) {
          div.className += ' log-highlight';
        }
        div.textContent = log;
        logStream.appendChild(div);
        logStream.scrollTop = logStream.scrollHeight;
        sfx.click();

        // When last log finishes
        if (i === scn.agentLogs.length - 1) {
          if (liveDot) liveDot.className = 't-dot green';
          renderDossier(scn, liveMatchResult);
          checkExistingPayment(scn.invoiceId);
        }
      }, (i + 1) * 260);
    });
  }

  function renderDossier(scn, liveResult) {
    dossierTitle.textContent = `${scn.invoiceId} // ${scn.vendorName}`;
    
    const currentStatus = liveResult ? liveResult.overall_status : scn.status;
    const actionType = liveResult ? liveResult.resolution_action.action_type : scn.actionType;
    const confidence = liveResult ? `${(liveResult.confidence_score * 100).toFixed(1)}%` : scn.confidence;
    const discrepancy = liveResult ? `$${liveResult.discrepancy_amount.toFixed(2)}` : scn.discrepancy;
    const comm = liveResult ? liveResult.resolution_action.generated_communication : scn.communication;

    // Status pill
    dossierStatusPill.className = 'dossier-status-pill';
    if (currentStatus === 'PERFECT_MATCH' || actionType === 'AUTO_APPROVE') {
      dossierStatusPill.classList.add('status-success');
      dossierStatusPill.textContent = 'AUTO_APPROVE';
    } else if (currentStatus === 'EXCEPTION_RATE_VARIANCE') {
      dossierStatusPill.classList.add('status-danger');
      dossierStatusPill.textContent = 'RATE DISPUTE DRAFTED';
    } else if (currentStatus === 'DISPUTE_DISPATCHED') {
      dossierStatusPill.classList.add('status-danger');
      dossierStatusPill.textContent = 'DISPUTE DISPATCHED';
    } else {
      dossierStatusPill.classList.add('status-warning');
      dossierStatusPill.textContent = currentStatus.replace('EXCEPTION_', '');
    }

    // Dossier Info
    dossierInfo.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.6rem; font-size: 0.76rem; color: #94A3B8;">
        <div>PO NUMBER: <strong style="color:#FFF;">${scn.poNumber}</strong></div>
        <div>INVOICED TOTAL: <strong style="color:#FFF;">${scn.amount}</strong></div>
        <div>CONFIDENCE: <strong style="color:#00E575;">${confidence}</strong></div>
        <div>VARIANCE: <strong style="color:${discrepancy !== '$0.00' ? '#EF4444' : '#00E575'};">${discrepancy}</strong></div>
      </div>
      <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 0.4rem;">
        CITATIONS: ${scn.citations[0]}
      </div>
    `;

    // Communication draft
    dossierComm.textContent = comm;

    // Render Contextual Action Buttons
    renderActionButtons(scn, currentStatus, actionType);
  }

  function renderActionButtons(scn, status, actionType) {
    if (!actionButtons) return;
    actionButtons.innerHTML = '';

    // If auto-approved or perfect match: Can disburse payment
    if (status === 'PERFECT_MATCH' || actionType === 'AUTO_APPROVE') {
      const achBtn = document.createElement('button');
      achBtn.className = 'btn-hitl btn-hitl-pay';
      achBtn.innerHTML = `⚡ DISBURSE VIA ACH NACHA`;
      achBtn.addEventListener('click', () => executePayment(scn, 'ACH'));
      actionButtons.appendChild(achBtn);

      const isoBtn = document.createElement('button');
      isoBtn.className = 'btn-hitl btn-hitl-pay';
      isoBtn.innerHTML = `🌐 DISBURSE VIA ISO 20022 XML`;
      isoBtn.addEventListener('click', () => executePayment(scn, 'ISO20022'));
      actionButtons.appendChild(isoBtn);
    } 
    // If rate variance: Can transmit dispute notice
    else if (status === 'EXCEPTION_RATE_VARIANCE') {
      const disputeBtn = document.createElement('button');
      disputeBtn.className = 'btn-hitl btn-hitl-dispute';
      disputeBtn.innerHTML = `✉ TRANSMIT FORMAL DISPUTE NOTICE`;
      disputeBtn.addEventListener('click', () => dispatchDispute(scn));
      actionButtons.appendChild(disputeBtn);
    } 
    // If missing GR: Can trigger PM Sign-Off
    else if (status === 'EXCEPTION_MISSING_GR') {
      const grBtn = document.createElement('button');
      grBtn.className = 'btn-hitl btn-hitl-gr';
      grBtn.innerHTML = `✍ PM ACTION: SIGN OFF & CREATE GOODS RECEIPT`;
      grBtn.addEventListener('click', () => approveGoodsReceipt(scn));
      actionButtons.appendChild(grBtn);
    }
  }

  async function executePayment(scn, rail) {
    sfx.click();
    appendTerminalLog(`> INITIATING PAYMENT DISBURSEMENT VIA ${rail} RAIL...`, 'log-highlight');

    try {
      const res = await fetch('/api/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: scn.invoiceId,
          rail: rail,
          authorized_by: 'AP_SUPERVISOR_HITL',
          force_override: true
        })
      });
      const data = await res.json();

      if (data.success) {
        appendTerminalLog(`>> SETTLEMENT CLEARED: Ref ${data.payment_ref} | Trace ${data.trace_number}`, 'log-highlight');
        appendTerminalLog(`>> ${rail === 'ACH' ? 'NACHA 94-column file' : 'ISO 20022 pain.001 XML'} generated and persisted to database ledger.`, 'log-highlight');
        
        ACTIVE_DISBURSEMENT = data.disbursement || data;
        renderSettlementCard(ACTIVE_DISBURSEMENT, rail);
        
        dossierStatusPill.className = 'dossier-status-pill status-success';
        dossierStatusPill.textContent = 'PAID / CLEARED';
        actionButtons.innerHTML = '';
        if (window.refreshLiveLedger) window.refreshLiveLedger();
      } else {
        appendTerminalLog(`>> PAYMENT FAILED: ${data.message || 'Error processing payment'}`, 'log-error');
      }
    } catch (e) {
      appendTerminalLog(`>> NETWORK ERROR: ${e.message}`, 'log-error');
    }
  }

  async function dispatchDispute(scn) {
    sfx.click();
    appendTerminalLog(`> TRANSMITTING FORMAL DISPUTE MEMO TO VENDOR AP...`, 'log-warn');

    try {
      const res = await fetch('/api/action/dispute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: scn.invoiceId,
          reason: 'Contractual SOW Rate Variance (+$25/hr)',
          memo: scn.communication
        })
      });
      const data = await res.json();

      if (data.success) {
        appendTerminalLog(`>> DISPUTE MEMO TRANSMITTED: Notice ID #${data.dispute_id}. Payment frozen pending reissue.`, 'log-warn');
        dossierStatusPill.className = 'dossier-status-pill status-danger';
        dossierStatusPill.textContent = 'DISPUTE TRANSMITTED';
        actionButtons.innerHTML = `<span style="font-family:var(--font-mono);font-size:0.72rem;color:#EF4444;">✓ FORMAL NOTICE TRANSMITTED TO VENDOR</span>`;
        if (window.refreshLiveLedger) window.refreshLiveLedger();
      }
    } catch (e) {
      appendTerminalLog(`>> ERROR DISPATCHING DISPUTE: ${e.message}`, 'log-error');
    }
  }

  async function approveGoodsReceipt(scn) {
    sfx.click();
    appendTerminalLog(`> PM SIGN-OFF RECEIVED: Creating Goods/Services Receipt in SAP S/4HANA...`, 'log-highlight');

    try {
      const res = await fetch('/api/action/approve-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: scn.invoiceId,
          po_number: scn.poNumber,
          po_line_num: 30,
          delivered_qty: 60.0,
          approved_by: "David Ross (IBM Project Manager)"
        })
      });
      const data = await res.json();

      if (data.success) {
        appendTerminalLog(`>> RECEIPT CREATED: ${data.receipt_id} recorded in SAP ledger.`, 'log-highlight');
        appendTerminalLog(`>> RE-EVALUATING 3-WAY MATCH: Transitioned to PERFECT_MATCH (100% confidence)!`, 'log-highlight');

        // Update UI
        dossierStatusPill.className = 'dossier-status-pill status-success';
        dossierStatusPill.textContent = 'AUTO_APPROVE';

        // Re-render action buttons to allow payment
        renderActionButtons(scn, 'PERFECT_MATCH', 'AUTO_APPROVE');
        if (window.refreshLiveLedger) window.refreshLiveLedger();
      }
    } catch (e) {
      appendTerminalLog(`>> ERROR APPROVING RECEIPT: ${e.message}`, 'log-error');
    }
  }

  async function checkExistingPayment(invoiceId) {
    try {
      const res = await fetch(`/api/invoices/${invoiceId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.disbursement && data.disbursement.status === 'CLEARED') {
          ACTIVE_DISBURSEMENT = data.disbursement;
          renderSettlementCard(data.disbursement, data.disbursement.rail);
          dossierStatusPill.className = 'dossier-status-pill status-success';
          dossierStatusPill.textContent = 'PAID / CLEARED';
          if (actionButtons) actionButtons.innerHTML = '';
        }
      }
    } catch (e) {
      // Silent
    }
  }

  function renderSettlementCard(disb, rail) {
    if (!settlementCard) return;
    settlementCard.style.display = 'block';

    const railTag = document.getElementById('settlementRailTag');
    if (railTag) railTag.textContent = rail === 'ACH' ? 'ACH NACHA (94-COL)' : 'ISO 20022 XML';

    const grid = document.getElementById('settlementDetailsGrid');
    if (grid) {
      grid.innerHTML = `
        <div>PAYMENT REF: <strong style="color:#FFF;">${disb.payment_ref}</strong></div>
        <div>TRACE NUMBER: <strong style="color:#FFF;">${disb.trace_number}</strong></div>
        <div>STATUS: <strong style="color:#00E575;">${disb.status}</strong></div>
        <div>TIMESTAMP: <strong style="color:#94A3B8;">${disb.disbursed_at ? disb.disbursed_at.split('T')[0] : 'TODAY'}</strong></div>
      `;
    }

    // Attach click events for download/view
    const viewBtn = document.getElementById('btnViewPayload');
    const dlAchBtn = document.getElementById('btnDownloadAch');
    const dlXmlBtn = document.getElementById('btnDownloadXml');

    if (viewBtn) {
      viewBtn.onclick = () => openPayloadModal(ACTIVE_INVOICE_ID, disb);
    }
    if (dlAchBtn) {
      dlAchBtn.onclick = () => window.open(`/api/payments/${ACTIVE_INVOICE_ID}/payload?format=ach`, '_blank');
    }
    if (dlXmlBtn) {
      dlXmlBtn.onclick = () => window.open(`/api/payments/${ACTIVE_INVOICE_ID}/payload?format=xml`, '_blank');
    }
  }

  function appendTerminalLog(text, className = '') {
    const div = document.createElement('div');
    div.className = `log-line ${className}`;
    div.textContent = text;
    logStream.appendChild(div);
    logStream.scrollTop = logStream.scrollHeight;
  }
}

// Subtab Switcher: Log Telemetry vs Gemini Reasoning
function initGeminiSubtabs() {
  const tabTelemetry = document.getElementById('tabTelemetry');
  const tabGemini = document.getElementById('tabGeminiReasoning');
  const logStream = document.getElementById('terminalLogStream');
  const geminiPane = document.getElementById('geminiReasoningPane');

  if (!tabTelemetry || !tabGemini || !logStream || !geminiPane) return;

  tabTelemetry.addEventListener('click', () => {
    tabTelemetry.classList.add('active');
    tabGemini.classList.remove('active');
    logStream.style.display = 'block';
    geminiPane.classList.remove('active');
    sfx.click();
  });

  tabGemini.addEventListener('click', () => {
    tabGemini.classList.add('active');
    tabTelemetry.classList.remove('active');
    logStream.style.display = 'none';
    geminiPane.classList.add('active');
    sfx.click();
  });
}

function renderGeminiReasoning(analysis) {
  const pane = document.getElementById('geminiReasoningPane');
  if (!pane || !analysis) return;

  let citationsHtml = '';
  if (analysis.contract_citations) {
    citationsHtml = analysis.contract_citations.map(c => `<span class="cot-citation-tag">§ ${c}</span>`).join('');
  }

  let stepsHtml = '';
  if (analysis.chain_of_thought) {
    stepsHtml = analysis.chain_of_thought.map(step => `<div class="cot-step-item">${step}</div>`).join('');
  }

  pane.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.75rem; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 0.4rem;">
      <span style="font-weight:700; color:#00E575;">✨ ${analysis.model_used.toUpperCase()} REASONING</span>
      <span style="font-size:0.68rem; color:#94A3B8;">${analysis.engine || 'Active Reasoner'}</span>
    </div>
    
    <div class="cot-summary-box">
      <strong>EXECUTIVE SUMMARY:</strong><br>
      ${analysis.executive_summary}
    </div>

    <div style="font-size:0.72rem; color:#94A3B8; margin-bottom: 0.4rem;">
      >> MULTI-STEP CHAIN-OF-THOUGHT INFERENCE:
    </div>
    <div style="margin-bottom: 0.85rem;">
      ${stepsHtml}
    </div>

    <div style="font-size:0.72rem; color:#94A3B8; margin-bottom: 0.3rem;">
      >> CONTRACT & POLICY CITATIONS:
    </div>
    <div>
      ${citationsHtml}
    </div>
  `;
}

// Modal Handlers for Inspecting NACHA and ISO 20022 Payloads
function initModalHandlers() {
  const backdrop = document.getElementById('payloadModalBackdrop');
  const closeBtn = document.getElementById('btnModalClose');
  const tabNacha = document.getElementById('tabNacha');
  const tabIso = document.getElementById('tabIso');
  const copyBtn = document.getElementById('btnModalCopy');
  const dlBtn = document.getElementById('btnModalDownload');
  const codeBox = document.getElementById('modalPayloadContent');

  if (!backdrop || !closeBtn) return;

  let currentTab = 'nacha';

  closeBtn.addEventListener('click', () => {
    backdrop.style.display = 'none';
    sfx.click();
  });

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      backdrop.style.display = 'none';
    }
  });

  tabNacha.addEventListener('click', () => {
    currentTab = 'nacha';
    tabNacha.classList.add('active');
    tabIso.classList.remove('active');
    updateModalContent();
    sfx.click();
  });

  tabIso.addEventListener('click', () => {
    currentTab = 'iso';
    tabIso.classList.add('active');
    tabNacha.classList.remove('active');
    updateModalContent();
    sfx.click();
  });

  copyBtn.addEventListener('click', () => {
    if (codeBox) {
      navigator.clipboard.writeText(codeBox.textContent).then(() => {
        copyBtn.textContent = 'COPIED!';
        sfx.click();
        setTimeout(() => copyBtn.textContent = 'COPY TO CLIPBOARD', 2000);
      });
    }
  });

  dlBtn.addEventListener('click', () => {
    const fmt = currentTab === 'nacha' ? 'ach' : 'xml';
    window.open(`/api/payments/${ACTIVE_INVOICE_ID}/payload?format=${fmt}`, '_blank');
    sfx.click();
  });

  function updateModalContent() {
    if (!ACTIVE_DISBURSEMENT) return;
    if (currentTab === 'nacha') {
      codeBox.textContent = ACTIVE_DISBURSEMENT.nacha_payload || "NACHA file not generated.";
    } else {
      codeBox.textContent = ACTIVE_DISBURSEMENT.iso20022_xml || "ISO 20022 XML not generated.";
    }
  }
}

function openPayloadModal(invoiceId, disb) {
  const backdrop = document.getElementById('payloadModalBackdrop');
  const codeBox = document.getElementById('modalPayloadContent');
  const modalTitle = document.getElementById('modalTitle');
  if (!backdrop || !codeBox) return;

  ACTIVE_DISBURSEMENT = disb;
  if (modalTitle) {
    modalTitle.textContent = `SETTLEMENT PAYLOAD // ${invoiceId} [${disb.payment_ref}]`;
  }

  codeBox.textContent = disb.nacha_payload || disb.iso20022_xml || "No payload found.";
  backdrop.style.display = 'flex';
  sfx.click();
}

// Gemini Configuration Modal
function initGeminiConfigModal() {
  const btnOpen = document.getElementById('btnGeminiConfig');
  const backdrop = document.getElementById('geminiKeyModalBackdrop');
  const btnClose = document.getElementById('btnGeminiModalClose');
  const btnSave = document.getElementById('btnSaveGeminiKey');
  const btnDefault = document.getElementById('btnTestGeminiDefault');
  const inputKey = document.getElementById('inputGeminiApiKey');
  const statusMsg = document.getElementById('geminiKeyStatusMsg');

  if (!btnOpen || !backdrop || !btnClose) return;

  btnOpen.addEventListener('click', () => {
    backdrop.style.display = 'flex';
    sfx.click();
  });

  btnClose.addEventListener('click', () => {
    backdrop.style.display = 'none';
    sfx.click();
  });

  btnDefault.addEventListener('click', () => {
    if (statusMsg) {
      statusMsg.textContent = '✓ Using Built-In Gemini 2.5 Flash Autonomous Engine.';
      statusMsg.style.color = '#00E575';
    }
    sfx.click();
  });

  btnSave.addEventListener('click', async () => {
    const key = inputKey.value.trim();
    if (!key) {
      if (statusMsg) {
        statusMsg.textContent = 'Please enter an API key or use built-in engine.';
        statusMsg.style.color = '#EF4444';
      }
      return;
    }

    try {
      const res = await fetch('/api/settings/gemini-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: key })
      });
      const data = await res.json();
      if (data.success) {
        statusMsg.textContent = '✓ Gemini 2.5 Flash Cloud Inference Activated!';
        statusMsg.style.color = '#00E575';
        btnOpen.textContent = '✨ GEMINI 2.5 (LIVE CLOUD)';
        sfx.click();
        setTimeout(() => { backdrop.style.display = 'none'; }, 1200);
      }
    } catch (e) {
      statusMsg.textContent = 'Error saving key.';
      statusMsg.style.color = '#EF4444';
    }
  });
}

// Custom Invoice Modal
function initCustomInvoiceModal() {
  const btnOpen = document.getElementById('btnOpenCustomInvoice');
  const backdrop = document.getElementById('customInvoiceModalBackdrop');
  const btnClose = document.getElementById('btnCustomModalClose');
  const btnCancel = document.getElementById('btnCustCancel');
  const btnSubmit = document.getElementById('btnSubmitCustomInvoice');

  const inVendor = document.getElementById('inputCustVendor');
  const inPo = document.getElementById('inputCustPo');
  const inRole = document.getElementById('inputCustRole');
  const inRate = document.getElementById('inputCustRate');
  const inHours = document.getElementById('inputCustHours');
  const inTotal = document.getElementById('inputCustTotal');

  if (!btnOpen || !backdrop) return;

  function updateTotal() {
    const rate = parseFloat(inRate.value) || 0;
    const hours = parseFloat(inHours.value) || 0;
    inTotal.value = (rate * hours).toFixed(2);
  }

  inRate.addEventListener('input', updateTotal);
  inHours.addEventListener('input', updateTotal);

  btnOpen.addEventListener('click', () => {
    backdrop.style.display = 'flex';
    sfx.click();
  });

  const closeModal = () => {
    backdrop.style.display = 'none';
    sfx.click();
  };

  btnClose.addEventListener('click', closeModal);
  btnCancel.addEventListener('click', closeModal);

  btnSubmit.addEventListener('click', async () => {
    sfx.click();
    const rate = parseFloat(inRate.value) || 170.0;
    const hours = parseFloat(inHours.value) || 50.0;
    const total = rate * hours;

    const payload = {
      vendor_name: inVendor.value.trim() || "Cognitive Platform Solutions LLC",
      po_number: inPo.value.trim() || "PO-45009812",
      role_title: inRole.value.trim() || "Senior Infrastructure Consultant Tier 1",
      unit_price: rate,
      quantity: hours,
      total_amount: total
    };

    closeModal();

    // Stream to terminal
    const logStream = document.getElementById('terminalLogStream');
    const dossierTitle = document.getElementById('dossierTitle');
    const dossierStatusPill = document.getElementById('dossierStatusPill');
    const dossierInfo = document.getElementById('dossierInfo');
    const dossierComm = document.getElementById('dossierCommunication');
    const actionButtons = document.getElementById('dossierActionButtons');
    const settlementCard = document.getElementById('settlementCard');

    if (settlementCard) settlementCard.style.display = 'none';
    logStream.innerHTML = `<div class="log-line log-highlight">> INGESTING CUSTOM INVOICE FOR ${payload.vendor_name}...</div>`;

    try {
      const res = await fetch('/api/invoices/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        const inv = data.invoice;
        const match = data.matching_result;
        ACTIVE_INVOICE_ID = inv.invoice_id;
        ACTIVE_GEMINI_ANALYSIS = data.gemini_analysis;
        if (window.refreshLiveLedger) window.refreshLiveLedger();

        // Render Gemini reasoning
        renderGeminiReasoning(ACTIVE_GEMINI_ANALYSIS);

        // Stream custom logs
        const logs = [
          `>> Ingested ${inv.invoice_id} | Invoiced: $${inv.total_amount.toFixed(2)}`,
          `>> Normalizer: Parsed role "${payload.role_title}" at $${rate}/hr across ${hours}h`,
          `>> Contract RAG: Grounded against SOW-IBM-2025-09 rate card caps`,
          `>> SAP ERP: Checked line commitment and remaining balance on ${payload.po_number}`,
          `>> Gemini 2.5 Flash: ${ACTIVE_GEMINI_ANALYSIS.executive_summary}`
        ];

        logs.forEach((log, idx) => {
          setTimeout(() => {
            const div = document.createElement('div');
            div.className = 'log-line log-highlight';
            div.textContent = log;
            logStream.appendChild(div);
            logStream.scrollTop = logStream.scrollHeight;
            sfx.click();

            if (idx === logs.length - 1) {
              // Update dossier
              dossierTitle.textContent = `${inv.invoice_id} // ${inv.vendor_name}`;
              dossierStatusPill.className = 'dossier-status-pill';
              if (match.overall_status === 'PERFECT_MATCH') {
                dossierStatusPill.classList.add('status-success');
                dossierStatusPill.textContent = 'AUTO_APPROVE';
              } else {
                dossierStatusPill.classList.add('status-warning');
                dossierStatusPill.textContent = match.overall_status.replace('EXCEPTION_', '');
              }

              dossierInfo.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.6rem; font-size: 0.76rem; color: #94A3B8;">
                  <div>PO NUMBER: <strong style="color:#FFF;">${inv.po_number}</strong></div>
                  <div>INVOICED TOTAL: <strong style="color:#FFF;">$${inv.total_amount.toFixed(2)}</strong></div>
                  <div>CONFIDENCE: <strong style="color:#00E575;">${(match.confidence_score * 100).toFixed(1)}%</strong></div>
                  <div>VARIANCE: <strong style="color:${match.discrepancy_amount > 0 ? '#EF4444' : '#00E575'};">$${match.discrepancy_amount.toFixed(2)}</strong></div>
                </div>
                <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 0.4rem;">
                  AI MODEL: ${ACTIVE_GEMINI_ANALYSIS.model_used} (${ACTIVE_GEMINI_ANALYSIS.engine})
                </div>
              `;

              dossierComm.textContent = match.resolution_action.generated_communication;

              // Render action buttons
              actionButtons.innerHTML = '';
              if (match.overall_status === 'PERFECT_MATCH') {
                const achBtn = document.createElement('button');
                achBtn.className = 'btn-hitl btn-hitl-pay';
                achBtn.innerHTML = `⚡ DISBURSE VIA ACH NACHA`;
                achBtn.addEventListener('click', () => {
                  fetch('/api/pay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ invoice_id: inv.invoice_id, rail: 'ACH', force_override: true })
                  }).then(r => r.json()).then(pData => {
                    if (pData.success) {
                      dossierStatusPill.className = 'dossier-status-pill status-success';
                      dossierStatusPill.textContent = 'PAID / CLEARED';
                      actionButtons.innerHTML = '';
                      if (window.refreshLiveLedger) window.refreshLiveLedger();
                    }
                  });
                });
                actionButtons.appendChild(achBtn);
              }
            }
          }, (idx + 1) * 300);
        });
      }
    } catch (e) {
      logStream.innerHTML += `<div class="log-line log-error">> Error processing custom invoice: ${e.message}</div>`;
    }
  });
}

// SQLite Live AP Audit Ledger Component
function initLiveLedger() {
  const tableBody = document.getElementById('ledgerTableBody');
  const btnRefresh = document.getElementById('btnRefreshLedger');

  if (!tableBody) return;

  async function fetchAndRenderLedger() {
    try {
      const res = await fetch('/api/invoices');
      if (!res.ok) return;
      const data = await res.json();
      const invoices = data.invoices || [];

      if (invoices.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding: 2rem; color: #64748B;">NO INVOICES RECORDED IN SQLITE AP_FINANCE.DB</td></tr>`;
        return;
      }

      tableBody.innerHTML = invoices.map(inv => {
        let statusPillClass = 'status-warning';
        let statusText = inv.match_status.replace('EXCEPTION_', '');
        if (inv.match_status === 'PERFECT_MATCH') {
          statusPillClass = 'status-success';
          statusText = 'PERFECT MATCH';
        } else if (inv.match_status === 'EXCEPTION_RATE_VARIANCE') {
          statusPillClass = 'status-danger';
          statusText = 'RATE VARIANCE';
        }

        const isCleared = inv.payment_status === 'CLEARED';
        const paymentBadge = isCleared
          ? `<span style="color: #00E575; font-weight: 700; display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width:6px;height:6px;border-radius:50%;background:#00E575;display:inline-block;"></span>CLEARED</span>`
          : `<span style="color: #94A3B8; display: inline-flex; align-items: center; gap: 0.35rem;"><span style="width:6px;height:6px;border-radius:50%;background:#64748B;display:inline-block;"></span>UNPAID</span>`;

        let railBadge = '<span style="color:#64748B;">—</span>';
        if (inv.rail === 'ACH') {
          railBadge = `<span style="background: rgba(0,229,117,0.12); color: #00E575; border: 1px solid rgba(0,229,117,0.3); padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.65rem;">ACH NACHA</span>`;
        } else if (inv.rail === 'ISO20022') {
          railBadge = `<span style="background: rgba(59,130,246,0.12); color: #60A5FA; border: 1px solid rgba(59,130,246,0.3); padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.65rem;">ISO 20022</span>`;
        }

        const discAmount = parseFloat(String(inv.discrepancy).replace('$', '').replace(',', '')) || 0;
        const discColor = discAmount > 0 ? '#EF4444' : '#00E575';

        return `
          <tr>
            <td><strong style="color: #FFF;">${inv.invoice_id}</strong></td>
            <td style="color: #E2E8F0;">${inv.vendor_name}</td>
            <td style="color: #94A3B8;">${inv.po_number}</td>
            <td style="font-weight: 600; color: #FFF;">$${Number(inv.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td><span class="dossier-status-pill ${statusPillClass}" style="font-size: 0.65rem; padding: 0.2rem 0.5rem;">${statusText}</span></td>
            <td style="color: ${discColor}; font-weight: 600;">${inv.discrepancy}</td>
            <td style="font-size: 0.68rem; color: #94A3B8;">${inv.action_type}</td>
            <td>${paymentBadge}</td>
            <td>${railBadge}</td>
            <td style="font-size: 0.68rem; color: #64748B;">${inv.payment_ref || '—'}</td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.warn('Failed to load SQLite ledger:', e);
    }
  }

  window.refreshLiveLedger = fetchAndRenderLedger;

  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      sfx.click();
      fetchAndRenderLedger();
    });
  }

  fetchAndRenderLedger();
}

// Helper to convert backend Invoice + MatchingResult into interactive Scenario object
function convertMatchToScenario(inv, matchResult) {
  const isApproved = matchResult.overall_status === 'PERFECT_MATCH' || matchResult.resolution_action?.action_type === 'AUTO_APPROVE';
  const discrepancy = matchResult.discrepancy_amount || 0;
  return {
    id: `syn_${inv.invoice_id}`,
    code: inv.invoice_id,
    title: `${inv.vendor_name} (${matchResult.overall_status.replace(/_/g, ' ')})`,
    subtitle: `${inv.line_items[0]?.description || 'Service Consulting'} ($${Number(inv.total_amount).toLocaleString()})`,
    category: 'Dynamic Synthetic / Ingestion',
    status: matchResult.overall_status,
    actionType: matchResult.resolution_action?.action_type || 'ESCALATE_TO_HUMAN',
    badgeColor: isApproved ? 'success' : (discrepancy > 0 ? 'danger' : 'warning'),
    confidence: `${(matchResult.confidence_score * 100).toFixed(1)}%`,
    invoiceId: inv.invoice_id,
    vendorName: inv.vendor_name,
    vendorId: inv.vendor_id,
    poNumber: inv.po_number,
    amount: `$${Number(inv.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
    allowable: `$${Number(matchResult.allowable_amount || inv.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
    discrepancy: `$${Number(discrepancy).toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
    description: matchResult.resolution_action?.summary || inv.notes || 'Autonomous 3-Way Match Verification.',
    lineItems: (inv.line_items || []).map((it, idx) => ({
      line: String(idx + 1).padStart(2, '0'),
      desc: it.description,
      qty: String(it.quantity),
      unit: it.unit,
      billedRate: `$${Number(it.unit_price).toFixed(2)}`,
      contractMax: it.unit_price > 0 ? `$${Number(it.unit_price).toFixed(2)}` : 'N/A',
      variance: `$${Number(matchResult.discrepancy_amount || 0).toFixed(2)}`,
      grStatus: matchResult.overall_status === 'EXCEPTION_MISSING_GR' ? 'MISSING (SAP PO Line Hold)' : 'VERIFIED',
      status: matchResult.overall_status
    })),
    citations: matchResult.resolution_action?.citations || [
      'SOW-IBM-2025-09 Master Services Agreement Clause Schedule A',
      `SAP S/4HANA PO ${inv.po_number}`
    ],
    communication: matchResult.resolution_action?.generated_communication || `SYSTEM AP AUDIT MEMORANDUM\nInvoice: ${inv.invoice_id}\nStatus: ${matchResult.overall_status}`,
    agentLogs: [
      `[09:30:01] NormalizerAgent: Ingested invoice ${inv.invoice_id} from '${inv.vendor_name}'.`,
      `[09:30:02] ContractValidatorAgent (RAG): Grounded against SOW-IBM-2025-09. Match Status: ${matchResult.overall_status}.`,
      `[09:30:03] ERPAgent (SAP S/4HANA): Checked PO ${inv.po_number}. Line status verified.`,
      `[09:30:04] ResolutionAgent: Confidence score ${(matchResult.confidence_score).toFixed(2)}. ${matchResult.resolution_action?.summary || 'Resolved.'}`
    ]
  };
}

// Data Lab: File Upload (JSON/CSV) & Synthetic Data Generator Modal
function initDataLabModal() {
  const btnOpen = document.getElementById('btnOpenDataLab');
  const backdrop = document.getElementById('dataLabModalBackdrop');
  const btnClose = document.getElementById('btnDataLabModalClose');
  const btnCancel = document.getElementById('btnDataLabCancel');
  const btnExecute = document.getElementById('btnDataLabExecute');

  const tabBtnUpload = document.getElementById('tabBtnUpload');
  const tabBtnSynthetic = document.getElementById('tabBtnSynthetic');
  const panelUpload = document.getElementById('panelUpload');
  const panelSynthetic = document.getElementById('panelSynthetic');

  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('fileInvoiceInput');
  const textPayload = document.getElementById('textInvoicePayload');
  const previewBox = document.getElementById('uploadPreviewBox');

  const btnJsonTpl = document.getElementById('btnDownloadJsonTemplate');
  const btnCsvTpl = document.getElementById('btnDownloadCsvTemplate');

  const selectPreset = document.getElementById('selectSyntheticPreset');
  const rangeCount = document.getElementById('rangeSyntheticCount');
  const labelCount = document.getElementById('labelSyntheticCount');
  const specTitle = document.getElementById('specTitle');
  const specDesc = document.getElementById('specDesc');
  const synthMsg = document.getElementById('syntheticStatusMsg');

  if (!btnOpen || !backdrop) return;

  let activeTab = 'upload'; // 'upload' | 'synthetic'
  let cachedSpecs = [];

  function openModal() {
    backdrop.style.display = 'flex';
    if (synthMsg) synthMsg.textContent = '';
    fetchSpecs();
  }

  function closeModal() {
    backdrop.style.display = 'none';
  }

  btnOpen.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);
  if (btnCancel) btnCancel.addEventListener('click', closeModal);
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  });

  // Tab switching
  if (tabBtnUpload && tabBtnSynthetic) {
    tabBtnUpload.addEventListener('click', () => {
      activeTab = 'upload';
      tabBtnUpload.classList.add('active');
      tabBtnSynthetic.classList.remove('active');
      panelUpload.style.display = 'block';
      panelSynthetic.style.display = 'none';
      if (btnExecute) btnExecute.textContent = '⚡ INGEST & RUN MATCH';
    });

    tabBtnSynthetic.addEventListener('click', () => {
      activeTab = 'synthetic';
      tabBtnSynthetic.classList.add('active');
      tabBtnUpload.classList.remove('active');
      panelSynthetic.style.display = 'block';
      panelUpload.style.display = 'none';
      if (btnExecute) btnExecute.textContent = '⚡ GENERATE & INGEST BATCH';
    });
  }

  // Drag and Drop
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
      }
    });
  }

  function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      if (textPayload) textPayload.value = content;
      updatePreview(file.name, content);
    };
    reader.readAsText(file);
  }

  function updatePreview(filename, content) {
    if (!previewBox) return;
    previewBox.style.display = 'block';
    const isJson = content.trim().startsWith('{') || content.trim().startsWith('[');
    if (isJson) {
      try {
        const parsed = JSON.parse(content);
        const count = Array.isArray(parsed) ? parsed.length : (parsed.invoices ? parsed.invoices.length : 1);
        previewBox.innerHTML = `✓ Loaded <strong>${filename || 'JSON'}</strong>: Detected <strong>${count}</strong> invoice record(s) ready for ingestion.`;
      } catch (e) {
        previewBox.innerHTML = `⚠ Loaded <strong>${filename}</strong>: Warning: JSON format syntax error.`;
      }
    } else {
      const lines = content.trim().split('\n').filter(Boolean);
      const rows = Math.max(0, lines.length - 1);
      previewBox.innerHTML = `✓ Loaded <strong>${filename || 'CSV'}</strong>: Detected <strong>${rows}</strong> line item row(s) ready for parsing.`;
    }
  }

  if (textPayload) {
    textPayload.addEventListener('input', () => {
      if (textPayload.value.trim().length > 10) {
        updatePreview('Pasted Text', textPayload.value);
      } else if (previewBox) {
        previewBox.style.display = 'none';
      }
    });
  }

  // Download Templates
  if (btnJsonTpl) {
    btnJsonTpl.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/data/template?format=json');
        const text = await res.text();
        if (textPayload) textPayload.value = text;
        updatePreview('invoice_template.json', text);
      } catch (e) {
        console.error(e);
      }
    });
  }

  if (btnCsvTpl) {
    btnCsvTpl.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/data/template?format=csv');
        const text = await res.text();
        if (textPayload) textPayload.value = text;
        updatePreview('invoice_template.csv', text);
      } catch (e) {
        console.error(e);
      }
    });
  }

  // Range count slider
  if (rangeCount && labelCount) {
    rangeCount.addEventListener('input', () => {
      labelCount.textContent = `${rangeCount.value} Invoices`;
    });
  }

  // Fetch specs for synthetic dropdown
  async function fetchSpecs() {
    if (cachedSpecs.length > 0) return;
    try {
      const res = await fetch('/api/data/synthetic-specs');
      if (res.ok) {
        const data = await res.json();
        cachedSpecs = data.specs || [];
      }
    } catch (e) {
      console.warn('Could not fetch specs:', e);
    }
  }

  if (selectPreset) {
    selectPreset.addEventListener('change', () => {
      const val = selectPreset.value;
      if (val === 'ALL') {
        if (specTitle) specTitle.textContent = 'Full Multi-Scenario Enterprise AP Test Suite';
        if (specDesc) specDesc.textContent = 'Generates a balanced batch across clean matches, rate bumps, missing receipts, quantity overruns, and tax tolerances. Each invoice is checked by RAG, SAP, and Gemini Reasoner.';
      } else {
        const found = cachedSpecs.find(s => s.key === val);
        if (found) {
          if (specTitle) specTitle.textContent = `${found.code}: ${found.title}`;
          if (specDesc) specDesc.textContent = `${found.description} (Expected: ${found.expected_status})`;
        }
      }
    });
  }

  // Execute Action
  if (btnExecute) {
    btnExecute.addEventListener('click', async () => {
      sfx.click();
      btnExecute.disabled = true;
      const origText = btnExecute.textContent;
      btnExecute.textContent = 'PROCESSING...';

      try {
        if (activeTab === 'upload') {
          const raw = textPayload.value.trim();
          if (!raw) {
            alert('Please upload a file or paste invoice JSON / CSV content first.');
            btnExecute.disabled = false;
            btnExecute.textContent = origText;
            return;
          }

          const res = await fetch('/api/data/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: raw })
          });
          const data = await res.json();
          if (!res.ok) {
            alert(`Ingestion failed: ${data.error || 'Invalid payload'}`);
            btnExecute.disabled = false;
            btnExecute.textContent = origText;
            return;
          }

          handleIngestedBatch(data.invoices, data.results);
        } else {
          // Synthetic Generation
          const count = parseInt(rangeCount.value) || 5;
          const preset = selectPreset.value;
          const scenarioKeys = preset === 'ALL' ? null : [preset];

          const res = await fetch('/api/data/generate-synthetic', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ count: count, scenario_keys: scenarioKeys })
          });
          const data = await res.json();
          if (!res.ok) {
            alert(`Generation failed: ${data.error || 'Server error'}`);
            btnExecute.disabled = false;
            btnExecute.textContent = origText;
            return;
          }

          handleIngestedBatch(data.invoices, data.results);
        }
      } catch (e) {
        alert(`Error communicating with backend: ${e.message}`);
      } finally {
        btnExecute.disabled = false;
        btnExecute.textContent = origText;
      }
    });
  }

  function handleIngestedBatch(invoices, results) {
    if (!invoices || invoices.length === 0) return;

    let firstNewScenario = null;
    invoices.forEach((inv, i) => {
      const matchRes = results[i];
      const scn = convertMatchToScenario(inv, matchRes);

      // Check if already in SCENARIOS by invoiceId
      const existingIdx = SCENARIOS.findIndex(s => s.invoiceId === inv.invoice_id);
      if (existingIdx >= 0) {
        SCENARIOS[existingIdx] = scn;
      } else {
        SCENARIOS.push(scn);
      }

      if (!firstNewScenario) firstNewScenario = scn;
    });

    // Re-render buttons in terminal
    if (window.renderScenarioButtons) {
      window.renderScenarioButtons(firstNewScenario.invoiceId);
    }
    // Run scenario
    if (window.runTerminalScenario) {
      window.runTerminalScenario(firstNewScenario);
    }
    // Refresh live ledger table
    if (window.refreshLiveLedger) {
      window.refreshLiveLedger();
    }

    closeModal();
  }
}

