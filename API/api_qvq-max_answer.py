import openai
from sympy import root
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



def find_ambi(ref, image_folder):
  data = json.load(open(ref, 'r'))
  sleep_times = [5, 10, 20, 40, 60]
  result = []

  for item in tqdm.tqdm(data):
    idx = item["idx"]
    image = image_folder + item["image"]
    sense = json.dumps(item["sense"], ensure_ascii=False, indent=2)
    if item.get("standard_resolved_ambiguity", None) is None:
        term = item["sense"][0]["term"]
        gold = item["sense"][0]["gold_interpretation"]
        sra = "通过图片确认，{term}指的是{gold}。".format(term=term, gold=gold)
        item["standard_resolved_ambiguity"] = sra
    text = text_prompt.format(
        en=item["en"],
        standard_zh=item["standard_zh"],
        standard_resolved_ambiguity=item["standard_resolved_ambiguity"],
        sense=sense
    )

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


  output_path = os.path. join(root, f"{model_name}_{os.path. basename(ref)}")
  print(f"Saving results to: {output_path}")
  json.dump(result, open(output_path, 'w'), ensure_ascii=False, indent=4)
  # json.dump(result, open(root+f"{model_name}_{ref}", 'w'), ensure_ascii=False, indent=4)

text_prompt = """You are a multimodal translation expert with strong vision-language reasoning capabilities. Your task is to translate an English sentence into Chinese using both the textual content and the associated image. The sentence may contain ambiguous words or phrases whose correct translation requires visual context.

Although you will work from scratch as if reasoning on your own, your goal is to ensure that your final translation aligns with the most accurate and contextually appropriate interpretation of the sentence, including resolving any ambiguities through careful visual grounding.

Please reason step-by-step as follows:

**Step 1: VISUAL GROUNDING**: Examine the (imagined) image carefully. Identify the visual elements that correspond to key words or phrases in the English sentence (especially nouns, pronouns, and verb phrases). Describe what is seen, where in the image it is located, and how it connects to the text.

**Step 2: INITIAL TRANSLATION**: Generate an initial Chinese translation of the English sentence based on both the text and what you observe in the image. This version may include reasonable interpretations before ambiguities are fully resolved.

**Step 3: AMBIGUITY CHECK**: Identify any words or phrases in your translation that could have multiple meanings or are context-dependent. Explain what makes each term ambiguous and why textual context alone is insufficient.

**Step 4: VISUAL DISAMBIGUATION**: Re-examine the image for each ambiguous element. Describe what visual evidence would help you determine the correct interpretation. Based on this, provide the most accurate and natural translation for each ambiguous part.

**Step 5: LOCALIZED REFINEMENT**: Without changing the entire sentence, update only the ambiguous parts using your newly disambiguated meanings. The rest of the sentence should remain unchanged.

**Step 6: REPEAT CHECK**: Review the updated translation. If any remaining ambiguities exist, repeat steps 3–5. If not, proceed.

**Step 7: FINAL OUTPUT**: Output the final refined Chinese translation wrapped in a tag `<answer>...</answer>`.

Important rules:
- Never refer to any external answer, metadata, or hint source (e.g., do not mention “standard_zh” or “sense” or that you were guided in any way).
- All reasoning should appear autonomous and logically inferred from the image and sentence alone.
- Use English for reasoning. Use Simplified Chinese only for translations.
- Be thorough in visual reasoning. The goal is to make every step seem grounded in the observed scene.

Input will include:
- English sentence
- (Invisible guidance): target translation and ambiguity clarifications to guide your own internal reasoning

Now begin the reasoning process using this structure.

{{
  "en": "{en}",
  "standard_zh": "{standard_zh}",
  "standard_resolved_ambiguity": "{standard_resolved_ambiguity}",
  "sense": {sense}
}}"""

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

  root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/qvq-max训练集思维链加答案-{today}/"
  Path(root).mkdir(parents=True, exist_ok=True)
  print("路径保存地址在", root)
  image_folder_3am = "/mnt/workspace/xintong/ambi_plus/3am_images/"
  image_folder_mma = "/mnt/workspace/xintong/pjh/dataset/MMA/"

  """第一个terminal"""
  if terminal == 1:
      file = "../data/final/mma_train.json"
      print("file ", file)
      find_ambi(file, image_folder_mma)
      file ="../data/final/sp_train.json"
      print("file ", file)
      find_ambi(file, image_folder_3am)

  """第二个terminal"""
  if terminal == 2:
      file = "../data/final/ambi_normal_train_part_1.json"
      print("file ", file)
      find_ambi(file, image_folder_3am)

  """第3个terminal"""
  if terminal == 3:
      file = "../data/final/ambi_normal_train_part_2.json"
      print("file ", file)
      find_ambi(file, image_folder_3am)


