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
* Primarily use English for reasoning, and only use Simplified Chinese for the translation. Don't translate the reasoning part into Chinese.

"""
user_input = "English sentence: {en}"

# system_prompt2 = """You are a multimodal translation expert with strong vision-language reasoning capabilities. Your task is to **simulate** the reasoning process that leads to a correct Chinese translation of an English sentence, using both the textual content and an associated image.

# You are provided with:
# - The English sentence.
# - A human-verified standard Chinese translation (`standard_zh`).
# - A disambiguation note that resolves ambiguities using visual information (`standard_resolved_ambiguity`).
# - A list of ambiguous terms or phrases and their correct interpretations (`sense`).

# Your goal is to **generate a detailed, plausible step-by-step reasoning process** that could realistically lead to the provided correct translation and disambiguation, as if you were working from the image and the sentence alone.

# Please proceed using the following steps:

# 1. **VISUAL GROUNDING**: Pretend to examine the image. Identify the visual elements that correspond to each key word or phrase in the English sentence (especially nouns, pronouns, and verb phrases). Describe what is (supposedly) seen, where in the image it is, and how it connects to the text. Make this visual reasoning consistent with the disambiguation and final translation.

# 2. **INITIAL TRANSLATION**: Produce an initial Chinese translation of the English sentence, as if it were based on both the text and your visual observations. This initial translation should include **a plausible but not yet disambiguated** interpretation of any ambiguous terms.

# 3. **AMBIGUITY CHECK**: Identify any ambiguous terms in your initial translation that are also listed in the provided `sense` list. Explain why they are ambiguous and note that visual inspection is needed.

# 4. **VISUAL DISAMBIGUATION**: Simulate examining the image again, and describe what visual evidence would help you disambiguate each term. Then explain how this resolves the ambiguity, using the content from `standard_resolved_ambiguity`.

# 5. **LOCALIZED REFINEMENT**: Update **only the ambiguous parts** of your initial translation, incorporating the correct meaning based on the visual evidence. Keep all other parts unchanged.

# 6. **REPEAT CHECK**: Review the refined sentence again to ensure no unresolved ambiguities remain. If all are resolved, continue.

# 7. **FINAL OUTPUT**: Output the final refined Chinese translation wrapped within a tag `<answer>...</answer>`.

# Important constraints:
# - Your reasoning must clearly show how the correct answer was derived.
# - Do not invent different interpretations — align your reasoning with the given standard translation and disambiguation.
# - Write all reasoning in English. Only write the translations in Simplified Chinese.
# - Be comprehensive and specific — assume a human reader will use this to fine-tune a model.

# Now simulate the reasoning process as described."""

system_prompt2 = """You are a multimodal translation expert with strong vision-language reasoning capabilities. Your task is to translate an English sentence into Chinese using both the textual content and the associated image. The sentence may contain ambiguous words or phrases whose correct translation requires visual context.

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

{
  "en": "The man is flashing the peace sign.",
  "standard_zh": "那个男人正在向某人比划和平手势。",
  "standard_resolved_ambiguity": "通过图片确认，该短语指的是用手做出和平手势（V字手势），而不是展示其他物理标志。",
  "sense": [
    {
      "term": "flashing the peace sign",
      "type": "lexical",
      "gold_interpretation": "正在向某人比划和平手势"
    }
  ]
}"""
user_input2 = """{{
  "en": "{en}",
  "standard_zh": "{standard_zh}",
  "standard_resolved_ambiguity": "{standard_resolved_ambiguity}",
  "sense": {sense}
}}"""

def find_ambi(ref, image_folder):
    data = json.load(open(ref, 'r'))
    sleep_times = [5, 10, 20, 40, 60]
    result = []

    for item in tqdm.tqdm(data):
        sense = json.dumps(item["sense"], ensure_ascii=False, indent=2)
        if item.get("standard_resolved_ambiguity", None) is None:
            term = item["sense"][0]["term"]
            gold = item["sense"][0]["gold_interpretation"]
            sra = "通过图片确认，{term}指的是{gold}。".format(term=term, gold=gold)
            item["standard_resolved_ambiguity"] = sra
        text = user_input2.format(
            en=item["en"],
            standard_zh=item["standard_zh"],
            standard_resolved_ambiguity=item["standard_resolved_ambiguity"],
            sense=sense
        )

        idx = item["idx"]
        image = image_folder + item["image"]

        last_error = None  # 用于存储最后一次尝试的错误

        for sleep_time in sleep_times:
            try:
                outputs = call_api(text,system_prompt2,image)
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
            outputs = ""
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

    root = f"/mnt/workspace/xintong/pjh/All_result/JP_AmbiTrans/{model_name}训练集思维链加答案-{today}/"
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
