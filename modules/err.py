from fastapi.responses import JSONResponse

def err_message(errcode, message):
    return JSONResponse(status_code=errcode,content={"status":"error", "message":"An error occurred", "data":{}, "exception":message})