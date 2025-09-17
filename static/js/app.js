/* LegalSaathi Document Advisor - JavaScript Functionality */

// Loading overlay functionality
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    const progressBar = overlay.querySelector('.analysis-progress-bar');
    
    if (!overlay) return;
    
    overlay.style.display = 'flex';
    
    // Simulate progress with realistic timing
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10 + 5; // Progress between 5-15% each step
        if (progress > 90) progress = 90; // Cap at 90% until completion
        progressBar.style.width = progress + '%';
    }, 800);
    
    // Store interval for cleanup
    overlay.dataset.interval = interval;
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;
    
    const interval = overlay.dataset.interval;
    
    if (interval) {
        clearInterval(interval);
    }
    
    // Complete the progress bar
    const progressBar = overlay.querySelector('.analysis-progress-bar');
    progressBar.style.width = '100%';
    
    // Hide after a brief delay to show completion
    setTimeout(() => {
        overlay.style.display = 'none';
        progressBar.style.width = '0%';
    }, 800);
}

// Document ready functionality
document.addEventListener('DOMContentLoaded', function() {
    // If we're on the results page, hide any loading that might be showing
    if (window.location.pathname.includes('/analyze') || 
        document.querySelector('.clause-analysis-item')) {
        hideLoading();
    }
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to all form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Show loading for analysis forms
                if (form.action.includes('/analyze') || form.method.toLowerCase() === 'post') {
                    showLoading();
                    
                    // Update button state
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
                    
                    // Store original text for potential restoration
                    submitBtn.dataset.originalText = originalText;
                }
            }
        });
    });
    
    // Add enhanced tooltips for traffic lights
    const trafficLights = document.querySelectorAll('.traffic-light, .traffic-light-medium, .traffic-light-large');
    trafficLights.forEach(light => {
        if (!light.title) {
            if (light.classList.contains('red')) {
                light.title = 'High Risk - Requires immediate attention';
            } else if (light.classList.contains('yellow')) {
                light.title = 'Moderate Risk - Review recommended';
            } else if (light.classList.contains('green')) {
                light.title = 'Low Risk - Standard terms';
            }
        }
    });
    
    // Add print functionality
    const printButtons = document.querySelectorAll('[onclick*="print"]');
    printButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });
    
    // Add copy to clipboard functionality for analysis results
    const analysisResults = document.querySelector('.clause-analysis-item');
    if (analysisResults) {
        // Add a copy button to the results page
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-outline-secondary btn-sm position-fixed';
        copyBtn.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000;';
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy Results';
        copyBtn.title = 'Copy analysis results to clipboard';
        
        copyBtn.addEventListener('click', async function() {
            try {
                const resultsText = extractAnalysisText();
                await navigator.clipboard.writeText(resultsText);
                
                // Show success feedback
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="bi bi-check"></i> Copied!';
                copyBtn.classList.add('btn-success');
                copyBtn.classList.remove('btn-outline-secondary');
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.classList.remove('btn-success');
                    copyBtn.classList.add('btn-outline-secondary');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text: ', err);
                // Fallback for older browsers
                fallbackCopyTextToClipboard(extractAnalysisText());
            }
        });
        
        document.body.appendChild(copyBtn);
    }
});

// Extract analysis text for copying
function extractAnalysisText() {
    const title = document.querySelector('h2')?.textContent || 'Document Analysis Results';
    const overallRisk = document.querySelector('.card-header h3')?.textContent || '';
    const summary = document.querySelector('.alert.lead')?.textContent || '';
    
    let text = `${title}\n${'='.repeat(title.length)}\n\n`;
    text += `${overallRisk}\n${'-'.repeat(overallRisk.length)}\n`;
    text += `${summary}\n\n`;
    
    // Add clause analysis
    const clauses = document.querySelectorAll('.clause-analysis-item');
    clauses.forEach((clause, index) => {
        const clauseTitle = clause.querySelector('h5')?.textContent || `Clause ${index + 1}`;
        const explanation = clause.querySelector('.alert p')?.textContent || '';
        const riskLevel = clause.querySelector('.badge')?.textContent || '';
        
        text += `${clauseTitle} (${riskLevel})\n`;
        text += `${explanation}\n\n`;
    });
    
    return text;
}

// Fallback copy function for older browsers
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        console.log('Fallback: Copying text command was successful');
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + P for print
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
    
    // Escape to hide loading overlay (emergency)
    if (e.key === 'Escape') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay && overlay.style.display === 'flex') {
            hideLoading();
        }
    }
});

// Handle page visibility changes (hide loading if user switches tabs)
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Check if we're on results page and hide loading
        if (window.location.pathname.includes('/analyze') || 
            document.querySelector('.clause-analysis-item')) {
            setTimeout(hideLoading, 500);
        }
    }
});

// Add error handling for failed requests
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    hideLoading(); // Hide loading on any JavaScript errors
});

// Add network error handling
window.addEventListener('online', function() {
    console.log('Network connection restored');
});

window.addEventListener('offline', function() {
    console.log('Network connection lost');
    hideLoading(); // Hide loading if network is lost
});