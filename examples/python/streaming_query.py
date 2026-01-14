#!/usr/bin/env python3
"""
Streaming Query Example

Example of streaming responses with Server-Sent Events (SSE).
Shows AI thinking process in real-time.
"""

import requests
import json


def stream_question(question: str, base_url: str = "http://localhost:8000"):
    """
    Ask a question with streaming enabled.
    
    Args:
        question: Question to ask
        base_url: Base URL of orchestrator API
    """
    print(f"Question: {question}")
    print("=" * 50)
    print()
    
    response = requests.post(
        f"{base_url}/ask",
        json={
            "question": question,
            "stream": True
        },
        stream=True
    )
    
    response.raise_for_status()
    
    # Process SSE stream
    buffer = ""
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            buffer += chunk
            
            # Process complete events
            while "\n\n" in buffer:
                event_text, buffer = buffer.split("\n\n", 1)
                
                if event_text.strip():
                    process_event(event_text)
    
    print()


def process_event(event_text: str):
    """
    Process a single SSE event.
    
    Args:
        event_text: Raw SSE event text
    """
    lines = event_text.strip().split("\n")
    event_type = "message"
    data = None
    
    # Parse event
    for line in lines:
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            try:
                data = json.loads(line[6:])
            except json.JSONDecodeError:
                data = line[6:]
    
    if not data:
        return
    
    # Display based on event type
    icons = {
        'thought': '💭',
        'action': '⚡',
        'observation': '👀',
        'validation': '✓',
        'final_answer': '🤖',
        'error': '❌'
    }
    
    icon = icons.get(event_type, '•')
    
    if event_type == 'final_answer':
        print(f"\n{icon} Answer:")
        print(f"  {data.get('content', '')}")
        
        # Print citations if present
        if 'data' in data and 'citations' in data['data']:
            print("\n  Sources:")
            for citation in data['data']['citations']:
                print(f"    [{citation.get('source_number', '?')}] {citation.get('title', 'Unknown')}")
    else:
        content = data.get('content', data) if isinstance(data, dict) else data
        print(f"{icon} {content}")


def main():
    print("AI RAG - Streaming Query Example")
    print("=" * 50)
    print()
    
    # Example questions
    questions = [
        "What is the per diem rate for Denver?",
        "What are the mileage reimbursement rates?",
    ]
    
    for question in questions:
        try:
            stream_question(question)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    main()
