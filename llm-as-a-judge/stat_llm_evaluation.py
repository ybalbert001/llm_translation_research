import json
import numpy as np
import argparse
from collections import defaultdict

def extract_source_and_translations(json_str):
    """Extract source text and translations from the input."""
    try:
        data = json.loads(json_str)
        messages = data["modelInput"]["messages"][0]["content"]
        
        source_text = None
        translations = {}
        
        # Parse the text content to extract source and translations
        for item in messages:
            if item["type"] == "text":
                text = item["text"]
                if "Source Text" in text:
                    # Extract source text between <text> tags
                    start = text.find("<text>") + len("<text>")
                    end = text.find("</text>")
                    source_text = text[start:end].strip()
                
                if "<translations>" in text:
                    # Extract translations
                    trans_start = text.find("<translations>") + len("<translations>")
                    trans_end = text.find("</translations>")
                    trans_text = text[trans_start:trans_end]
                    
                    # Parse individual translations
                    for trans in trans_text.split("<translation"):
                        if 'id="' in trans:
                            trans_id = trans[trans.find('id="')+4:trans.find('"', trans.find('id="')+4)]
                            content_start = trans.find(">") + 1
                            content_end = trans.find("</translation>")
                            if content_end != -1:
                                translations[trans_id] = trans[content_start:content_end].strip()
        
        return source_text, translations
    except Exception as e:
        print(f"Error extracting source and translations: {str(e)}")
        return None, None

def parse_line_scores(json_str):
    """Parse a single line of JSON and extract scores and thoughts for each translation."""
    try:
        data = json.loads(json_str)
        # Get the text content from modelOutput
        content = data["modelOutput"]["content"][0]["text"]
        
        # Remove any leading/trailing whitespace and 'json' markers
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        # Parse the JSON array from the content
        evaluations = json.loads(content)
        
        # Extract scores and thoughts for each translation
        translation_data = {}
        for eval in evaluations:
            translation_id = str(eval["id"])  # Convert id to string for consistency
            translation_data[translation_id] = {
                "scores": eval["scores"],
                "thought": eval["thought"]
            }
        
        return translation_data
    except Exception as e:
        print(f"Error parsing scores: {str(e)}")
        print(f"Content that failed to parse: {content if 'content' in locals() else 'content not available'}")
        return None

def process_file(file_path):
    """Process the .jsonl file and collect all information."""
    all_data = []
    all_scores = defaultdict(list)
    error_count = 0
    success_count = 0
    total_lines = 0
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            try:
                # Parse the line
                source_text, translations = extract_source_and_translations(line.strip())
                translation_data = parse_line_scores(line.strip())
                
                if translation_data:
                    # Collect scores for statistics
                    for trans_id, data in translation_data.items():
                        all_scores[trans_id].append(data["scores"])
                    
                    # Create simplified entry
                    entry = {
                        "source": source_text,
                        "translations": translations,
                        "evaluations": translation_data
                    }
                    all_data.append(entry)
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing line {line_num}: {str(e)}")
                continue
    
    print(f"\nProcessing Summary:")
    print(f"Total lines processed: {total_lines}")
    print(f"Successfully processed: {success_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Success rate: {(success_count/total_lines)*100:.2f}%\n")
    
    return all_data, all_scores

