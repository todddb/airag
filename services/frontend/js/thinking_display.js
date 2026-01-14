/**
 * Thinking Display - Visualize AI reasoning process
 * Shows thinking steps as they stream in real-time
 */

class ThinkingDisplay {
    constructor(containerId = 'thinking-container') {
        this.container = document.getElementById(containerId);
        this.stepsContainer = document.getElementById('thinking-steps');
        this.steps = [];
    }

    /**
     * Show thinking container
     */
    show() {
        if (this.container) {
            this.container.style.display = 'block';
            this.clear();
        }
    }

    /**
     * Hide thinking container
     */
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
        }
    }

    /**
     * Clear all thinking steps
     */
    clear() {
        this.steps = [];
        if (this.stepsContainer) {
            this.stepsContainer.innerHTML = '';
        }
    }

    /**
     * Add a thinking step
     */
    addStep(step) {
        this.steps.push(step);
        this._renderStep(step);
        
        // Auto-scroll to show new step
        if (this.stepsContainer) {
            Utils.scrollToBottom(this.stepsContainer, true);
        }
    }

    /**
     * Render a single step
     */
    _renderStep(step) {
        if (!this.stepsContainer) return;

        const stepEl = document.createElement('div');
        stepEl.className = 'thinking-step';

        // Icon based on step type
        const icon = this._getIcon(step.type);
        
        stepEl.innerHTML = `
            <div class="thinking-step-icon">${icon}</div>
            <div class="thinking-step-text">${Utils.sanitizeText(step.content)}</div>
        `;

        this.stepsContainer.appendChild(stepEl);
    }

    /**
     * Get icon for step type
     */
    _getIcon(type) {
        const icons = {
            'thought': '💭',
            'action': '⚡',
            'observation': '👀',
            'validation': '✓',
            'error': '❌'
        };
        return icons[type] || '•';
    }

    /**
     * Update last step (for streaming content)
     */
    updateLastStep(content) {
        if (this.steps.length === 0) return;

        const lastStep = this.steps[this.steps.length - 1];
        lastStep.content = content;

        // Update DOM
        const stepElements = this.stepsContainer.querySelectorAll('.thinking-step');
        if (stepElements.length > 0) {
            const lastStepEl = stepElements[stepElements.length - 1];
            const textEl = lastStepEl.querySelector('.thinking-step-text');
            if (textEl) {
                textEl.textContent = content;
            }
        }
    }

    /**
     * Add thinking step with animation
     */
    addStepAnimated(step, delay = 0) {
        setTimeout(() => {
            this.addStep(step);
        }, delay);
    }

    /**
     * Show thinking steps in sequence
     */
    showSequence(steps, intervalMs = 500) {
        this.clear();
        this.show();

        steps.forEach((step, index) => {
            this.addStepAnimated(step, index * intervalMs);
        });
    }

    /**
     * Create summary of thinking process
     */
    createSummary() {
        const summary = {
            totalSteps: this.steps.length,
            stepsByType: {},
            duration: 0
        };

        // Count steps by type
        this.steps.forEach(step => {
            const type = step.type || 'unknown';
            summary.stepsByType[type] = (summary.stepsByType[type] || 0) + 1;
        });

        // Calculate duration if timestamps available
        if (this.steps.length >= 2) {
            const first = new Date(this.steps[0].timestamp);
            const last = new Date(this.steps[this.steps.length - 1].timestamp);
            summary.duration = (last - first) / 1000; // seconds
        }

        return summary;
    }

    /**
     * Export thinking steps
     */
    export() {
        return {
            steps: [...this.steps],
            summary: this.createSummary()
        };
    }

    /**
     * Get all steps
     */
    getSteps() {
        return this.steps;
    }

    /**
     * Get step count
     */
    getStepCount() {
        return this.steps.length;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThinkingDisplay;
}
