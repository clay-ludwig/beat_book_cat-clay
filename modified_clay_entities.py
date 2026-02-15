import json
import subprocess
import time
import argparse
import sys
from pathlib import Path
import random
import re


def extract_direct_quotes(text):
    """Extract direct quotes wrapped in double quotes."""

    return re.findall(r'"([^"]+)"', text)


def summarize_story(story_title, story_content, model, max_attempts=2):
    """Use LLM to summarize a story while retaining all direct quotes."""

    base_prompt = f"""
Summarize this public safety news story in 3-6 sentences.

REQUIREMENTS:
- Preserve ALL direct quotes exactly as written in the story.
- Do not drop any quotes, even if you shorten surrounding context.
- Keep the speaker attribution with each quote when possible.
- Be concise and factual.

Story Title: {story_title}
Story Content: {story_content}

Return only the summary text.
"""

    quotes = extract_direct_quotes(story_content)
    prompt = base_prompt

    for attempt in range(1, max_attempts + 1):
        try:
            result = subprocess.run(
                ['llm', '-m', model, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                stderr_msg = result.stderr[:200] if result.stderr else "No error message"
                return {"error": "LLM failed", "stderr": stderr_msg, "returncode": result.returncode}

            summary_text = result.stdout.strip()
            if quotes:
                missing_quotes = [q for q in quotes if q not in summary_text]
                if missing_quotes and attempt < max_attempts:
                    missing_block = "\n".join(f"- \"{q}\"" for q in missing_quotes)
                    prompt = (
                        f"""
Your previous summary dropped some required direct quotes. Revise the summary and include ALL of the following quotes exactly as written:
{missing_block}

Keep the summary 3-6 sentences, preserve speaker attribution when possible, and return only the summary text.

Story Title: {story_title}
Story Content: {story_content}
"""
                    )
                    continue

            return {"summary": summary_text}
        except subprocess.TimeoutExpired:
            return {"error": "LLM request timed out after 60 seconds"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


def extract_entities(story_title, story_content, model):
    """Use LLM to extract named entities (people, places, organizations) from full public safety news stories."""

    prompt = f"""
Extract ALL named entities from this PUBLIC SAFETY news story and return them in JSON format.

CONTEXT: This story is from the Public Safety beat covering law enforcement, fire departments, emergency services, courts, crime, accidents, and public safety-related news. Extract ALL people, places, and organizations mentioned in the story.

Extract the following entities:

- people: Array of ALL people mentioned in the story. Include their name and title/role/description when available:
  * Law enforcement officers: Include rank and agency (e.g., "Chief John Smith, Easton Police Department", "Sgt. Jane Doe, Maryland State Police")
  * Fire and EMS personnel: Include rank and department (e.g., "Chief Robert Lee, St. Michaels Volunteer Fire Department")
  * Court officials: Include role and jurisdiction (e.g., "Judge William Brown, Talbot County Circuit Court")
  * Suspects/defendants: Include name and any details stated (e.g., "James Wilson, 35, of Easton")
  * Victims: Include if named (e.g., "Michael Roberts, victim")
  * Public officials: Include title and organization (e.g., "Mayor Carol Westfall, Klamath Falls")
  * Any other person mentioned: Include name and any identifying information provided
  Format: "First Last, Title/Role" or "First Last, age, description" as appropriate

- places: Array of ALL geographic locations and specific places mentioned:
  * Cities/Towns: Include state (e.g., "Easton, Maryland", "St. Michaels, Maryland")
  * Counties: Use format "Talbot County, Maryland"
  * States and countries: (e.g., "Oregon", "Nevada")
  * Specific locations: Roads, buildings, facilities (e.g., "Route 50", "Easton Police Department", "Talbot County Courthouse")
  * Any other location mentioned in the story


- organizations: Array of ALL organizations, institutions, and agencies mentioned:
  * Law enforcement agencies: (e.g., "Easton Police Department", "Maryland State Police", "FBI")
  * Fire departments: (e.g., "St. Michaels Volunteer Fire Department")
  * Emergency services: (e.g., "Talbot County Emergency Medical Services")
  * Courts and legal: (e.g., "Talbot County Circuit Court", "U.S. District Court")
  * Government agencies: (e.g., "Maryland State Fire Marshal", "U.S. Coast Guard")
  * Any other organization mentioned
  Use full official names when possible

IMPORTANT RULES:
- Extract ALL entities mentioned in the story, regardless of location
- Do NOT include news organizations, reporters, photographers, or newsroom staff
- Do NOT include the story's author/byline
- Do NOT include photographer names
- Do NOT include these news organizations: Star Democrat, Chesapeake Publishing, APG Media
- Be thorough - include every person, place, and organization that appears in the story
- Maintain consistent naming: use full names and official titles

Example output:
{{
  "people": ["Chief Chris Thomas, St. Michaels Volunteer Fire Department", "Sgt. Robert Reynolds, Klamath Falls Police Department", "Mayor Carol Westfall, Klamath Falls", "Negasi Zuberi, 29, suspect"],
  "places": ["St. Michaels, Maryland", "Talbot County, Maryland", "Klamath Falls, Oregon", "Reno, Nevada", "Route 50"],
  "organizations": ["St. Michaels Volunteer Fire Department", "Klamath Falls Police Department", "FBI Portland Field Office", "Maryland State Police"]
}}

Story Title: {story_title}
Story Content: {story_content}

Return only valid JSON with the three arrays. If a category has no entities, use an empty array []:
"""

    try:
        result = subprocess.run(
            ['llm', '-m', model, prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            response_text = result.stdout.strip()
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('\n', 1)[0]

            metadata = json.loads(response_text)
            return metadata

        stderr_msg = result.stderr[:200] if result.stderr else "No error message"
        return {"error": "LLM failed", "stderr": stderr_msg, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "LLM request timed out after 60 seconds"}
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parsing failed: {str(e)}",
            "response": result.stdout[:200] if 'result' in locals() else "No response"
        }
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(
        description='Add entity metadata (people, places, organizations) then summarize public safety stories using LLM'
    )
    parser.add_argument('--model', required=True, help='LLM model to use (e.g., groq/openai/gpt-oss-120b)')
    parser.add_argument('--input', default='public_safety_stories.json', help='Input JSON file with stories (default: public_safety_stories.json)')
    parser.add_argument('--output', default='stories_and_entities_2.json', help='Output JSON file (default: stories_and_entities_2.json)')
    parser.add_argument('--sample-size', type=int, default=300, help='Number of stories to randomly sample (default: 300)')
    parser.add_argument('--limit', type=int, help='Limit the number of stories to process (useful for testing)')

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    try:
        with open(args.input) as f:
            all_stories = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{args.input}'")
        print("Make sure the input file exists in the current directory!")
        return

    stories = []
    filtered_out = []

    for story in all_stories:
        title = story.get('title', '')
        content = story.get('content', '')

        if 'TODAY IN HISTORY' in title.upper():
            filtered_out.append(f"{title} (TODAY IN HISTORY)")
            continue
        if 'RELIGION CALENDAR' in title.upper():
            filtered_out.append(f"{title} (RELIGION CALENDAR)")
            continue
        if 'MID-SHORE CALENDAR' in title.upper():
            filtered_out.append(f"{title} (MID-SHORE CALENDAR)")
            continue

        if 'Section: Calendar' in content or 'Section: Columns' in content or 'Section: Letters' in content:
            filtered_out.append(f"{title} (Calendar/Columns/Letters section)")
            continue

        stories.append(story)

    print(f"\nLoaded {len(all_stories)} public safety stories from {args.input}")
    print(f"Filtered out {len(filtered_out)} stories (calendars, columns, history, letters)")
    print(f"Remaining stories after filtering: {len(stories)}")

    sample_size = min(args.sample_size, len(stories))
    if sample_size < len(stories):
        print(f"Randomly sampling {sample_size} stories from {len(stories)} available stories")
        random.seed(42)
        stories = random.sample(stories, sample_size)
    else:
        print(f"Using all {len(stories)} stories (less than requested sample size of {args.sample_size})")

    if args.limit and args.limit < len(stories):
        print(f"Limiting processing to first {args.limit} stories (--limit argument)")
        stories = stories[:args.limit]

    print(f"Will process {len(stories)} stories\n")

    if filtered_out and len(filtered_out) <= 10:
        print("Filtered stories:")
        for item in filtered_out:
            print(f"  - {item}")
        print()

    output_filename = args.output

    if Path(output_filename).exists():
        print(f"Found existing output file {output_filename}, loading previous results...")
        with open(output_filename) as f:
            enhanced_stories = json.load(f)
        print(f"Loaded {len(enhanced_stories)} previously processed stories\n")
    else:
        enhanced_stories = []
        print(f"Starting fresh with new output file: {output_filename}\n")

    errors = []
    starting_count = len(enhanced_stories)

    for i, story in enumerate(stories):
        if i < starting_count:
            continue

        print(f"Processing {i+1}/{len(stories)}: {story.get('title', 'Untitled')[:60]}...")

        story_content = story.get('content', '')
        if not story_content:
            print("  ⚠️  Warning: No content found for story")
            continue

        entities = extract_entities(story.get('title', ''), story_content, args.model)

        summary_result = summarize_story(story.get('title', ''), story_content, args.model)
        if 'error' in summary_result:
            print(f"  ✗ Summary error: {summary_result.get('error', 'Unknown error')[:80]}")
            if 'stderr' in summary_result:
                print(f"     stderr: {summary_result['stderr'][:200]}")
            if 'returncode' in summary_result:
                print(f"     return code: {summary_result['returncode']}")
            errors.append(f"Story {i+1}: Summary error - {summary_result.get('error', 'Unknown error')[:100]}")
            continue

        story_summary = summary_result.get('summary', '').strip()
        if not story_summary:
            print("  ⚠️  Warning: Summary returned empty text")
            errors.append(f"Story {i+1}: Empty summary returned")
            continue

        enhanced_story = story.copy()
        # Replace story content with the summary text (quotes preserved) and omit separate summary.
        enhanced_story['content'] = story_summary

        if 'error' not in entities:
            enhanced_story['people'] = entities.get('people', [])
            enhanced_story['places'] = entities.get('places', [])
            enhanced_story['organizations'] = entities.get('organizations', [])
            print(
                f"  ✓ Found {len(enhanced_story['people'])} people, "
                f"{len(enhanced_story['places'])} places, "
                f"{len(enhanced_story['organizations'])} orgs"
            )
        else:
            enhanced_story['people'] = []
            enhanced_story['places'] = []
            enhanced_story['organizations'] = []
            enhanced_story['entity_extraction_error'] = entities.get('error', 'Unknown error')
            errors.append(f"Story {i+1}: {entities.get('error', 'Unknown error')[:100]}")
            print(f"  ✗ Error: {entities.get('error', 'Unknown error')[:80]}")
            if 'stderr' in entities:
                print(f"     stderr: {entities['stderr'][:200]}")
            if 'returncode' in entities:
                print(f"     return code: {entities['returncode']}")

        enhanced_stories.append(enhanced_story)

        with open(output_filename, 'w') as f:
            json.dump(enhanced_stories, f, indent=2)

        time.sleep(1)

    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total stories loaded: {len(all_stories)}")
    print(f"Filtered out (calendars, columns, etc.): {len(filtered_out)}")
    print(f"Randomly sampled: {sample_size} stories")
    if starting_count > 0:
        print(f"Previously processed: {starting_count}")
        print(f"Newly processed in this run: {len(enhanced_stories) - starting_count}")
    print(f"Total successfully processed with entities: {len(enhanced_stories)}")
    print(f"\nOutput saved to: {output_filename}")
    print("(File is saved incrementally after each story)")

    if errors:
        print(f"\n⚠️  {len(errors)} stories had errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    successful = sum(1 for s in enhanced_stories if 'entity_extraction_error' not in s)
    print(f"\n✓ Successfully extracted entities from {successful}/{len(enhanced_stories)} stories")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
