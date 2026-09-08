async function loadStats() {
    const response = await fetch('/api/admin/stats');
    const data = await response.json();
    document.getElementById('stat-businesses').textContent = data.businesses;
    document.getElementById('stat-users').textContent = data.users;
    document.getElementById('stat-docs').textContent = data.documents;
}

async function loadBusinesses() {
    const response = await fetch('/api/admin/businesses');
    const businesses = await response.json();
    
    const list = document.getElementById('businesses-list');
    list.innerHTML = businesses.map(b => `
        <div class="business-card">
            <h3>${b.name}</h3>
            <p>${b.slug}</p>
            <p>${b.description}</p>
        </div>
    `).join('');
}

function showSection(section) {
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
    document.getElementById(section + '-section').style.display = 'block';
    
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
}

function showCreateBusiness() {
    const name = prompt('Business name:');
    const slug = prompt('Business slug:');
    
    if (name && slug) {
        fetch('/api/admin/businesses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, slug})
        }).then(() => {
            loadBusinesses();
            alert('Business created!');
        });
    }
}
