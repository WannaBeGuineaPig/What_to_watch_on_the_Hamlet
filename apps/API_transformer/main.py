import uvicorn
from fastapi import FastAPI
from moduls.classification_comment import *

app = FastAPI()
classification_message = ClassificationMessage()

@app.get('/predict-type-message')
def get_predict_type_message(message: str):
    predict = classification_message.get_predict(message)
    return predict

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)