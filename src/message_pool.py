"""
Message pool management for morning messages rotation.

Implements full-cycle rotation:
- No repeats until ALL messages shown
- Independent pools (emotional and psychological)
- Automatic cycle reset when exhausted
"""

import json
import random
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Базовая директория проекта (относительно этого файла)
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "tanya_dataset_generator" / "output_v2"


class MessagePool:
    """Manages message rotation with full-cycle logic."""

    def __init__(self, pool_name: str, messages: List[Dict]):
        """
        Initialize message pool.

        Args:
            pool_name: "emotional" or "psychological"
            messages: List of message dicts from JSON
        """
        self.pool_name = pool_name
        self.all_messages = messages
        self.total_count = len(messages)

        logger.info(f"Initialized {pool_name} pool with {self.total_count} messages")

    def get_next(self, shown_ids: List[str]) -> tuple[Dict, List[str]]:
        """
        Get next message for user.

        Args:
            shown_ids: List of already shown message IDs in current cycle

        Returns:
            Tuple of (selected_message, updated_shown_ids)
        """
        # Validate shown_ids type
        if not isinstance(shown_ids, list):
            logger.warning(f"Invalid shown_ids type ({type(shown_ids).__name__}), resetting to empty list")
            shown_ids = []

        # Calculate available messages
        all_ids = [msg["id"] for msg in self.all_messages]
        available_ids = [id for id in all_ids if id not in shown_ids]

        # If exhausted, reset cycle
        if not available_ids:
            logger.info(f"Pool {self.pool_name} exhausted. Resetting cycle.")
            shown_ids = []
            available_ids = all_ids

        # Random selection
        selected_id = random.choice(available_ids)
        selected_message = next(msg for msg in self.all_messages if msg["id"] == selected_id)

        # Update shown list
        new_shown_ids = shown_ids + [selected_id]

        logger.info(f"Selected {selected_id} from {self.pool_name} ({len(new_shown_ids)}/{self.total_count} shown)")

        return selected_message, new_shown_ids


def load_compliments() -> List[Dict]:
    """Load compliments dataset."""
    path = DATASETS_DIR / "compliments_final.json"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("compliments_final.json: expected object at root")
        if "compliments" not in data:
            raise ValueError("compliments_final.json: missing 'compliments' key")
        if not isinstance(data["compliments"], list):
            raise ValueError("compliments_final.json: 'compliments' must be array")

        # Validate each message has required fields
        for i, msg in enumerate(data["compliments"]):
            if not isinstance(msg, dict) or "id" not in msg or "text" not in msg:
                raise ValueError(f"compliments_final.json: message[{i}] missing 'id' or 'text'")

        return data.get("compliments", [])


def load_psychology() -> List[Dict]:
    """Load psychology messages dataset."""
    path = DATASETS_DIR / "psychology_final.json"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("psychology_final.json: expected object at root")
        if "quotes" not in data:
            raise ValueError("psychology_final.json: missing 'quotes' key")
        if not isinstance(data["quotes"], list):
            raise ValueError("psychology_final.json: 'quotes' must be array")

        # Validate each message has required fields
        for i, msg in enumerate(data["quotes"]):
            if not isinstance(msg, dict) or "id" not in msg or "text" not in msg:
                raise ValueError(f"psychology_final.json: message[{i}] missing 'id' or 'text'")

        return data.get("quotes", [])


def format_combined_message(emotional: str, psychological: str) -> str:
    """
    Format combined morning message.

    Args:
        emotional: Compliment text
        psychological: Psychology principle text

    Returns:
        Formatted message (closure + compliment + quoted psychology)
    """
    return f"Для тебя 💌\n\n{emotional}\n\n\"{psychological}\""
