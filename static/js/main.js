// JobSphere ATS Frontend Application Logic

document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initRealtimeSearch();
    initApplicationModal();
    initRecruiterActions();
});

/* ==========================================================================
   1. Theme Toggle (Dark / Light Mode)
   ========================================================================== */
function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

/* ==========================================================================
   2. Real-time Keyword & Skill Search
   ========================================================================== */
function initRealtimeSearch() {
    const searchInput = document.getElementById('keyword-search');
    const locationSelect = document.getElementById('location-filter');
    const typeSelect = document.getElementById('type-filter');
    const jobCards = document.querySelectorAll('.job-card-item');
    const countBadge = document.getElementById('jobs-count-badge');
    
    if (!searchInput && !locationSelect && !typeSelect) return;

    function filterJobs() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedLoc = locationSelect ? locationSelect.value.toLowerCase() : '';
        const selectedType = typeSelect ? typeSelect.value.toUpperCase() : '';
        
        let visibleCount = 0;

        jobCards.forEach(card => {
            // Read card metadata for matching
            const title = card.getAttribute('data-title').toLowerCase();
            const company = card.getAttribute('data-company').toLowerCase();
            const description = card.getAttribute('data-description').toLowerCase();
            const skills = card.getAttribute('data-skills').toLowerCase();
            const location = card.getAttribute('data-location').toLowerCase();
            const type = card.getAttribute('data-type'); // e.g. FULL, PART, REMOTE, INTERN
            
            // Search text includes title, company, skills, description, location
            const matchesQuery = query === '' || 
                                 title.includes(query) || 
                                 company.includes(query) || 
                                 description.includes(query) || 
                                 skills.includes(query) ||
                                 location.includes(query);
                                 
            // Filter checks
            const matchesLocation = selectedLoc === '' || location.includes(selectedLoc);
            const matchesType = selectedType === '' || type === selectedType;

            if (matchesQuery && matchesLocation && matchesType) {
                card.style.display = 'block';
                visibleCount++;
                // Add micro-animation fade-in class
                card.classList.add('fade-in-quick');
            } else {
                card.style.display = 'none';
                card.classList.remove('fade-in-quick');
            }
        });

        // Update display counter if it exists
        if (countBadge) {
            countBadge.textContent = `${visibleCount} active position${visibleCount !== 1 ? 's' : ''}`;
        }
        
        // Show/hide empty state message
        const emptyState = document.getElementById('empty-state-message');
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    if (searchInput) searchInput.addEventListener('input', filterJobs);
    if (locationSelect) locationSelect.addEventListener('change', filterJobs);
    if (typeSelect) typeSelect.addEventListener('change', filterJobs);
}

/* ==========================================================================
   3. Job Application Modal & Form Submission
   ========================================================================== */
function initApplicationModal() {
    const applyModalEl = document.getElementById('applyModal');
    if (!applyModalEl) return;

    // Listen to "Apply Now" buttons to populate modal fields
    const applyButtons = document.querySelectorAll('.btn-apply-trigger');
    applyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            const jobTitle = this.getAttribute('data-job-title');
            const companyName = this.getAttribute('data-company-name');
            
            // Set fields in the modal form
            const form = document.getElementById('job-application-form');
            if (form) {
                form.action = `/job/${jobId}/apply/`;
                form.setAttribute('data-job-id', jobId);
            }
            
            const modalTitleSpan = document.getElementById('modal-job-title');
            const modalCompanySpan = document.getElementById('modal-company-name');
            
            if (modalTitleSpan) modalTitleSpan.textContent = jobTitle;
            if (modalCompanySpan) modalCompanySpan.textContent = companyName;
            
            // Clean previous errors / messages
            clearFormErrors();
        });
    });

    // Client-side Validation and AJAX Submission
    const form = document.getElementById('job-application-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            clearFormErrors();
            
            if (validateApplicationForm()) {
                submitApplicationAJAX(this);
            }
        });
    }
}

