/**
 * YouTube Turbo Studio - Frontend Client Controller
 * Manages live SSE streams, API key validation, YouTube OAuth, generation pipeline, and review studio.
 */

// ── GLOBAL APPLICATION STATE ──
let currentConfig = {};
let currentStatus = {};
let sseSource = null;
let currentTags = [];
let currentChannelId = "the-ai-brief-it";

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initSSE();
    initChannelManager();
    loadSettings();
    loadYouTubeStatus();
    startStatusPolling();
    setupEventListeners();
});

// ── NOTIFICATION TOASTS ──
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : (type === "error" ? "✗" : "ℹ");
    toast.innerHTML = `<span><strong>${icon}</strong> ${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── TAB SWITCHING ──
function initTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.classList.remove("active");
            });

            const activePane = document.getElementById(targetTab);
            if (activePane) activePane.classList.add("active");

            // Refresh specific tab contents on switch
            if (targetTab === "tab-review") loadReviewData();
            if (targetTab === "tab-youtube") loadYouTubeStatus();
            if (targetTab === "tab-api-keys") loadSettings();
        });
    });
}

// ── SSE REAL-TIME LOGS ──
function initSSE() {
    const consoleBox = document.getElementById("console-logs");
    if (!consoleBox) return;

    if (sseSource) sseSource.close();
    sseSource = new EventSource("/api/logs/stream");

    sseSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            const line = document.createElement("div");
            line.className = `log-line log-${data.level || 'info'}`;
            line.innerHTML = `<span class="time">[${data.time}]</span> ${data.msg}`;
            consoleBox.appendChild(line);
            requestAnimationFrame(() => {
                consoleBox.scrollTop = consoleBox.scrollHeight;
            });
        } catch (e) {
            // Heartbeat or raw message
        }
    };

    sseSource.onerror = () => {
        // SSE disconnected, will auto-reconnect
    };
}

// ── STATUS POLLING ──
function startStatusPolling() {
    setInterval(async () => {
        try {
            const resp = await fetch("/api/status");
            const data = await resp.json();
            currentStatus = data;
            updateStatusUI(data);
        } catch (e) {
            // Server offline
        }
    }, 3000);
}

function updateStatusUI(status) {
    const chip = document.getElementById("status-chip");
    const chipDot = document.getElementById("status-dot");
    const chipText = document.getElementById("status-text");

    if (status.running) {
        chipDot.className = "status-dot dot-running";
        chipText.innerText = "Running Pipeline...";
        document.getElementById("btn-generate").disabled = true;
        document.getElementById("btn-stop").style.display = "inline-flex";
    } else if (status.error) {
        chipDot.className = "status-dot dot-error";
        chipText.innerText = "Pipeline Error";
        document.getElementById("btn-generate").disabled = false;
        document.getElementById("btn-stop").style.display = "none";
    } else if (status.stages && status.stages.video === "done") {
        chipDot.className = "status-dot dot-success";
        chipText.innerText = "Video Ready";
        document.getElementById("btn-generate").disabled = false;
        document.getElementById("btn-stop").style.display = "none";
    } else {
        chipDot.className = "status-dot dot-idle";
        chipText.innerText = "Studio Idle";
        document.getElementById("btn-generate").disabled = false;
        document.getElementById("btn-stop").style.display = "none";
    }

    // Update Stage tracker in sidebar
    if (status.stages) {
        for (const [stg, stgState] of Object.entries(status.stages)) {
            const el = document.getElementById(`stage-${stg}`);
            if (el) {
                el.className = `stage-step ${stgState}`;
                const icon = el.querySelector(".stage-step-icon");
                if (icon) {
                    if (stgState === "done") icon.innerText = "✓";
                    else if (stgState === "running") icon.innerText = "⟳";
                    else if (stgState === "error") icon.innerText = "✗";
                    else icon.innerText = "•";
                }
            }
        }
    }

    // Update upload progress
    if (status.uploading) {
        const uploadProgress = document.getElementById("upload-progress-box");
        const uploadPct = document.getElementById("upload-pct-label");
        const uploadBar = document.getElementById("upload-progress-bar");
        if (uploadProgress) uploadProgress.style.display = "block";
        if (uploadPct) uploadPct.innerText = `${status.upload_pct}%`;
        if (uploadBar) uploadBar.style.width = `${status.upload_pct}%`;
    } else {
        const uploadProgress = document.getElementById("upload-progress-box");
        if (uploadProgress && status.upload_pct >= 100) {
            // Keep completed
        } else if (uploadProgress) {
            uploadProgress.style.display = "none";
        }
    }

    // Direct YouTube link
    if (status.yt_url) {
        const ytLinkBox = document.getElementById("yt-published-link");
        if (ytLinkBox) {
            ytLinkBox.style.display = "block";
            ytLinkBox.innerHTML = `🎉 Video Published: <a href="${status.yt_url}" target="_blank" style="color:var(--accent-emerald);">${status.yt_url}</a>`;
        }
    }
}

// ── CHANNEL MANAGEMENT (MULTI-CHANNEL) ──
async function initChannelManager() {
    const selectEl = document.getElementById("active-channel-select");
    if (!selectEl) return;

    try {
        const resp = await fetch("/api/channels");
        const data = await resp.json();
        if (data.ok && data.channels) {
            selectEl.innerHTML = "";
            data.channels.forEach(ch => {
                const opt = document.createElement("option");
                opt.value = ch.channel_id;
                opt.textContent = ch.name;
                if (ch.is_active || ch.channel_id === data.active_channel_id) {
                    opt.selected = true;
                    currentChannelId = ch.channel_id;
                }
                selectEl.appendChild(opt);
            });
            // Update UI based on active channel
            const activeCh = data.channels.find(c => c.channel_id === currentChannelId);
            if (activeCh) {
                updateChannelUI(activeCh);
                await loadEligibleParents(activeCh.channel_id);
            }
        }
    } catch (e) {
        console.error("Error loading channels:", e);
    }

    selectEl.addEventListener("change", () => {
        switchChannel(selectEl.value);
    });
}

async function loadEligibleParents(channelId) {
    try {
        const cid = channelId || currentChannelId;
        const resp = await fetch(`/api/content-modes/eligible-parents?channel_id=${encodeURIComponent(cid)}`);
        const data = await resp.json();
        const parents = data.eligible_parents || [];
        const linkedRadio = document.getElementById("mode-shorts-linked");
        const lockedMsg = document.getElementById("shorts-linked-locked-msg");
        const parentSelect = document.getElementById("parent-long-select");
        const linkedConfig = document.getElementById("linked-shorts-config");

        if (parents.length > 0) {
            if (linkedRadio) linkedRadio.disabled = false;
            if (lockedMsg) lockedMsg.style.display = "none";
            if (parentSelect) {
                parentSelect.innerHTML = parents.map(p => 
                    `<option value="${p.content_id}">${p.title} (${p.created_at ? p.created_at.substring(0, 10) : 'Recent'})</option>`
                ).join("");
            }
        } else {
            if (linkedRadio) {
                linkedRadio.disabled = true;
                if (linkedRadio.checked) {
                    const longRadio = document.getElementById("mode-long");
                    if (longRadio) longRadio.checked = true;
                    if (linkedConfig) linkedConfig.style.display = "none";
                }
            }
            if (lockedMsg) lockedMsg.style.display = "block";
            if (parentSelect) parentSelect.innerHTML = "";
            if (linkedConfig) linkedConfig.style.display = "none";
        }
    } catch (e) {
        console.error("Error loading eligible parents:", e);
    }
}

function updateChannelUI(chan) {
    if (!chan) return;
    const name = chan.name || "Default Channel";
    const engine = (chan.engine || "media_video").toLowerCase();

    // Update target badges
    const targetPillName = document.getElementById("target-channel-name");
    if (targetPillName) targetPillName.innerText = name;

    const reviewTargetName = document.getElementById("review-target-channel-name");
    if (reviewTargetName) reviewTargetName.innerText = name;

    // Update engine badge
    const badge = document.getElementById("active-engine-badge");
    if (badge) {
        if (engine === "animation") {
            badge.innerText = "Animation Engine";
            badge.className = "engine-badge engine-animation";
        } else {
            badge.innerText = "Media Video";
            badge.className = "engine-badge engine-media";
        }
    }

    // Update audience badge
    const audBadge = document.getElementById("active-audience-badge");
    const audType = chan.audience?.type || "";
    const cid = chan.id || chan.channel_id;
    if (audBadge) {
        if (audType === "children" || cid === "kids") {
            audBadge.innerText = "👶 Kids Only (COPPA)";
            audBadge.className = "audience-badge audience-kids";
        } else if (audType === "mature_adults" || cid === "elders") {
            audBadge.innerText = "📖 Elders (45-75)";
            audBadge.className = "audience-badge audience-elders";
        } else {
            audBadge.innerText = "General Audience";
            audBadge.className = "audience-badge audience-general";
        }
    }

    // Synchronize sub-tabs in API Keys and YouTube
    switchSubTab("api", cid);
    switchSubTab("yt", cid);

    // Set format radio button if specified in channel defaults
    const defFormat = chan.video?.default_format || (chan.default_format || "normal");
    const fmtRadio = document.querySelector(`input[name="video_format"][value="${defFormat}"]`);
    if (fmtRadio) fmtRadio.checked = true;
}

function switchSubTab(type, channelId) {
    if (type === "api") {
        document.querySelectorAll(".channel-subtab-btn[data-subchannel]").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-subchannel") === channelId);
        });
        document.querySelectorAll(".channel-subpane").forEach(pane => {
            pane.style.display = (pane.id === `subpane-api-${channelId}`) ? "block" : "none";
        });
    } else if (type === "yt") {
        document.querySelectorAll(".channel-subtab-btn[data-subchannel-yt]").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-subchannel-yt") === channelId);
        });
        document.querySelectorAll(".channel-subpane-yt").forEach(pane => {
            pane.style.display = (pane.id === `subpane-yt-${channelId}`) ? "block" : "none";
        });
    }
}

async function switchChannel(channelId) {
    try {
        showToast(`Switching channel to ${channelId}...`, "info");
        const resp = await fetch("/api/channels/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ channel_id: channelId })
        });
        const res = await resp.json();
        if (res.ok) {
            currentChannelId = channelId;
            updateChannelUI(res.channel);
            await loadSettings();
            await loadYouTubeStatus();
            await loadEligibleParents(channelId);
            showToast(`Active channel switched to "${res.channel.name}"!`, "success");
        } else {
            showToast(`Switch failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error switching channel: ${e.message}`, "error");
    }
}

// ── LOAD SETTINGS ──
async function loadSettings() {
    try {
        const resp = await fetch("/api/settings");
        if (!resp.ok) {
            const errText = await resp.text();
            let errMsg = `Server error (${resp.status})`;
            try {
                const parsed = JSON.parse(errText);
                if (parsed.error) errMsg = parsed.error;
            } catch (_) {}
            throw new Error(errMsg);
        }
        const data = await resp.json();
        if (!data || !data.config) {
            throw new Error("Invalid configuration received from server");
        }
        currentConfig = data.config;

        // Populate API Keys
        setVal("gemini-api-key", currentConfig.gemini_api_key);
        setVal("groq-api-key", currentConfig.groq_api_key || "");
        setVal("pexels-api-key", currentConfig.pexels_api_key);
        setVal("pixabay-api-key", currentConfig.pixabay_api_key);
        setVal("elevenlabs-api-key", currentConfig.elevenlabs_api_key);

        // Active AI Brain Radio Button
        const activeProvider = currentConfig.llm_provider || "gemini";
        const radioGemini = document.getElementById("radio-provider-gemini");
        const radioGroq = document.getElementById("radio-provider-groq");
        if (activeProvider === "groq" && radioGroq) {
            radioGroq.checked = true;
        } else if (radioGemini) {
            radioGemini.checked = true;
        }

        // Reliably set select dropdowns — adds option if value not present
        setSelectVal("gemini-model-select", currentConfig.gemini_model || "gemini-3.8-flash");
        setSelectVal("groq-model-select", currentConfig.groq_model || "llama-3.3-70b-versatile");
        setSelectVal("video-source-select", currentConfig.video_source || "pexels_images");
        setSelectVal("tts-provider-select", currentConfig.tts_provider || "edge-tts");
        setSelectVal("yt-default-privacy", currentConfig.youtube_privacy || "private");
        setSelectVal("yt-default-category", currentConfig.youtube_category_id || "28");

        // Sliders and numeric inputs
        setVal("voice-rate-input", currentConfig.voice_rate || "+0%");
        setVal("voice-pitch-input", currentConfig.voice_pitch || "+0Hz");
        setVal("music-volume-slider", currentConfig.music_volume != null ? currentConfig.music_volume : 0.12);
        setVal("kb-zoom-end-slider", currentConfig.kb_zoom_end != null ? currentConfig.kb_zoom_end : 1.15);
        
        const musicCheck = document.getElementById("music-enabled-check");
        if (musicCheck) musicCheck.checked = (currentConfig.music_enabled !== false);

        const subCheck = document.getElementById("subtitles-enabled-check");
        if (subCheck) subCheck.checked = (currentConfig.subtitles_enabled !== false);

        // Update slider value badges
        const volEl = document.getElementById("music-vol-display");
        if (volEl && currentConfig.music_volume != null) {
            volEl.innerText = Math.round(currentConfig.music_volume * 100) + "%";
        }
        const zoomEl = document.getElementById("zoom-display");
        if (zoomEl && currentConfig.kb_zoom_end != null) {
            zoomEl.innerText = parseFloat(currentConfig.kb_zoom_end).toFixed(2) + "×";
        }

        // Channel Info & YouTube Defaults
        setVal("channel-name-input", currentConfig.channel_name || "");
        setVal("channel-desc-input", currentConfig.channel_description || "");

        // Voice Select — build options from server list and mark saved voice as selected
        const voiceSelect = document.getElementById("voice-select");
        if (voiceSelect && data.voices) {
            const savedVoice = currentConfig.voice_id || "en-US-ChristopherNeural";
            voiceSelect.innerHTML = "";
            data.voices.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v.id;
                opt.textContent = `${v.name} (${v.gender})`;
                if (v.id === savedVoice) opt.selected = true;
                voiceSelect.appendChild(opt);
            });
            // If saved voice not in list, add it
            if (!Array.from(voiceSelect.options).some(o => o.value === savedVoice)) {
                const customOpt = document.createElement("option");
                customOpt.value = savedVoice;
                customOpt.textContent = `${savedVoice} (saved)`;
                customOpt.selected = true;
                voiceSelect.insertBefore(customOpt, voiceSelect.firstChild);
            }
        }

        // Banned Topics
        const bannedArea = document.getElementById("banned-topics-textarea");
        if (bannedArea && data.banned_topics) {
            bannedArea.value = data.banned_topics.join("\n");
        }

        console.log("[Settings] Loaded from server:", {
            model: currentConfig.gemini_model,
            voice: currentConfig.voice_id,
            provider: currentConfig.llm_provider
        });
        await loadAllChannelSettings();
    } catch (e) {
        showToast(`Failed loading settings: ${e.message}`, "error");
    }
}

// ── SAVE SETTINGS ──
async function saveAllSettings() {
    const selectedProvider = document.querySelector('input[name="ai_provider_radio"]:checked')?.value || currentConfig.llm_provider || "gemini";
    
    // Only send non-masked credentials to prevent overwriting keys with bullet points
    const cleanKey = (val) => (val && !val.includes("••••")) ? val : undefined;

    const payload = {
        channel_id: currentChannelId,
        name: getVal("channel-name-input") || currentConfig.channel_name,
        credentials: {
            llm_provider: selectedProvider,
            gemini_model: getVal("gemini-model-select") || currentConfig.gemini_model || "gemini-3.8-flash",
            groq_model: getVal("groq-model-select") || currentConfig.groq_model || "llama-3.3-70b-versatile",
            video_source: getVal("video-source-select") || currentConfig.video_source || "pexels_images",
        },
        voice: {
            tts_provider: getVal("tts-provider-select") || currentConfig.tts_provider || "edge-tts",
            voice_id: getVal("voice-select") || currentConfig.voice_id || "en-US-ChristopherNeural",
            voice_rate: getVal("voice-rate-input") || currentConfig.voice_rate || "+0%",
            voice_pitch: getVal("voice-pitch-input") || currentConfig.voice_pitch || "+0Hz",
            music_volume: parseFloat(getVal("music-volume-slider")) || currentConfig.music_volume || 0.12,
            music_enabled: document.getElementById("music-enabled-check") ? document.getElementById("music-enabled-check").checked : (currentConfig.music_enabled !== false),
        },
        video: {
            kb_zoom_end: parseFloat(getVal("kb-zoom-end-slider")) || currentConfig.kb_zoom_end || 1.15,
            subtitles_enabled: document.getElementById("subtitles-enabled-check") ? document.getElementById("subtitles-enabled-check").checked : (currentConfig.subtitles_enabled !== false),
        },
        prompts: {
            description: getVal("channel-desc-input") || currentConfig.channel_description || "",
        },
        youtube: {
            privacy: getVal("yt-default-privacy") || currentConfig.youtube_privacy || "private",
            category_id: getVal("yt-default-category") || currentConfig.youtube_category_id || "28",
        },
        // Flat aliases for backwards compatibility
        llm_provider: selectedProvider,
        gemini_model: getVal("gemini-model-select") || currentConfig.gemini_model || "gemini-3.8-flash",
        groq_model: getVal("groq-model-select") || currentConfig.groq_model || "llama-3.3-70b-versatile",
        video_source: getVal("video-source-select") || currentConfig.video_source || "pexels_images",
        tts_provider: getVal("tts-provider-select") || currentConfig.tts_provider || "edge-tts",
        voice_id: getVal("voice-select") || currentConfig.voice_id || "en-US-ChristopherNeural",
        voice_rate: getVal("voice-rate-input") || currentConfig.voice_rate || "+0%",
        voice_pitch: getVal("voice-pitch-input") || currentConfig.voice_pitch || "+0Hz",
        music_volume: parseFloat(getVal("music-volume-slider")) || currentConfig.music_volume || 0.12,
        kb_zoom_end: parseFloat(getVal("kb-zoom-end-slider")) || currentConfig.kb_zoom_end || 1.15,
        music_enabled: document.getElementById("music-enabled-check") ? document.getElementById("music-enabled-check").checked : (currentConfig.music_enabled !== false),
        subtitles_enabled: document.getElementById("subtitles-enabled-check") ? document.getElementById("subtitles-enabled-check").checked : (currentConfig.subtitles_enabled !== false),
        channel_name: getVal("channel-name-input") || currentConfig.channel_name || "",
        channel_description: getVal("channel-desc-input") || currentConfig.channel_description || "",
        youtube_privacy: getVal("yt-default-privacy") || currentConfig.youtube_privacy || "private",
        youtube_category_id: getVal("yt-default-category") || currentConfig.youtube_category_id || "28"
    };

    const gKey = cleanKey(getVal("gemini-api-key"));
    if (gKey !== undefined) payload.gemini_api_key = gKey;
    const grKey = cleanKey(getVal("groq-api-key"));
    if (grKey !== undefined) payload.groq_api_key = grKey;
    const pxKey = cleanKey(getVal("pexels-api-key"));
    if (pxKey !== undefined) payload.pexels_api_key = pxKey;
    const pbKey = cleanKey(getVal("pixabay-api-key"));
    if (pbKey !== undefined) payload.pixabay_api_key = pbKey;
    const elKey = cleanKey(getVal("elevenlabs-api-key"));
    if (elKey !== undefined) payload.elevenlabs_api_key = elKey;

    try {
        const resp = await fetch("/api/channels/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("Settings permanently saved for active channel!", "success");
            await loadSettings();
        } else {
            showToast(`Save failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error saving settings: ${e.message}`, "error");
    }
}

// ── PER-CHANNEL MULTI-VIEW LOGIC ──
async function loadAllChannelSettings() {
    try {
        const resp = await fetch("/api/channels/all-settings");
        if (!resp.ok) return;
        const data = await resp.json();
        if (!data.ok || !data.channels) return;

        for (const [cid, cData] of Object.entries(data.channels)) {
            const creds = cData.credentials || {};
            const yt = cData.youtube_status || {};
            const cfg = cData.config || {};

            // API Keys
            setVal(`gemini-api-key-${cid}`, creds.gemini_api_key || "");
            setVal(`groq-api-key-${cid}`, creds.groq_api_key || "");
            setVal(`nano-banana-api-key-${cid}`, creds.nano_banana_api_key || "");
            setVal(`pexels-api-key-${cid}`, creds.pexels_api_key || "");
            setVal(`pixabay-api-key-${cid}`, creds.pixabay_api_key || "");
            setVal(`elevenlabs-api-key-${cid}`, creds.elevenlabs_api_key || "");
            setVal(`elevenlabs-voice-id-${cid}`, creds.elevenlabs_voice_id || "");

            setSelectVal(`gemini-model-${cid}`, cfg.gemini_model || "gemini-3.8-flash");
            setSelectVal(`groq-model-${cid}`, cfg.groq_model || "openai/gpt-oss-120b");
            setSelectVal(`nano-banana-model-${cid}`, cfg.nano_banana_model || "");
            setSelectVal(`voice-select-${cid}`, cfg.voice_id || "");

            const provRadio = document.querySelector(`input[name="ai_provider_radio_${cid}"][value="${cfg.llm_provider || 'gemini'}"]`);
            if (provRadio) provRadio.checked = true;

            // YouTube Status
            const detailsEl = document.getElementById(`yt-details-${cid}`);
            const nameEl = document.getElementById(`yt-name-${cid}`);
            const idEl = document.getElementById(`yt-id-${cid}`);
            const subsEl = document.getElementById(`yt-subs-${cid}`);
            const secretPathInput = document.getElementById(`yt-secret-path-${cid}`);

            if (secretPathInput && yt.default_secret_path) {
                secretPathInput.value = yt.default_secret_path;
            }

            if (yt.token_valid && yt.channel) {
                if (detailsEl) detailsEl.style.display = "block";
                if (nameEl) nameEl.innerText = yt.channel.title || "Authenticated Channel";
                if (idEl) idEl.innerText = `ID: ${yt.channel.id || ""}`;
                if (subsEl) subsEl.innerText = `Subscribers: ${yt.channel.subscribers || "Active"}`;
            } else if (detailsEl) {
                detailsEl.style.display = "none";
            }
        }
    } catch (e) {
        console.error("Failed loading all channel settings:", e);
    }
}

async function saveChannelKeys(channelId) {
    const cleanKey = (val) => (val && !val.includes("••••")) ? val : "";
    const gKey = cleanKey(getVal(`gemini-api-key-${channelId}`));
    const grKey = cleanKey(getVal(`groq-api-key-${channelId}`));
    const nbKey = cleanKey(getVal(`nano-banana-api-key-${channelId}`));
    const pxKey = cleanKey(getVal(`pexels-api-key-${channelId}`));
    const pbKey = cleanKey(getVal(`pixabay-api-key-${channelId}`));
    const elKey = cleanKey(getVal(`elevenlabs-api-key-${channelId}`));
    const elVoiceId = getVal(`elevenlabs-voice-id-${channelId}`);
    const gModel = getVal(`gemini-model-${channelId}`);
    const grModel = getVal(`groq-model-${channelId}`);
    const nbModel = getVal(`nano-banana-model-${channelId}`);
    const provider = document.querySelector(`input[name="ai_provider_radio_${channelId}"]:checked`)?.value || "gemini";
    const voiceId = getVal(`voice-select-${channelId}`);

    const payload = {
        gemini_api_key: gKey,
        groq_api_key: grKey,
        nano_banana_api_key: nbKey,
        pexels_api_key: pxKey,
        pixabay_api_key: pbKey,
        elevenlabs_api_key: elKey,
        elevenlabs_voice_id: elVoiceId,
        llm_provider: provider,
        gemini_model: gModel,
        groq_model: grModel,
        nano_banana_model: nbModel
    };
    if (voiceId) {
        payload.voice = { voice_id: voiceId };
    }

    try {
        const resp = await fetch(`/api/channels/${channelId}/credentials`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.ok) {
            showToast(`API Keys saved permanently for ${channelId}!`, "success");
            await loadAllChannelSettings();
            if (channelId === currentChannelId) {
                await loadSettings();
            }
        } else {
            showToast(`Save failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Save error: ${e.message}`, "error");
    }
}

async function saveChannelYtSettings(channelId) {
    const cat = getVal(`yt-cat-${channelId}`);
    const priv = getVal(`yt-priv-${channelId}`);
    const payload = {
        channel_id: channelId,
        youtube: {
            category_id: cat || "28",
            privacy: priv || "private"
        }
    };
    try {
        const resp = await fetch("/api/channels/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.ok) {
            showToast(`YouTube settings saved for ${channelId}!`, "success");
        } else {
            showToast(`Failed saving YouTube settings: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error: ${e.message}`, "error");
    }
}

async function triggerChannelYouTubeAuth(channelId) {
    showToast(`Launching YouTube OAuth for ${channelId}...`, "info");
    try {
        const resp = await fetch("/api/youtube/authenticate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ channel_id: channelId })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast(res.message || `Successfully connected ${channelId}!`, "success");
            await loadAllChannelSettings();
            if (channelId === currentChannelId) {
                await loadYouTubeStatus();
            }
        } else {
            showToast(`YouTube Auth error: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Auth failed: ${e.message}`, "error");
    }
}

async function loadSecretFromPathForChannel(channelId) {
    const path = getVal(`yt-secret-path-${channelId}`);
    if (!path) {
        showToast("Please enter a file path to client_secret.json", "warning");
        return;
    }
    try {
        const resp = await fetch("/api/youtube/load-secret-path", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filepath: path, channel_id: channelId })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast(`Loaded client secret for ${channelId}!`, "success");
            await loadAllChannelSettings();
        } else {
            showToast(`Failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error: ${e.message}`, "error");
    }
}

async function uploadSecretFileForChannel(file, channelId) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("channel_id", channelId);
    try {
        const resp = await fetch("/api/youtube/save-secret-json", {
            method: "POST",
            body: formData
        });
        const res = await resp.json();
        if (res.ok) {
            showToast(`Uploaded client secret for ${channelId}!`, "success");
            await loadAllChannelSettings();
        } else {
            showToast(`Upload failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Upload error: ${e.message}`, "error");
    }
}

// ── YOUTUBE STATUS & CREDENTIALS ──
async function loadYouTubeStatus() {
    try {
        const resp = await fetch(`/api/youtube/status?channel_id=${encodeURIComponent(currentChannelId)}`);
        const yt = await resp.json();

        const badge = document.getElementById("yt-auth-badge");
        const details = document.getElementById("yt-channel-details");
        const authBtn = document.getElementById("btn-yt-authenticate");

        if (yt.token_valid) {
            badge.className = "status-pill";
            badge.style.borderColor = "var(--accent-emerald)";
            badge.innerHTML = `<span class="status-dot dot-success"></span> Connected & Authorized`;
            authBtn.innerText = "Re-Authenticate Channel";
            
            if (yt.channel) {
                details.style.display = "block";
                document.getElementById("yt-channel-name").innerText = yt.channel.title || "YouTube Channel";
                document.getElementById("yt-channel-id").innerText = `ID: ${yt.channel.id}`;
                document.getElementById("yt-channel-subs").innerText = `${yt.channel.subscribers} Subscribers`;
            }
        } else if (yt.has_token && yt.token_expired) {
            badge.className = "status-pill";
            badge.style.borderColor = "var(--accent-amber)";
            badge.innerHTML = `<span class="status-dot dot-running"></span> Token Expired (Click to Refresh)`;
            authBtn.innerText = "Refresh YouTube Token";
        } else if (yt.has_client_secret) {
            badge.className = "status-pill";
            badge.style.borderColor = "var(--primary)";
            badge.innerHTML = `<span class="status-dot dot-idle"></span> Secret Present (Needs Sign-In)`;
            authBtn.innerText = "Connect YouTube Channel";
        } else {
            badge.className = "status-pill";
            badge.style.borderColor = "var(--accent-rose)";
            badge.innerHTML = `<span class="status-dot dot-error"></span> Missing client_secret.json`;
            authBtn.innerText = "Add Secret First";
        }

        if (yt.default_secret_path) {
            setVal("yt-secret-path-input", yt.default_secret_path);
        }
    } catch (e) {
        console.error("YouTube status error:", e);
    }
}

async function loadSecretFromPath() {
    const filepath = getVal("yt-secret-path-input");
    if (!filepath) {
        showToast("Please enter a path to client_secret.json", "error");
        return;
    }
    showToast("Loading client_secret.json from path...", "info");
    try {
        const resp = await fetch("/api/youtube/load-secret-path", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filepath: filepath, channel_id: currentChannelId })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("client_secret.json loaded and saved successfully!", "success");
            loadYouTubeStatus();
        } else {
            showToast(res.error || "Failed to load secret file", "error");
        }
    } catch (e) {
        showToast(`Load error: ${e.message}`, "error");
    }
}

async function triggerYouTubeAuth() {
    try {
        showToast(`Opening Google Sign-In in browser for channel '${currentChannelId}'...`, "info");
        const resp = await fetch("/api/youtube/authenticate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ channel_id: currentChannelId })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("Complete authorization in the browser window.", "success");
            // Poll for completion
            let checks = 0;
            const checkInterval = setInterval(async () => {
                checks++;
                const statusResp = await fetch(`/api/youtube/status?channel_id=${encodeURIComponent(currentChannelId)}`);
                const ytData = await statusResp.json();
                if (ytData.token_valid || checks > 30) {
                    clearInterval(checkInterval);
                    loadYouTubeStatus();
                    if (ytData.token_valid) showToast("YouTube channel connected successfully!", "success");
                }
            }, 3000);
        } else {
            showToast(`Auth error: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Auth launch error: ${e.message}`, "error");
    }
}

async function uploadSecretFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
        const resp = await fetch("/api/youtube/save-secret-json", {
            method: "POST",
            body: formData
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("client_secret.json uploaded and saved!", "success");
            loadYouTubeStatus();
        } else {
            showToast(`Upload failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`File error: ${e.message}`, "error");
    }
}

