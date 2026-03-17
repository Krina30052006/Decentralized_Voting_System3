// VOTE.CHAIN - Unified Frontend Logic
const API_BASE = "http://127.0.0.1:5000";

let userRole = null; // 'voter' or 'admin'
let selectedCandidateId = null;
let candidatesData = [];

// --- SECTION & TAB NAVIGATION ---
function showSection(id) {
    document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
}

function switchTab(tabId) {
    document.querySelectorAll('.content-tab').forEach(t => t.classList.add('hidden'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    document.getElementById(tabId).classList.remove('hidden');
    
    // Highlight the correct button
    const btnMap = {
        'candidateTab': 'btn-candidates',
        'votingTab': 'btn-voting',
        'resultsTab': 'btn-results',
        'adminControlTab': 'btn-adminControl',
        'adminVotersTab': 'btn-adminVoters'
    };
    if (btnMap[tabId]) document.getElementById(btnMap[tabId]).classList.add('active');

    // Tab-specific loads
    if (tabId === 'resultsTab') fetchResults();
    if (tabId === 'votingTab') fetchElectionStatus();
    if (tabId === 'adminControlTab') {
        fetchAdminStats();
        fetchAdminCandidates();
    }
    if (tabId === 'adminVotersTab') fetchVoters();
    if (tabId === 'candidateTab') fetchCandidates();
}

// --- AUTH MODAL ---
function openAuthModal(role) {
    userRole = role;
    document.getElementById('modalTitle').textContent = role === 'admin' ? '🛡️ Admin Portal Access' : '🗳️ Voter Authorization';
    document.getElementById('modalSub').textContent = role === 'admin' ? 'Enter administrative security credentials.' : 'Enter your Voter ID and PIN.';
    document.getElementById('authModal').classList.remove('hidden');
    document.getElementById('loginId').value = '';
    document.getElementById('loginPin').value = '';
    document.getElementById('authMsg').classList.add('hidden');
}

function closeAuthModal() {
    document.getElementById('authModal').classList.add('hidden');
}

async function handleLogin() {
    const id = document.getElementById('loginId').value;
    const pin = document.getElementById('loginPin').value;
    const msgEl = document.getElementById('authMsg');

    if (!id || !pin) {
        showMsg(msgEl, "Please fill in all fields.", "error");
        return;
    }

    const endpoint = userRole === 'admin' ? '/admin/login' : '/login';
    const payload = userRole === 'admin' 
        ? { username: id, password: pin } 
        : { voter_id: id, password: pin };

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (res.ok) {
            localStorage.setItem("userRole", userRole);
            localStorage.setItem("userId", userRole === 'admin' ? 'Admin' : data.voter_id);
            setupUIForRole(userRole);
            showSection('dashboard');
            switchTab('candidateTab');
        } else {
            showMsg(msgEl, data.message || "Invalid credentials", "error");
        }
    } catch (err) {
        showMsg(msgEl, "Backend server unreachable. Connection error.", "error");
    }
}

function setupUIForRole(role) {
    const isAdmin = role === 'admin';
    document.getElementById('adminNav').classList.toggle('hidden', !isAdmin);
    document.getElementById('voterNav').classList.toggle('hidden', isAdmin);
    
    document.getElementById('userNameDisplay').textContent = localStorage.getItem("userId");
    document.getElementById('userRoleDisplay').textContent = isAdmin ? "Election Official" : "Certified Voter";
}

// --- DATA FETCHING ---
async function fetchCandidates() {
    try {
        const res = await fetch(`${API_BASE}/candidates`);
        candidatesData = await res.json();
        renderCandidateMenu();
        fetchAdminCandidates();
    } catch (err) { console.error("Err fetching candidates", err); }
}

async function fetchResults() {
    const grid = document.getElementById('resultsGrid');
    grid.innerHTML = "<p>Loading blockchain stream...</p>";
    try {
        const res = await fetch(`${API_BASE}/results`);
        const data = await res.json();
        
        grid.innerHTML = "";
        data.forEach(c => {
            const bar = document.createElement('div');
            bar.className = "bg-white p-6 rounded-2xl border border-slate-100 shadow-sm";
            bar.innerHTML = `
                <div class="flex justify-between items-center mb-2 font-bold">
                    <span>${c.candidate} <small class="text-slate-400">(${c.party})</small></span>
                    <span class="text-blue-500">${c.votes} Votes</span>
                </div>
                <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div class="bg-blue-500 h-full" style="width: ${c.votes * 10}%"></div>
                </div>
            `;
            grid.appendChild(bar);
        });
    } catch (err) { grid.innerHTML = "Error loading standings."; }
}

async function fetchElectionStatus() {
    try {
        const res = await fetch(`${API_BASE}/election/status`);
        const data = await res.json();
        const label = document.getElementById('voterStatusLabel');
        label.textContent = `Election ${data.status}`;
        label.className = `inline-block px-4 py-1 rounded-full text-xs font-bold mb-4 uppercase tracking-widest ${data.status === 'Started' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`;
        
        if (data.status === 'Started') {
            document.getElementById('voteGrid').classList.remove('hidden');
            fetchCandidatesForVoting();
        } else {
            document.getElementById('voteGrid').innerHTML = `<div class="col-span-3 py-10 opacity-50">Voting is currently closed.</div>`;
        }
    } catch (err) { console.error(err); }
}

// --- VOTING LOGIC ---
function renderCandidateMenu() {
    const grid = document.getElementById('partyGrid');
    grid.innerHTML = "";
    candidatesData.forEach(c => {
        const card = document.createElement('div');
        card.className = "party-select-card";
        card.onclick = () => showPartyDetails(c);
        card.innerHTML = `
            <img src="${c.party_logo}" class="party-logo-sq">
            <span class="mt-4 text-slate-800 font-bold">${c.party_name}</span>
            <span class="text-[10px] text-slate-400 uppercase font-black tracking-widest">${c.name}</span>
        `;
        grid.appendChild(card);
    });
}

function showPartyDetails(c) {
    document.getElementById('partyMenu').classList.add('hidden');
    document.getElementById('partyDetailView').classList.remove('hidden');
    
    document.getElementById('detailPartyLogo').src = c.party_logo;
    document.getElementById('partyVisionTitle').textContent = c.party_name;
    document.getElementById('detailCandidateName').textContent = `Represented by ${c.name}`;
    
    // Update advocacy/bio if present
    const advEl = document.getElementById('partyAdvocacy');
    if (c.biography) {
        advEl.innerHTML = `<b>Vision:</b> ${c.slogan}<br><br>${c.biography}`;
    }
}

function hidePartyDetails() {
    document.getElementById('partyMenu').classList.remove('hidden');
    document.getElementById('partyDetailView').classList.add('hidden');
}

async function fetchCandidatesForVoting() {
    const grid = document.getElementById('voteGrid');
    grid.innerHTML = "";
    candidatesData.forEach(c => {
        const card = document.createElement('div');
        card.id = `vcard-${c.id}`;
        card.className = "vote-party-card";
        card.onclick = () => {
            selectedCandidateId = c.id;
            document.querySelectorAll('.vote-party-card').forEach(el => el.classList.remove('selected'));
            card.classList.add('selected');
            document.getElementById('selectedCandidateName').textContent = `${c.name} (${c.party_name})`;
            document.getElementById('voteActionBtn').disabled = false;
            document.getElementById('voteActionBtn').classList.add('vote-btn-active');
        };
        card.innerHTML = `
            <img src="${c.party_logo}" class="party-logo-lg">
            <b class="text-slate-800">${c.party_name}</b>
        `;
        grid.appendChild(card);
    });
}

async function submitVote() {
    const voterId = localStorage.getItem("userId");
    const msgEl = document.getElementById('voteMsg');
    const btn = document.getElementById('voteActionBtn');
    
    btn.textContent = "VERIFYING BALLOT...";
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                candidate_id: selectedCandidateId,
                voter_id: voterId
            })
        });
        const data = await res.json();
        if (res.ok) {
            switchTab('successView');
        } else {
            showMsg(msgEl, data.message, "error");
            btn.textContent = "CONFIRM SECURE VOTE";
            btn.disabled = false;
        }
    } catch (err) {
        showMsg(msgEl, "Network failure.", "error");
        btn.disabled = false;
    }
}

