let currentEmailId = null;

async function loadStats() {
    const response = await fetch('/api/stats');
    const data = await response.json();
    document.getElementById('pending-count').textContent = data.pending;
    document.getElementById('auto-count').textContent = data.auto_replied;
    document.getElementById('total-count').textContent = data.total;
}

async function loadPendingEmails() {
    const response = await fetch('/api/pending-emails');
    const emails = await response.json();
    const list = document.getElementById('email-list');
    
    if (emails.length === 0) {
        list.innerHTML = '<p class="loading">No pending emails 🎉</p>';
        return;
    }
    
    list.innerHTML = emails.map(e => `
        <div class="email-item" onclick="viewEmail(${e.id})">
            <div class="email-subject">${e.subject}</div>
            <div class="email-sender">From: ${e.sender}</div>
            <div class="email-preview">${e.body.substring(0, 50)}...</div>
        </div>
    `).join('');
}

async function viewEmail(id) {
    const response = await fetch(`/api/email/${id}`);
    const email = await response.json();
    
    currentEmailId = id;
    document.getElementById('detail-subject').textContent = email.subject;
    document.getElementById('detail-sender').textContent = email.sender;
    document.getElementById('detail-date').textContent = new Date(email.created_at).toLocaleString();
    document.getElementById('detail-body').textContent = email.body;
    document.getElementById('reply-text').value = email.suggested_reply || '';
    document.getElementById('email-detail').style.display = 'flex';
}

function closeDetail() {
    document.getElementById('email-detail').style.display = 'none';
}

async function approveEmail() {
    await fetch(`/api/email/${currentEmailId}/approve`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})});
    closeDetail();
    loadPendingEmails();
    loadStats();
}

async function rejectEmail() {
    await fetch(`/api/email/${currentEmailId}/reject`, {method: 'POST'});
    closeDetail();
    loadPendingEmails();
    loadStats();
}