// Client side inputs validator
function validateApplicationForm() {
    let isValid = true;
    
    const fullName = document.getElementById('id_full_name');
    const email = document.getElementById('id_email');
    const phone = document.getElementById('id_phone');
    const portfolioUrl = document.getElementById('id_portfolio_url');
    const skills = document.getElementById('id_skills');
    
    // Helper to display input error
    function showError(element, message) {
        element.classList.add('is-invalid');
        const feedback = element.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = message;
        } else {
            const div = document.createElement('div');
            div.className = 'invalid-feedback';
            div.textContent = message;
            element.parentNode.insertBefore(div, element.nextSibling);
        }
        isValid = false;
    }

    // 1. Full name validation
    if (!fullName.value.trim()) {
        showError(fullName, 'Please enter your full name.');
    }

    // 2. Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.value.trim()) {
        showError(email, 'Email address is required.');
    } else if (!emailRegex.test(email.value.trim())) {
        showError(email, 'Please enter a valid email address.');
    }

    // 3. Phone validation (numbers, spaces, plus, dashes, parenthesis; length: 7-15 digits)
    const rawPhoneDigits = phone.value.replace(/\D/g, '');
    if (!phone.value.trim()) {
        showError(phone, 'Phone number is required.');
    } else if (rawPhoneDigits.length < 7 || rawPhoneDigits.length > 15) {
        showError(phone, 'Please enter a valid phone number (between 7 and 15 digits).');
    }

    // 4. Portfolio URL validation
    if (portfolioUrl.value.trim()) {
        try {
            new URL(portfolioUrl.value.trim());
        } catch (_) {
            showError(portfolioUrl, 'Please enter a valid URL (e.g. https://github.com/name).');
        }
    }

    // 5. Skills character and empty limits (required, e.g. under 200 chars)
    if (!skills.value.trim()) {
        showError(skills, 'Please enter at least one skill tag.');
    } else if (skills.value.length > 200) {
        showError(skills, `Skills tags must be under 200 characters (currently: ${skills.value.length}).`);
    }

    return isValid;
}

function clearFormErrors() {
    const inputs = document.querySelectorAll('#job-application-form .form-control');
    inputs.forEach(input => {
        input.classList.remove('is-invalid');
    });
    
    const banner = document.getElementById('modal-error-banner');
    if (banner) {
        banner.style.display = 'none';
        banner.textContent = '';
    }
}

function submitApplicationAJAX(formElement) {
    const submitBtn = formElement.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    
    // Show spinner/loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin me-2"></i> Submitting...';
    
    const formData = new FormData(formElement);
    formData.append('ajax', 'true');
    
    const csrfToken = formElement.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(formElement.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => {
        return response.json().then(data => {
            if (!response.ok) {
                throw data;
            }
            return data;
        });
    })
    .then(data => {
        // Success
        submitBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i> Application Submitted!';
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-success');
        
        // Show success alert in modal
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success mt-3';
        successDiv.innerHTML = `<i class="fa-solid fa-circle-check me-2"></i> ${data.message}`;
        formElement.appendChild(successDiv);
        
        showNotification(data.message, 'success');
        
        // Reset and close modal
        setTimeout(() => {
            formElement.reset();
            successDiv.remove();
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            submitBtn.classList.remove('btn-success');
            submitBtn.classList.add('btn-primary');
            
            // Hide modal
            const bootstrapModal = bootstrap.Modal.getInstance(document.getElementById('applyModal'));
            if (bootstrapModal) bootstrapModal.hide();
        }, 2000);
    })
    .catch(errorData => {
        // Reset button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        // Display validation errors or backend message
        const banner = document.getElementById('modal-error-banner');
        if (banner) {
            banner.style.display = 'block';
            banner.textContent = errorData.error || 'Please correct the errors in the form below.';
        }
        
        // Map individual field errors
        if (errorData.errors) {
            for (const [field, message] of Object.entries(errorData.errors)) {
                const element = document.getElementById(`id_${field}`);
                if (element) {
                    element.classList.add('is-invalid');
                    const feedback = element.nextElementSibling;
                    if (feedback && feedback.classList.contains('invalid-feedback')) {
                        feedback.textContent = message;
                    }
                }
            }
        }
    });
}

