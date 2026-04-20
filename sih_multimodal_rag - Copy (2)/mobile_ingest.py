import os
import io
import socket
from datetime import datetime
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import uvicorn

app = FastAPI(title="Mobile Ingestion Server")

# Allows the frontend to communicate with this backend over the network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STRICT DESTINATION FOLDER ---
UPLOAD_DIR = r"C:\Users\dheer\Desktop\rag"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    print(f"\n[INCOMING] Receiving payload: {file.filename}")
    
    if not file.filename:
        return {"info": "No file"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Handle Images -> Convert to PDF
    if file.content_type.startswith("image/"):
        try:
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

            pdf_name = f"{timestamp}_mobile_scan.pdf"
            save_path = os.path.join(UPLOAD_DIR, pdf_name)

            image.save(save_path, "PDF", resolution=100.0)
            print(f"[SUCCESS] Converted and saved to: {save_path}")
            return {"info": "Converted", "filename": pdf_name}

        except Exception as e:
            print(f"[ERROR] {e}")
            return {"error": str(e)}

    # 2. Handle PDFs/Docs -> Save directly
    else:
        save_name = f"{timestamp}_{file.filename}"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        with open(save_path, "wb+") as f:
            f.write(await file.read())

        print(f"[SUCCESS] Saved document to: {save_path}")
        return {"info": "Saved", "filename": save_name}

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    ip_address = get_ip()
    print("\n" + "="*50)
    print("📡 DEDICATED INGESTION SERVER ONLINE")
    print(f"-> Saving files to: {UPLOAD_DIR}")
    print(f"-> Listening on: http://{ip_address}:5000")
    print("="*50 + "\n")

    # Binds to all network interfaces on port 5000
    uvicorn.run(app, host="0.0.0.0", port=5000)