// --- ADMIN LOGIC ---
async function fetchAdminStats() {
    try {
        // Voters & Turnout
        const resV = await fetch(`${API_BASE}/admin/voters`);
        const voters = await resV.json();
        
        const votedCount = voters.filter(v => v.has_voted).length;
        const totalVoters = voters.length;
        const turnoutPercent = totalVoters > 0 ? ((votedCount / totalVoters) * 100).toFixed(1) : 0;
        
        // Candidates
        const resC = await fetch(`${API_BASE}/candidates`);
        const candidates = await resC.json();
        const totalCandidates = candidates.length;

        // UI Update (Status Grid)
        if (document.getElementById('candidateCountStat')) {
            document.getElementById('candidateCountStat').textContent = totalCandidates;
            document.getElementById('votesCastStat').textContent = votedCount;
            document.getElementById('registeredVotersStat').textContent = totalVoters;
            document.getElementById('turnoutRateStat').textContent = `${turnoutPercent}%`;
        }
        
        // Status & Lifecycle
        const resS = await fetch(`${API_BASE}/election/status`);
        const sData = await resS.json();
        document.getElementById('adminStatusDisplay').textContent = `Status: ${sData.status}`;
        document.getElementById('startElectionBtn').disabled = (sData.status !== 'NotStarted' || totalCandidates === 0);
        document.getElementById('endElectionBtn').disabled = (sData.status !== 'Started');

        // Simulate activity log
        updateActivityLog(`Registry synced with ${totalVoters} voters.`);
        
    } catch (err) { console.error(err); }
}

