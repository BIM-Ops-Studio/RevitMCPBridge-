"""
DiffusionService - AI Rendering Integration for RevitMCPBridge

Provides endpoints for submitting viewport captures to Stable Diffusion
(ComfyUI or Automatic1111) for architectural rendering enhancement.

Usage:
    service = DiffusionService(backend="automatic1111", url="http://localhost:7860")
    job_id = service.submit_render(image_path, prompt, style_preset)
    status = service.get_status(job_id)
    result = service.get_result(job_id)
"""

import os
import sys
import json
import time
import base64
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from queue import Queue
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DiffusionService")


class RenderStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Backend(Enum):
    AUTOMATIC1111 = "automatic1111"
    COMFYUI = "comfyui"


@dataclass
class RenderJob:
    job_id: str
    status: RenderStatus
    input_image: str
    prompt: str
    negative_prompt: str
    style_preset: str
    backend: Backend
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    result_image: Optional[str] = None
    error: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


# Style presets for architectural rendering
STYLE_PRESETS = {
    "photorealistic": {
        "prompt_prefix": "photorealistic architectural visualization, 8k uhd, professional photography, ",
        "prompt_suffix": ", sharp focus, natural lighting, high detail",
        "negative_prompt": "cartoon, anime, drawing, sketch, blurry, low quality, distorted",
        "steps": 30,
        "cfg_scale": 7.5,
        "denoising_strength": 0.5,
    },
    "sketch": {
        "prompt_prefix": "architectural pencil sketch, hand drawn, ",
        "prompt_suffix": ", clean lines, professional drafting, technical drawing",
        "negative_prompt": "photo, realistic, 3d render, color",
        "steps": 25,
        "cfg_scale": 8.0,
        "denoising_strength": 0.7,
    },
    "watercolor": {
        "prompt_prefix": "watercolor architectural illustration, artistic rendering, ",
        "prompt_suffix": ", soft colors, painterly style, architectural presentation",
        "negative_prompt": "photo, realistic, sharp, digital",
        "steps": 28,
        "cfg_scale": 7.0,
        "denoising_strength": 0.65,
    },
    "blueprint": {
        "prompt_prefix": "technical blueprint, architectural drawing, white lines on blue background, ",
        "prompt_suffix": ", precise technical illustration, engineering drawing",
        "negative_prompt": "photo, color, realistic, sketch",
        "steps": 25,
        "cfg_scale": 8.5,
        "denoising_strength": 0.8,
    },
    "night_render": {
        "prompt_prefix": "nighttime architectural visualization, dramatic lighting, ",
        "prompt_suffix": ", warm interior lighting, blue hour, professional render",
        "negative_prompt": "daylight, overexposed, flat lighting, amateur",
        "steps": 35,
        "cfg_scale": 7.0,
        "denoising_strength": 0.55,
    },
    "minimalist": {
        "prompt_prefix": "minimalist architectural rendering, clean aesthetic, ",
        "prompt_suffix": ", white background, simple composition, modern design",
        "negative_prompt": "cluttered, busy, ornate, complex",
        "steps": 25,
        "cfg_scale": 7.5,
        "denoising_strength": 0.6,
    },
}


