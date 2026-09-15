import json
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import ForeignKey, LargeBinary, String, Text, create_engine, func, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./teaching_app.db",
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


class ClassModel(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subjects: Mapped[List["SubjectModel"]] = relationship(back_populates="class_", cascade="all, delete-orphan")


class SubjectModel(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    class_: Mapped[ClassModel] = relationship(back_populates="subjects")
    chapters: Mapped[List["ChapterModel"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class ChapterModel(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    subject: Mapped[SubjectModel] = relationship(back_populates="chapters")
    notes: Mapped[List["NoteModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    videos: Mapped[List["VideoModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    worksheets: Mapped[List["WorksheetModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    homework_assignments: Mapped[List["HomeworkAssignmentModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    practice_sets: Mapped[List["PracticeSetModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    question_papers: Mapped[List["QuestionPaperModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
    books: Mapped[List["BookModel"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")


class NoteModel(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(String(500), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="notes")


class NoteContentModel(Base):
    __tablename__ = "note_contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), unique=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)


class VideoModel(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(String(1000), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="videos")


class WorksheetModel(Base):
    __tablename__ = "worksheets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="worksheets")


class HomeworkAssignmentModel(Base):
    __tablename__ = "homework_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="homework_assignments")


class PracticeSetModel(Base):
    __tablename__ = "practice_sets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    questions_json: Mapped[str] = mapped_column(Text, nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="practice_sets")


class QuestionPaperModel(Base):
    __tablename__ = "question_papers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="question_papers")


class BookModel(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(250), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    chapter: Mapped[ChapterModel] = relationship(back_populates="books")


engine_options = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
a_engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=a_engine, autoflush=False, autocommit=False)


app = FastAPI(title="Teaching App API", version="1.0.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=a_engine)
    with a_engine.begin() as connection:
        for table_name in ("question_papers", "books"):
            columns = {column["name"] for column in inspect(a_engine).get_columns(table_name)}
            if "file_data" not in columns:
                column_type = a_engine.dialect.type_compiler.process(LargeBinary())
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN file_data {column_type}"))


from pydantic import BaseModel, ConfigDict


class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    name: str
    class_id: int

    model_config = ConfigDict(from_attributes=True)


class ChapterCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject_id: int

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    title: str
    description: Optional[str] = None
    link: str
    chapter_id: int

    model_config = ConfigDict(from_attributes=True)


class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    link: str
    chapter_id: int

    model_config = ConfigDict(from_attributes=True)


class PracticeQuestion(BaseModel):
    question: str
    answer: Optional[str] = None
    options: Optional[List[str]] = None


class PracticeSetCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[PracticeQuestion]
    chapter_id: int

    model_config = ConfigDict(from_attributes=True)


class QuestionPaperCreate(BaseModel):
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    mime_type: str
    chapter_id: int

    model_config = ConfigDict(from_attributes=True)


class ClassUpdate(BaseModel):
    name: str
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: str
    class_id: int


class ChapterUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    subject_id: int


class NoteUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    link: str
    chapter_id: int


class VideoUpdate(VideoCreate):
    pass


class PracticeSetUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[PracticeQuestion]
    chapter_id: int


class ClassOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class SubjectOut(BaseModel):
    id: int
    name: str
    class_id: int


class ChapterOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    subject_id: int


class NoteOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    link: str
    chapter_id: int


class VideoOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    link: str
    chapter_id: int


class WorksheetOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    mime_type: str
    chapter_id: int


class HomeworkAssignmentOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    mime_type: str
    chapter_id: int


class PracticeSetOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    chapter_id: int
    questions: List[PracticeQuestion]


class QuestionPaperOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    mime_type: str
    chapter_id: int


class BookOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    mime_type: str
    chapter_id: int


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/classes", response_model=List[ClassOut])
def list_classes(db: Session = Depends(get_db)):
    return db.query(ClassModel).all()


@app.post("/api/classes", response_model=ClassOut)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):
    item = ClassModel(name=payload.name, description=payload.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/classes/{class_id}", response_model=ClassOut)
def update_class(class_id: int, payload: ClassUpdate, db: Session = Depends(get_db)):
    item = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Class not found")
    item.name = payload.name
    item.description = payload.description
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    item = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/classes/{class_id}/subjects", response_model=List[SubjectOut])
def list_subjects(class_id: int, db: Session = Depends(get_db)):
    items = db.query(SubjectModel).filter(SubjectModel.class_id == class_id).all()
    return items


@app.post("/api/subjects", response_model=SubjectOut)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)):
    class_exists = db.query(ClassModel).filter(ClassModel.id == payload.class_id).first()
    if not class_exists:
        raise HTTPException(status_code=404, detail="Class not found")
    item = SubjectModel(name=payload.name, class_id=payload.class_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db)):
    item = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Subject not found")
    if not db.query(ClassModel).filter(ClassModel.id == payload.class_id).first():
        raise HTTPException(status_code=404, detail="Class not found")
    item.name = payload.name
    item.class_id = payload.class_id
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    item = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/subjects/{subject_id}/chapters", response_model=List[ChapterOut])
def list_chapters(subject_id: int, db: Session = Depends(get_db)):
    return db.query(ChapterModel).filter(ChapterModel.subject_id == subject_id).all()


@app.post("/api/chapters", response_model=ChapterOut)
def create_chapter(payload: ChapterCreate, db: Session = Depends(get_db)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    item = ChapterModel(title=payload.title, description=payload.description, subject_id=payload.subject_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)):
    item = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if not db.query(SubjectModel).filter(SubjectModel.id == payload.subject_id).first():
        raise HTTPException(status_code=404, detail="Subject not found")
    item.title = payload.title
    item.description = payload.description
    item.subject_id = payload.subject_id
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    item = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Chapter not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/notes", response_model=List[NoteOut])
def list_notes(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(NoteModel).filter(NoteModel.chapter_id == chapter_id).all()


@app.post("/api/notes", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    item = NoteModel(title=payload.title, description=payload.description, link=payload.link, chapter_id=payload.chapter_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/notes/upload", response_model=NoteOut)
async def upload_note(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    original_name = Path(file.filename or "uploaded-note").name
    file_data = await file.read()

    item = NoteModel(title=title, description=description, link="", chapter_id=chapter_id)
    db.add(item)
    db.flush()
    item.link = f"/api/notes/{item.id}/download"
    db.add(NoteContentModel(
        note_id=item.id,
        file_name=original_name,
        file_data=file_data,
        mime_type=file.content_type or "application/octet-stream",
    ))
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/notes/{note_id}/download")
def download_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    note_content = db.query(NoteContentModel).filter(NoteContentModel.note_id == note_id).first()
    if not note or not note_content:
        raise HTTPException(status_code=404, detail="Uploaded note not found")
    return Response(
        content=note_content.file_data,
        media_type=note_content.mime_type,
        headers={"Content-Disposition": f'inline; filename="{note_content.file_name}"'},
    )


@app.put("/api/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    item = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Note not found")
    if not db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first():
        raise HTTPException(status_code=404, detail="Chapter not found")
    item.title = payload.title
    item.description = payload.description
    item.link = payload.link
    item.chapter_id = payload.chapter_id
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    item = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/videos", response_model=List[VideoOut])
def list_videos(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(VideoModel).filter(VideoModel.chapter_id == chapter_id).all()


@app.post("/api/videos", response_model=VideoOut)
def create_video(payload: VideoCreate, db: Session = Depends(get_db)):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    item = VideoModel(title=payload.title, description=payload.description, link=payload.link, chapter_id=payload.chapter_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/videos/{video_id}", response_model=VideoOut)
def update_video(video_id: int, payload: VideoUpdate, db: Session = Depends(get_db)):
    item = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Video not found")
    if not db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first():
        raise HTTPException(status_code=404, detail="Chapter not found")
    item.title = payload.title
    item.description = payload.description
    item.link = payload.link
    item.chapter_id = payload.chapter_id
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    item = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/worksheets", response_model=List[WorksheetOut])
def list_worksheets(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(WorksheetModel).filter(WorksheetModel.chapter_id == chapter_id).all()


@app.post("/api/worksheets", response_model=WorksheetOut)
async def upload_worksheet(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    safe_name = f"{uuid.uuid4()}_{file.filename}"
    destination = UPLOAD_DIR / safe_name
    content = await file.read()
    destination.write_bytes(content)

    item = WorksheetModel(
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(destination),
        mime_type=file.content_type or "application/octet-stream",
        chapter_id=chapter_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/worksheets/{worksheet_id}/download")
def download_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    item = db.query(WorksheetModel).filter(WorksheetModel.id == worksheet_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    if not Path(item.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=item.file_path, media_type=item.mime_type, headers={"Content-Disposition": "inline"})


@app.delete("/api/worksheets/{worksheet_id}")
def delete_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    item = db.query(WorksheetModel).filter(WorksheetModel.id == worksheet_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    file_path = Path(item.file_path)
    db.delete(item)
    db.commit()
    if file_path.exists():
        file_path.unlink()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/homework-assignments", response_model=List[HomeworkAssignmentOut])
def list_homework_assignments(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(HomeworkAssignmentModel).filter(HomeworkAssignmentModel.chapter_id == chapter_id).all()


@app.post("/api/homework-assignments", response_model=HomeworkAssignmentOut)
async def upload_homework_assignment(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    safe_name = f"{uuid.uuid4()}_{file.filename}"
    destination = UPLOAD_DIR / safe_name
    content = await file.read()
    destination.write_bytes(content)

    item = HomeworkAssignmentModel(
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(destination),
        mime_type=file.content_type or "application/octet-stream",
        chapter_id=chapter_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/homework-assignments/{assignment_id}/download")
def download_homework_assignment(assignment_id: int, db: Session = Depends(get_db)):
    item = db.query(HomeworkAssignmentModel).filter(HomeworkAssignmentModel.id == assignment_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Homework assignment not found")
    if not Path(item.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=item.file_path, media_type=item.mime_type, headers={"Content-Disposition": "inline"})


@app.delete("/api/homework-assignments/{assignment_id}")
def delete_homework_assignment(assignment_id: int, db: Session = Depends(get_db)):
    item = db.query(HomeworkAssignmentModel).filter(HomeworkAssignmentModel.id == assignment_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Homework assignment not found")
    file_path = Path(item.file_path)
    db.delete(item)
    db.commit()
    if file_path.exists():
        file_path.unlink()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/practice-sets", response_model=List[PracticeSetOut])
def list_practice_sets(chapter_id: int, db: Session = Depends(get_db)):
    practice_sets = db.query(PracticeSetModel).filter(PracticeSetModel.chapter_id == chapter_id).all()
    serialized = []
    for item in practice_sets:
        serialized.append(
            PracticeSetOut(
                id=item.id,
                title=item.title,
                description=item.description,
                chapter_id=item.chapter_id,
                questions=[PracticeQuestion.model_validate(question) for question in json.loads(item.questions_json)],
            )
        )
    return serialized


@app.post("/api/practice-sets", response_model=PracticeSetOut)
def create_practice_set(payload: PracticeSetCreate, db: Session = Depends(get_db)):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    item = PracticeSetModel(
        title=payload.title,
        description=payload.description,
        chapter_id=payload.chapter_id,
        questions_json=json.dumps([question.model_dump(mode="json") for question in payload.questions]),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return PracticeSetOut(
        id=item.id,
        title=item.title,
        description=item.description,
        chapter_id=item.chapter_id,
        questions=[PracticeQuestion.model_validate(question) for question in json.loads(item.questions_json)],
    )


@app.put("/api/practice-sets/{practice_set_id}", response_model=PracticeSetOut)
def update_practice_set(practice_set_id: int, payload: PracticeSetUpdate, db: Session = Depends(get_db)):
    item = db.query(PracticeSetModel).filter(PracticeSetModel.id == practice_set_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Practice set not found")
    if not db.query(ChapterModel).filter(ChapterModel.id == payload.chapter_id).first():
        raise HTTPException(status_code=404, detail="Chapter not found")
    item.title = payload.title
    item.description = payload.description
    item.chapter_id = payload.chapter_id
    item.questions_json = json.dumps([question.model_dump(mode="json") for question in payload.questions])
    db.commit()
    db.refresh(item)
    return PracticeSetOut(
        id=item.id,
        title=item.title,
        description=item.description,
        chapter_id=item.chapter_id,
        questions=[PracticeQuestion.model_validate(question) for question in json.loads(item.questions_json)],
    )


@app.delete("/api/practice-sets/{practice_set_id}")
def delete_practice_set(practice_set_id: int, db: Session = Depends(get_db)):
    item = db.query(PracticeSetModel).filter(PracticeSetModel.id == practice_set_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Practice set not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/question-papers", response_model=List[QuestionPaperOut])
def list_question_papers(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(QuestionPaperModel).filter(QuestionPaperModel.chapter_id == chapter_id).all()


@app.post("/api/question-papers", response_model=QuestionPaperOut)
async def upload_question_paper(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    safe_name = f"{uuid.uuid4()}_{file.filename}"
    destination = UPLOAD_DIR / safe_name
    content = await file.read()
    destination.write_bytes(content)

    item = QuestionPaperModel(
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(destination),
        file_data=content,
        mime_type=file.content_type or "application/octet-stream",
        chapter_id=chapter_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/question-papers/{question_paper_id}/download")
def download_question_paper(question_paper_id: int, db: Session = Depends(get_db)):
    item = db.query(QuestionPaperModel).filter(QuestionPaperModel.id == question_paper_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question paper not found")
    if item.file_data is not None:
        return Response(content=item.file_data, media_type=item.mime_type, headers={"Content-Disposition": "inline"})
    if not Path(item.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=item.file_path, media_type=item.mime_type, headers={"Content-Disposition": "inline"})


@app.delete("/api/question-papers/{question_paper_id}")
def delete_question_paper(question_paper_id: int, db: Session = Depends(get_db)):
    item = db.query(QuestionPaperModel).filter(QuestionPaperModel.id == question_paper_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question paper not found")
    file_path = Path(item.file_path)
    db.delete(item)
    db.commit()
    if file_path.exists():
        file_path.unlink()
    return {"status": "deleted"}


@app.get("/api/chapters/{chapter_id}/books", response_model=List[BookOut])
def list_books(chapter_id: int, db: Session = Depends(get_db)):
    return db.query(BookModel).filter(BookModel.chapter_id == chapter_id).all()


@app.post("/api/books", response_model=BookOut)
async def upload_book(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    chapter = db.query(ChapterModel).filter(ChapterModel.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF books are supported")

    safe_name = f"{uuid.uuid4()}_{file.filename}"
    destination = UPLOAD_DIR / safe_name
    content = await file.read()
    destination.write_bytes(content)
    item = BookModel(
        title=title,
        description=description,
        file_name=file.filename,
        file_path=str(destination),
        file_data=content,
        mime_type="application/pdf",
        chapter_id=chapter_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/books/{book_id}/download")
def download_book(book_id: int, db: Session = Depends(get_db)):
    item = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Book not found")
    if item.file_data is not None:
        return Response(content=item.file_data, media_type=item.mime_type, headers={"Content-Disposition": "inline"})
    if not Path(item.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path=item.file_path, media_type=item.mime_type, headers={"Content-Disposition": "inline"})


@app.delete("/api/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    item = db.query(BookModel).filter(BookModel.id == book_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Book not found")
    file_path = Path(item.file_path)
    db.delete(item)
    db.commit()
    if file_path.exists():
        file_path.unlink()
    return {"status": "deleted"}


@app.get("/api/question-papers/{question_paper_id}", response_model=QuestionPaperOut)
def get_question_paper(question_paper_id: int, db: Session = Depends(get_db)):
    item = db.query(QuestionPaperModel).filter(QuestionPaperModel.id == question_paper_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Question paper not found")
    return item
