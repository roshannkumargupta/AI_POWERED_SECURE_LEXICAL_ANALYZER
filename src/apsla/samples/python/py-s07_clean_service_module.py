from dataclasses import dataclass
from typing import Iterable
import logging

logger = logging.getLogger(__name__)

@dataclass
class Job:
    name: str

def describe(jobs: Iterable[Job]) -> list[str]:
    with open('README.md', encoding='utf-8') as guide:
        prefix = guide.readline().strip()
    return [f'{prefix}: {job.name}' for job in jobs]

async def ready() -> bool:
    return True
