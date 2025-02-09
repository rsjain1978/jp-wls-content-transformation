import requests
import os

def download_image(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(f"static/images/{filename}", "wb") as f:
            f.write(response.content)
        print(f"Successfully downloaded {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")

# Create directory if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# Image URLs
images = {
    "youtube.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/2560px-YouTube_full-color_icon_%282017%29.svg.png",
    "substack.png": "https://substackcdn.com/image/fetch/w_256,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack.com%2Fimg%2Fsubstack.png",
    "background.jpg": "https://img.freepik.com/free-vector/white-abstract-background_23-2148806276.jpg"
}

# Download each image
for filename, url in images.items():
    download_image(url, filename) 