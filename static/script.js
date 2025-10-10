// Global variables
let allLeads = [];

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadLeads();
    
    // Event listeners
    document.getElementById('scrapeBtn').addEventListener('click', scrapeLeads);
    document.getElementById('exportBtn').addEventListener('click', exportLeads);
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
    
    // Enter key to scrape
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            scrapeLeads();
        }
    });
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('totalLeads').textContent = data.total_leads;
        document.getElementById('avgScore').textContent = data.avg_score;
        document.getElementById('validEmails').textContent = data.valid_emails;
        
        // Calculate quality rate
        const qualityRate = data.total_leads > 0 
            ? Math.round((data.valid_emails / data.total_leads) * 100) 
            : 0;
        document.getElementById('conversionRate').textContent = qualityRate + '%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load all leads
async function loadLeads() {
    try {
        const response = await fetch('/api/leads');
        const data = await response.json();
        allLeads = data.leads;
        displayLeads(allLeads);
    } catch (error) {
        console.error('Error loading leads:', error);
    }
}

// Scrape new leads
async function scrapeLeads() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a company URL');
        return;
    }
    
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    
    // Show loading state
    scrapeBtn.disabled = true;
    loadingIndicator.style.display = 'flex';
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                type: 'url'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload leads and stats
            await loadLeads();
            await loadStats();
            
            // Clear input
            searchInput.value = '';
            
            // Show success message
            showNotification('Successfully scraped and enriched ' + data.count + ' lead(s)!', 'success');
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Error scraping leads: ' + error.message, 'error');
    } finally {
        scrapeBtn.disabled = false;
        loadingIndicator.style.display = 'none';
    }
}

