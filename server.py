from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os

app = FastAPI()

# CORS 설정 (Live Server와 연동 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEQUENCE_DIAGRAM_DIR = os.path.join(os.path.dirname(__file__), "build", "sequence_diagram")

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")
VIEWER_HTML_PATH = os.path.join(os.path.dirname(__file__), "viewer.html")

@app.get("/api/sequence-diagrams")
def get_sequence_diagrams():
    try:
        files = [f for f in os.listdir(SEQUENCE_DIAGRAM_DIR) if os.path.isfile(os.path.join(SEQUENCE_DIAGRAM_DIR, f))]
        return JSONResponse(content={"files": files})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 루트에서 index.html 반환
@app.get("/")
def serve_index():
    return FileResponse(INDEX_HTML_PATH, media_type="text/html")

# /viewer.html에서 viewer.html 반환
@app.get("/viewer.html")
def serve_viewer():
    return FileResponse(VIEWER_HTML_PATH, media_type="text/html")

# /build/sequence_diagram/{filename}에서 JSON 파일 반환
from fastapi import Path

@app.get("/build/sequence_diagram/{file_path:path}")
def serve_sequence_json(file_path: str = Path(...)):
    abs_path = os.path.join(SEQUENCE_DIAGRAM_DIR, file_path)
    print(f"Requested file path: {file_path}, Absolute path: {abs_path}")
    print(f"File exists: {os.path.isfile(abs_path)}")
    if not os.path.isfile(abs_path):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(abs_path, media_type="application/json")
