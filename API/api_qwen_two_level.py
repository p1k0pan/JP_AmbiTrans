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

text_prompt = '''
You are given an English sentence that describes an image (a caption). Your task is to identify whether it contains any **second-level ambiguous nouns** that could cause semantic ambiguity when translating into Chinese.

A **second-level ambiguous noun** is defined as:

1. A word that has **two or more completely unrelated meanings** in English;
2. Each meaning corresponds to a **different Chinese translation**;
3. Each Chinese translation could be **further specified** if image context were available;
4. The ambiguity exists in the sentence itself — not caused by visual information;
5. The purpose is to detect words where translation **accuracy** depends on image context.

Do **NOT** include:
- Verbs, adjectives, or other non-nouns.
- Nouns with only one core meaning (e.g., "flag" → "旗帜");
- Nouns that are vague but not ambiguous (e.g., "object", "thing").

---

### Output format:
Return a JSON object like this:

{
  "has_2nd_level_ambiguity": true or false,
  "ambiguous_terms": [
    {
      "term": "<original word>",
      "translations": ["<Chinese meaning 1>", "<Chinese meaning 2>"],
      "possible_specific_translations": {
        "<Chinese meaning 1>": ["...", "..."],
        "<Chinese meaning 2>": ["...", "..."]
      },
      "explain": "<brief English explanation of how the meanings differ and how they could be specified with image context>"
    }
  ]
}

If no such ambiguous words are found, return:

{
  "has_2nd_level_ambiguity": false,
  "ambiguous_terms": []
}

---

### Examples:

#### Example 1:
Sentence: "The children played with a ball at the party."

Expected output:
{
  "has_2nd_level_ambiguity": true,
  "ambiguous_terms": [
    {
      "term": "ball",
      "translations": ["球", "舞会"],
      "possible_specific_translations": {
        "球": ["足球", "篮球", "排球"],
        "舞会": ["化妆舞会", "晚宴舞会"]
      },
      "explain": "The word 'ball' can mean a round sports object (球) or a formal dancing event (舞会), and both can be further specified depending on the image."
    }
  ]
}

#### Example 2:
Sentence: "The engineer adjusted the instruments on the panel."

Expected output:
{
  "has_2nd_level_ambiguity": true,
  "ambiguous_terms": [
    {
      "term": "instruments",
      "translations": ["仪器", "乐器"],
      "possible_specific_translations": {
        "仪器": ["温度计", "电压表", "传感器"],
        "乐器": ["小提琴", "吉他", "萨克斯"]
      },
      "explain": "The word 'instruments' may refer to scientific tools (仪器) or musical devices (乐器), and each can be visually identified more specifically."
    }
  ]
}

#### Example 3:
Sentence: "A man waves a flag near the river."

Expected output:
{
  "has_2nd_level_ambiguity": false,
  "ambiguous_terms": []
}

---

Now analyze the following sentence and return only the JSON result.
'''
user_input = """
En: {en}
"""
def find_ambi(ref):
    data = json.load(open(ref, 'r'))
    sleep_times = [5, 10, 20, 40, 60]
    result = []

    for item in tqdm.tqdm(data):
        text = user_input.format(en=item["en"])

        idx = item["idx"]

        last_error = None  # 用于存储最后一次尝试的错误

        for sleep_time in sleep_times:
            try:
                outputs = call_api(text,text_prompt)
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
        item["two_level"]=outputs
        result.append(item)

    output_path = os.path.join(root, f"{model_name}_{os.path.basename(ref)}")
    print(f"Saving results to: {output_path}")
    json.dump(result, open(output_path, 'w'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
    model_name = "qwen-max-2025-01-25"
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

    root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qwen_max判断二级歧义-{today}/"
    Path(root).mkdir(parents=True, exist_ok=True)
    image_folder = "/mnt/workspace/xintong/ambi_plus/3am_images/"

    files = [
        "../data/图文匹配/test_plus_图文匹配.json",
        "../data/图文匹配/val_plus_图文匹配.json",
        "../data/图文匹配/train_plus_图文匹配.json",
    ]
    for file in files:
        print("file ", file)
        find_ambi(file)