@app.post("/api/generate/{content_type}")
async def generate_content(content_type: str, video_id: str = Form(...), target_language: str = Form(...)):
    """Generate content from video transcript"""
    try:
        # Get transcript
        transcript = await get_transcript(video_id)
        
        processor = ContentProcessor()
        
        if content_type == "tweet":
            result = await processor.generate_tweet(transcript, target_language)
            return {"content": result}
            
        elif content_type == "summary": 
            result = await processor.generate_summary(transcript, target_language)
            return {"content": result}
            
        elif content_type == "podcast":
            # Create temp directory if it doesn't exist
            os.makedirs("static/temp", exist_ok=True)
            
            # Generate podcast
            audio_path = await processor.generate_podcast(transcript, target_language)
            
            # Return path relative to static directory
            relative_path = audio_path.replace("static/", "")
            return {"audio_url": relative_path}
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid content type: {content_type}")
            
    except Exception as e:
        logger.error(f"Error generating {content_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 