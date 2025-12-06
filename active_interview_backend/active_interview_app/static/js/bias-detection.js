/**
 * Bias Detection Client-Side Library
 *
 * Provides real-time bias detection and highlighting for feedback text.
 * Uses pattern matching against bias term library loaded from server.
 *
 * Related to Issues #18, #57, #58, #59 (Bias Guardrails)
 *
 * Usage:
 *   const detector = new BiasDetector(biasTerms, {
 *     textareaId: 'interviewer_feedback',
 *     saveButtonIds: ['save-btn', 'review-btn'],
 *     onAnalysisChange: (analysis) => { ... }
 *   });
 */

class BiasDetector {
    constructor(biasTerms, options = {}) {
        this.biasTerms = biasTerms || [];
        this.options = {
            textareaId: options.textareaId || 'interviewer_feedback',
            saveButtonIds: options.saveButtonIds || [],
            reviewButtonId: options.reviewButtonId || null,
            debounceMs: options.debounceMs || 500,
            onAnalysisChange: options.onAnalysisChange || null,
        };

        // State
        this.currentAnalysis = null;
        this.debounceTimer = null;
        this.highlightContainer = null;
        this.textarea = null;
        this.compiledPatterns = [];

        // Initialize
        this.init();
    }

    init() {
        // Get textarea element
        this.textarea = document.getElementById(this.options.textareaId);
        if (!this.textarea) {
            console.error(`Textarea with id '${this.options.textareaId}' not found`);
            return;
        }

        // Compile regex patterns for performance
        this.compilePatterns();

        // Create highlight container overlay
        this.createHighlightOverlay();

        // Attach event listeners
        this.attachEventListeners();

        // Run initial analysis if textarea has content
        if (this.textarea.value.trim()) {
            this.analyzeText(this.textarea.value);
        }
    }

    compilePatterns() {
        /**
         * Pre-compile all regex patterns for better performance.
         * Each pattern is compiled with case-insensitive flag.
         */
        this.compiledPatterns = this.biasTerms.map(term => {
            try {
                return {
                    ...term,
                    regex: new RegExp(term.pattern, 'gi')
                };
            } catch (e) {
                console.error(`Invalid regex pattern for term '${term.term}':`, e);
                return null;
            }
        }).filter(Boolean);
    }

    createHighlightOverlay() {
        /**
         * Create an overlay div that sits behind the textarea to show highlights.
         * Uses the "behind-textarea" technique for performance.
         */
        const wrapper = document.createElement('div');
        wrapper.className = 'bias-detection-wrapper';
        wrapper.style.position = 'relative';

        // Create highlight background
        this.highlightContainer = document.createElement('div');
        this.highlightContainer.className = 'bias-highlight-container';
        this.highlightContainer.setAttribute('aria-hidden', 'true');

        // Wrap textarea
        this.textarea.parentNode.insertBefore(wrapper, this.textarea);
        wrapper.appendChild(this.highlightContainer);
        wrapper.appendChild(this.textarea);

        // Make textarea transparent background
        this.textarea.style.backgroundColor = 'transparent';
        this.textarea.style.position = 'relative';
        this.textarea.style.zIndex = '2';
    }