async function saveManualCredentials() {
    const clientId = getVal("manual-client-id");
    const clientSecret = getVal("manual-client-secret");
    if (!clientId || !clientSecret) {
        showToast("Please provide both Client ID and Client Secret.", "error");
        return;
    }
    try {
        const resp = await fetch("/api/youtube/save-credentials", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: clientId, client_secret: clientSecret })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("OAuth credentials saved successfully!", "success");
            loadYouTubeStatus();
        } else {
            showToast(`Failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Save error: ${e.message}`, "error");
    }
}

// ── GENERATE WORKFLOW ──
function startPipeline() {
    const topic = getVal("gen-topic-input");
    const angle = getVal("gen-angle-select");
    const modeEl = document.querySelector('input[name="content_mode"]:checked');
    const contentMode = modeEl ? modeEl.value : "long";
    const videoType = (contentMode === "long") ? "normal" : "shorts";

    let parentContentId = null;
    let numShorts = 1;
    let genMode = "purpose_built";
    let options = {};

    if (contentMode === "shorts_linked") {
        parentContentId = getVal("parent-long-select");
        if (!parentContentId) {
            showToast("Please select an eligible Long video parent first.", "error");
            return;
        }
        numShorts = parseInt(getVal("num-shorts-input") || 1, 10);
        genMode = getVal("linked-gen-mode-select") || "purpose_built";
        options = {
            unique_hook: document.getElementById("opt-unique-hook")?.checked ?? true,
            preserve_value: document.getElementById("opt-preserve-value")?.checked ?? true,
            add_url: document.getElementById("opt-add-url")?.checked ?? true,
            add_cta: document.getElementById("opt-add-cta")?.checked ?? true,
            keep_family: document.getElementById("opt-keep-family")?.checked ?? true,
            prevent_duplicate: document.getElementById("opt-prevent-duplicate")?.checked ?? true
        };
    }

    const steps = [];
    if (document.getElementById("chk-research").checked) steps.push("research");
    if (document.getElementById("chk-script").checked) steps.push("script");
    if (document.getElementById("chk-narration").checked) steps.push("narration");
    if (document.getElementById("chk-media").checked) steps.push("media");
    if (document.getElementById("chk-video").checked) steps.push("video");
    if (document.getElementById("chk-thumbnail").checked) steps.push("thumbnail");

    if (steps.length === 0) {
        showToast("Please select at least one step to execute.", "error");
        return;
    }

    fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            channel_id: currentChannelId,
            steps: steps,
            topic: topic,
            focus_angle: angle,
            video_type: videoType,
            content_mode: contentMode,
            parent_content_id: parentContentId,
            num_shorts: numShorts,
            generation_mode: genMode,
            options: options
        })
    }).then(r => r.json()).then(res => {
        if (res.ok) {
            showToast("Pipeline launched! Watch live logs below.", "success");
        } else {
            showToast(`Launch failed: ${res.error}`, "error");
        }
    }).catch(e => {
        showToast(`Network error: ${e.message}`, "error");
    });
}