function updateActivityLog(msg) {
    const feed = document.getElementById('activityFeed');
    if (!feed) return;
    const item = document.createElement('div');
    item.className = 'activity-item activity-info';
    item.innerHTML = `<strong>${msg}</strong> - Just now`;
    feed.prepend(item);
    if (feed.children.length > 5) feed.lastElementChild.remove();
}

async function controlElection(action) {
    try {
        const res = await fetch(`${API_BASE}/admin/${action}-election`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            updateActivityLog(`Election ${action}ed successfully.`);
            fetchAdminStats();
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) { alert("Connection failed."); }
}

async function resetSystem() {
    const confirmation = confirm("CRITICAL: This will archive all current candidates and votes to the blockchain history. The live dashboard will be cleared for a new election. Reset turnout for all registered voters?");
    if (!confirmation) return;
    
    try {
        const res = await fetch(`${API_BASE}/admin/reset`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            updateActivityLog("Election archived. System ready for new round.");
            fetchAdminStats();
            fetchCandidates();
            switchTab('adminControlTab');
        } else {
            alert("Reset failed: " + data.message);
        }
    } catch (err) { alert("Blockchain synchronization failed."); }
}

// --- ADMIN LOGIC ---
function previewLogo(event) {
    const file = event.target.files[0];
    const previewImg = document.getElementById('logoPreviewImg');
    const placeholder = document.getElementById('logoPlaceholder');
    const nameDisplay = document.getElementById('previewName');
    const partyDisplay = document.getElementById('previewParty');
    const fileNameDisplay = document.getElementById('fileNameDisplay');

    if (file) {
        fileNameDisplay.textContent = file.name;
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            previewImg.classList.remove('hidden');
            placeholder.classList.add('hidden');
        }
        reader.readAsDataURL(file);
    }
    
    // Sync text fields for live feel
    nameDisplay.textContent = document.getElementById('cand-name').value || "Candidate Name";
    partyDisplay.textContent = document.getElementById('cand-party').value || "Select Party";
}

// Add event listeners for live preview sync
document.addEventListener('input', (e) => {
    if (['cand-name', 'cand-party'].includes(e.target.id)) {
        document.getElementById('previewName').textContent = document.getElementById('cand-name').value || "Candidate Name";
        document.getElementById('previewParty').textContent = document.getElementById('cand-party').value || "Select Party";
    }
});

