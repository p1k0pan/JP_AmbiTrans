import openai
import tqdm
import json
from pathlib import Path
from PIL import Image
from io import BytesIO
import os
import sys
import base64
import time
import argparse
import datetime

with open('/mnt/workspace/xintong/api_key.txt', 'r') as f:
    lines = f.readlines()

API_KEY = lines[0].strip()
BASE_URL = lines[1].strip()

openai.api_key = API_KEY
openai.base_url = BASE_URL

def call_api(text,system_prompt):
    response = openai.chat.completions.create(
        # model="模型",
        model = model_name, # 图文
        messages=[
            {'role': 'system', 'content': system_prompt},
            {
                "role": "user",
                "content": text
            }
        ],
    )
    return response.choices[0].message.content

system_prompt2 = """You are an expert linguistic annotator.

You will be given structured JSON input with the following fields:
- "en": the original English sentence
- "trans_zh": the human annotated Chinese translation of the sentence
- "zh_resolved_ambi": additional Chinese clarification on the resolved ambiguities.
- "agree_ambi": a list of ambiguity entries, where each entry contains:
    - "type": the type of ambiguity (e.g., lexical, syntactic, pragmatic, cultural/background)
    - "explanation": a description of the ambiguity
    - "ambiguous_terms": a list of ambiguous terms or phrases
    - "translations": example translations for each interpretation

Your task:
1. Carefully examine the "en", "trans_zh", and "zh_resolved_ambi" fields.
2. For each ambiguity listed in "agree_ambi":
   - For each ambiguous term, provide:
     - "term": the ambiguous word or phrase
     - "type": the ambiguity type (e.g., lexical, syntactic, etc.)
     - "gold_interpretation": the correct interpretation or Chinese translation based on trans_zh or zh_resolved_ambi

Instruction: 
- If a single ambiguous term involves multiple ambiguity types, return a separate JSON object for each type.
- **Do not merge different ambiguity types.**
- If the intended meaning is not covered in the example "translations", infer the correct sense from the context and provide it as "gold_interpretation".
- Output strictly in valid JSON format, one object per ambiguous term.
- No extra explanation or commentary outside the JSON.

Output format:
```json
[
  {
    "term": "ambiguous term",
    "type": "ambiguity type",
    "gold_interpretation": "correct interpretation in Chinese"
  }
]
```
"""

system_prompt3 = """You are an expert linguistic annotator.

You will be given structured JSON input with the following fields:
- "en": the original English sentence
- "standard_zh": the human annotated Chinese translation of the sentence
- "standard_resolved_ambiguity": additional Chinese clarification on the resolved ambiguities.
- "ambiguity_type": ambiguity type

Your task:
1. Carefully examine the "en", "standard_zh", and "standard_resolved_ambiguity" fields.
2. Find the ambiguious terms from "en".
   - For each ambiguous term, provide:
     - "term": the ambiguous word or phrase
     - "type": the ambiguity type
     - "gold_interpretation": the correct interpretation or Chinese translation based on standard_zh or standard_resolved_ambiguity

Instruction: 
- Output strictly in valid JSON format, one object per ambiguous term.
- No extra explanation or commentary outside the JSON.

Output format:
```json
[
  {
    "term": "ambiguous term",
    "type": "ambiguity type",
    "gold_interpretation": "correct interpretation in Chinese"
  }
]
```
"""

user_input = "en: {en}\nstandard_zh: {zh}\nstandard_resolved_ambiguity: {zh_resolved_ambi}\nambiguity_type: {ambiguity_type}"

def find_ambi(ref):
    data = json.load(open(ref, 'r'))
    sleep_times = [5, 10, 20, 40, 60]
    result = []

    for item in tqdm.tqdm(data):
        text = user_input.format(en=item["en"],zh=item["standard_zh"], zh_resolved_ambi=item["standard_resolved_ambiguity"],ambiguity_type=item["class"])

        idx = item["idx"]

        last_error = None  # 用于存储最后一次尝试的错误

        for sleep_time in sleep_times:
            try:
                outputs = call_api(text,system_prompt3)
                break  # 成功调用时跳出循环
            except Exception as e:
                last_error = e  # 记录最后一次错误
                print(f"Error on {idx}: {e}. Retry after sleeping {sleep_time} sec...")
                if "Error code: 400" in str(e) or "Error code: 429" in str(e):
                    time.sleep(sleep_time)
                else:
                    item["error"]=str(e)
                    outputs = ""
                    break
        else:
            # 如果达到最大重试次数仍然失败，记录空结果, break不会进入else
            print(f"Skipping {idx}")
            outputs
            if last_error:  # 确保 last_error 不是 None
                item["error"]=str(last_error)
        item["sense"]=outputs
        result.append(item)

    output_path = os.path.join(root, f"{model_name}_{os.path.basename(ref)}")
    print(f"Saving results to: {output_path}")
    json.dump(result, open(output_path, 'w'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
    model_name = "gpt-4o-2024-11-20"
    print(model_name)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--terminal', 
        type=int, 
        required=False,  # 如果一定要提供terminal参数
        choices=list(range(1, 7)),  # 限定可选值为 1~6
        help="Specify which terminal block (1 to 6) to run"
    )
        
    # 解析命令行参数
    args = parser.parse_args()
    terminal = args.terminal

    today=datetime.date.today()

    root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/gpt4o找mma歧义-{today}/"
    Path(root).mkdir(parents=True, exist_ok=True)

    file = "../data/mma_correct_zh.json"
    print("file ", file)
    find_ambi(file)