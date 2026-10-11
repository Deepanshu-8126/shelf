// Fleet Studio Command Center - Client Logic
let currentChannel = 2;
let currentMode = "manual";
let activeEventSource = null;

document.addEventListener("DOMContentLoaded", () => {
    setupChannelTabs();
    setupWordCounter();
    fetchRecentVideos();
    fetchSystemStatus();
});

// 1. Channel Selector
function setupChannelTabs() {
    const tabs = document.querySelectorAll(".channel-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentChannel = parseInt(tab.dataset.channel);
            
            // Adjust defaults per channel
            if (currentChannel === 1) {
                document.getElementById("input-title").value = "Entitled Karen Tries to Steal My Dog";
                document.getElementById("input-script").value = "So I was walking my German Shepherd at the park when this random woman walks up, grabs his leash, and tells her kid: 'Look honey, mommy found you a puppy!' I thought she was joking... until she called the police on ME.";
                document.getElementById("select-lang-manual").value = "en";
            } else if (currentChannel === 2) {
                document.getElementById("input-title").value = "The FBI 4-Second Silence Rule";
                document.getElementById("input-script").value = "Four seconds of absolute silence can break any human mind. When federal agents interrogate a suspect, they never argue. They just stare.";
                document.getElementById("select-lang-manual").value = "en";
            } else if (currentChannel === 3) {
                document.getElementById("input-title").value = "अगर आज रात चाँद गायब हो जाए?";
                document.getElementById("input-script").value = "अगर आज रात अचानक चाँद गायब हो जाए, तो सबसे पहले समंदर में 300 फीट ऊंची सुनामी उठेगी और किनारे के सारे शहर डूब जाएंगे। चाँद धरती की स्पीड को रोकता है, उसके हटते ही हमारा 24 घंटे का दिन सिर्फ 6 घंटे का रह जाएगा!";
                document.getElementById("select-lang-manual").value = "hi_swara";
            }
            updateWordCount();
            appendLog(`[CHANNEL] Switched to Channel ${currentChannel}`);
        });
    });
}

// 2. Mode Switcher
function setMode(mode) {
    currentMode = mode;
    const btnManual = document.getElementById("btn-mode-manual");
    const btnAuto = document.getElementById("btn-mode-auto");
    const manualControls = document.getElementById("manual-controls");
    const autoControls = document.getElementById("autopilot-controls");

    if (mode === "manual") {
        btnManual.classList.add("active");
        btnAuto.classList.remove("active");
        manualControls.style.display = "block";
        autoControls.style.display = "none";
        appendLog(`[MODE] Switched to Manual Script Mode. Type or paste your custom 50-60 word script.`);
    } else {
        btnManual.classList.remove("active");
        btnAuto.classList.add("active");
        manualControls.style.display = "none";
        autoControls.style.display = "block";
        appendLog(`[MODE] Switched to 1-Click AI Autopilot Mode.`);
    }
}

// 3. Word Counter & Timing Calculator
function setupWordCounter() {
    const textarea = document.getElementById("input-script");
    textarea.addEventListener("input", updateWordCount);
    updateWordCount();
}

function updateWordCount() {
    const text = document.getElementById("input-script").value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    const estSec = Math.round(words / 2.7); // ~160 wpm speaking rate
    document.getElementById("word-count").innerText = `${words} words (~${estSec}s audio)`;
}

function updateVol(val) {
    document.getElementById("vol-display").innerText = `${val}%`;
}

async function fetchScriptFromUrl() {
    const urlInput = document.getElementById("input-script-url");
    const url = urlInput ? urlInput.value.trim() : "";
    if (!url) {
        alert("Please paste a valid raw URL or GitHub raw text link.");
        return;
    }
    appendLog(`[GITHUB] Fetching script from ${url}...`);
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const text = await res.text();
        document.getElementById("input-script").value = text.trim();
        updateWordCount();
        appendLog(`[GITHUB] Script successfully imported (${text.trim().length} chars)!`);
    } catch (e) {
        appendLog(`[GITHUB ERROR] Could not load script: ${e.message}`, "error");
        alert("Could not load script directly in browser (CORS). The backend will fetch it directly on render.");
    }
}

// 4. Trigger Render Action
async function triggerRender() {
    const btn = document.getElementById("render-btn");
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-icon">⏳</span> RENDERING SHORT...`;

    // Reset Progress & Terminal
    updateProgress(5, "INITIALIZING WORKER...", "running");
    document.getElementById("video-preview-container").style.display = "none";

    const scriptUrlInput = document.getElementById("input-script-url");
    const payload = {
        channel: currentChannel,
        mode: currentMode,
        title: document.getElementById("input-title").value.trim(),
        script: document.getElementById("input-script").value.trim(),
        script_url: scriptUrlInput ? scriptUrlInput.value.trim() : "",
        pillar: parseInt(currentMode === "manual" ? document.getElementById("select-pillar-manual").value : document.getElementById("select-pillar-auto").value),
        topic: document.getElementById("input-topic").value.trim(),
        lang: document.getElementById("select-lang-manual").value,
        bg_volume: parseFloat(document.getElementById("input-bgm-volume").value) / 100.0
    };

    try {
        const res = await fetch("/api/render", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.job_id) {
            appendLog(`[JOB QUEUED] Task ID: ${data.job_id}`);
            startSSE(data.job_id);
        } else {
            appendLog(`[ERROR] Failed to schedule job`, "error");
            btn.disabled = false;
            btn.innerHTML = `<span class="btn-icon">⚡</span> RENDER 100% 4K VIRAL SHORT`;
        }
    } catch (e) {
        appendLog(`[NETWORK ERROR] ${e.message}`, "error");
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-icon">⚡</span> RENDER 100% 4K VIRAL SHORT`;
    }
}

