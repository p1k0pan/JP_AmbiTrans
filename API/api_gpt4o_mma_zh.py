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

system_prompt = """
You are an English→Chinese multimodal translation expert. 
Input:
  1. A single English caption (text).
  2. One images that show the scene the caption describes.
  3. Ambiguity type of the caption
  4. Disambiguate hints

Your task:
  - Look at BOTH the text and the image(s). 
  - Use the visual evidence and disambiguate hints to accurately disambiguate and translate the caption into Chinese.
  - Briefly state which ambiguity was resolved by the visual evidence.

Output JSON (Chinese UTF‑8):
{
  "translation_zh": "<最终中文译文>",
  "resolved_ambiguity": "<简要说明是哪一类歧义，以及图片如何消解>",
  "confidence_0_to_1": <0‑1 浮点数, 1 表示完全确定>
}

Rules:
  - If the caption is actually unambiguous even without the image, set "resolved_ambiguity" to "N/A".
  - Do not describe the image; focus on producing the best translation.
  - Use concise, standard‑register Mandarin (简体中文) a natural and fluent word order.
"""

user_prompt = """
Caption: "{english_caption}"
Ambiguity type: {ambiguity_type}
Disambiguate hints: {disambiguate_hints}
"""

def find_ambi(ref):
  data = json.load(open(ref, 'r'))
  sleep_times = [5, 10, 20, 40, 60]
  result = []

  for item in tqdm.tqdm(data):
    hint = item["hint"]
    text = user_prompt.format(english_caption=item["en"], ambiguity_type=item["class"], disambiguate_hints=hint)
    idx = item["idx"]
    image = image_folder + item["image"]

    last_error = None  # 用于存储最后一次尝试的错误

    for sleep_time in sleep_times:
      try:
        outputs = call_api(text, image, system_prompt)
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
    item["ambi"]=outputs
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

  root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/mma翻译_v2-{today}/"
  Path(root).mkdir(parents=True, exist_ok=True)
  image_folder = "/mnt/workspace/xintong/pjh/dataset/MMA/"
  
  file = "../data/mma_hint.json"
  print("file ", file)
  find_ambi(file)
