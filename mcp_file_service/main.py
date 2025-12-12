from fastapi import FastAPI, HTTPException
from typing import List
app = FastAPI()

@app.get("/status")
def read_status():
    return {"status": "ok"} 

@app.get("/list-files", response_model=List[str])
def list_files(folder_name: str):
    # list files in the specified folder
    try:
        import os
        files = os.listdir(folder_name)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/create-file/{folder_name}/{file_name}")
def create_file(folder_name: str, file_name: str, content: str):
    # create a file with the specified content
    try:
        import os
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        with open(os.path.join(folder_name, file_name), 'w') as f:
            f.write(content)
        return {"message": "File created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/delete-file/{folder_name}/{file_name}")
def delete_file(folder_name: str, file_name: str):
    # delete the specified file
    try:
        import os
        os.remove(os.path.join(folder_name, file_name))
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6001, log_level="info", reload=True)