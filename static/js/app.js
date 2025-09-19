/* LegalSaathi Document Advisor - Enhanced JavaScript Functionality */

// Translation functionality
let currentLanguage = 'en';
const supportedLanguages = {
    'en': 'English',
    'hi': 'Hindi (हिंदी)',
    'es': 'Spanish (Español)',
    'fr': 'French (Français)',
    'de': 'German (Deutsch)',
    'pt': 'Portuguese (Português)',
    'ar': 'Arabic (العربية)',
    'zh': 'Chinese (中文)',
    'ja': 'Japanese (日本語)',
    'ko': 'Korean (한국어)'
};

async function translateResults(targetLanguage) {
    if (targetLanguage === currentLanguage) return;
    
    try {
        showNotification('Translating results...', 'info');
        
        // Get all translatable elements
        const elementsToTranslate = document.querySelectorAll('[data-translatable]');
        
        for (const element of elementsToTranslate) {
            const originalText = element.textContent;
            if (originalText.trim()) {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: originalText,
                        target_language: targetLanguage,
                        source_language: currentLanguage
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    element.textContent = result.translated_text;
                }
            }
        }
        
        currentLanguage = targetLanguage;
        showNotification(`Results translated to ${supportedLanguages[targetLanguage]}`, 'success');
        
    } catch (error) {
        console.error('Translation error:', error);
        showNotification('Translation failed. Please try again.', 'error');
    }
}

function initializeLanguageSelector() {
    const languageSelector = document.getElementById('languageSelector');
    if (!languageSelector) return;
    
    // Populate language options
    Object.entries(supportedLanguages).forEach(([code, name]) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        languageSelector.appendChild(option);
    });
    
    // Add change event listener
    languageSelector.addEventListener('change', (e) => {
        translateResults(e.target.value);
    });
}

// Enhanced loading overlay functionality with better progress simulation
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    const progressBar = overlay.querySelector('.analysis-progress-bar');
    const loadingText = overlay.querySelector('.loading-text');
    const loadingSubtext = overlay.querySelector('.loading-subtext');

    if (!overlay) return;

    overlay.style.display = 'flex';

    // Enhanced progress simulation with realistic stages
    let progress = 0;
    let stage = 0;
    const stages = [
        { text: 'Analyzing Your Document', subtext: 'Our AI is carefully reviewing your legal document...', duration: 1000 },
        { text: 'Identifying Clauses', subtext: 'Breaking down the document into key sections...', duration: 800 },
        { text: 'Assessing Risk Levels', subtext: 'Evaluating each clause for potential concerns...', duration: 1200 },
        { text: 'Generating Explanations', subtext: 'Creating plain-language explanations...', duration: 900 },
        { text: 'Finalizing Results', subtext: 'Preparing your comprehensive analysis...', duration: 600 }
    ];

    function updateStage() {
        if (stage < stages.length) {
            const currentStage = stages[stage];
            loadingText.textContent = currentStage.text;
            loadingSubtext.textContent = currentStage.subtext;

            // Add animation class
            loadingText.classList.add('fade-in-up');
            loadingSubtext.classList.add('fade-in-up');

            setTimeout(() => {
                loadingText.classList.remove('fade-in-up');
                loadingSubtext.classList.remove('fade-in-up');
            }, 500);

            stage++;
            setTimeout(updateStage, currentStage.duration);
        }
    }

    // Start stage updates
    updateStage();

    // Simulate realistic progress
    const interval = setInterval(() => {
        const increment = Math.random() * 8 + 3; // Progress between 3-11% each step
        progress = Math.min(progress + increment, 92); // Cap at 92% until completion
        progressBar.style.width = progress + '%';

        // Add some visual feedback
        if (progress > 25 && progress < 30) {
            progressBar.style.background = 'linear-gradient(90deg, #007bff, #17a2b8)';
        } else if (progress > 60 && progress < 65) {
            progressBar.style.background = 'linear-gradient(90deg, #17a2b8, #28a745)';
        }
    }, 600);

    // Store interval for cleanup
    overlay.dataset.interval = interval;
    overlay.dataset.startTime = Date.now();
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (!overlay) return;

    const interval = overlay.dataset.interval;
    const startTime = overlay.dataset.startTime;

    if (interval) {
        clearInterval(interval);
    }

    // Complete the progress bar with success animation
    const progressBar = overlay.querySelector('.analysis-progress-bar');
    const loadingText = overlay.querySelector('.loading-text');
    const loadingSubtext = overlay.querySelector('.loading-subtext');

    progressBar.style.width = '100%';
    progressBar.style.background = 'linear-gradient(90deg, #28a745, #20c997)';

    // Show completion message
    if (loadingText && loadingSubtext) {
        loadingText.textContent = 'Analysis Complete!';
        loadingSubtext.textContent = 'Redirecting to your results...';
        loadingText.classList.add('success-bounce');
    }

    // Calculate minimum display time (ensure at least 2 seconds for UX)
    const elapsedTime = startTime ? Date.now() - parseInt(startTime) : 0;
    const minDisplayTime = 2000;
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime);

    // Hide after completion animation
    setTimeout(() => {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
            overlay.style.opacity = '1';
            progressBar.style.width = '0%';
            progressBar.style.background = 'linear-gradient(90deg, #007bff, #28a745)';

            // Reset text
            if (loadingText && loadingSubtext) {
                loadingText.textContent = 'Analyzing Your Document';
                loadingSubtext.textContent = 'Our AI is carefully reviewing your legal document...';
                loadingText.classList.remove('success-bounce');
            }
        }, 300);
    }, Math.max(800, remainingTime));
}

