"""
Fast Local AI Rendering for Revit Views
Uses SD-Turbo optimized for CPU - produces results in ~30-60 seconds
"""

import sys
import os
import argparse
from pathlib import Path

def render_image(input_path: str, output_path: str = None, strength: float = 0.5,
                 prompt: str = "photorealistic architectural rendering, professional photography, natural lighting"):
    """
    Transform a Revit 3D view into a photorealistic rendering.

    Args:
        input_path: Path to input image (captured from Revit)
        output_path: Path for output image (default: input_rendered.png)
        strength: Denoising strength 0.3-0.7 (lower = more geometry preservation)
        prompt: Style prompt for rendering
    """
    import torch
    from diffusers import AutoPipelineForImage2Image
    from PIL import Image

    print(f"Loading SDXL-Turbo model (first time will download ~7GB)...")

    # Use SDXL-Turbo for better quality (larger model but better results)
    pipe = AutoPipelineForImage2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float32,  # CPU needs float32
        variant="fp16" if torch.cuda.is_available() else None,
        safety_checker=None,
        requires_safety_checker=False
    )

    # CPU optimization
    pipe.to("cpu")

    # Enable memory efficient attention if available
    try:
        pipe.enable_attention_slicing()
    except:
        pass

    print(f"Loading input image: {input_path}")
    input_image = Image.open(input_path).convert("RGB")

    # Resize for faster processing if too large (max 768px on longest side)
    max_size = 768
    w, h = input_image.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        # Round to nearest 8 for model compatibility
        new_w = (new_w // 8) * 8
        new_h = (new_h // 8) * 8
        input_image = input_image.resize((new_w, new_h), Image.LANCZOS)
        print(f"Resized to {new_w}x{new_h} for faster processing")

    print(f"Generating photorealistic rendering (this takes ~30-60 seconds on CPU)...")
    print(f"Prompt: {prompt}")
    print(f"Strength: {strength} (lower = more original geometry preserved)")

    # SD-Turbo is designed for 4 steps
    result = pipe(
        prompt=prompt,
        image=input_image,
        strength=strength,
        num_inference_steps=4,
        guidance_scale=0.0,  # SD-Turbo doesn't use guidance
    ).images[0]

    # Determine output path
    if output_path is None:
        input_p = Path(input_path)
        output_path = str(input_p.parent / f"{input_p.stem}_rendered{input_p.suffix}")

    # Save result
    result.save(output_path, quality=95)
    print(f"Rendered image saved to: {output_path}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Fast AI Rendering for Revit Views")
    parser.add_argument("input", help="Input image path (Revit 3D view capture)")
    parser.add_argument("-o", "--output", help="Output image path")
    parser.add_argument("-s", "--strength", type=float, default=0.5,
                       help="Denoising strength 0.3-0.7 (default: 0.5, lower preserves more geometry)")
    parser.add_argument("-p", "--prompt", default="photorealistic architectural rendering, professional photography, natural lighting, high detail",
                       help="Style prompt")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    try:
        output = render_image(args.input, args.output, args.strength, args.prompt)
        print(f"\nSuccess! Rendering complete: {output}")
    except Exception as e:
        print(f"Error during rendering: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
