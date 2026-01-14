/**
 * Main Application
 * Coordinates all components and handles user interactions
 */

class App {
    constructor() {
        this.streamingClient = new StreamingClient();
        this.thinkingDisplay = new ThinkingDisplay();
        this.messages = [];
        this.isProcessing = false;
        
        // DOM elements
        this.welcomeEl = document.getElementById('welcome');
        this.messagesEl = document.getElementById('messages');
        this.chatForm = document.getElementById('chat-form');
        this.questionInput = document.getElementById('question-input');
        this.submitButton = document.getElementById('submit-button');
        this.charCount = document.getElementById('char-count');
        
        this.init();
    }

    /**
     * Initialize application
     */
    init() {
        // Set initial theme
        Utils.setTheme(Utils.getTheme());
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup streaming handlers
        this.setupStreaming();
        
        console.log('AI RAG Frontend initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form submission
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        themeToggle.addEventListener('click', () => {
            Utils.toggleTheme();
        });

        // Example questions
        const exampleButtons = document.querySelectorAll('.example-button');
        exampleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const question = button.getAttribute('data-question');
                this.questionInput.value = question;
                this.handleSubmit();
            });
        });

        // Character count
        this.questionInput.addEventListener('input', () => {
            const count = this.questionInput.value.length;
            this.charCount.textContent = count;
            
            // Auto-resize
            Utils.autoResizeTextarea(this.questionInput);
        });

        // Enter to submit (Shift+Enter for newline)
        this.questionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });
    }

    /**
     * Setup streaming handlers
     */
    setupStreaming() {
        // Thinking step received
        this.streamingClient.onThinkingStep = (step) => {
            this.thinkingDisplay.addStep(step);
        };

        // Final answer received
        this.streamingClient.onFinalAnswer = (answer) => {
            this.thinkingDisplay.hide();
            this.addMessage({
                role: 'assistant',
                content: answer.content,
                citations: answer.citations,
                confidence: answer.confidence,
                intent: answer.intent
            });
            this.setProcessing(false);
        };

        // Error occurred
        this.streamingClient.onError = (error) => {
            this.thinkingDisplay.hide();
            Utils.showError(`Error: ${error.message}`);
            this.setProcessing(false);
        };

        // Stream complete
        this.streamingClient.onComplete = () => {
            console.log('Stream complete');
        };
    }

    /**
     * Handle form submission
     */
    async handleSubmit() {
        const question = this.questionInput.value.trim();
        
        if (!question || this.isProcessing) {
            return;
        }

        // Add user message
        this.addMessage({
            role: 'user',
            content: question
        });

        // Clear input
        this.questionInput.value = '';
        this.charCount.textContent = '0';
        Utils.autoResizeTextarea(this.questionInput);

        // Hide welcome, show messages
        this.showChat();

        // Show thinking display
        this.thinkingDisplay.show();

        // Set processing state
        this.setProcessing(true);

        // Start streaming
        try {
            await this.streamingClient.stream(question);
        } catch (error) {
            console.error('Error:', error);
            Utils.showError('Failed to process question');
            this.setProcessing(false);
            this.thinkingDisplay.hide();
        }
    }

    /**
     * Add message to chat
     */
    addMessage(message) {
        // Add timestamp
        message.timestamp = new Date();
        message.id = Utils.generateId();
        
        this.messages.push(message);
        this.renderMessage(message);
        
        // Scroll to bottom
        Utils.scrollToBottom(this.messagesEl, true);
    }

    /**
     * Render a single message
     */
    renderMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role}`;
        messageEl.setAttribute('data-message-id', message.id);

        const avatar = message.role === 'user' ? '👤' : '🤖';
        const sender = message.role === 'user' ? 'You' : 'AI Assistant';

        let html = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${sender}</span>
                    <span class="message-time">${Utils.formatTime(message.timestamp)}</span>
                </div>
                <div class="message-text">${Utils.formatText(message.content)}</div>
        `;

        // Add citations if present
        if (message.citations && message.citations.length > 0) {
            html += '<div class="message-citations">';
            html += '<div class="citations-title">Sources</div>';
            
            message.citations.forEach((citation, index) => {
                const url = citation.url || '#';
                const title = citation.title || Utils.getDomain(url);
                
                html += `
                    <div class="citation">
                        <span class="citation-number">[${index + 1}]</span>
                        <a href="${url}" target="_blank" rel="noopener noreferrer" class="citation-link">
                            ${Utils.sanitizeText(title)}
                        </a>
                    </div>
                `;
            });
            
            html += '</div>';
        }

        html += '</div>'; // Close message-content

        messageEl.innerHTML = html;
        this.messagesEl.appendChild(messageEl);
    }

    /**
     * Show chat interface
     */
    showChat() {
        if (this.welcomeEl) {
            this.welcomeEl.style.display = 'none';
        }
        if (this.messagesEl) {
            this.messagesEl.style.display = 'flex';
        }
    }

    /**
     * Set processing state
     */
    setProcessing(processing) {
        this.isProcessing = processing;
        this.submitButton.disabled = processing;
        this.questionInput.disabled = processing;
        
        if (processing) {
            this.questionInput.placeholder = 'Processing...';
        } else {
            this.questionInput.placeholder = 'Ask a question...';
            this.questionInput.focus();
        }
    }

    /**
     * Clear chat
     */
    clearChat() {
        this.messages = [];
        this.messagesEl.innerHTML = '';
        this.messagesEl.style.display = 'none';
        this.welcomeEl.style.display = 'flex';
        this.thinkingDisplay.hide();
    }

    /**
     * Get message history
     */
    getMessages() {
        return this.messages;
    }

    /**
     * Export chat
     */
    exportChat() {
        return {
            messages: this.messages,
            timestamp: new Date().toISOString(),
            version: '1.0.0'
        };
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
}
