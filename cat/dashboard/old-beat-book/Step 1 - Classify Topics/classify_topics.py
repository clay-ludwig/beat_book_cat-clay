#!/usr/bin/env python3
"""
Star-Democrat Topic Classification Script
Option 1: Let the LLM Decide

This script reads Star-Democrat stories from a JSON file and uses an LLM
to classify each story into a single topic category. The LLM determines
the topics based on story content, creating consistent topic names.

This version uses Ollama running on a local Mac instead of Groq's API.
"""

import json
import os
import sys
import argparse
import requests
from pathlib import Path


# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "gemma3:4b"  # Can be changed to any model you have pulled in Ollama


def call_ollama(prompt, model=OLLAMA_MODEL, max_tokens=512):
    """
    Call the local Ollama API with the given prompt.
    
    Args:
        prompt: The prompt text to send
        model: The Ollama model to use (default: gemma3:4b)
        max_tokens: Maximum tokens to generate
        
    Returns:
        The response text from Ollama, or None if failed
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to Ollama at {OLLAMA_BASE_URL}", file=sys.stderr)
        print("Make sure Ollama is running on your Mac.", file=sys.stderr)
        print("If using a remote Mac, set OLLAMA_BASE_URL environment variable.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Ollama API call failed: {e}", file=sys.stderr)
        return None


def classify_story_with_llm(story, model=OLLAMA_MODEL):
    """
    Use the LLM to classify a single story into a topic and identify the county/region.
    
    Args:
        story: Dictionary containing story data with 'title' and 'content'
        model: The LLM model to use for classification
    
    Returns:
        dict: Dictionary with 'topic' and 'county' keys
    """
    prompt = f"""Analyze this news story and provide TWO pieces of information:

1. TOPIC: Assign a single BROAD topic category, NOT specific subjects. For example:
   - Use "Sports" not "Baseball" or "Lacrosse"
   - Use "History" not "Harriet Tubman" or "Civil War"
   - Use "Education" not specific school names
   - Use "Local Government" not specific official names
   - Use "Crime" not specific crime types
   - Use "Business" not specific business names
   
   Choose a 1-2 word broad topic that represents the general category this story belongs to.
   Be consistent - reuse the same topic names across similar stories.

2. COUNTY/REGION: Identify the primary Maryland county or region mentioned in the story.
   Common counties in this area include: Talbot, Caroline, Dorchester, Queen Anne's, Kent, Cecil
   If multiple counties are mentioned, choose the primary one.
   If it's about Maryland state-level or regional news, use "Maryland" or "Regional"
   If no specific location is mentioned, use "General"

Title: {story['title']}
Content: {story['content']}