function stopPipeline() {
    fetch("/api/stop", { method: "POST" })
        .then(r => r.json())
        .then(res => {
            showToast("Pipeline halt requested.", "info");
        });
}

// ── REVIEW & PUBLISH ──
async function loadReviewData() {
    try {
        const resp = await fetch("/api/script");
        const data = await resp.json();

        if (data.script) {
            setVal("review-title-input", data.script.title || "");
            setVal("review-desc-input", data.description || "");
            currentTags = data.tags || [];
            renderTagBadges();
        }

        // Check video
        const videoPlayer = document.getElementById("review-video-player");
        const statusResp = await fetch("/api/status");
        const statusData = await statusResp.json();

        if (statusData.has_video) {
            videoPlayer.src = `/api/media/video?t=${Date.now()}`;
            videoPlayer.style.display = "block";
            document.getElementById("no-video-placeholder").style.display = "none";
        }

        if (statusData.has_thumb) {
            const thumbImg = document.getElementById("review-thumb-img");
            thumbImg.src = `/api/media/thumbnail?t=${Date.now()}`;
            thumbImg.style.display = "block";
            document.getElementById("no-thumb-placeholder").style.display = "none";
        }

        // Load QC Report
        try {
            const qcResp = await fetch("/api/qc/report");
            const qcData = await qcResp.json();
            if (qcData.ok && qcData.report) {
                const rep = qcData.report;
                const qcBadge = document.getElementById("qc-badge");
                const qcDetails = document.getElementById("qc-details-box");
                if (qcBadge && rep.score > 0) {
                    qcBadge.innerText = `QC Score: ${rep.score}/100 [${rep.status}]`;
                    qcBadge.style.color = rep.passed ? "var(--accent-emerald)" : "var(--accent-amber)";
                }
                if (qcDetails && rep.details && rep.details.length > 0) {
                    qcDetails.innerHTML = rep.details.map(d => `<div>• ${d}</div>`).join("");
                }
            }
        } catch (qcErr) {
            console.error("Error fetching QC report:", qcErr);
        }

        // Load Internal Readiness Panel
        try {
            if (statusData.content_id) {
                const readResp = await fetch(`/api/readiness/${encodeURIComponent(statusData.content_id)}`);
                const readData = await readResp.json();
                if (readData.ok && readData.readiness) {
                    const r = readData.readiness;
                    const rBadge = document.getElementById("readiness-status-badge");
                    if (rBadge) {
                        rBadge.innerText = `STATUS: ${r.status}`;
                        rBadge.style.color = (r.status === "READY FOR REVIEW") ? "var(--accent-emerald)" : "#ef4444";
                    }
                    const pqEl = document.getElementById("readiness-pq");
                    if (pqEl) pqEl.innerText = `${r.production_quality.score}/100 [${r.production_quality.status}]`;
                    const origEl = document.getElementById("readiness-orig");
                    if (origEl) origEl.innerText = `${r.originality.score}/100 [${r.originality.status}]`;
                    const techEl = document.getElementById("readiness-tech");
                    if (techEl) techEl.innerText = r.technical_qc;
                    const compEl = document.getElementById("readiness-comp");
                    if (compEl) compEl.innerText = r.content_compliance;
                    const chanEl = document.getElementById("readiness-chan");
                    if (chanEl) chanEl.innerText = r.channel_validation;
                    const kidsEl = document.getElementById("readiness-kids");
                    if (kidsEl) kidsEl.innerText = r.kids_safety;
                    const assetEl = document.getElementById("readiness-asset");
                    if (assetEl) assetEl.innerText = r.asset_provenance;
                }
            }
        } catch (rErr) {
            console.error("Error fetching readiness report:", rErr);
        }
    } catch (e) {
        console.error("Error loading review data:", e);
    }
}

