/**
 * IBM FINANCIAL SOLUTIONS // FRONTEND ENGINE
 * Interactive Terminal, Scenario Runner, ASCII Toggle, and Mechanical Audio FX
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
    "A> RAG_MATCH\n>> SOW: FOUND\n>> RATE: $170/H\n>> STATUS: OK\n_ ",
    "A> EXCEPTION\n>> TAX: +$8.50\n>> TOLERANCE: OK\n>> APPROVED\n_ ",
    "A> DISPUTE\n>> RATE: $195/H\n>> CAP: $170/H\n>> DRAFT SENT\n_ "
  ];

  let msgIdx = 0;
  setInterval(() => {
    crtText.textContent = messages[msgIdx];
    msgIdx = (msgIdx + 1) % messages.length;
  }, 3200);
}

// Terminal Engine for Scenario Simulation
function initTerminalEngine() {
  const scenarioBtnsContainer = document.getElementById('scenarioPills');
  const logStream = document.getElementById('terminalLogStream');
  const dossierTitle = document.getElementById('dossierTitle');
  const dossierStatusPill = document.getElementById('dossierStatusPill');
  const dossierInfo = document.getElementById('dossierInfo');
  const dossierComm = document.getElementById('dossierCommunication');
  const liveDot = document.getElementById('terminalStatusDot');

  if (!scenarioBtnsContainer || typeof SCENARIOS === 'undefined') return;

  // Render scenario selector buttons
  scenarioBtnsContainer.innerHTML = '';
  SCENARIOS.forEach((scn, idx) => {
    const btn = document.createElement('button');
    btn.className = `scenario-btn ${idx === 0 ? 'active' : ''}`;
    btn.textContent = `[${scn.code}: ${scn.title.split('(')[0].trim()}]`;
    btn.dataset.id = scn.id;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      runScenario(scn);
    });
    scenarioBtnsContainer.appendChild(btn);
  });

  // Automatically execute first scenario on load
  runScenario(SCENARIOS[0]);

  function runScenario(scn) {
    if (liveDot) liveDot.className = 't-dot yellow';

    // Clear logs
    logStream.innerHTML = `<div class="log-line log-highlight">> INITIATING AP 3-WAY MATCHING ON ${scn.invoiceId}...</div>`;

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
          renderDossier(scn);
        }
      }, (i + 1) * 350);
    });
  }

  function renderDossier(scn) {
    dossierTitle.textContent = `${scn.invoiceId} // ${scn.vendorName}`;
    
    // Status pill
    dossierStatusPill.className = 'dossier-status-pill';
    if (scn.status === 'PERFECT_MATCH' || scn.actionType === 'AUTO_APPROVE') {
      dossierStatusPill.classList.add('status-success');
      dossierStatusPill.textContent = scn.actionType;
    } else if (scn.status === 'EXCEPTION_RATE_VARIANCE') {
      dossierStatusPill.classList.add('status-danger');
      dossierStatusPill.textContent = 'RATE DISPUTE DRAFTED';
    } else {
      dossierStatusPill.classList.add('status-warning');
      dossierStatusPill.textContent = scn.status.replace('EXCEPTION_', '');
    }

    // Dossier Info
    dossierInfo.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.6rem; font-size: 0.76rem; color: #94A3B8;">
        <div>PO NUMBER: <strong style="color:#FFF;">${scn.poNumber}</strong></div>
        <div>INVOICED TOTAL: <strong style="color:#FFF;">${scn.amount}</strong></div>
        <div>CONFIDENCE: <strong style="color:#00E575;">${scn.confidence}</strong></div>
        <div>VARIANCE: <strong style="color:${scn.discrepancy !== '$0.00' ? '#EF4444' : '#00E575'};">${scn.discrepancy}</strong></div>
      </div>
      <div style="font-size: 0.72rem; color: #64748B; margin-bottom: 0.4rem;">
        CITATIONS: ${scn.citations[0]}
      </div>
    `;

    // Communication draft
    dossierComm.textContent = scn.communication;
  }
}
