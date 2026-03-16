# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.stocks import router as stocks_router
# from routes.news import router as news_router
# from routes.users import router as users_router
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(stocks_router)
# app.include_router(news_router)
# app.include_router(users_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)