// Enhanced document ready functionality with better UX
document.addEventListener('DOMContentLoaded', function () {
    // Initialize page
    initializePage();

    // If we're on the results page, hide any loading that might be showing
    if (window.location.pathname.includes('/analyze') ||
        document.querySelector('.clause-analysis-item')) {
        hideLoading();
        animateResults();
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

    // Add keyboard navigation support
    setupKeyboardNavigation();

    // Add connection status indicator
    setupConnectionMonitoring();
});

// Initialize page with animations and accessibility
function initializePage() {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.container');
    if (mainContent) {
        mainContent.classList.add('slide-in-up');
    }

    // Setup accessibility features
    setupAccessibilityFeatures();

    // Add skip link for keyboard users
    addSkipLink();
}

// Animate results page elements
function animateResults() {
    const clauseItems = document.querySelectorAll('.clause-analysis-item');
    clauseItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';

        setTimeout(() => {
            item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 150);
    });
}

// Setup keyboard navigation
function setupKeyboardNavigation() {
    // Add keyboard support for file upload area
    const fileUploadArea = document.getElementById('fileUploadArea');
    if (fileUploadArea) {
        fileUploadArea.setAttribute('tabindex', '0');
        fileUploadArea.setAttribute('role', 'button');
        fileUploadArea.setAttribute('aria-label', 'Click to upload file or drag and drop');

        fileUploadArea.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                document.getElementById('document_file').click();
            }
        });
    }
}

// Setup accessibility features
function setupAccessibilityFeatures() {
    // Add ARIA labels to traffic lights
    document.querySelectorAll('.traffic-light, .traffic-light-medium, .traffic-light-large').forEach(light => {
        if (light.classList.contains('red')) {
            light.setAttribute('aria-label', 'High risk indicator');
            light.setAttribute('role', 'img');
        } else if (light.classList.contains('yellow')) {
            light.setAttribute('aria-label', 'Moderate risk indicator');
            light.setAttribute('role', 'img');
        } else if (light.classList.contains('green')) {
            light.setAttribute('aria-label', 'Low risk indicator');
            light.setAttribute('role', 'img');
        }
    });

    // Add live region for dynamic content
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.id = 'live-region';
    document.body.appendChild(liveRegion);
}

// Add skip link for accessibility
function addSkipLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);

    // Add main content ID if not present
    const mainContent = document.querySelector('.container');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
}

// Setup connection monitoring
function setupConnectionMonitoring() {
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'status-indicator online';
    statusIndicator.title = 'Connection status';
    statusIndicator.setAttribute('aria-label', 'Online');

    // Add to navbar if present
    const navbar = document.querySelector('.navbar .container');
    if (navbar) {
        const statusContainer = document.createElement('div');
        statusContainer.className = 'd-flex align-items-center';
        statusContainer.appendChild(statusIndicator);
        navbar.appendChild(statusContainer);
    }

    // Monitor connection
    window.addEventListener('online', () => {
        statusIndicator.className = 'status-indicator online';
        statusIndicator.setAttribute('aria-label', 'Online');
        showNotification('Connection restored', 'success');
    });

    window.addEventListener('offline', () => {
        statusIndicator.className = 'status-indicator offline';
        statusIndicator.setAttribute('aria-label', 'Offline');
        showNotification('Connection lost', 'warning');
    });
}

// Enhanced form handling with better loading states
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Show loading for analysis forms
                if (form.action.includes('/analyze') || form.method.toLowerCase() === 'post') {
                    showLoading();

                    // Enhanced button loading state
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.classList.add('btn-loading');
                    submitBtn.innerHTML = '<span class="sr-only">Processing...</span>';
                    submitBtn.setAttribute('aria-label', 'Processing your request');

                    // Store original text for potential restoration
                    submitBtn.dataset.originalText = originalText;

                    // Announce to screen readers
                    announceToScreenReader('Analysis started. Please wait...');
                }
            }
        });
    });
});

// Enhanced notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification slide-in-up`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-radius: 8px;
    `;

    const icon = {
        success: 'bi-check-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        danger: 'bi-x-circle-fill',
        info: 'bi-info-circle-fill'
    }[type] || 'bi-info-circle-fill';

    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi ${icon} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto-remove
    const timer = setTimeout(() => {
        removeNotification(notification);
    }, duration);

    // Manual close
    notification.querySelector('.btn-close').addEventListener('click', () => {
        clearTimeout(timer);
        removeNotification(notification);
    });

    // Announce to screen readers
    announceToScreenReader(message);
}

function removeNotification(notification) {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

// Screen reader announcements
function announceToScreenReader(message) {
    const liveRegion = document.getElementById('live-region');
    if (liveRegion) {
        liveRegion.textContent = message;
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
}

// Add enhanced tooltips for traffic lights
document.addEventListener('DOMContentLoaded', function() {
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
        btn.addEventListener('click', function (e) {
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

        copyBtn.addEventListener('click', async function () {
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
        // Using deprecated execCommand as fallback for older browsers
        const successful = document.execCommand('copy');
        if (successful) {
            console.log('Fallback: Copying text command was successful');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }

    document.body.removeChild(textArea);
}

// Add keyboard shortcuts
document.addEventListener('keydown', function (e) {
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
document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
        // Check if we're on results page and hide loading
        if (window.location.pathname.includes('/analyze') ||
            document.querySelector('.clause-analysis-item')) {
            setTimeout(hideLoading, 500);
        }
    }
});

// Add error handling for failed requests
window.addEventListener('error', function (e) {
    console.error('JavaScript error:', e.error);
    hideLoading(); // Hide loading on any JavaScript errors
});

// Add network error handling
window.addEventListener('online', function () {
    console.log('Network connection restored');
});

window.addEventListener('offline', function () {
    console.log('Network connection lost');
    hideLoading(); // Hide loading if network is lost
});