#!/usr/bin/env python3
"""
Filter classified news articles to only include Talbot County stories.
Reads from Step 1's output and writes filtered results to Step 2.
"""

import json
import os

def filter_talbot_county(input_file, output_file):
    """
    Filter articles to only include those with 'Talbot' in the county field.
    
    Args:
        input_file: Path to the input JSON file with classified topics
        output_file: Path to write the filtered JSON output
    """
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Filter articles where county contains 'Talbot' (case-insensitive)
    talbot_articles = [
        article for article in articles 
        if 'county' in article and 
        article['county'] and 
        'talbot' in article['county'].lower()
    ]
    
    # Write filtered results to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(talbot_articles, f, indent=2, ensure_ascii=False)
    
    # Print summary statistics
    print(f"Total articles in input: {len(articles)}")
    print(f"Talbot County articles: {len(talbot_articles)}")
    print(f"Filtered out: {len(articles) - len(talbot_articles)}")
    print(f"\nOutput written to: {output_file}")

def main():
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_file = os.path.join(
        project_root, 
        'Step 1 - Classify Topics', 
        'stardem_topics_classified_v1.json'
    )
    
    output_file = os.path.join(
        script_dir, 
        'stardem_talbot_filtered.json'
    )
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    # Run the filter
    filter_talbot_county(input_file, output_file)

if __name__ == "__main__":
    main()
