#!/usr/bin/env python3
import json
import os
import argparse

Threshold = 4

def process_file(input_file, terms_dict):
    """Process a single input file and extract terms."""
    print(f"Processing file: {input_file}")

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            # Parse the JSON line
            data = json.loads(line)
            try:
                # Check if there are extracted terms
                if data and 'modelOutput' in data and 'results' in data['modelOutput'] and 'extracted_terms' in data['modelOutput']['results']:
                    extracted_terms = data['modelOutput']['results']['extracted_terms']
                    
                    # Process each extracted term
                    for term in extracted_terms:
                        # Check if specialty_score >= Threshold
                        if 'specialty_score' not in term or term['specialty_score'] < Threshold:
                            continue
                        
                        # Check if accuracy_scores >= Threshold for all languages
                        if 'accuracy_scores' not in term:
                            continue
                        
                        accuracy_scores = term['accuracy_scores']
                        all_scores_valid = True
                        for lang, score in accuracy_scores.items():
                            if score < Threshold:
                                all_scores_valid = False
                                break
                        
                        if not all_scores_valid:
                            continue
                        
                        if 'terms' in term:
                            # Create a unique key for the term
                            # Using the zh-cn term as the key if available, otherwise use en-us or ja-jp
                            key = None
                            if 'zh-cn' in term['terms'] and term['terms']['zh-cn']:
                                key = term['terms']['zh-cn']
                            elif 'en-us' in term['terms'] and term['terms']['en-us']:
                                key = term['terms']['en-us']
                            elif 'ja-jp' in term['terms'] and term['terms']['ja-jp']:
                                key = term['terms']['ja-jp']
                            
                            if key:
                                # If this term is not already in our dictionary, add it
                                if key not in terms_dict:
                                    # Initialize the mapping with only languages that have terms
                                    mapping = {}
                                    
                                    # Fill in the available translations
                                    for lang, translation in term['terms'].items():
                                        if translation:  # Only add languages with non-empty translations
                                            mapping[lang] = [translation]
                                    
                                    # Determine entity type based on domain if available
                                    entity_type = "Term"
                                    if 'domain' in term:
                                        domain = term['domain']
                                        if any(keyword in domain for keyword in ["角色", "人物", "Character"]):
                                            entity_type = "Character"
                                        elif any(keyword in domain for keyword in ["地点", "Location", "地名"]):
                                            entity_type = "Location"
                                        elif any(keyword in domain for keyword in ["物品", "Item", "道具"]):
                                            entity_type = "Item"
                                    
                                    terms_dict[key] = {
                                        "mapping": mapping,
                                        "entity_type": entity_type
                                    }
            except Exception as e:
                print(f"Exception:{e}; Data: {data}")
    
    return terms_dict

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert JSONL files to dictionary format')
    parser.add_argument('input_files', nargs='+', help='Input JSONL files to process')
    parser.add_argument('-o', '--output', default='./output_dictionary.json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Dictionary to store unique terms
    terms_dict = {}
    
    # Process each input file
    for input_file in args.input_files:
        terms_dict = process_file(input_file, terms_dict)
    
    # Create the output dictionary structure
    output_dict = {
        "type": "multilingual_terminology",
        "author": "",
        "data": list(terms_dict.values())
    }
    
    # Write the output file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete. Output written to {args.output}")
    print(f"Total terms extracted: {len(terms_dict)}")
    print(f"Terms filtered by specialty_score >= {Threshold} and accuracy_scores >= {Threshold}")

if __name__ == "__main__":
    main()
