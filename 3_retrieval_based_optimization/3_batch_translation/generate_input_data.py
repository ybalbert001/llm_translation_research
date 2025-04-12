import json

input_files = ["./GenshinReadable/en-us-zh-cn_readable_testset.txt", "./GenshinSubtitle/en-us-zh-cn_subtitle_testset.txt"]

methods = ["No", "Reference_Retrieval", "Glossary_Retrieval", "ReferenceAndGlossary_Retrieval"]

for input_file in input_files:
    outputs = { method:[] for method in methods }
    with open(input_file) as file:
        content = file.read()
        pairs = content.split("=====")
        for pair in pairs:
            src, translation = pair.split("===>")
            for method in methods:
                record = {"src": src.strip(),"label": translation.strip(),"src_lang": 'en-us',"dest_lang": 'zh-cn',"Optimization" : method}
                line = json.dumps(record, ensure_ascii=False)
                outputs[method].append(line)

    for k, lines in outputs.items():
        part1, part2 = input_file.split('.txt')
        file_name = f"{part1}_{k}.jsonl"
        with open(file_name, 'w') as outf:
            outf.write('\n'.join(lines))