class DiffusionService:
    """Main service class for AI rendering integration."""

    def __init__(
        self,
        backend: str = "automatic1111",
        url: str = "http://localhost:7860",
        output_dir: str = None,
    ):
        self.backend = Backend(backend.lower())
        self.base_url = url.rstrip("/")
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "renders"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.jobs: Dict[str, RenderJob] = {}
        self.job_queue: Queue = Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        logger.info(f"DiffusionService initialized: backend={backend}, url={url}")

    def start(self):
        """Start the background worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("DiffusionService worker started")

    def stop(self):
        """Stop the background worker thread."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("DiffusionService worker stopped")

    def submit_render(
        self,
        image_path: str,
        prompt: str,
        style_preset: str = "photorealistic",
        negative_prompt: str = None,
        **kwargs
    ) -> str:
        """
        Submit a render job to the queue.

        Args:
            image_path: Path to the input image (viewport capture)
            prompt: Description of the desired rendering
            style_preset: One of the predefined style presets
            negative_prompt: Things to avoid in the render
            **kwargs: Additional parameters (steps, cfg_scale, etc.)

        Returns:
            job_id: Unique identifier for tracking the job
        """
        job_id = str(uuid.uuid4())[:8]

        # Get style preset settings
        preset = STYLE_PRESETS.get(style_preset, STYLE_PRESETS["photorealistic"])

        # Build full prompt
        full_prompt = f"{preset['prompt_prefix']}{prompt}{preset['prompt_suffix']}"
        full_negative = negative_prompt or preset["negative_prompt"]

        # Merge parameters
        parameters = {
            "steps": kwargs.get("steps", preset["steps"]),
            "cfg_scale": kwargs.get("cfg_scale", preset["cfg_scale"]),
            "denoising_strength": kwargs.get("denoising_strength", preset["denoising_strength"]),
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 768),
            "sampler_name": kwargs.get("sampler", "DPM++ 2M Karras"),
        }

        job = RenderJob(
            job_id=job_id,
            status=RenderStatus.QUEUED,
            input_image=image_path,
            prompt=full_prompt,
            negative_prompt=full_negative,
            style_preset=style_preset,
            backend=self.backend,
            created_at=time.time(),
            parameters=parameters,
        )

        self.jobs[job_id] = job
        self.job_queue.put(job_id)

        logger.info(f"Job {job_id} queued: style={style_preset}")
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a render job."""
        if job_id not in self.jobs:
            return {"success": False, "error": f"Job {job_id} not found"}

        job = self.jobs[job_id]
        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error": job.error,
        }

    def get_result(self, job_id: str) -> Dict[str, Any]:
        """Get the result of a completed render job."""
        if job_id not in self.jobs:
            return {"success": False, "error": f"Job {job_id} not found"}

        job = self.jobs[job_id]
        if job.status != RenderStatus.COMPLETED:
            return {
                "success": False,
                "error": f"Job not completed. Status: {job.status.value}",
                "status": job.status.value,
            }

        return {
            "success": True,
            "job_id": job.job_id,
            "result_image": job.result_image,
            "input_image": job.input_image,
            "prompt": job.prompt,
            "style_preset": job.style_preset,
            "processing_time": job.completed_at - job.started_at if job.started_at else 0,
        }

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a queued or processing job."""
        if job_id not in self.jobs:
            return {"success": False, "error": f"Job {job_id} not found"}

        job = self.jobs[job_id]
        if job.status in [RenderStatus.COMPLETED, RenderStatus.FAILED]:
            return {"success": False, "error": "Job already finished"}

        job.status = RenderStatus.CANCELLED
        return {"success": True, "message": f"Job {job_id} cancelled"}

    def list_jobs(self, status: str = None) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        jobs = []
        for job in self.jobs.values():
            if status and job.status.value != status:
                continue
            jobs.append({
                "job_id": job.job_id,
                "status": job.status.value,
                "style_preset": job.style_preset,
                "created_at": job.created_at,
                "progress": job.progress,
            })
        return sorted(jobs, key=lambda x: x["created_at"], reverse=True)

    def list_presets(self) -> Dict[str, Any]:
        """List available style presets."""
        return {
            name: {
                "description": preset["prompt_prefix"].strip(", "),
                "steps": preset["steps"],
                "denoising_strength": preset["denoising_strength"],
            }
            for name, preset in STYLE_PRESETS.items()
        }

    def _process_queue(self):
        """Background worker that processes the job queue."""
        while self._running:
            try:
                # Non-blocking get with timeout
                try:
                    job_id = self.job_queue.get(timeout=1)
                except:
                    continue

                if job_id not in self.jobs:
                    continue

                job = self.jobs[job_id]
                if job.status == RenderStatus.CANCELLED:
                    continue

                job.status = RenderStatus.PROCESSING
                job.started_at = time.time()
                logger.info(f"Processing job {job_id}")

                try:
                    if self.backend == Backend.AUTOMATIC1111:
                        result = self._render_automatic1111(job)
                    else:
                        result = self._render_comfyui(job)

                    job.result_image = result
                    job.status = RenderStatus.COMPLETED
                    job.completed_at = time.time()
                    job.progress = 100.0
                    logger.info(f"Job {job_id} completed: {result}")

                except Exception as e:
                    job.status = RenderStatus.FAILED
                    job.error = str(e)
                    job.completed_at = time.time()
                    logger.error(f"Job {job_id} failed: {e}")

            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    def _render_automatic1111(self, job: RenderJob) -> str:
        """Render using Automatic1111 WebUI API."""
        # Load and encode input image
        with open(job.input_image, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # Prepare img2img payload
        payload = {
            "init_images": [image_data],
            "prompt": job.prompt,
            "negative_prompt": job.negative_prompt,
            "steps": job.parameters["steps"],
            "cfg_scale": job.parameters["cfg_scale"],
            "denoising_strength": job.parameters["denoising_strength"],
            "width": job.parameters["width"],
            "height": job.parameters["height"],
            "sampler_name": job.parameters["sampler_name"],
        }

        # Call API
        response = requests.post(
            f"{self.base_url}/sdapi/v1/img2img",
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()

        if "images" not in result or not result["images"]:
            raise Exception("No images returned from API")

        # Save result image
        output_path = self.output_dir / f"{job.job_id}_render.png"
        image_bytes = base64.b64decode(result["images"][0])
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return str(output_path)

    def _render_comfyui(self, job: RenderJob) -> str:
        """Render using ComfyUI API."""
        # Load input image
        with open(job.input_image, "rb") as f:
            image_data = f.read()

        # Upload image to ComfyUI
        files = {"image": (Path(job.input_image).name, image_data, "image/png")}
        upload_response = requests.post(
            f"{self.base_url}/upload/image",
            files=files,
            timeout=30,
        )
        upload_response.raise_for_status()
        uploaded_name = upload_response.json()["name"]

        # Build workflow (simplified img2img workflow)
        workflow = self._build_comfyui_workflow(uploaded_name, job)

        # Queue prompt
        prompt_response = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": workflow},
            timeout=30,
        )
        prompt_response.raise_for_status()
        prompt_id = prompt_response.json()["prompt_id"]

        # Poll for completion
        output_images = self._poll_comfyui(prompt_id, job)

        if not output_images:
            raise Exception("No output images from ComfyUI")

        # Download first output image
        output_path = self.output_dir / f"{job.job_id}_render.png"
        image_response = requests.get(
            f"{self.base_url}/view",
            params={"filename": output_images[0]},
            timeout=30,
        )
        with open(output_path, "wb") as f:
            f.write(image_response.content)

        return str(output_path)

    def _build_comfyui_workflow(self, input_image: str, job: RenderJob) -> Dict:
        """Build a ComfyUI workflow for img2img rendering."""
        return {
            "1": {
                "class_type": "LoadImage",
                "inputs": {"image": input_image},
            },
            "2": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"},
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": job.prompt,
                    "clip": ["2", 1],
                },
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": job.negative_prompt,
                    "clip": ["2", 1],
                },
            },
            "5": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["1", 0],
                    "vae": ["2", 2],
                },
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int(time.time()),
                    "steps": job.parameters["steps"],
                    "cfg": job.parameters["cfg_scale"],
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": job.parameters["denoising_strength"],
                    "model": ["2", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0],
                },
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["2", 2],
                },
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": job.job_id,
                    "images": ["7", 0],
                },
            },
        }

    def _poll_comfyui(self, prompt_id: str, job: RenderJob, timeout: int = 300) -> List[str]:
        """Poll ComfyUI for job completion."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if job.status == RenderStatus.CANCELLED:
                return []

            history_response = requests.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10,
            )
            history = history_response.json()

            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        return [img["filename"] for img in node_output["images"]]

            # Update progress (estimated)
            elapsed = time.time() - start_time
            job.progress = min(95, (elapsed / 60) * 100)
            time.sleep(1)

        raise Exception("ComfyUI render timeout")


# Simple HTTP API wrapper for MCP integration
class DiffusionServiceAPI:
    """HTTP API wrapper for use with MCP server."""

    def __init__(self, service: DiffusionService):
        self.service = service

    def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an API request from MCP."""
        try:
            if method == "render.submit":
                job_id = self.service.submit_render(
                    image_path=params["imagePath"],
                    prompt=params.get("prompt", "architectural visualization"),
                    style_preset=params.get("stylePreset", "photorealistic"),
                    negative_prompt=params.get("negativePrompt"),
                    **params.get("parameters", {}),
                )
                return {"success": True, "jobId": job_id}

            elif method == "render.status":
                return self.service.get_status(params["jobId"])

            elif method == "render.result":
                return self.service.get_result(params["jobId"])

            elif method == "render.cancel":
                return self.service.cancel_job(params["jobId"])

            elif method == "render.list":
                jobs = self.service.list_jobs(params.get("status"))
                return {"success": True, "jobs": jobs}

            elif method == "render.presets":
                presets = self.service.list_presets()
                return {"success": True, "presets": presets}

            else:
                return {"success": False, "error": f"Unknown method: {method}"}

        except Exception as e:
            logger.error(f"API error: {e}")
            return {"success": False, "error": str(e)}


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Rendering Service for RevitMCPBridge")
    parser.add_argument("--backend", default="automatic1111", choices=["automatic1111", "comfyui"])
    parser.add_argument("--url", default="http://localhost:7860", help="Backend API URL")
    parser.add_argument("--output", default="./renders", help="Output directory")
    parser.add_argument("--test", action="store_true", help="Run test render")
    parser.add_argument("--image", help="Input image for test render")
    parser.add_argument("--prompt", default="modern architectural visualization", help="Render prompt")
    parser.add_argument("--style", default="photorealistic", help="Style preset")

    args = parser.parse_args()

    service = DiffusionService(
        backend=args.backend,
        url=args.url,
        output_dir=args.output,
    )
    service.start()

    if args.test:
        if not args.image:
            print("Error: --image required for test render")
            sys.exit(1)

        print(f"Submitting test render: {args.image}")
        job_id = service.submit_render(
            image_path=args.image,
            prompt=args.prompt,
            style_preset=args.style,
        )
        print(f"Job ID: {job_id}")

        # Wait for completion
        while True:
            status = service.get_status(job_id)
            print(f"Status: {status['status']} ({status['progress']:.0f}%)")
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
            time.sleep(2)

        if status["status"] == "completed":
            result = service.get_result(job_id)
            print(f"Result: {result['result_image']}")
        else:
            print(f"Error: {status.get('error')}")

    service.stop()
