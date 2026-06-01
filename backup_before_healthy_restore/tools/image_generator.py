from urllib.parse import quote


def make_pollinations_image_url(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None
) -> str:
    clean = (prompt or "NeuroMV generated image").strip()
    safe = quote(clean)

    url = (
        f"https://image.pollinations.ai/prompt/{safe}"
        f"?width={width}&height={height}&nologo=true"
    )

    if seed is not None:
        url += f"&seed={seed}"

    return url


def make_image_markdown(prompt: str) -> str:
    url = make_pollinations_image_url(prompt)

    return (
        "Generated image:\n\n"
        f"![Generated image]({url})\n\n"
        f"Prompt used: {prompt}"
    )