/* ==========================================================================
   4. Recruiter Dashboard Kanban Board Actions
   ========================================================================== */
function initRecruiterActions() {
    const kanbanBoard = document.querySelector('.kanban-board');
    if (!kanbanBoard) return;

    // Delegate click events on kanban board buttons
    kanbanBoard.addEventListener('click', function(e) {
        const actionButton = e.target.closest('.btn-kanban-action');
        if (!actionButton) return;

        const card = actionButton.closest('.kanban-card');
        if (!card) return;

        const applicationId = card.getAttribute('data-application-id');
        const currentStage = card.getAttribute('data-status');
        
        let newStage = '';
        
        if (actionButton.classList.contains('btn-move-left')) {
            newStage = getAdjacentStage(currentStage, -1);
        } else if (actionButton.classList.contains('btn-move-right')) {
            newStage = getAdjacentStage(currentStage, 1);
        } else if (actionButton.classList.contains('btn-reject')) {
            newStage = 'REJECTED';
        }
        
        if (newStage && newStage !== currentStage) {
            updateApplicationStatusAJAX(applicationId, newStage, card);
        }
    });
}

const STAGES_ORDER = ['APPLIED', 'REVIEW', 'SHORTLIST', 'REJECTED'];

function getAdjacentStage(currentStage, direction) {
    const currentIndex = STAGES_ORDER.indexOf(currentStage);
    if (currentIndex === -1) return null;
    
    // We don't slide through REJECTED easily in linear order, 
    // but the prompt says 'Applied', 'Under Review', 'Shortlisted', 'Rejected'.
    // Moving right from shortlist goes to nowhere, reject takes directly to rejected.
    // Moving left from review goes to applied, from shortlist goes to review, from rejected goes to review (or shortlist).
    // Let's implement normal pipeline progression: APPLIED <-> REVIEW <-> SHORTLIST
    // REJECTED is a terminal state that you click explicitly, but you can move it back to REVIEW to reconsider.
    
    let targetIndex = currentIndex + direction;
    
    // Boundaries
    if (currentStage === 'REJECTED' && direction === -1) {
        return 'REVIEW'; // Move rejected back to review
    }
    
    if (targetIndex < 0 || targetIndex >= 3) { // Cap right movement at SHORTLIST (index 2)
        return null;
    }
    
    return STAGES_ORDER[targetIndex];
}