// 5. Real-Time SSE Stream Listener
function startSSE(jobId) {
    if (activeEventSource) {
        activeEventSource.close();
    }

    activeEventSource = new EventSource(`/api/stream/${jobId}`);

    activeEventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            appendLog(`[${data.timestamp}] [${data.step}] ${data.message}`, data.step.toLowerCase());
            
            if (data.progress !== null && data.progress !== undefined) {
                updateProgress(data.progress, data.message);
            }

            if (data.video_url) {
                onVideoCompleted(data.video_url);
            }
        } catch (e) {
            console.error(e);
        }
    };

    activeEventSource.onerror = () => {
        // SSE stream closed or completed
        activeEventSource.close();
        const btn = document.getElementById("render-btn");
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-icon">⚡</span> RENDER 100% 4K VIRAL SHORT`;
    };
}

function updateProgress(percent, label, statusState) {
    document.getElementById("progress-fill").style.width = `${percent}%`;
    document.getElementById("progress-percent").innerText = `${percent}%`;
    document.getElementById("current-step-label").innerText = label;

    const badge = document.getElementById("job-status-badge");
    if (percent === 100) {
        badge.innerText = "COMPLETED";
        badge.className = "status-badge success";
    } else {
        badge.innerText = "RENDERING";
        badge.className = "status-badge running";
    }
}

function onVideoCompleted(videoUrl) {
    const btn = document.getElementById("render-btn");
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-icon">⚡</span> RENDER 100% 4K VIRAL SHORT`;
    
    appendLog(`[DONE] Video ready for streaming: ${videoUrl}`, "success");
    
    // Show Preview Video Player
    const container = document.getElementById("video-preview-container");
    const player = document.getElementById("preview-player");
    const dl = document.getElementById("download-link");

    container.style.display = "block";
    player.src = videoUrl;
    dl.href = videoUrl;
    player.play().catch(() => {});

    // Refresh Gallery
    setTimeout(fetchRecentVideos, 1200);
}

function appendLog(msg, type = "normal") {
    const term = document.getElementById("terminal-output");
    const div = document.createElement("div");
    div.className = `log-line ${type}`;
    div.innerText = msg;
    term.appendChild(div);
    term.scrollTop = term.scrollHeight;
}

// 6. Recent Videos Gallery
async function fetchRecentVideos() {
    try {
        const res = await fetch("/api/videos");
        const videos = await res.json();
        const gallery = document.getElementById("video-gallery");
        gallery.innerHTML = "";

        if (videos.length === 0) {
            gallery.innerHTML = `<div style="color: #64748b; font-size: 13px; grid-column: 1/-1;">No videos generated yet. Trigger your first Short above!</div>`;
            return;
        }

        videos.slice(0, 8).forEach(v => {
            const card = document.createElement("div");
            card.className = "video-card";
            const chTag = v.channel === 1 ? "CH 1 Reddit" : (v.channel === 2 ? "CH 2 Vox Noir" : "CH 3 Cosmic");
            card.innerHTML = `
                <div class="card-meta-row">
                    <span>${chTag}</span>
                    <span>${v.size_mb} MB</span>
                </div>
                <div class="card-title">${v.name}</div>
                <div style="font-size: 11px; color: #64748b;">${v.modified}</div>
                <div class="card-actions">
                    <button class="card-btn" onclick="playInPreview('${v.url}')">▶️ Play</button>
                    <a class="card-btn" href="${v.url}" download>⬇️ Save</a>
                </div>
            `;
            gallery.appendChild(card);
        });
    } catch (e) {
        console.error("Gallery fetch error:", e);
    }
}

function playInPreview(videoUrl) {
    const container = document.getElementById("video-preview-container");
    const player = document.getElementById("preview-player");
    const dl = document.getElementById("download-link");

    container.style.display = "block";
    player.src = videoUrl;
    dl.href = videoUrl;
    player.scrollIntoView({ behavior: 'smooth' });
    player.play().catch(() => {});
}

async function fetchSystemStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        if (data.keys) {
            document.getElementById("pill-pexels").innerHTML = `<span class="dot"></span> 4K Pexels: <strong>${data.keys.pexels ? 'ONLINE' : 'OFFLINE'}</strong>`;
            document.getElementById("pill-bgm").innerHTML = `<span class="dot"></span> Tuned BGM: <strong>${data.bgm_tracks_count} TRACKS</strong>`;
        }
    } catch (e) {
        console.error("Status fetch error:", e);
    }
}
