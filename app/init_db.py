from app.database import engine, Base
from app import models

def init_db():
    Base.metadata.create_all(bind=engine)
    print("DB 테이블 생성 완료")

if __name__ == "__main__":
    init_db()