#from dotenv import load_dotenv

# load_dotenv()

import json
from datasets import load_dataset
from transformers import AutoTokenizer





tok = AutoTokenizer.from_pretrained("openai/gpt-oss-20b", use_fast=True)


DEVELOPER_MESSAGE = {"role": "system", "content": "You are a helpful biology lab assistant."}
USER_MESSAGE = {"role": "user", "content": "Your task is to identify the schedule of administering the drug compounds to the test subjects from the provided text. For example, 'Single oral gavage (po) dose once daily' along with the dose levels, which are typically in the format of 'mg/kg/day'. Identify at least one possible value, but no more than two total values. If the two values appear to be similar, just use one of the values instead of both."}
ASSISTANT_MESSAGE = {"role": "assistant", "content": "Sure! Please provide the text from the toxicology experiment report, and I will do my best to identify the schedule of administering the drug compounds along with the dose levels."}


def create_chat_messages(text, truth=''):
    return {
        "messages": [
            DEVELOPER_MESSAGE,
            USER_MESSAGE,
            ASSISTANT_MESSAGE,
            {"role": "user", "content": text},
            {"role": "assistant", "content": truth},
        ]
    }


def main():
    # Iterate through schedule_admin_training_sft.json and pass the 'schedule_text' and the 'Schedule of Administration' value to the create_chat_messages function to create the messages
    conversations = []
    with open("schedule_admin_training_sft.json", "r", encoding="utf-8") as f:
        training_data = json.load(f)
    for item in training_data:
        schedule_text = item.get("schedule_text", "")
        schedule_of_admin = item.get("Schedule of Administration", "")
        if schedule_of_admin == "":
            continue
        if len(schedule_text) < 100:
            continue
        messages = create_chat_messages(schedule_text, schedule_of_admin)
        conversations.append(messages)
    
    written = 0
    # Write the conversations list to a json file
    with open("train_trl.jsonl", "w", encoding="utf-8") as f:
        for item in conversations:
            # expected: {"messages": [ {"role":..., "content":...}, ... ]}
            if not isinstance(item, dict):
                continue
            msgs = item.get("messages")
            if not isinstance(msgs, list) or not msgs:
                continue

            # basic sanity cleanup: keep only role/content pairs
            cleaned = []
            for m in msgs:
                if isinstance(m, dict) and "role" in m and "content" in m:
                    cleaned.append({"role": m["role"], "content": m["content"]})

            if not cleaned:
                continue

            f.write(json.dumps({"conversations": cleaned}, ensure_ascii=False) + "\n")
        written += 1
    print(f"Wrote {written} TRL-ready examples to train_trl.jsonl")

def to_text(example):
    # If your tokenizer supports chat templates, use them (best)
    if hasattr(tok, "apply_chat_template"):
        text = tok.apply_chat_template(
            example["conversations"],
            tokenize=False,
            add_generation_prompt=False,
        )
    else:
        # Fallback: simple serialization
        text = ""
        for m in example["conversations"]:
            text += f"{m['role']}: {m['content']}\n"
    return {"text": text}

if __name__ == "__main__":
    main()

    # test
    ds = load_dataset("json", data_files="train_trl.jsonl", split="train")
    ds = ds.map(to_text, remove_columns=ds.column_names)
    ds.to_json("train_trl_text.jsonl")