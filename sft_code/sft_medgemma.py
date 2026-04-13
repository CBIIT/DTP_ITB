"""
PEFT (LoRA) SFT for google/medgemma-27b-text-it

Single-node usage:
    python sft_peft_medgemma.py

Multi-GPU usage:
    accelerate launch --num_processes <N> sft_peft_medgemma.py

Multi-node DeepSpeed usage:
    accelerate launch --config_file accelerate_config.yaml sft_peft_medgemma.py
"""

from trl import SFTTrainer, SFTConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from peft import LoraConfig
import torch


def main():
    model_name = "google/medgemma-27b-text-it"

    # --- Data ---
    ds = load_dataset("json", data_files="train_trl.jsonl", split="train")
    ds = ds.rename_column("conversations", "messages")
    split_ds = ds.train_test_split(test_size=0.1, seed=42)
    train_ds = split_ds["train"]
    val_ds = split_ds["test"]

    # --- Tokenizer ---
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
        use_cache=False,
    )

    # --- LoRA ---
    peft_config = LoraConfig(
        r=32,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        task_type="CAUSAL_LM",
    )

    # --- Training ---
    training_args = SFTConfig(
        output_dir="/data/ITBgenAI/sft/medgemma-27b-lora-sft",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=2,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=3,
        dataloader_num_workers=2,
        report_to="none",
        push_to_hub=False,
        use_liger_kernel=True
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        peft_config=peft_config,
        args=training_args,
    )

    trainer.train()
    trainer.save_model()


if __name__ == "__main__":
    main()