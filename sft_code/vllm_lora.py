"""
Inference with a LoRA adapter on google/medgemma-27b-text-it via a vLLM
server running in a Singularity/Docker container.

Start the container (example):
    singularity run --nv --bind /data:/data vllm_latest.sif \
        --model google/medgemma-27b-text-it \
        --enable-lora \
        --max-lora-rank 16 \
        --dtype bfloat16 \
        --max-model-len 2048 \
        --lora-modules medgemma-lora=/data/ITBgenAI/sft/medgemma-27b-peft-sft

Usage:
    python vllm_lora.py
"""

from openai import OpenAI

VLLM_BASE_URL = "http://localhost:8000/v1"
LORA_MODEL = "medgemma-lora"

client = OpenAI(base_url=VLLM_BASE_URL, api_key="unused")

messages = [
    {"role": "system", "content": "You are a helpful biology lab assistant."},
    {"role": "user", "content": "What is the typical dosing schedule for a 14-day oral gavage toxicology study in rats?"},
]

response = client.chat.completions.create(
    model=LORA_MODEL,
    messages=messages,
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
)

print(response.choices[0].message.content)
