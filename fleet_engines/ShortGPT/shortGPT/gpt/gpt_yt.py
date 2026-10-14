from shortGPT.gpt import gpt_utils
import json

def generate_title_description_dict(content):
    out = {"title": "", "description":""}
    chat, system = gpt_utils.load_local_yaml_prompt('prompt_templates/yt_title_description.yaml')
    chat = chat.replace("<<CONTENT>>", f"{content}")
    
    attempts = 0
    import re
    while (out["title"] == "" or out["description"] == "") and attempts < 3:
        attempts += 1
        result = gpt_utils.llm_completion(chat_prompt=chat, system=system, temp=0.7)
        try:
            match = re.search(r'\{.*\}', result, re.DOTALL)
            raw = match.group(0) if match else result
            response = json.loads(raw)
            if "title" in response:
                out["title"] = response["title"]
            if "description" in response:
                out["description"] = response["description"]
        except Exception as e:
            pass
            
    if not out["title"]:
        out["title"] = "Instant Karma Story"
    if not out["description"]:
        out["description"] = "#shorts #redditstories #viral"
        
    return out['title'], out['description']