Return your answer in this EXACT format (two lines only):
TOPIC: [topic name]
COUNTY: [county name]"""

    try:
        # Call Ollama API
        response = call_ollama(prompt, model=model, max_tokens=150)
        
        if response is None:
            return {"topic": "Unknown", "county": "Unknown"}
        
        # Parse the response
        topic = "Unknown"
        county = "Unknown"
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TOPIC:'):
                topic = line.replace('TOPIC:', '').strip()
            elif line.startswith('COUNTY:'):
                county = line.replace('COUNTY:', '').strip()
        
        return {"topic": topic, "county": county}
    
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return "Unknown"


def get_next_version_number():
    """
    Find the next available version number for output files.
    
    Returns:
        int: The next version number to use
    """
    current_dir = Path(".")
    existing_files = list(current_dir.glob("stardem_topics_classified_v*.json"))
    
    if not existing_files:
        return 1
    
    # Extract version numbers from existing files
    version_numbers = []
    for file in existing_files:
        try:
            # Extract number from filename like "stardem_topics_classified_v3.json"
            version_str = file.stem.split("_v")[-1]
            version_numbers.append(int(version_str))
        except (ValueError, IndexError):
            continue
    
    return max(version_numbers) + 1 if version_numbers else 1


def load_existing_progress(output_file):
    """
    Load previously classified stories from the output file if it exists.
    
    Args:
        output_file: Path to the output file
        
    Returns:
        tuple: (list of classified stories, set of processed story IDs)
    """
    if not output_file.exists():
        return [], set()
    
    try:
        with open(output_file, 'r') as f:
            classified_stories = json.load(f)
        
        # Create a set of story IDs that have already been classified
        # Use title as ID since stories don't have unique IDs
        processed_ids = {story['title'] for story in classified_stories if 'topic' in story}
        
        print(f"Found existing progress file with {len(classified_stories)} stories")
        print(f"Resuming from where we left off...\n")
        
        return classified_stories, processed_ids
    except Exception as e:
        print(f"Warning: Could not load existing progress: {e}")
        print("Starting fresh...\n")
        return [], set()


def save_progress(output_file, classified_stories):
    """
    Save classified stories to the output file.
    
    Args:
        output_file: Path to the output file
        classified_stories: List of stories to save
    """
    with open(output_file, 'w') as f:
        json.dump(classified_stories, f, indent=2)


def main():
    """Main function to process all stories and classify them."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Classify Star-Democrat stories into topics using Ollama"
    )
    parser.add_argument(
        "input_files",
        nargs="*",
        default=["stardem_sample.json"],
        help="Path(s) to input JSON file(s) (default: stardem_sample.json)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output filename (default: auto-versioned stardem_topics_classified_v{N}.json)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing output file if it exists"
    )
    args = parser.parse_args()
    
    print(f"Using Ollama model: {OLLAMA_MODEL}")
    print(f"Ollama base URL: {OLLAMA_BASE_URL}\n")
    
    # Load all stories from all input files
    all_stories = []
    for input_path in args.input_files:
        input_file = Path(input_path)
        
        # Check if input file exists
        if not input_file.exists():
            print(f"Error: {input_file} not found!", file=sys.stderr)
            print(f"Skipping {input_file}...")
            continue
        
        # Load the stories
        print(f"Loading stories from {input_file}...")
        with open(input_file, 'r') as f:
            stories = json.load(f)
        
        print(f"  Found {len(stories)} stories")
        all_stories.extend(stories)
    
    if not all_stories:
        print("Error: No stories loaded from any input files!", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Get the next version number
        version = get_next_version_number()
        output_file = Path(f"stardem_topics_classified_v{version}.json")
    
    print(f"\nTotal stories to classify: {len(all_stories)}")
    print(f"Output will be saved to: {output_file}\n")
    
    # Load existing progress if resuming
    if args.resume:
        classified_stories, processed_ids = load_existing_progress(output_file)
    else:
        classified_stories = []
        processed_ids = set()
    
    # Use all_stories instead of stories
    stories = all_stories
    
    # Process each story
    stories_processed = 0
    stories_skipped = 0
    
    for i, story in enumerate(stories, 1):
        # Check if this story has already been processed
        if story['title'] in processed_ids:
            print(f"Skipping story {i}/{len(stories)} (already classified): {story['title'][:60]}...")
            stories_skipped += 1
            continue
        
        print(f"Processing story {i}/{len(stories)}: {story['title'][:60]}...")
        
        # Classify the story (returns dict with 'topic' and 'county')
        classification = classify_story_with_llm(story, model=OLLAMA_MODEL)
        
        # Add the topic and county to the story
        story_with_classification = story.copy()
        story_with_classification['topic'] = classification['topic']
        story_with_classification['county'] = classification['county']
        classified_stories.append(story_with_classification)
        processed_ids.add(story['title'])
        stories_processed += 1
        
        print(f"  → Topic: {classification['topic']}")
        print(f"  → County: {classification['county']}")
        
        # Save progress after each story
        save_progress(output_file, classified_stories)
        print(f"  ✓ Progress saved ({len(classified_stories)} total stories)\n")
    
    print(f"\nDone! Classified {stories_processed} new stories.")
    if stories_skipped > 0:
        print(f"Skipped {stories_skipped} previously classified stories.")
    print(f"Total stories in output: {len(classified_stories)}")
    print(f"Results saved to {output_file}")
    
    # Print topic summary
    print("\n" + "="*60)
    print("TOPIC SUMMARY")
    print("="*60)
    topic_counts = {}
    for story in classified_stories:
        topic = story.get('topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{topic}: {count} stories")
    
    # Print county summary
    print("\n" + "="*60)
    print("COUNTY SUMMARY")
    print("="*60)
    county_counts = {}
    for story in classified_stories:
        county = story.get('county', 'Unknown')
        county_counts[county] = county_counts.get(county, 0) + 1
    
    for county, count in sorted(county_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{county}: {count} stories")


if __name__ == "__main__":
    main()
