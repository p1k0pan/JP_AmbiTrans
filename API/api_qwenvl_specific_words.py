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

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def call_api(text,image, system_prompt):
    base64_image = encode_image(image)
    response = openai.chat.completions.create(
        # model="模型",
        model = model_name, # 图文
        messages=[
                {'role': 'system', 'content': system_prompt},
                {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        # 需要注意，传入Base64，图像格式（即image/{format}）需要与支持的图片列表中的Content Type保持一致。"f"是字符串格式化的方法。
                        # PNG图像：  f"data:image/png;base64,{base64_image}"
                        # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
                        # WEBP图像： f"data:image/webp;base64,{base64_image}"
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}, 
                    },
                    {"type": "text", "text": text},
                ],
            }
        ],
    )
    return response.choices[0].message.content

text_prompt ='''
You are given:
- An English sentence that describes an image (a caption).
- A list of abstract or general nouns extracted from the sentence.
- The corresponding image.

Your task is to determine whether the abstract terms can be made more specific based on the image.

For each term:
1. If the image allows a more specific interpretation of the term, provide:
   - The original abstract term.
   - A more specific Chinese translation of this term.
   - A brief explanation in English of why this more specific translation is possible from the image.
2. If no terms can be made more specific, return an empty detail list.

Your final response must be a JSON object in the following format:

{
  "is_specific": true or false,
  "detail": [
    {
      "term": "<original abstract term>",
      "specific_trans": "<specific Chinese translation>",
      "explain": "<short explanation in English>"
    },
    ...
  ]
}

Do not include any other output besides the JSON. Do not translate the whole sentence. Only analyze and translate the abstract terms.

---

Here are some examples to guide your output format and reasoning:

### Example 1:
Sentence: "A game in progress (prototype shown)."  
Abstract terms: ["game"]  
Image: A photo showing people sitting around a table playing a card-based board game.

Expected output:
{
  "is_specific": true,
  "detail": [
    {
      "term": "game",
      "specific_trans": "桌游",
      "explain": "The image shows people playing a board/card game at a table, clearly indicating it's a tabletop game."
    }
  ]
}

---

### Example 2:
Sentence: "A paneled van and car sit at an intersection by a large round object."  
Abstract terms: ["object"]  
Image: A street scene with a round metal gas tank or cylinder on the roadside.

Expected output:
{
  "is_specific": true,
  "detail": [
    {
      "term": "object",
      "specific_trans": "煤气罐",
      "explain": "The large round object in the image resembles a gas cylinder, so it can be translated more specifically."
    }
  ]
}

---

### Example 3:
Sentence: "A group of people with umbrellas sitting next to a picture."  
Abstract terms: ["group", "people", "picture"]  
Image: A crowd of people sitting on a bench under umbrellas, with a framed image beside them.

Expected output:
{
  "is_specific": false,
  "detail": []
}

---
Now begin the task.
'''
user_input = """
En: {en}
Abstract terms: {abstract_terms}
"""

def find_ambi(ref):
  data = json.load(open(ref, 'r'))
  sleep_times = [5, 10, 20, 40, 60]
  result = []

  for item in tqdm.tqdm(data):
    en = item["en"]
    hyper = item["hyper"]["hypernyms"]
    abstract_terms = []
    for h in hyper:
      abstract_terms.append(h["word"])
    text = user_input.format(en=en, abstract_terms=abstract_terms)
    idx = item["idx"]
    image = image_folder + item["image"]

    last_error = None  # 用于存储最后一次尝试的错误

    for sleep_time in sleep_times:
      try:
        outputs = call_api(text, image, text_prompt)
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
    item["qvq_output"]=outputs
    result.append(item)

  output_path = os.path.join(root, f"{model_name}_{os.path.basename(ref)}")
  print(f"Saving results to: {output_path}")
  json.dump(result, open(output_path, 'w'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
  model_name = "qwen-vl-max"
  print(model_name)
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--terminal', 
    type=int, 
    required=True,  # 如果一定要提供terminal参数
    choices=list(range(1, 7)),  # 限定可选值为 1~6
    help="Specify which terminal block (1 to 6) to run"
)
    
  # 解析命令行参数
  args = parser.parse_args()
  terminal = args.terminal

  today=datetime.date.today()

  root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qwenvl_找具体词-{today}/"
  Path(root).mkdir(parents=True, exist_ok=True)
  image_folder = "/mnt/workspace/xintong/ambi_plus/3am_images/"
  
  file = "../data/找具体词/hyper_不重复_2976.json"
  print("file ", file)
  find_ambi(file)