// Display leads in table
function displayLeads(leads) {
    const tbody = document.getElementById('leadsTableBody');
    
    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="9">
                    <i class="fas fa-inbox"></i>
                    <p>No leads found. Try adjusting your filters or scrape new leads!</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = leads.map(lead => `
        <tr>
            <td>
                <span class="score-badge ${getScoreClass(lead.lead_score)}">
                    ${lead.lead_score}
                </span>
            </td>
            <td>
                <strong>${lead.company_name || 'Unknown'}</strong>
                <br>
                <small style="color: var(--text-secondary);">${lead.url || ''}</small>
            </td>
            <td>${lead.industry || 'N/A'}</td>
            <td>
                ${lead.email ? `
                    <div>
                        ${lead.email}
                        ${lead.email_valid ? 
                            '<i class="fas fa-check-circle" style="color: var(--success);"></i>' : 
                            '<i class="fas fa-times-circle" style="color: var(--danger);"></i>'
                        }
                    </div>
                    <small style="color: var(--text-secondary);">
                        Confidence: ${lead.email_confidence || 0}%
                    </small>
                ` : 'N/A'}
            </td>
            <td>${lead.phone || 'N/A'}</td>
            <td>${lead.employee_estimate || 'N/A'}</td>
            <td>${lead.revenue_estimate || 'N/A'}</td>
            <td>
                <div class="tech-stack">
                    ${(lead.tech_stack || []).slice(0, 3).map(tech => 
                        `<span class="tech-badge">${tech}</span>`
                    ).join('')}
                    ${(lead.tech_stack || []).length > 3 ? 
                        `<span class="tech-badge">+${(lead.tech_stack || []).length - 3}</span>` : 
                        ''
                    }
                </div>
            </td>
            <td>
                <button class="btn-view" onclick="viewLeadDetails(${leads.indexOf(lead)})">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
}

// Get score badge class
function getScoreClass(score) {
    if (score >= 70) return 'score-high';
    if (score >= 40) return 'score-medium';
    return 'score-low';
}

// View lead details in modal
function viewLeadDetails(index) {
    const lead = allLeads[index];
    const modal = document.getElementById('leadModal');
    const detailsDiv = document.getElementById('leadDetails');
    
    detailsDiv.innerHTML = `
        <h2>${lead.company_name}</h2>
        <div style="margin-top: 1.5rem;">
            <h3>Company Information</h3>
            <p><strong>Website:</strong> <a href="${lead.url}" target="_blank">${lead.url}</a></p>
            <p><strong>Industry:</strong> ${lead.industry || 'N/A'}</p>
            <p><strong>Description:</strong> ${lead.description || 'N/A'}</p>
            <p><strong>Domain Age:</strong> ${lead.domain_age_years || 'Unknown'} years</p>
            
            <h3 style="margin-top: 1.5rem;">Contact Information</h3>
            <p><strong>Email:</strong> ${lead.email || 'N/A'} 
                ${lead.email_valid ? '✓ Verified' : '✗ Unverified'}
            </p>
            <p><strong>Phone:</strong> ${lead.phone || 'N/A'}</p>
            <p><strong>Contact Quality:</strong> ${lead.contact_quality || 'N/A'}/5 ⭐</p>
            
            <h3 style="margin-top: 1.5rem;">Company Size & Revenue</h3>
            <p><strong>Employees:</strong> ${lead.employee_estimate || 'N/A'}</p>
            <p><strong>Revenue Estimate:</strong> ${lead.revenue_estimate || 'N/A'}</p>
            
            <h3 style="margin-top: 1.5rem;">Technology Stack</h3>
            <div class="tech-stack">
                ${(lead.tech_stack || ['Unknown']).map(tech => 
                    `<span class="tech-badge">${tech}</span>`
                ).join('')}
            </div>
            
            <h3 style="margin-top: 1.5rem;">Lead Score Analysis</h3>
            <p><strong>Overall Score:</strong> <span class="score-badge ${getScoreClass(lead.lead_score)}">${lead.lead_score}/100</span></p>
            
            <h3 style="margin-top: 1.5rem;">Social Media</h3>
            ${Object.keys(lead.social_links || {}).length > 0 ? 
                Object.entries(lead.social_links).map(([platform, url]) => 
                    `<p><strong>${platform.charAt(0).toUpperCase() + platform.slice(1)}:</strong> 
                    <a href="${url}" target="_blank">${url}</a></p>`
                ).join('') :
                '<p>No social links found</p>'
            }
        </div>
    `;
    
    modal.style.display = 'block';
    
    // Close modal
    const closeBtn = document.getElementsByClassName('close')[0];
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    };
    
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
}

// Apply filters
async function applyFilters() {
    const minScore = parseInt(document.getElementById('minScore').value) || 0;
    const industry = document.getElementById('industryFilter').value.trim();
    const hasEmail = document.getElementById('emailFilter').checked;
    
    try {
        const response = await fetch('/api/leads/filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                min_score: minScore,
                industry: industry,
                has_email: hasEmail
            })
        });
        
        const data = await response.json();
        displayLeads(data.leads);
        showNotification(`Found ${data.count} matching leads`, 'success');
    } catch (error) {
        showNotification('Error filtering leads: ' + error.message, 'error');
    }
}

// Reset filters
function resetFilters() {
    document.getElementById('minScore').value = '';
    document.getElementById('industryFilter').value = '';
    document.getElementById('emailFilter').checked = false;
    displayLeads(allLeads);
    showNotification('Filters reset', 'success');
}

// Export leads to CSV
async function exportLeads() {
    if (allLeads.length === 0) {
        showNotification('No leads to export', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/export');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `leads_export_${new Date().getTime()}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('Leads exported successfully!', 'success');
        } else {
            showNotification('Error exporting leads', 'error');
        }
    } catch (error) {
        showNotification('Error exporting leads: ' + error.message, 'error');
    }
}

// Show notification
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles if not already added
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 500;
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            
            .notification-success {
                background: var(--success);
                color: white;
            }
            
            .notification-error {
                background: var(--danger);
                color: white;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}