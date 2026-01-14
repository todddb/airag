/**
 * Frontend Integration Example
 * 
 * Example of integrating AI RAG API into a JavaScript frontend application.
 */

class AIRAGClient {
    /**
     * Create AI RAG API client.
     * 
     * @param {string} baseUrl - Base URL of the API (default: /api)
     */
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    /**
     * Ask a question (non-streaming).
     * 
     * @param {string} question - Question to ask
     * @returns {Promise<Object>} Response with answer, citations, confidence
     */
    async ask(question) {
        const response = await fetch(`${this.baseUrl}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Ask a question with streaming (SSE).
     * 
     * @param {string} question - Question to ask
     * @param {Object} callbacks - Callback functions
     * @param {Function} callbacks.onThinking - Called for thinking steps
     * @param {Function} callbacks.onAnswer - Called with final answer
     * @param {Function} callbacks.onError - Called on error
     */
    async askStreaming(question, callbacks = {}) {
        const response = await fetch(`${this.baseUrl}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                stream: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Process SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete events
            const events = buffer.split('\n\n');
            buffer = events.pop(); // Keep incomplete event

            for (const event of events) {
                if (event.trim()) {
                    this._processEvent(event, callbacks);
                }
            }
        }
    }

    /**
     * Process SSE event.
     * 
     * @private
     * @param {string} eventText - Raw event text
     * @param {Object} callbacks - Callback functions
     */
    _processEvent(eventText, callbacks) {
        const lines = eventText.split('\n');
        let eventType = 'message';
        let data = null;

        for (const line of lines) {
            if (line.startsWith('event: ')) {
                eventType = line.substring(7).trim();
            } else if (line.startsWith('data: ')) {
                try {
                    data = JSON.parse(line.substring(6));
                } catch (e) {
                    data = line.substring(6);
                }
            }
        }

        if (!data) return;

        // Route to appropriate callback
        if (eventType === 'final_answer' && callbacks.onAnswer) {
            callbacks.onAnswer({
                answer: data.content,
                citations: data.data?.citations || [],
                confidence: data.data?.confidence
            });
        } else if (['thought', 'action', 'observation', 'validation'].includes(eventType) && callbacks.onThinking) {
            callbacks.onThinking({
                type: eventType,
                content: data.content || data
            });
        } else if (eventType === 'error' && callbacks.onError) {
            callbacks.onError(new Error(data.content || data));
        }
    }
}

// =============================================================================
// Example Usage
// =============================================================================

/**
 * Example 1: Simple question
 */
async function example1() {
    const client = new AIRAGClient();
    
    try {
        const result = await client.ask("What is the per diem rate for Denver?");
        
        console.log("Answer:", result.answer);
        console.log("Confidence:", result.confidence);
        console.log("Citations:", result.citations);
    } catch (error) {
        console.error("Error:", error);
    }
}

/**
 * Example 2: Streaming with real-time updates
 */
async function example2() {
    const client = new AIRAGClient();
    
    const thinkingSteps = [];
    
    await client.askStreaming(
        "What are the travel policies?",
        {
            onThinking: (step) => {
                thinkingSteps.push(step);
                console.log(`${step.type}: ${step.content}`);
            },
            onAnswer: (result) => {
                console.log("\nFinal Answer:", result.answer);
                console.log("Confidence:", result.confidence);
            },
            onError: (error) => {
                console.error("Error:", error);
            }
        }
    );
}

/**
 * Example 3: Integration with React component
 */
class QuestionForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            question: '',
            answer: null,
            thinking: [],
            loading: false
        };
        this.client = new AIRAGClient();
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        this.setState({ loading: true, thinking: [], answer: null });
        
        await this.client.askStreaming(
            this.state.question,
            {
                onThinking: (step) => {
                    this.setState(state => ({
                        thinking: [...state.thinking, step]
                    }));
                },
                onAnswer: (result) => {
                    this.setState({
                        answer: result,
                        loading: false
                    });
                },
                onError: (error) => {
                    console.error(error);
                    this.setState({ loading: false });
                }
            }
        );
    }

    render() {
        return (
            <div>
                <form onSubmit={this.handleSubmit.bind(this)}>
                    <input
                        type="text"
                        value={this.state.question}
                        onChange={(e) => this.setState({ question: e.target.value })}
                        placeholder="Ask a question..."
                    />
                    <button type="submit" disabled={this.state.loading}>
                        Ask
                    </button>
                </form>

                {this.state.thinking.length > 0 && (
                    <div className="thinking">
                        {this.state.thinking.map((step, i) => (
                            <div key={i}>{step.type}: {step.content}</div>
                        ))}
                    </div>
                )}

                {this.state.answer && (
                    <div className="answer">
                        <p>{this.state.answer.answer}</p>
                        {this.state.answer.citations.map((citation, i) => (
                            <div key={i}>
                                [{citation.source_number}] {citation.title}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }
}

/**
 * Example 4: Vanilla JavaScript integration
 */
function setupVanillaJS() {
    const client = new AIRAGClient();
    const form = document.getElementById('question-form');
    const input = document.getElementById('question-input');
    const thinkingDiv = document.getElementById('thinking');
    const answerDiv = document.getElementById('answer');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = input.value;
        thinkingDiv.innerHTML = '';
        answerDiv.innerHTML = '';

        await client.askStreaming(question, {
            onThinking: (step) => {
                const stepEl = document.createElement('div');
                stepEl.textContent = `${step.type}: ${step.content}`;
                thinkingDiv.appendChild(stepEl);
            },
            onAnswer: (result) => {
                answerDiv.innerHTML = `
                    <p>${result.answer}</p>
                    <div class="citations">
                        ${result.citations.map(c => 
                            `<div>[${c.source_number}] ${c.title}</div>`
                        ).join('')}
                    </div>
                `;
            },
            onError: (error) => {
                answerDiv.innerHTML = `<p class="error">${error.message}</p>`;
            }
        });
    });
}

// =============================================================================
// Export for use in modules
// =============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIRAGClient;
}
