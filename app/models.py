from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Repository: 봇이 감시 중인 저장소, 웹훅 시크릿/리뷰 설정
class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    webhook_secret = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="repository")

# Review: PR 1건당 리뷰 1건
# PR 번호 + 커밋 SHA 기준으로 중복 방지
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    pr_number = Column(Integer, nullable=False)
    title = Column(String)
    status = Column(String, default="pending")
    score = Column(Float)
    summary = Column(Text)
    commit_sha = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="reviews")
    comments = relationship("ReviewComment", back_populates="review")

# ReviewComment: 라인별 코멘트
# 파일 + 라인 위치 저장
class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    file_path = Column(String)
    line_number = Column(Integer)
    category = Column(String)
    body = Column(Text)
    severity = Column(String)

    review = relationship("Review", back_populates="comments")