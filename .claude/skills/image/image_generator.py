#!/usr/bin/env python3
import os
import sys
import re
import glob
import asyncio
import datetime
import shutil
import logging
from PIL import Image

# Setup directories relative to the script location to ensure portability
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
IMAGES_DIR = os.path.join(REPO_ROOT, 'images')

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('image_generator')

def slugify(text):
    # Remove slash commands
    text = re.sub(r'^/[a-zA-Z0-9_-]+\s*', '', text)
    text = text.lower()
    # Replace non-alphanumeric characters with underscores
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = text.strip('_')
    # Limit to the first 4 words or 35 characters
    words = text.split('_')[:4]
    slug = '_'.join(words)[:35]
    return slug if slug else 'bible_image'

async def generate_bible_image(prompt_text):
    # Try to import SDK
    try:
        from google.antigravity import Agent, LocalAgentConfig
        from google.antigravity.hooks import policy
    except ImportError:
        logger.error("google-antigravity SDK is not installed.")
        sys.exit(1)

    image_title = slugify(prompt_text)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    target_filename = f"{timestamp}_{image_title}.png"
    target_path = os.path.join(IMAGES_DIR, target_filename)

    logger.info(f"Refined image title: '{image_title}'")
    logger.info(f"Target destination: '{target_path}'")

    # Construct Agent config
    system_rules = (
        "You are an image generation agent. Your task is to call the 'generate_image' tool "
        "with the user's prompt as the prompt. After the tool call is finished, write a short "
        "response to the user confirming that the image was successfully generated."
    )

    config = LocalAgentConfig(
        system_instructions=system_rules,
        policies=[policy.allow_all()] # Auto-approve tool calls
    )

    conv_id = None
    logger.info("Initializing Agent connection...")
    async with Agent(config) as agent:
        logger.info(f"Submitting image generation request: '{prompt_text}'")
        response = await agent.chat(prompt_text)
        
        # Stream response chunks to make it feel alive
        async for chunk in response:
            pass
            
        conv_id = agent.conversation_id
        logger.info(f"Conversation completed. ID: {conv_id}")

    if not conv_id:
        logger.error("Failed to retrieve conversation ID from agent session.")
        sys.exit(1)

    # Search for the generated image file in standard brain directories
    home = os.path.expanduser('~')
    possible_brain_dirs = [
        os.path.join(home, '.gemini', 'antigravity', 'brain', conv_id),
        os.path.join(home, '.gemini', 'antigravity-ide', 'brain', conv_id),
    ]

    # Add agent save_dir to search options if available
    if agent._strategy and hasattr(agent._strategy, 'save_dir') and agent._strategy.save_dir:
        possible_brain_dirs.append(agent._strategy.save_dir)

    found_files = []
    for sdir in possible_brain_dirs:
        if os.path.exists(sdir):
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                found_files.extend(glob.glob(os.path.join(sdir, ext)))

    if not found_files:
        logger.error(f"Could not find any generated image files in conversation search paths: {possible_brain_dirs}")
        sys.exit(1)

    # Sort to find the latest generated image
    found_files.sort(key=os.path.getmtime, reverse=True)
    src_image = found_files[0]
    logger.info(f"Discovered raw generated image: '{src_image}'")

    # Make sure target directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Move / Convert to PNG
    try:
        if src_image.lower().endswith('.png'):
            shutil.copy2(src_image, target_path)
            logger.info("Image was already PNG. Copied directly.")
        else:
            logger.info("Converting image to PNG format...")
            with Image.open(src_image) as img:
                img.save(target_path, "PNG")
            logger.info("Successfully converted and saved image.")
            
        # Print expected response format for user verification
        print(f"\nSUCCESS: Generated image saved at images/{target_filename}")
        
    except Exception as e:
        logger.error(f"Error copying/converting image: {e}")
        sys.exit(1)

def main():
    args = [a for a in sys.argv[1:] if a.strip() and not (a.startswith('$') or a == '""')]
    if not args:
        logger.error("No prompt was provided for image generation.")
        print("Usage: python3 image_generator.py <prompt>")
        sys.exit(1)

    prompt = " ".join(args)
    asyncio.run(generate_bible_image(prompt))

if __name__ == "__main__":
    main()
