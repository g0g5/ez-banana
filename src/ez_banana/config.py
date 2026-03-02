OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"
REQUEST_TIMEOUT: tuple[float, float] = (3.05, 60.0)
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
SUPPORTED_REFERENCE_IMAGE_MIME_TYPES = frozenset(
    {
        "image/bmp",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    }
)
