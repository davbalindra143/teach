import json
import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def create_class(name, description=None):
    response = requests.post(f"{API_BASE_URL}/api/classes", json={"name": name, "description": description})
    response.raise_for_status()
    return response.json()


def create_subject(class_id, name):
    response = requests.post(f"{API_BASE_URL}/api/subjects", json={"class_id": class_id, "name": name})
    response.raise_for_status()
    return response.json()


def create_chapter(subject_id, title, description=None):
    response = requests.post(
        f"{API_BASE_URL}/api/chapters",
        json={"subject_id": subject_id, "title": title, "description": description},
    )
    response.raise_for_status()
    return response.json()


def create_note(chapter_id, title, link, description=None):
    response = requests.post(
        f"{API_BASE_URL}/api/notes",
        json={"chapter_id": chapter_id, "title": title, "link": link, "description": description},
    )
    response.raise_for_status()
    return response.json()


def create_practice_set(chapter_id, title, questions, description=None):
    response = requests.post(
        f"{API_BASE_URL}/api/practice-sets",
        json={"chapter_id": chapter_id, "title": title, "description": description, "questions": questions},
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    class_ = create_class("Class 10", "Science and Mathematics")
    subject = create_subject(class_["id"], "Physics")
    chapter = create_chapter(subject["id"], "Chapter 1: Motion", "Understanding speed, velocity and acceleration")
    create_note(
        chapter["id"],
        "Motion Notes",
        "https://example.com/notes/motion.pdf",
        "Chapter summary and diagram notes",
    )
    create_practice_set(
        chapter["id"],
        "Motion Practice",
        [
            {"question": "What is the SI unit of speed?", "options": ["m/s", "km/h", "m", "sec"], "answer": "m/s"},
            {"question": "A body moves in a straight line with constant velocity. Its acceleration is:", "options": ["Zero", "Positive", "Negative", "Infinite"], "answer": "Zero"},
        ],
        "Basic questions on motion",
    )
    print("Seed data created successfully.")