def calculate_aggregate_statistics(all_scores):
    """Calculate aggregate statistics for each translation across all evaluations."""
    stats = {}
    criteria_count = 7  # Number of criteria being evaluated
    
    for trans_id, score_lists in all_scores.items():
        # Convert list of score arrays to 2D numpy array
        scores_array = np.array(score_lists)
        
        # Initialize score distributions for each criterion
        per_criterion_distribution = []
        for i in range(criteria_count):
            criterion_scores = scores_array[:, i]
            distribution = {
                "0-1": 0,
                "1-2": 0,
                "2-3": 0,
                "3-4": 0,
                "4-5": 0
            }
            
            # Count scores for this criterion
            for score in criterion_scores:
                if 0 <= score <= 1:
                    distribution["0-1"] += 1
                elif 1 < score <= 2:
                    distribution["1-2"] += 1
                elif 2 < score <= 3:
                    distribution["2-3"] += 1
                elif 3 < score <= 4:
                    distribution["3-4"] += 1
                elif 4 < score <= 5:
                    distribution["4-5"] += 1
                    
            # Calculate percentages
            total_scores = len(criterion_scores)
            distribution_percentage = {
                k: round(v / total_scores * 100, 2)
                for k, v in distribution.items()
            }
            
            per_criterion_distribution.append({
                "counts": distribution,
                "percentages": distribution_percentage
            })
        
        # Calculate overall score distribution
        overall_distribution = {
            "0-1": 0,
            "1-2": 0,
            "2-3": 0,
            "3-4": 0,
            "4-5": 0
        }
        
        flattened_scores = scores_array.flatten()
        for score in flattened_scores:
            if 0 <= score <= 1:
                overall_distribution["0-1"] += 1
            elif 1 < score <= 2:
                overall_distribution["1-2"] += 1
            elif 2 < score <= 3:
                overall_distribution["2-3"] += 1
            elif 3 < score <= 4:
                overall_distribution["3-4"] += 1
            elif 4 < score <= 5:
                overall_distribution["4-5"] += 1
        
        stats[trans_id] = {
            "mean_per_criterion": np.mean(scores_array, axis=0).tolist(),
            "overall_mean": float(np.mean(scores_array)),
            "overall_median": float(np.median(scores_array)),
            "num_evaluations": len(score_lists),
            "overall_distribution": overall_distribution,
            "overall_distribution_percentage": {
                k: round(v / len(flattened_scores) * 100, 2)
                for k, v in overall_distribution.items()
            },
            "per_criterion_distribution": per_criterion_distribution
        }
    
    return stats

def print_aggregate_statistics(stats):
    """Print the aggregate statistics in a readable format."""
    criteria_names = [
        "Sensitive content translation",
        "Target language consistency",
        "No irrelevant words",
        "No spelling/grammar errors", 
        "Quantity accuracy",
        "Format maintenance",
        "Key words accuracy"
    ]
    
    print("\nAggregate Translation Statistics:")
    print("=" * 80)
    
    # Sort translations by overall mean score
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['overall_mean'], reverse=True)
    
    for trans_id, trans_stats in sorted_stats:
        print(f"\nTranslation {trans_id}:")
        print("-" * 80)
        print(f"Number of evaluations: {trans_stats['num_evaluations']}")
        print(f"Overall mean score: {trans_stats['overall_mean']:.2f}")
        print(f"Overall median score: {trans_stats['overall_median']:.2f}")
        
        print("\nOverall score distribution:")
        for range_key, count in trans_stats['overall_distribution'].items():
            percentage = trans_stats['overall_distribution_percentage'][range_key]
            print(f"  {range_key}: {count} scores ({percentage}%)")
        
        print("\nScores by criteria:")
        for i, (criterion, score) in enumerate(zip(criteria_names, trans_stats['mean_per_criterion'])):
            print(f"\n{i+1}. {criterion}:")
            print(f"  Mean score: {score:.2f}")
            print("  Score distribution:")
            criterion_dist = trans_stats['per_criterion_distribution'][i]
            for range_key in ["0-1", "1-2", "2-3", "3-4", "4-5"]:
                count = criterion_dist['counts'][range_key]
                percentage = criterion_dist['percentages'][range_key]
                print(f"    {range_key}: {count} scores ({percentage}%)")

def main():
    parser = argparse.ArgumentParser(description='Process LLM evaluation results and generate statistics.')
    parser.add_argument('--input', '-i', required=True,
                      help='Input JSONL file path containing LLM evaluation results')

    args = parser.parse_args()
    
    print(f"Processing file: {args.input}")

    import os
    filename = os.path.basename(args.input)

    filename_detail = filename+ "_detail.json"
    filename_stat = filename+ "_stat.json"
    
    # Process all lines in the file
    all_data, all_scores = process_file(args.input)
    
    # Calculate aggregate statistics
    statistics = calculate_aggregate_statistics(all_scores)
 
    # Save simplified JSON output
    with open(filename_detail, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    with open(filename_stat, 'w', encoding='utf-8') as f:
        json.dump(statistics, f, ensure_ascii=False, indent=2)
    
    # Print statistics
    print(f"\nSummary data has been saved to {args.output}")

if __name__ == "__main__":
    main()