function renderTagBadges() {
    const container = document.getElementById("tag-chips");
    if (!container) return;
    container.innerHTML = "";
    currentTags.forEach((tag, idx) => {
        const badge = document.createElement("span");
        badge.className = "tag-badge";
        badge.innerHTML = `#${tag} <span class="tag-remove" onclick="removeTag(${idx})">×</span>`;
        container.appendChild(badge);
    });
}

function addTag(tag) {
    const clean = tag.replace(/#/g, "").trim();
    if (clean && !currentTags.includes(clean)) {
        currentTags.push(clean);
        renderTagBadges();
    }
}

function removeTag(idx) {
    currentTags.splice(idx, 1);
    renderTagBadges();
}

async function saveMetadata() {
    const title = getVal("review-title-input");
    const desc = getVal("review-desc-input");
    try {
        const resp = await fetch("/api/script/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: title, description: desc, tags: currentTags })
        });
        const res = await resp.json();
        if (res.ok) showToast("Metadata saved to script!", "success");
    } catch (e) {
        showToast(`Save error: ${e.message}`, "error");
    }
}

async function regenerateDescriptionAI() {
    showToast("AI is writing an engaging description...", "info");
    try {
        const resp = await fetch("/api/script/regenerate-description", { method: "POST" });
        const res = await resp.json();
        if (res.ok) {
            setVal("review-desc-input", res.description);
            showToast("New YouTube description generated!", "success");
        } else {
            showToast(`Failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error: ${e.message}`, "error");
    }
}

async function regenerateThumbnail() {
    const title = getVal("review-title-input");
    showToast("Re-rendering YouTube thumbnail...", "info");
    try {
        const resp = await fetch("/api/script/regenerate-thumbnail", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: title })
        });
        const res = await resp.json();
        if (res.ok) {
            const thumbImg = document.getElementById("review-thumb-img");
            thumbImg.src = `/api/media/thumbnail?t=${res.timestamp}`;
            showToast("Thumbnail regenerated successfully!", "success");
        }
    } catch (e) {
        showToast(`Thumbnail error: ${e.message}`, "error");
    }
}

