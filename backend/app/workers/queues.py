import json
import logging
import os
from typing import Any, Dict, List

from rq import Queue
from redis import Redis

logger = logging.getLogger(__name__)


def get_redis() -> Redis:
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return Redis(host=host, port=port, db=0)


def get_queue(name: str) -> Queue:
    return Queue(name, connection=get_redis(), default_timeout=600)


def enqueue_ocr(doc_id: str, storage_path: str) -> str:
    q = get_queue("ocr")
    job = q.enqueue("app.workers.tasks.ocr_and_extract", doc_id, storage_path)
    logger.info("Enqueued OCR job %s for doc %s", job.id, doc_id)
    return job.id


def enqueue_generate_questions(
    doc_id: str,
    gen_id: str,
    selected_questions: List[Dict[str, Any]],
    target_count: int,
) -> List[str]:
    q = get_queue("generate")
    jobs = []
    for idx, qdata in enumerate(selected_questions[:target_count]):
        job = q.enqueue(
            "app.workers.tasks.generate_one_question", doc_id, gen_id, qdata, idx
        )
        jobs.append(job.id)
    logger.info(
        "Enqueued %d question jobs for doc %s gen %s", len(jobs), doc_id, gen_id
    )
    return jobs
