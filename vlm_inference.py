from vllm import LLM
from vllm.sampling_params import SamplingParams

model_name = "mistralai/Pixtral-12B-2409"

sampling_params = SamplingParams(max_tokens=8192)

llm = LLM(model=model_name, tokenizer_mode="mistral")

prompt = "Analyze this edge detector processed image and output in under 50 words. Don't mention edge detection in the response. Speak like a hardware expert and help me understand what the hardware in the image is, its design pros, and its primary use case."
url = f"data:image/jpeg;base64,{base64_image}"

messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]
    },
]

outputs = vllm_model.model.chat(messages, sampling_params=sampling_params)

print(outputs[0].outputs[0].text)
