#!/usr/bin/env python3
"""
Batch Processing Example

Process multiple questions efficiently with rate limiting and error handling.
"""

import requests
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchProcessor:
    """Process multiple questions in batch."""
    
    def __init__(self, base_url: str = "http://localhost:8000", max_workers: int = 5):
        """
        Initialize batch processor.
        
        Args:
            base_url: Base URL of orchestrator API
            max_workers: Maximum concurrent requests
        """
        self.base_url = base_url
        self.max_workers = max_workers
    
    def process_question(self, question: str) -> Dict:
        """
        Process a single question.
        
        Args:
            question: Question to ask
            
        Returns:
            Result dict
        """
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json={"question": question, "stream": False},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "question": question,
                "success": True,
                "answer": result.get("answer"),
                "confidence": result.get("confidence"),
                "citations": result.get("citations", [])
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "question": question,
                "success": False,
                "error": str(e)
            }
    
    def process_batch(self, questions: List[str]) -> List[Dict]:
        """
        Process multiple questions in parallel.
        
        Args:
            questions: List of questions
            
        Returns:
            List of results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all questions
            future_to_question = {
                executor.submit(self.process_question, q): q 
                for q in questions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_question):
                result = future.result()
                results.append(result)
        
        return results
    
    def process_from_file(self, filepath: str) -> List[Dict]:
        """
        Process questions from a file (one per line).
        
        Args:
            filepath: Path to questions file
            
        Returns:
            List of results
        """
        with open(filepath, 'r') as f:
            questions = [line.strip() for line in f if line.strip()]
        
        return self.process_batch(questions)


def print_results(results: List[Dict]):
    """
    Print batch processing results.
    
    Args:
        results: List of result dicts
    """
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\nResults: {successful} successful, {failed} failed")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['question']}")
        
        if result['success']:
            print(f"    ✓ Answer: {result['answer'][:100]}...")
            print(f"    Confidence: {result['confidence']:.2f}")
            print(f"    Citations: {len(result['citations'])}")
        else:
            print(f"    ✗ Error: {result['error']}")


def main():
    print("AI RAG - Batch Processing Example")
    print("=" * 70)
    
    # Initialize processor
    processor = BatchProcessor(max_workers=3)
    
    # Example questions
    questions = [
        "What is the per diem rate for Denver?",
        "What is the per diem rate for Seattle?",
        "What is the per diem rate for New York?",
        "What are the travel policies?",
        "How do I submit an expense report?",
        "What is the mileage reimbursement rate?",
    ]
    
    print(f"\nProcessing {len(questions)} questions...")
    
    # Process batch
    start_time = time.time()
    results = processor.process_batch(questions)
    elapsed = time.time() - start_time
    
    # Print results
    print_results(results)
    
    print(f"\nTotal time: {elapsed:.2f} seconds")
    print(f"Average: {elapsed/len(questions):.2f} seconds per question")


def example_from_file():
    """Example: Process questions from file."""
    # Create example file
    with open('/tmp/questions.txt', 'w') as f:
        f.write("What is the per diem rate for Denver?\n")
        f.write("What are the travel policies?\n")
        f.write("How do I submit an expense report?\n")
    
    processor = BatchProcessor()
    results = processor.process_from_file('/tmp/questions.txt')
    print_results(results)


if __name__ == "__main__":
    # Run main example
    main()
    
    # Uncomment to run file example
    # example_from_file()
