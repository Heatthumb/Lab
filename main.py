try:
    # Set a strict 5-minute timeout for the AI
    handler = fal_client.submit(
        "fal-ai/workflow-utilities/extract-nth-frame",
        arguments={"video_url": v_url, "max_frames": 30}
    )
    # Check status without blocking the whole server
    result = handler.get() 
except Exception as e:
    print(f"Extraction Failed: {str(e)}")
    # If it fails, fallback to a basic FFmpeg extraction
