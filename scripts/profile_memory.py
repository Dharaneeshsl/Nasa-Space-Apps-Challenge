"""Memory and Latency Profiling Script for CombustionLens.

Measures cold-start latency, peak Resident Set Size (RSS) memory, and ML runtime
footprint across REST endpoints using psutil. Appends execution records to docs/profiling.md.
"""
import os
import sys
import time
import platform
import psutil
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def get_current_rss_mb() -> float:
    """Get current process RSS in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def run_profiling():
    print("=" * 60)
    print("COMBUSTIONLENS: RESOURCE & MEMORY PROFILING")
    print("=" * 60)
    
    start_time = time.time()
    rss_initial = get_current_rss_mb()
    print(f"Initial Process RSS: {rss_initial:.2f} MB")
    
    # 1. Cold-start import measurement (FastAPI + Core logic)
    t0 = time.time()
    from fastapi.testclient import TestClient
    from api.main import app
    import core.retrieval
    import core.compare
    import core.generate
    import core.evidence
    import core.ranking
    
    cold_start_duration = time.time() - t0
    rss_post_import = get_current_rss_mb()
    print(f"Cold-Start Import Duration: {cold_start_duration:.3f} s")
    print(f"Post-Import RSS (FastAPI + Core): {rss_post_import:.2f} MB")
    
    # 2. PyTorch & Model Runtime footprint measurement
    t_ml0 = time.time()
    import torch
    ml_import_duration = time.time() - t_ml0
    rss_post_torch = get_current_rss_mb()
    print(f"PyTorch Runtime Loaded in: {ml_import_duration:.3f} s (RSS: {rss_post_torch:.2f} MB, Delta: +{rss_post_torch - rss_post_import:.2f} MB)")
    
    # 3. Endpoint execution profiling
    client = TestClient(app)
    
    # Query 1: Healthcheck
    res_health = client.get("/health")
    print(f"Healthcheck: Status {res_health.status_code}")
    
    # Query 2: Search / Ask endpoint
    t_query_start = time.time()
    res_ask = client.post("/api/ask", json={"query": "PMMA flame spread rate in microgravity"})
    query_duration = time.time() - t_query_start
    rss_post_query = get_current_rss_mb()
    print(f"Ask Endpoint (/api/ask): {query_duration:.3f} s (Status: {res_ask.status_code})")
    print(f"Post-Query RSS: {rss_post_query:.2f} MB")
    
    # Query 3: Structured Experiments
    res_exp = client.get("/api/experiments")
    print(f"Experiments Endpoint (/api/experiments): Status {res_exp.status_code}")
    
    # Query 4: Safety Brief endpoint
    res_brief = client.post("/api/brief", json={"question": "flame spread rate in microgravity"})
    rss_post_brief = get_current_rss_mb()
    print(f"Safety Brief Endpoint (/api/brief): Status {res_brief.status_code}")
    
    # Peak RSS recorded for this process
    peak_rss = max(rss_initial, rss_post_import, rss_post_torch, rss_post_query, rss_post_brief)
    total_duration = time.time() - start_time
    print("-" * 60)
    print(f"PEAK RSS (with PyTorch runtime): {peak_rss:.2f} MB")
    print(f"TOTAL PROFILING DURATION: {total_duration:.3f} s")
    print("=" * 60)
    
    # 4. Update docs/profiling.md
    profiling_md = Path("docs/profiling.md")
    today = datetime.now().strftime("%Y-%m-%d")
    os_name = f"{platform.system()} {platform.release()} (Python {platform.python_version()})"
    
    row_entry = (
        f"| {today} | {os_name} | Full Stack + PyTorch Runtime (/api/ask, /api/brief) | "
        f"{peak_rss:.1f} MB | {cold_start_duration + ml_import_duration:.2f}s | "
        f"Query latency: {query_duration:.2f}s; PyTorch + Core + FastAPI live memory |\n"
    )
    
    if profiling_md.exists():
        content = profiling_md.read_text(encoding="utf-8")
        if "| Test Date |" in content:
            lines = content.splitlines(keepends=True)
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if line.strip().startswith("| :--- | :--- | :--- | :--- | :--- | :--- |") and not inserted:
                    new_lines.append(row_entry)
                    inserted = True
            
            final_content = "".join(new_lines)
            profiling_md.write_text(final_content, encoding="utf-8")
            print(f"Updated profiling results in '{profiling_md}'.")
        else:
            with open(profiling_md, "a", encoding="utf-8") as f:
                f.write(row_entry)
            print(f"Appended profiling entry to '{profiling_md}'.")


if __name__ == "__main__":
    run_profiling()
