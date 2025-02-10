from fastapi import FastAPI, Request, UploadFile, Form, Body, HTTPException, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
import uvicorn
import os
from dotenv import load_dotenv
from termcolor import colored
import webbrowser
from pathlib import Path
import asyncio
from youtube import PlaylistProcessor, TranscriptionProcessor
from llm.processor import ContentProcessor
from document.generator import DocumentGenerator
from document.processor import DocumentProcessor
from typing import List, Dict
import tempfile
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="YouTube Content Processor")

# Create static and templates directories if they don't exist
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("static/thumbnails").mkdir(exist_ok=True)
Path("static/uploads").mkdir(exist_ok=True)
Path("static/temp").mkdir(exist_ok=True)
Path("static/podcasts").mkdir(exist_ok=True)
Path("static/images").mkdir(exist_ok=True)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize processors
playlist_processor = PlaylistProcessor()
transcription_processor = TranscriptionProcessor()
content_processor = ContentProcessor()
document_generator = DocumentGenerator()
document_processor = DocumentProcessor()

# Default playlist URL
DEFAULT_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLBzmUd_ESwos3u2FDXZ1JPMnX44fACTMt"

@app.get("/")
async def home(request: Request):
    """Render the landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/tool")
async def tool(request: Request):
    """Render the YouTube processing tool page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/documents")
async def documents(request: Request):
    """Render the document processing page"""
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/podcast")
async def podcast(request: Request):
    """Render the podcast generation page"""
    return templates.TemplateResponse("podcast.html", {"request": request})

@app.get("/default-playlist")
async def get_default_playlist():
    """Process the default YouTube playlist"""
    try:
        videos_info = await playlist_processor.process_playlist(DEFAULT_PLAYLIST_URL)
        return JSONResponse(content={"status": "success", "videos": videos_info})
    except Exception as e:
        print(colored(f"Error processing default playlist: {str(e)}", "red"))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/process-playlist")
async def process_playlist(playlist_url: str = Form(...)):
    """Process YouTube playlist and return video information"""
    try:
        videos_info = await playlist_processor.process_playlist(playlist_url)
        return JSONResponse(content={"status": "success", "videos": videos_info})
    except Exception as e:
        print(colored(f"Error processing playlist: {str(e)}", "red"))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/generate-version")
async def generate_version(
    video_ids: List[str] = Body(...),
    target_language: str = Body(...),
    output_type: str = Body(...)
):
    """Generate version or tweet in specified language"""
    temp_file = None
    try:
        print(colored(f"Starting generation for {output_type} in {target_language}", "cyan"))
        
        # Get transcripts
        transcriptions = await transcription_processor.process_videos(video_ids)
        
        # Process each video
        results = []
        for video_id, transcript in transcriptions.items():
            if transcript.startswith("Error:"):
                print(colored(f"Skipping video {video_id} due to transcript error", "yellow"))
                continue
                
            # Clean and format transcript
            clean_transcript = await content_processor.clean_transcript(transcript)
            print(colored("Transcript cleaned successfully", "green"))
            
            if output_type == "version":
                # Translate transcript
                translated = await content_processor.translate_content(
                    clean_transcript,
                    target_language
                )
                results.append(translated)
                print(colored("Translation completed", "green"))
            elif output_type == "summary":
                # Generate and translate summary
                summary = await content_processor.generate_summary(
                    clean_transcript,
                    target_language
                )
                results.append(summary)
                print(colored("Summary generated", "green"))
            else:  # tweet
                # Generate and translate tweet
                tweet = await content_processor.generate_tweet(
                    clean_transcript,
                    target_language
                )
                results.append(tweet)
                print(colored("Tweet generated", "green"))
        
        if not results:
            raise Exception("No content was generated from the videos")
        
        # Generate document
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        await DocumentGenerator.create_document(
            results,
            temp_file.name,
            output_type,
            target_language
        )
        print(colored(f"Document created at {temp_file.name}", "green"))
        
        # Close the temp file before sending
        temp_file.close()
        
        response = FileResponse(
            temp_file.name,
            filename=f"{output_type}_{target_language.lower()}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Schedule file deletion after sending
        async def delete_file():
            await asyncio.sleep(5)  # Wait for file to be sent
            try:
                os.unlink(temp_file.name)
                print(colored(f"Temporary file {temp_file.name} deleted", "green"))
            except Exception as e:
                print(colored(f"Error deleting temporary file: {str(e)}", "red"))
        
        asyncio.create_task(delete_file())
        return response
            
    except Exception as e:
        print(colored(f"Error generating {output_type}: {str(e)}", "red"))
        # Clean up temp file if it exists
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/upload-document")
async def upload_document(file: UploadFile):
    """Handle document upload"""
    try:
        file_path = f"static/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return JSONResponse(content={"status": "success", "path": file_path})
    except Exception as e:
        print(colored(f"Error uploading document: {str(e)}", "red"))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/process-document")
async def process_document(
    file: UploadFile,
    target_language: str = Form(...)
):
    """Process and translate PDF document"""
    try:
        print(colored(f"Processing document: {file.filename}", "cyan"))
        
        # Save uploaded file
        file_path = f"static/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Process the document
        output_path = await document_processor.process_pdf(file_path, target_language)
        
        # Return the processed file
        return FileResponse(
            output_path,
            filename=f"translated_{file.filename}",
            media_type="application/pdf"
        )
        
    except Exception as e:
        print(colored(f"Error processing document: {str(e)}", "red"))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/generate/podcast")
async def generate_podcast_endpoint(
    file: UploadFile = File(...),
    target_language: str = Form(...)
):
    """Generate podcast from uploaded document"""
    file_path = None
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.txt', '.doc', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .txt, .doc, and .docx files are supported."
            )
        
        logger.info(f"Generating podcast from file: {file.filename} in {target_language}")
        
        # Create directories if they don't exist
        os.makedirs("static/uploads", exist_ok=True)
        os.makedirs("static/podcasts", exist_ok=True)
        
        # Save uploaded file with unique name to prevent conflicts
        timestamp = int(time.time())
        file_path = f"static/uploads/{timestamp}_{file.filename}"
        content = await file.read()
        
        if not content:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
            
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        # Process the document
        processor = ContentProcessor()
        
        # Generate podcast directly from file path
        audio_path = await processor.generate_podcast(file_path, target_language)
        logger.info(f"Generated podcast at {audio_path}")
        
        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio file"
            )
        
        # Return path relative to static directory
        relative_path = audio_path.replace("static/", "")
        return {"audio_url": relative_path}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {str(e)}")

def open_browser():
    """Open browser to application URL"""
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Open browser after a short delay
    asyncio.get_event_loop().run_in_executor(None, lambda: asyncio.get_event_loop().call_later(1.5, open_browser))
    # Run the FastAPI application
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True) 