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

def call_api(text, system_prompt, image):
    
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
You are a multimodal translation expert with strong vision-language reasoning capabilities. Your task is to translate an English sentence into Chinese, using both the textual content and the associated image. The sentence may contain ambiguous words or phrases whose correct translation requires visual context.

Please think and respond step-by-step using the following procedure:

1. **Visual Grounding**: Carefully examine the image and identify the visual elements that correspond to each key word or phrase in the English sentence (especially nouns, pronouns, and verb phrases). Describe what you see, where in the image it is, and how it connects to the text.

2. **Initial Translation**: Generate an initial Chinese translation of the English sentence, based on both the text and what you've seen in the image.

3. **Ambiguity Check**: Analyze your initial translation and identify any ambiguous terms—words or phrases whose meanings are unclear or context-dependent, and which cannot be confidently translated using text alone. List these ambiguous elements and explain why they are potentially unclear.

4. **Visual Disambiguation**: For each ambiguous word or phrase, re-examine the relevant parts of the image to infer the correct meaning. Explain what you see in the image that helps you resolve the ambiguity. Then, suggest a more accurate translation for the ambiguous part based on this visual evidence.

5. **Localized Refinement**: Without regenerating the entire sentence, replace or refine only the parts of your initial translation that contained ambiguity. Keep the rest of the sentence unchanged. Produce the improved version.

6. **Repeat Check**: Review the updated translation again to see if any other ambiguous terms remain. If so, repeat steps 3-5. If not, proceed.

7. **Final Output**: Output the final refined Chinese translation wrapped within a tag <answer>...</answer>.

**Important Notes**:
* Show each step of your reasoning explicitly and clearly.
* Give as much as possible detail of each step, make the explanation comprehensive.
* Do not regenerate the entire translation in step 5—only perform **localized edits** for disambiguation.
* Ensure the final Chinese sentence is fluent, accurate, and contextually appropriate.
* Primarily use English for reasoning, and only use Chinese for the translation. Don't translate the reasoning part into Chinese.

"""
user_input = "English sentence: {en}"

def find_ambi(ref, image_folder):
    data = json.load(open(ref, 'r'))
    sleep_times = [5, 10, 20, 40, 60]
    result = []

    for item in tqdm.tqdm(data):
        # ambi = json.dumps(item["agree_ambi"], ensure_ascii=False, indent=2)
        text = user_input.format(en=item["en"])

        idx = item["idx"]
        image = image_folder + item["image"]

        last_error = None  # 用于存储最后一次尝试的错误

        for sleep_time in sleep_times:
            try:
                outputs = call_api(text,system_prompt,image)
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
        item["o13_output"]=outputs
        result.append(item)

    output_path = os.path.join(root, f"{model_name}_{os.path.basename(ref)}")
    print(f"Saving results to: {output_path}")
    json.dump(result, open(output_path, 'w'), ensure_ascii=False, indent=4)


if __name__ == "__main__":
    model_name = "o1-2024-12-17"
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

    root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/{model_name}训练集思维链-{today}/"
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
