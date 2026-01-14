/**
 * Streaming Client - Server-Sent Events (SSE)
 * Handles real-time streaming of AI thinking process
 */

class StreamingClient {
    constructor(apiUrl = '/api/ask') {
        this.apiUrl = apiUrl;
        this.eventSource = null;
        this.onThinkingStep = null;
        this.onFinalAnswer = null;
        this.onError = null;
        this.onComplete = null;
    }

    /**
     * Start streaming a question
     */
    async stream(question, sessionId = null) {
        // Close any existing connection
        this.close();

        try {
            // Make request
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    stream: true,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Read stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                    // Process any remaining data in buffer
                    if (buffer.trim()) {
                        this._processBuffer(buffer);
                    }
                    
                    // Stream complete
                    if (this.onComplete) {
                        this.onComplete();
                    }
                    break;
                }

                // Decode chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete events in buffer
                const events = buffer.split('\n\n');
                buffer = events.pop(); // Keep incomplete event in buffer

                for (const event of events) {
                    if (event.trim()) {
                        this._processEvent(event);
                    }
                }
            }

        } catch (error) {
            console.error('Streaming error:', error);
            if (this.onError) {
                this.onError(error);
            }
        }
    }

    /**
     * Process SSE event
     */
    _processEvent(eventText) {
        try {
            // Parse SSE format
            const lines = eventText.split('\n');
            let eventType = 'message';
            let data = null;

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.substring(7).trim();
                } else if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        data = JSON.parse(dataStr);
                    } catch (e) {
                        data = dataStr;
                    }
                }
            }

            // Handle event
            this._handleEvent(eventType, data);

        } catch (error) {
            console.error('Error processing event:', error, eventText);
        }
    }

    /**
     * Process any remaining data in buffer
     */
    _processBuffer(buffer) {
        const trimmed = buffer.trim();
        if (trimmed) {
            this._processEvent(trimmed);
        }
    }

    /**
     * Handle parsed event
     */
    _handleEvent(eventType, data) {
        if (!data) return;

        // Convert string data to object if needed
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (e) {
                // Keep as string
            }
        }

        // Route to appropriate handler
        switch (eventType) {
            case 'thought':
            case 'action':
            case 'observation':
            case 'validation':
                if (this.onThinkingStep) {
                    this.onThinkingStep({
                        type: eventType,
                        content: data.content || data,
                        timestamp: data.timestamp || new Date().toISOString()
                    });
                }
                break;

            case 'final_answer':
                if (this.onFinalAnswer) {
                    this.onFinalAnswer({
                        content: data.content || data,
                        citations: data.data?.citations || [],
                        confidence: data.data?.confidence,
                        intent: data.data?.intent
                    });
                }
                break;

            case 'error':
                if (this.onError) {
                    this.onError(new Error(data.content || data));
                }
                break;

            default:
                console.log('Unknown event type:', eventType, data);
        }
    }

    /**
     * Close stream
     */
    close() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    /**
     * Make non-streaming request
     */
    async ask(question, sessionId = null) {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    stream: false,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Request error:', error);
            throw error;
        }
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamingClient;
}
