from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Segment:
    id: str
    kind: str
    source: str
    target: str = ""
    frozen: bool = False
    fingerprint: str = ""
    status: str = "new"
    meta: dict[str, Any] | None = None
    def to_catalog(self):
        d = asdict(self)
        d["meta"] = self.meta or {}
        return d

@dataclass
class DocumentIR:
    source: str
    nodes: list[dict[str, Any]]
    frontmatter: str = ""
    def to_dict(self):
        return {"type":"document", "source":self.source, "frontmatter":self.frontmatter, "nodes":self.nodes}