    attachEventListeners() {
        /**
         * Attach event listeners for real-time detection.
         */
        // Input event with debouncing
        this.textarea.addEventListener('input', () => {
            clearTimeout(this.debounceTimer);

            // Show "analyzing..." indicator
            this.showAnalyzingIndicator();

            this.debounceTimer = setTimeout(() => {
                this.analyzeText(this.textarea.value);
            }, this.options.debounceMs);
        });

        // Scroll synchronization
        this.textarea.addEventListener('scroll', () => {
            this.highlightContainer.scrollTop = this.textarea.scrollTop;
            this.highlightContainer.scrollLeft = this.textarea.scrollLeft;
        });

        // Form submit prevention if blocking flags exist
        const form = this.textarea.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (this.currentAnalysis && this.currentAnalysis.blocking_flags > 0) {
                    e.preventDefault();
                    this.showBlockingError();
                    return false;
                }
            });
        }
    }

    analyzeText(text) {
        /**
         * Analyze text for bias terms using pattern matching.
         * Returns analysis object similar to backend structure.
         */
        if (!text || !text.trim()) {
            this.currentAnalysis = this.emptyAnalysis();
            this.updateUI();
            return;
        }

        const flaggedTerms = [];
        const seenPositions = new Set(); // Avoid duplicate overlapping matches

        // Find all matches
        for (const term of this.compiledPatterns) {
            term.regex.lastIndex = 0; // Reset regex state
            let match;

            const positions = [];
            while ((match = term.regex.exec(text)) !== null) {
                const posKey = `${match.index}-${match.index + match[0].length}`;
                if (!seenPositions.has(posKey)) {
                    positions.push({
                        start: match.index,
                        end: match.index + match[0].length,
                        text: match[0]
                    });
                    seenPositions.add(posKey);
                }

                // Prevent infinite loop for zero-width matches
                if (match.index === term.regex.lastIndex) {
                    term.regex.lastIndex++;
                }
            }

            if (positions.length > 0) {
                flaggedTerms.push({
                    term_id: term.id,
                    term: term.term,
                    matched_text: positions[0].text,
                    category: term.category,
                    category_display: term.category_display,
                    severity: term.severity,
                    severity_display: term.severity_display,
                    explanation: term.explanation,
                    suggestions: term.suggestions,
                    positions: positions,
                    match_count: positions.length
                });
            }
        }

        // Calculate metrics
        const blocking_flags = flaggedTerms.filter(t => t.severity === 2).length;
        const warning_flags = flaggedTerms.filter(t => t.severity === 1).length;
        const total_flags = flaggedTerms.length;
        const has_bias = total_flags > 0;

        // Determine severity level
        let severity_level = 'CLEAN';
        if (blocking_flags > 0) {
            severity_level = 'HIGH';
        } else if (warning_flags > 0) {
            severity_level = warning_flags >= 3 ? 'MEDIUM' : 'LOW';
        }

        this.currentAnalysis = {
            has_bias,
            total_flags,
            blocking_flags,
            warning_flags,
            severity_level,
            flagged_terms: flaggedTerms
        };

        this.updateUI();
    }

    updateUI() {
        /**
         * Update all UI elements based on current analysis.
         */
        // Update highlights
        this.updateHighlights();

        // Update button states
        this.updateButtonStates();

        // Update status display
        this.updateStatusDisplay();

        // Callback for external listeners
        if (this.options.onAnalysisChange) {
            this.options.onAnalysisChange(this.currentAnalysis);
        }
    }

    updateHighlights() {
        /**
         * Update the highlight overlay with marked terms.
         * Uses spans with background colors for highlighting.
         */
        const text = this.textarea.value;
        if (!text) {
            this.highlightContainer.innerHTML = '';
            return;
        }

        // Collect all highlight ranges
        const highlights = [];
        if (this.currentAnalysis) {
            for (const flagged of this.currentAnalysis.flagged_terms) {
                for (const pos of flagged.positions) {
                    highlights.push({
                        start: pos.start,
                        end: pos.end,
                        severity: flagged.severity,
                        term: flagged.term,
                        category: flagged.category_display,
                        explanation: flagged.explanation,
                        suggestions: flagged.suggestions
                    });
                }
            }
        }

        // Sort by start position
        highlights.sort((a, b) => a.start - b.start);

        // Build highlighted HTML
        let html = '';
        let lastIndex = 0;

        for (const hl of highlights) {
            // Add text before highlight
            html += this.escapeHtml(text.substring(lastIndex, hl.start));

            // Add highlighted text with tooltip
            const severityClass = hl.severity === 2 ? 'blocking' : 'warning';
            const highlightedText = this.escapeHtml(text.substring(hl.start, hl.end));

            html += `<mark class="bias-highlight bias-${severityClass}"
                          data-term="${this.escapeHtml(hl.term)}"
                          data-category="${this.escapeHtml(hl.category)}"
                          data-explanation="${this.escapeHtml(hl.explanation)}"
                          data-suggestions='${JSON.stringify(hl.suggestions)}'
                          title="${this.escapeHtml(hl.explanation)}">${highlightedText}</mark>`;

            lastIndex = hl.end;
        }

        // Add remaining text
        html += this.escapeHtml(text.substring(lastIndex));

        this.highlightContainer.innerHTML = html;

        // Attach click handlers to highlights
        this.attachHighlightClickHandlers();
    }

    attachHighlightClickHandlers() {
        /**
         * Attach click handlers to highlighted terms to show suggestions modal.
         */
        const highlights = this.highlightContainer.querySelectorAll('.bias-highlight');
        highlights.forEach(mark => {
            mark.style.cursor = 'pointer';
            mark.addEventListener('click', (e) => {
                e.stopPropagation();
                const suggestions = JSON.parse(mark.dataset.suggestions || '[]');
                const term = mark.dataset.term;
                const explanation = mark.dataset.explanation;
                const category = mark.dataset.category;
                this.showSuggestionsModal(term, explanation, category, suggestions);
            });
        });
    }

    updateButtonStates() {
        /**
         * Update save/review button states based on analysis.
         * Disable buttons if blocking flags exist.
         */
        const analysis = this.currentAnalysis || this.emptyAnalysis();

        // Save buttons - disable if blocking flags
        for (const btnId of this.options.saveButtonIds) {
            const btn = document.getElementById(btnId);
            if (btn) {
                if (analysis.blocking_flags > 0) {
                    btn.disabled = true;
                    btn.classList.add('btn-disabled');
                    btn.title = 'Resolve blocking bias terms before saving';
                } else {
                    btn.disabled = false;
                    btn.classList.remove('btn-disabled');
                    btn.title = '';
                }
            }
        }

        // Review button - disable if ANY bias flags
        if (this.options.reviewButtonId) {
            const reviewBtn = document.getElementById(this.options.reviewButtonId);
            if (reviewBtn) {
                if (analysis.has_bias) {
                    reviewBtn.disabled = true;
                    reviewBtn.classList.add('btn-disabled');
                    reviewBtn.title = 'Resolve all bias flags before notifying candidate';
                } else {
                    reviewBtn.disabled = false;
                    reviewBtn.classList.remove('btn-disabled');
                    reviewBtn.title = '';
                }
            }
        }
    }

    showAnalyzingIndicator() {
        /**
         * Show "analyzing..." indicator while user is typing.
         */
        const statusEl = document.getElementById('bias-status');
        if (!statusEl) return;

        statusEl.innerHTML = '<span class="bias-status-analyzing">⏳ Analyzing for bias...</span>';
        statusEl.className = 'bias-status analyzing';
        statusEl.dataset.analyzing = 'true';
    }

    updateStatusDisplay() {
        /**
         * Update status message display (if element exists).
         */
        const statusEl = document.getElementById('bias-status');
        if (!statusEl) return;

        const analysis = this.currentAnalysis || this.emptyAnalysis();

        if (!analysis.has_bias) {
            statusEl.innerHTML = '<span class="bias-status-clean">✓ No bias detected - feedback is clean</span>';
            statusEl.className = 'bias-status clean';
        } else if (analysis.blocking_flags > 0) {
            statusEl.innerHTML = `<span class="bias-status-error">⚠ ${analysis.blocking_flags} blocking term${analysis.blocking_flags > 1 ? 's' : ''} must be resolved</span>`;
            statusEl.className = 'bias-status error';
        } else {
            statusEl.innerHTML = `<span class="bias-status-warning">⚠ ${analysis.warning_flags} warning${analysis.warning_flags > 1 ? 's' : ''} detected</span>`;
            statusEl.className = 'bias-status warning';
        }
    }

    showSuggestionsModal(term, explanation, category, suggestions) {
        /**
         * Show modal with neutral phrasing suggestions.
         * Creates/updates Bootstrap modal dynamically.
         */
        let modal = document.getElementById('bias-suggestions-modal');
        if (!modal) {
            modal = this.createSuggestionsModal();
        }

        // Update modal content
        document.getElementById('modal-term').textContent = term;
        document.getElementById('modal-category').textContent = category;
        document.getElementById('modal-explanation').textContent = explanation;

        const suggestionsList = document.getElementById('modal-suggestions-list');
        suggestionsList.innerHTML = '';

        if (suggestions && suggestions.length > 0) {
            suggestions.forEach(suggestion => {
                const li = document.createElement('li');
                li.className = 'suggestion-item';
                li.innerHTML = `
                    <span class="suggestion-text">${this.escapeHtml(suggestion)}</span>
                    <button type="button" class="btn btn-sm btn-primary accept-suggestion"
                            data-suggestion="${this.escapeHtml(suggestion)}"
                            data-term="${this.escapeHtml(term)}">
                        Accept
                    </button>
                `;
                suggestionsList.appendChild(li);
            });

            // Attach accept handlers
            suggestionsList.querySelectorAll('.accept-suggestion').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.acceptSuggestion(btn.dataset.term, btn.dataset.suggestion);
                    bootstrap.Modal.getInstance(modal).hide();
                });
            });
        } else {
            suggestionsList.innerHTML = '<li class="text-muted">No suggestions available</li>';
        }

        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    createSuggestionsModal() {
        /**
         * Create the suggestions modal HTML structure.
         */
        const modalHtml = `
            <div class="modal fade" id="bias-suggestions-modal" tabindex="-1" aria-labelledby="biasModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="biasModalLabel">Neutral Phrasing Suggestions</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="flagged-term-info">
                                <p><strong>Flagged term:</strong> <span id="modal-term"></span></p>
                                <p><strong>Category:</strong> <span id="modal-category" class="badge bg-secondary"></span></p>
                                <p><strong>Why this is problematic:</strong></p>
                                <p class="explanation-text" id="modal-explanation"></p>
                            </div>
                            <hr>
                            <p><strong>Suggested alternatives:</strong></p>
                            <ul id="modal-suggestions-list" class="suggestions-list"></ul>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const container = document.createElement('div');
        container.innerHTML = modalHtml;
        document.body.appendChild(container.firstElementChild);
        return document.getElementById('bias-suggestions-modal');
    }

    acceptSuggestion(term, suggestion) {
        /**
         * Replace flagged term with accepted suggestion in textarea.
         * Attempts to preserve case and context.
         */
        const text = this.textarea.value;

        // Find the term using the compiled pattern
        const termObj = this.compiledPatterns.find(t => t.term === term);
        if (!termObj) return;

        // Replace first occurrence (could be enhanced to replace specific instance)
        termObj.regex.lastIndex = 0;
        const match = termObj.regex.exec(text);

        if (match) {
            const before = text.substring(0, match.index);
            const after = text.substring(match.index + match[0].length);
            const newText = before + suggestion + after;

            this.textarea.value = newText;

            // Trigger analysis
            this.analyzeText(newText);

            // Set cursor position after suggestion
            const cursorPos = before.length + suggestion.length;
            this.textarea.setSelectionRange(cursorPos, cursorPos);
            this.textarea.focus();
        }
    }

    showBlockingError() {
        /**
         * Show error message when trying to save with blocking flags.
         */
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.setAttribute('role', 'alert');
        errorDiv.innerHTML = `
            <strong>Cannot save:</strong> Your feedback contains ${this.currentAnalysis.blocking_flags}
            blocking bias term${this.currentAnalysis.blocking_flags > 1 ? 's' : ''} that must be resolved.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insert before form
        const form = this.textarea.closest('form');
        if (form) {
            form.parentNode.insertBefore(errorDiv, form);
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    emptyAnalysis() {
        return {
            has_bias: false,
            total_flags: 0,
            blocking_flags: 0,
            warning_flags: 0,
            severity_level: 'CLEAN',
            flagged_terms: []
        };
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Public methods
    getCurrentAnalysis() {
        return this.currentAnalysis || this.emptyAnalysis();
    }

    destroy() {
        clearTimeout(this.debounceTimer);
        // Additional cleanup if needed
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BiasDetector;
}
