"""
A server represents a whendo process that listens on a host:port
and responds to restful api requests. Server objects are stored
on a whendo server to facilitate running schedulers and executing
actions on more than one machine.
"""

from pydantic import BaseModel
from typing import Dict, Set, List, Optional
from enum import Enum
import logging
from .util import KeyTagMode


logger = logging.getLogger(__name__)


class Server(BaseModel):
    host: str
    port: int
    tags: Optional[Dict[str, List[str]]] = None

    """
    A server has a dictionary mapping keys to sets of tags (sets
    implemented as lists). Keys serve as a way to qualify tags. It's
    up to the user to use this key:tag-set structure to some benefit.
    """

    def description(self):
        return f"This whendo server listens on host:port ({self.host}:{self.port} with tags ({self.tags})."

    def add_key_tag(self, key: str, tag: str):
        """
        Add a key:tag pair to the tags dictionary.
        """
        self.add_key_tags(key_tags={key: [tag]})

    def add_key_tags(self, key_tags: Dict[str, List[str]]):
        """
        The new tags dictionary will include all supplied
        key:tag pairs.
        """
        for key in key_tags:
            if not self.tags:
                self.tags = {}
            if key in self.tags:
                tags = self.tags[key]
                for tag in key_tags[key]:
                    if tag not in tags:
                        tags.append(tag)
            else:
                self.tags[key] = key_tags[key]

    def has_key(self, key: str):
        return key in self.tags if self.tags else False

    def has_key_tag(self, key: str, tag: str):
        if self.tags:
            return key in self.tags and tag in self.tags[key]
        else:
            return False

    def has_tag(self, tag: str):
        if self.tags:
            return any(tag in self.tags[x] for x in self.tags)
        else:
            return False

    def delete_key_tag(self, key: str, tag: str):
        """
        Remove the tag from the key's set, removing
        an empty key.
        """
        if self.tags:
            tags = self.tags.get(key, None)
            if tags:
                tags.remove(tag)
                if len(tags) == 0:
                    self.tags.pop(key)

    def delete_key(self, key: str):
        """
        Remove the dang key.
        """
        if self.tags:
            self.tags.pop(key)

    def delete_tag(self, tag: str):
        """
        Delete tag from all tag sets and remove
        all consequently empty tag sets.
        """
        if self.tags:
            to_remove: Set[str] = set()
            tags_copy = self.tags.copy()
            for key in tags_copy:
                if tag in self.tags[key]:
                    self.tags[key].remove(tag)
                    if len(self.tags[key]) == 0:
                        to_remove.add(key)
            for key in to_remove:
                self.tags.pop(key)

    def get_tags(self):
        return self.tags

    def get_tags_by_key(self, key: str):
        """
        Return a key's tags.
        """
        return self.tags.get(key, None) if self.tags else []

    def get_keys(self, tags: List[str], key_tag_mode: KeyTagMode = KeyTagMode.ANY):
        if self.tags:
            if key_tag_mode == KeyTagMode.ANY:
                """
                Return the keys having tag sets that intersect the supplied tags.
                """
                return set(
                    key
                    for key in self.tags
                    if len(set(tags).intersection(self.tags[key])) > 0
                )
            if key_tag_mode == KeyTagMode.ALL:
                """
                Return the keys where the supplied tag set covers the key's tags.
                """
                return set(
                    key
                    for key in self.tags
                    if len(set(self.tags[key]).difference(tags)) == 0
                )
        else:
            return []