async function uploadToYouTubeDirect() {
    const privacy = getVal("publish-privacy-select");
    const category = getVal("publish-category-select");
    const schedule = getVal("publish-schedule-input");
    const title = getVal("review-title-input");
    const desc = getVal("review-desc-input");

    showToast("Starting YouTube upload...", "info");
    try {
        const resp = await fetch("/api/youtube/upload", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                channel_id: currentChannelId,
                privacy: privacy,
                category_id: category,
                publish_at: schedule || null,
                title: title,
                description: desc
            })
        });
        const res = await resp.json();
        if (res.ok) {
            showToast("Video upload initiated! Watch progress bar.", "success");
        } else {
            showToast(`Upload failed: ${res.error}`, "error");
        }
    } catch (e) {
        showToast(`Error: ${e.message}`, "error");
    }
}

// ── EVENT LISTENERS SETUP ──
function setupEventListeners() {
    // Generate Tab
    document.getElementById("btn-generate").addEventListener("click", startPipeline);
    document.getElementById("btn-stop").addEventListener("click", stopPipeline);

    // Content Mode Radios
    document.querySelectorAll('input[name="content_mode"]').forEach(radio => {
        radio.addEventListener("change", (e) => {
            const linkedBox = document.getElementById("linked-shorts-config");
            if (linkedBox) {
                linkedBox.style.display = (e.target.value === "shorts_linked") ? "block" : "none";
            }
        });
    });

    // Review Tab
    document.getElementById("btn-save-meta").addEventListener("click", saveMetadata);
    document.getElementById("btn-regen-desc").addEventListener("click", regenerateDescriptionAI);
    document.getElementById("btn-regen-thumb").addEventListener("click", regenerateThumbnail);
    document.getElementById("btn-publish-yt").addEventListener("click", uploadToYouTubeDirect);

    // Tags input keydown
    const tagInput = document.getElementById("new-tag-input");
    if (tagInput) {
        tagInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === ",") {
                e.preventDefault();
                addTag(tagInput.value);
                tagInput.value = "";
            }
        });
    }

    // Voice preview
    document.getElementById("btn-preview-voice").addEventListener("click", async () => {
        const voiceId = getVal("voice-select");
        showToast("Synthesizing voice sample...", "info");
        try {
            const resp = await fetch("/api/preview/voice", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ voice_id: voiceId })
            });
            if (resp.ok) {
                const blob = await resp.blob();
                const audioUrl = URL.createObjectURL(blob);
                const audio = new Audio(audioUrl);
                audio.play();
                showToast("Playing voice sample!", "success");
            } else {
                showToast("Could not preview voice.", "error");
            }
        } catch (e) {
            showToast(`Preview error: ${e.message}`, "error");
        }
    });

    // API Key Testers
    document.getElementById("btn-test-gemini").addEventListener("click", async () => {
        showToast("Testing Google Gemini connection...", "info");
        const resp = await fetch("/api/settings/test-gemini", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                gemini_api_key: getVal("gemini-api-key"),
                gemini_model: getVal("gemini-model-select")
            })
        });
        const res = await resp.json();
        showToast(res.message, res.ok ? "success" : "error");
    });

    // Radio change listeners for instant provider switching
    document.querySelectorAll('input[name="ai_provider_radio"]').forEach(radio => {
        radio.addEventListener("change", () => {
            saveAllSettings();
        });
    });

    const subCheckEl = document.getElementById("subtitles-enabled-check");
    if (subCheckEl) {
        subCheckEl.addEventListener("change", () => {
            saveAllSettings();
        });
    }

    document.getElementById("btn-test-pexels").addEventListener("click", async () => {
        showToast("Testing Pexels API Key...", "info");
        const resp = await fetch("/api/settings/test-pexels", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pexels_api_key: getVal("pexels-api-key") })
        });
        const res = await resp.json();
        showToast(res.message, res.ok ? "success" : "error");
    });

    document.getElementById("btn-test-pixabay").addEventListener("click", async () => {
        showToast("Testing Pixabay API Key...", "info");
        const resp = await fetch("/api/settings/test-pixabay", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pixabay_api_key: getVal("pixabay-api-key") })
        });
        const res = await resp.json();
        showToast(res.message, res.ok ? "success" : "error");
    });

    // Test Groq API Key
    const btnTestGroq = document.getElementById("btn-test-groq");
    if (btnTestGroq) {
        btnTestGroq.addEventListener("click", async () => {
            showToast("Testing Groq API connection...", "info");
            const resp = await fetch("/api/settings/test-groq", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    groq_api_key: getVal("groq-api-key"),
                    groq_model: getVal("groq-model-select")
                })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    }

    // Save All Settings buttons
    document.getElementById("btn-save-settings").addEventListener("click", saveAllSettings);

    const btnSaveYt = document.getElementById("btn-save-youtube");
    if (btnSaveYt) {
        btnSaveYt.addEventListener("click", saveAllSettings);
    }

    // Auto-save when voice or audio controls are changed so selection is never lost
    const voiceSelectEl = document.getElementById("voice-select");
    if (voiceSelectEl) {
        voiceSelectEl.addEventListener("change", () => {
            saveAllSettings();
        });
    }
    const ttsSelectEl = document.getElementById("tts-provider-select");
    if (ttsSelectEl) {
        ttsSelectEl.addEventListener("change", () => {
            saveAllSettings();
        });
    }

    // Save Banned Topics
    document.getElementById("btn-save-banned").addEventListener("click", async () => {
        const raw = getVal("banned-topics-textarea");
        const lines = raw.split("\n").map(l => l.trim()).filter(l => l.length > 0);
        const resp = await fetch("/api/settings/banned-topics", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topics: lines })
        });
        const res = await resp.json();
        if (res.ok) showToast("Banned topics updated!", "success");
    });

    // ── CHANNEL SUB-TABS & PER-CHANNEL CONTROLS ──
    document.querySelectorAll(".channel-subtab-btn[data-subchannel]").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-subchannel");
            switchSubTab("api", cid);
        });
    });

    document.querySelectorAll(".channel-subtab-btn[data-subchannel-yt]").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-subchannel-yt");
            switchSubTab("yt", cid);
        });
    });

    document.querySelectorAll(".btn-save-channel-keys").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-chan");
            saveChannelKeys(cid);
        });
    });

    document.querySelectorAll(".btn-test-gemini").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`gemini-api-key-${cid}`);
            const model = getVal(`gemini-model-${cid}`) || "gemini-3.8-flash";
            showToast(`Testing Gemini for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-gemini", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ gemini_api_key: key, gemini_model: model })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-groq").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`groq-api-key-${cid}`);
            const model = getVal(`groq-model-${cid}`) || "openai/gpt-oss-120b";
            showToast(`Testing Groq for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-groq", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ groq_api_key: key, groq_model: model })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-pexels").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`pexels-api-key-${cid}`);
            showToast(`Testing Pexels for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-pexels", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pexels_api_key: key })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-pixabay").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`pixabay-api-key-${cid}`);
            showToast(`Testing Pixabay for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-pixabay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pixabay_api_key: key })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-nano-banana").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`nano-banana-api-key-${cid}`);
            const model = getVal(`nano-banana-model-${cid}`) || "nano-banana-flux";
            showToast(`Testing Nano Banana for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-nano-banana", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nano_banana_api_key: key, nano_banana_model: model })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-elevenlabs").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`elevenlabs-api-key-${cid}`);
            const voiceId = getVal(`elevenlabs-voice-id-${cid}`) || "";
            showToast(`Testing ElevenLabs for ${cid}...`, "info");
            const resp = await fetch("/api/settings/test-elevenlabs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ elevenlabs_api_key: key, elevenlabs_voice_id: voiceId })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-test-openai-tts").forEach(btn => {
        btn.addEventListener("click", async () => {
            const cid = btn.getAttribute("data-chan");
            const key = getVal(`gemini-api-key-${cid}`) || ""; // Or global key
            showToast(`Testing OpenAI TTS connection...`, "info");
            const resp = await fetch("/api/settings/test-openai-tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ openai_api_key: key, openai_tts_model: "tts-1", openai_tts_voice: "alloy" })
            });
            const res = await resp.json();
            showToast(res.message, res.ok ? "success" : "error");
        });
    });

    document.querySelectorAll(".btn-yt-auth").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-chan");
            triggerChannelYouTubeAuth(cid);
        });
    });

    document.querySelectorAll(".btn-load-secret-path").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-chan");
            loadSecretFromPathForChannel(cid);
        });
    });

    document.querySelectorAll(".yt-secret-file").forEach(input => {
        input.addEventListener("change", (e) => {
            const cid = input.getAttribute("data-chan");
            if (e.target.files.length > 0) {
                uploadSecretFileForChannel(e.target.files[0], cid);
            }
        });
    });

    document.querySelectorAll(".btn-save-yt-settings").forEach(btn => {
        btn.addEventListener("click", () => {
            const cid = btn.getAttribute("data-chan");
            saveChannelYtSettings(cid);
        });
    });

    // YouTube Auth legacy buttons fallback
    const legacyYtAuth = document.getElementById("btn-yt-authenticate");
    if (legacyYtAuth) legacyYtAuth.addEventListener("click", triggerYouTubeAuth);
    const legacyManualCreds = document.getElementById("btn-save-manual-creds");
    if (legacyManualCreds) legacyManualCreds.addEventListener("click", saveManualCredentials);
}

// ── UTILITY HELPERS ──
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}

// Set a <select> to a given value; if option doesn't exist, create it so saved value is never lost
function setSelectVal(id, val) {
    if (val === undefined || val === null) return;
    const el = document.getElementById(id);
    if (!el) return;
    el.value = String(val);
    if (el.value !== String(val)) {
        const opt = document.createElement("option");
        opt.value = String(val);
        opt.textContent = val + " (saved)";
        el.insertBefore(opt, el.firstChild);
        el.value = String(val);
    }
}