async function addCandidate() {
    const name = document.getElementById('cand-name').value;
    const party = document.getElementById('cand-party').value;
    const slogan = document.getElementById('cand-slogan').value;
    const biography = document.getElementById('cand-bio').value;
    const logoFile = document.getElementById('cand-logo-file').files[0];
    const msgEl = document.getElementById('adminCandMsg');

    if (!name || !party || !logoFile) {
        showMsg(msgEl, "Name, Party, and Logo are required.", "error");
        return;
    }

    try {
        showMsg(msgEl, "Uploading secure logo...", "success");
        
        // 1. Upload Logo
        const formData = new FormData();
        formData.append('logo', logoFile);
        
        const uploadRes = await fetch(`${API_BASE}/admin/upload-logo`, {
            method: 'POST',
            body: formData
        });
        const uploadData = await uploadRes.json();
        
        if (!uploadRes.ok) throw new Error(uploadData.message || "Upload failed");
        
        const logoUrl = uploadData.logo_url;

        // 2. Add to Blockchain
        showMsg(msgEl, "Finalizing blockchain record...", "success");
        const res = await fetch(`${API_BASE}/admin/add-candidate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name, 
                party_name: party, 
                party_logo: logoUrl,
                slogan: slogan,
                biography: biography
            })
        });
        const data = await res.json();
        
        if (res.ok) {
            showMsg(msgEl, "Candidate successfully enrolled!", "success");
            updateActivityLog(`Candidate ${name} added to blockchain.`);
            // Clear form
            document.getElementById('cand-name').value = '';
            document.getElementById('cand-party').value = '';
            document.getElementById('cand-slogan').value = '';
            document.getElementById('cand-bio').value = '';
            document.getElementById('cand-logo-file').value = '';
            document.getElementById('logoPreviewImg').src = '';
            document.getElementById('logoPreviewImg').classList.add('hidden');
            document.getElementById('logoPlaceholder').classList.remove('hidden');
            document.getElementById('fileNameDisplay').textContent = "No file selected";
            fetchCandidates();
        } else {
            showMsg(msgEl, data.message, "error");
        }
    } catch (err) { 
        showMsg(msgEl, err.message || "Protocol error.", "error"); 
    }
}

async function deleteCandidate(id) {
    if (!confirm("Are you sure you want to delete this candidate? This can only be done before the election starts.")) return;
    
    try {
        const res = await fetch(`${API_BASE}/admin/delete-candidate/${id}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (res.ok) {
            alert("Candidate deleted from ballot.");
            fetchCandidates();
        } else {
            alert("Delete failed: " + data.message);
        }
    } catch (err) { alert("Connection Error."); }
}

async function fetchAdminCandidates() {
    const tbody = document.getElementById('adminCandidateTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = "<tr><td colspan='4' class='p-8 text-center'>Loading...</td></tr>";
    try {
        const res = await fetch(`${API_BASE}/candidates`);
        const candidates = await res.json();
        tbody.innerHTML = "";
        candidates.forEach(c => {
            const tr = document.createElement('tr');
            tr.className = "border-b border-slate-50 hover:bg-slate-50/50 transition";
            tr.innerHTML = `
                <td class="px-8 py-4">
                    <img src="${c.party_logo}" class="w-10 h-10 rounded-lg object-cover shadow-sm">
                </td>
                <td class="px-8 py-4 font-bold text-slate-800">${c.name}</td>
                <td class="px-8 py-4 text-slate-600">${c.party_name}</td>
                <td class="px-8 py-4">
                    <button onclick="deleteCandidate(${c.id})" class="text-xs font-bold text-red-500 hover:underline">Remove</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        if (candidates.length === 0) {
            tbody.innerHTML = "<tr><td colspan='4' class='p-8 text-center text-slate-400'>No active candidates.</td></tr>";
        }
    } catch (err) { tbody.innerHTML = "Error loading candidates."; }
}

async function fetchVoters() {
    const tbody = document.getElementById('voterTableBody');
    tbody.innerHTML = "<tr><td colspan='4' class='p-8 text-center'>Syncing registry...</td></tr>";
    try {
        const res = await fetch(`${API_BASE}/admin/voters`);
        const voters = await res.json();
        tbody.innerHTML = "";
        voters.forEach(v => {
            const tr = document.createElement('tr');
            tr.className = "border-b border-slate-50 hover:bg-slate-50/50 transition";
            tr.innerHTML = `
                <td class="px-8 py-4 font-bold text-slate-800">${v.voter_id}</td>
                <td class="px-8 py-4 text-slate-600">${v.name}</td>
                <td class="px-8 py-4 text-slate-400 text-sm">${v.email}</td>
                <td class="px-8 py-4 text-[10px] font-black uppercase tracking-widest ${v.has_voted ? 'text-green-500' : 'text-red-500'}">
                    ${v.has_voted ? '✓ Cast' : '○ Pending'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) { tbody.innerHTML = "Error loading voters."; }
}

// --- UTILS ---
function showMsg(el, text, type) {
    el.textContent = text;
    el.className = `message ${type}`;
    el.classList.remove('hidden');
}

function logout() {
    localStorage.clear();
    location.reload();
}

// Session Cleanup: Always return to landing page on refresh
localStorage.clear();
showSection('landingPage');
