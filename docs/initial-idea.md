Let's create a simple Python CLI client of OpenRouter.ai's image generation. To be specific:

- Python 3.14, managed by `uv`
- using `requests` to access APIs

Input: text prompt + reference image (optional)
Ouput: generated image save with name "ezbanana_<timestamp>_<8-digit random string>.png"

- Image Generation API document: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
- Image input API document: https://openrouter.ai/docs/guides/overview/multimodal/images