import subprocess
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class DiffStats:
    files: List[str]
    total_add: int
    total_del: int

    @property
    def total_lines_changed(self) -> int:
        return self.total_add + self.total_del


def _run(cmd: List[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def staged_stats() -> DiffStats:
    out_files = _run(["git", "diff", "--cached", "--name-only"])
    files = [l.strip() for l in out_files.splitlines() if l.strip()]

    out_ns = _run(["git", "diff", "--cached", "--numstat"])
    total_add = 0
    total_del = 0
    for line in out_ns.splitlines():
        if not line.strip():
            continue
        a, d, _f = line.split("\t", 2)
        total_add += int(a) if a.isdigit() else 0
        total_del += int(d) if d.isdigit() else 0

    return DiffStats(files=files, total_add=total_add, total_del=total_del)


def range_stats(base_ref: str, head_ref: str) -> DiffStats:
    out_files = _run(["git", "diff", "--name-only", f"{base_ref}...{head_ref}"])
    files = [l.strip() for l in out_files.splitlines() if l.strip()]

    out_ns = _run(["git", "diff", "--numstat", f"{base_ref}...{head_ref}"])
    total_add = 0
    total_del = 0
    for line in out_ns.splitlines():
        if not line.strip():
            continue
        a, d, _f = line.split("\t", 2)
        total_add += int(a) if a.isdigit() else 0
        total_del += int(d) if d.isdigit() else 0

    return DiffStats(files=files, total_add=total_add, total_del=total_del)
