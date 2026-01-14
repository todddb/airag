#!/usr/bin/env python3
"""
Basic Query Example

Simple example of asking a question using the AI RAG API.
"""

import requests
import json


def ask_question(question: str, base_url: str = "http://localhost:8000") -> dict:
    """
    Ask a question (non-streaming).
    
    Args:
        question: Question to ask
        base_url: Base URL of orchestrator API
        
    Returns:
        Response dict with answer, citations, confidence
    """
    response = requests.post(
        f"{base_url}/ask",
        json={
            "question": question,
            "stream": False
        }
    )
    
    response.raise_for_status()
    return response.json()


def main():
    # Example questions
    questions = [
        "What is the per diem rate for Denver?",
        "What are the travel policies?",
        "How do I submit an expense report?",
    ]
    
    print("AI RAG - Basic Query Example")
    print("=" * 50)
    
    for question in questions:
        print(f"\nQuestion: {question}")
        print("-" * 50)
        
        try:
            result = ask_question(question)
            
            # Print answer
            print(f"Answer: {result['answer']}")
            print(f"Confidence: {result['confidence']:.2f}")
            
            # Print citations
            if result.get('citations'):
                print("\nSources:")
                for citation in result['citations']:
                    print(f"  [{citation['source_number']}] {citation['title']}")
                    print(f"      {citation['url']}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        
        print()


if __name__ == "__main__":
    main()