function updateApplicationStatusAJAX(applicationId, newStage, cardElement) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Add opacity styling to show processing
    cardElement.style.opacity = '0.5';
    
    fetch(`/application/${applicationId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: newStage })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Move card in DOM
            moveCardToColumn(cardElement, newStage);
            showNotification(data.message, 'success');
        } else {
            cardElement.style.opacity = '1';
            showNotification(data.error || 'Failed to update status.', 'danger');
        }
    })
    .catch(error => {
        cardElement.style.opacity = '1';
        showNotification('An error occurred. Please try again.', 'danger');
        console.error('Error updating status:', error);
    });
}

function moveCardToColumn(cardElement, targetStage) {
    const targetColumn = document.querySelector(`.kanban-col[data-stage="${targetStage}"] .kanban-cards`);
    if (!targetColumn) return;
    
    // Remove processing opacity
    cardElement.style.opacity = '1';
    
    // Update card dataset status attribute
    cardElement.setAttribute('data-status', targetStage);
    
    // Update action buttons on the card based on its new position
    updateCardActionButtons(cardElement, targetStage);
    
    // Move card in DOM
    targetColumn.appendChild(cardElement);
    
    // Smooth scroll card into view inside column
    cardElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Re-calculate all counters
    recalculateDashboardCounters();
}

function updateCardActionButtons(cardElement, stage) {
    const moveLeftBtn = cardElement.querySelector('.btn-move-left');
    const moveRightBtn = cardElement.querySelector('.btn-move-right');
    const rejectBtn = cardElement.querySelector('.btn-reject');
    
    if (stage === 'APPLIED') {
        if (moveLeftBtn) moveLeftBtn.style.display = 'none';
        if (moveRightBtn) moveRightBtn.style.display = 'inline-flex';
        if (rejectBtn) rejectBtn.style.display = 'inline-flex';
    } else if (stage === 'REVIEW') {
        if (moveLeftBtn) {
            moveLeftBtn.style.display = 'inline-flex';
            moveLeftBtn.title = "Revert to Applied";
        }
        if (moveRightBtn) {
            moveRightBtn.style.display = 'inline-flex';
            moveRightBtn.title = "Shortlist Candidate";
        }
        if (rejectBtn) rejectBtn.style.display = 'inline-flex';
    } else if (stage === 'SHORTLIST') {
        if (moveLeftBtn) {
            moveLeftBtn.style.display = 'inline-flex';
            moveLeftBtn.title = "Move back to Under Review";
        }
        if (moveRightBtn) moveRightBtn.style.display = 'none';
        if (rejectBtn) rejectBtn.style.display = 'inline-flex';
    } else if (stage === 'REJECTED') {
        if (moveLeftBtn) {
            moveLeftBtn.style.display = 'inline-flex';
            moveLeftBtn.title = "Move back to Under Review";
        }
        if (moveRightBtn) moveRightBtn.style.display = 'none';
        if (rejectBtn) rejectBtn.style.display = 'none';
    }
}

function recalculateDashboardCounters() {
    const stages = ['APPLIED', 'REVIEW', 'SHORTLIST', 'REJECTED'];
    let counts = {};
    let total = 0;
    
    // Update individual column headers
    stages.forEach(stage => {
        const columnCards = document.querySelectorAll(`.kanban-col[data-stage="${stage}"] .kanban-card`);
        const count = columnCards.length;
        counts[stage] = count;
        total += count;
        
        // Update column badge counter
        const badge = document.querySelector(`.kanban-col[data-stage="${stage}"] .kanban-badge`);
        if (badge) {
            badge.textContent = count;
        }
        
        // Show/hide empty state placeholder inside column
        const emptyPlaceholder = document.querySelector(`.kanban-col[data-stage="${stage}"] .kanban-empty`);
        if (emptyPlaceholder) {
            emptyPlaceholder.style.display = count === 0 ? 'flex' : 'none';
        }
    });
    
    // Update stat cards at the top
    const totalAppsBadge = document.getElementById('stat-total-apps');
    const appliedBadge = document.getElementById('stat-applied');
    const reviewBadge = document.getElementById('stat-review');
    const shortlistBadge = document.getElementById('stat-shortlist');
    const rejectedBadge = document.getElementById('stat-rejected');
    
    if (totalAppsBadge) totalAppsBadge.textContent = total;
    if (appliedBadge) appliedBadge.textContent = counts['APPLIED'];
    if (reviewBadge) reviewBadge.textContent = counts['REVIEW'];
    if (shortlistBadge) shortlistBadge.textContent = counts['SHORTLIST'];
    if (rejectedBadge) rejectedBadge.textContent = counts['REJECTED'];
}

/* ==========================================================================
   5. Global Notification System
   ========================================================================== */
function showNotification(message, type = 'success') {
    // Check if toast container exists, if not create it
    let container = document.querySelector('.toast-container-custom');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} shadow-lg border-0 d-flex align-items-center gap-2 py-3 px-4 fade-in-quick`;
    toast.style.borderRadius = '12px';
    toast.style.marginBottom = '10px';
    
    const icon = type === 'success' ? 'circle-check' : (type === 'danger' ? 'circle-exclamation' : 'circle-info');
    toast.innerHTML = `
        <i class="fa-solid fa-${icon}"></i>
        <div>${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Fade out and remove
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 3500);
}
