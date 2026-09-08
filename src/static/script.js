let currentEmailId = null;
let isEditingReply = false;

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('pending-count').textContent = data.pending;
        document.getElementById('auto-count').textContent = data.auto_replied;
        document.getElementById('reviewed-count').textContent = data.reviewed;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadPendingEmails() {
    try {
        const response = await fetch('/api/pending-emails');
        const emails = await response.json();
        
        const emailList = document.getElementById('email-list');
        
        if (emails.length === 0) {
            emailList.innerHTML = '<p class="loading">No pending emails 🎉</p>';
            return;
        }
        
        emailList.innerHTML = emails.map(email => `
            <div class="email-item" onclick="viewEmail(${email.id})">
                <div class="email-subject">${escapeHtml(email.subject)}</div>
                <div class="email-sender">From: ${escapeHtml(email.sender)}</div>
                <div class="email-preview">${escapeHtml(email.body.substring(0, 50))}...</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading emails:', error);
    }
}

async function viewEmail(emailId) {
    try {
        const response = await fetch(`/api/email/${emailId}`);
        const email = await response.json();
        
        currentEmailId = emailId;
        isEditingReply = false;
        
        document.getElementById('detail-subject').textContent = email.subject;
        document.getElementById('detail-sender').textContent = email.sender;
        document.getElementById('detail-date').textContent = new Date(email.created_at).toLocaleString();
        document.getElementById('detail-body').textContent = email.body;
        document.getElementById('reply-text').value = email.suggested_reply || '';
        document.getElementById('reply-text').readOnly = true;
        
        document.getElementById('email-detail').style.display = 'flex';
        
        // Highlight active email
        document.querySelectorAll('.email-item').forEach((item, idx) => {
            item.classList.remove('active');
        });
        event.target.closest('.email-item').classList.add('active');
    } catch (error) {
        console.error('Error loading email:', error);
    }
}

function closeDetail() {
    document.getElementById('email-detail').style.display = 'none';
    currentEmailId = null;
}

function editReply() {
    isEditingReply = !isEditingReply;
    document.getElementById('reply-text').readOnly = !isEditingReply;
    
    if (isEditingReply) {
        document.getElementById('reply-text').focus();
    }
}

async function approveEmail() {
    if (!currentEmailId) return;
    
    const reply = document.getElementById('reply-text').value;
    
    try {
        await fetch(`/api/email/${currentEmailId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reply })
        });
        
        alert('✓ Email approved!');
        closeDetail();
        loadPendingEmails();
        loadStats();
    } catch (error) {
        console.error('Error approving email:', error);
        alert('Error approving email');
    }
}

async function rejectEmail() {
    if (!currentEmailId) return;
    
    try {
        await fetch(`/api/email/${currentEmailId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        alert('✗ Email rejected and escalated');
        closeDetail();
        loadPendingEmails();
        loadStats();
    } catch (error) {
        console.error('Error rejecting email:', error);
        alert('Error rejecting email');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
