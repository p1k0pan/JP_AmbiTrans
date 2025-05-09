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

def call_api(text,image):
    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复
    base64_image = encode_image(image)

    # 创建聊天完成请求
    completion = openai.chat.completions.create(
    model="qvq-max",  # 此处以 qvq-max 为例，可按需更换模型名称
    messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                    {"type": "text", "text": text},
                ],
            },
        ],
        stream=True,
    )
    for chunk in completion:
        if not chunk.choices:  
            continue  # 跳过无效数据
        delta = chunk.choices[0].delta

        # 记录思考过程
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
            reasoning_content += delta.reasoning_content
        else:
            # 进入回复阶段
            if delta.content and not is_answering:
                is_answering = True

            # 记录最终的回答内容
            answer_content += delta.content

    return reasoning_content, answer_content

text_prompt = "You are a multimodal assistant. The user provides an image and an English text to be translated into Chinese. The text is ambiguous on its own, so first you need to analyze the ambiguities in the text, then use the visual context from the image carefully to analyze how the visual content helps clarify the meaning of the text and disambiguate. Finally, provide the most accurate translation based on the resolved meaning. Only output the final Chinese translation.\n\nCaption: {en}"

def find_ambi(ref):
  data = json.load(open(ref, 'r'))
  sleep_times = [5, 10, 20, 40, 60]
  result = []

  for item in tqdm.tqdm(data):
    text = text_prompt.format(en=item["en"])
    idx = item["idx"]
    image = image_folder + item["image"]

    last_error = None  # 用于存储最后一次尝试的错误

    for sleep_time in sleep_times:
      try:
        reasoning, answer = call_api(text, image)
        break  # 成功调用时跳出循环
      except Exception as e:
        last_error = e  # 记录最后一次错误
        print(f"Error on {idx}: {e}. Retry after sleeping {sleep_time} sec...")
        if "Error code: 400" in str(e) or "Error code: 429" in str(e):
          time.sleep(sleep_time)
        else:
            item["error"]=str(e)
            reasoning = ""
            answer = ""
            break
    else:
      # 如果达到最大重试次数仍然失败，记录空结果, break不会进入else
      print(f"Skipping {idx}")
      reasoning = ""
      answer = ""
      if last_error:  # 确保 last_error 不是 None
        item["error"]=str(last_error)
    item["qvq_output"]={"reasoning": reasoning, "answer": answer}
    result.append(item)


  json.dump(result, open(root+f"{model_name}_{ref}", 'w'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
  model_name = "qvq-max"
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

  root = "result/qvq推理翻译{today}/"
  Path(root).mkdir(parents=True, exist_ok=True)
  image_folder = "/mnt/workspace/xintong/ambi_plus/3am_images/"

  """第一个terminal"""
  if terminal == 1:
    file = "../data/final_clean_2000_v1.6_part1.json"
    print("file ", file)
    find_ambi(file)

  """第二个terminal"""
  if terminal == 2:
    file = "../data/final_clean_2000_v1.6_part2.json"
    print("file ", file)
    find_ambi(file)

  """第3个terminal"""
  if terminal == 3:
    file = "../data/final_clean_2000_v1.6_part3.json"
    print("file ", file)
    find_ambi(file)

  """第4个terminal"""
  if terminal == 4:
    file = "../data/final_clean_2000_v1.6_part4.json"
    print("file ", file)
    find_ambi(file)

  """第5个terminal"""
  if terminal == 5: 
    file = "../data/final_clean_2000_v1.6_part5.json"
    print("file ", file)
    find_ambi(file)
