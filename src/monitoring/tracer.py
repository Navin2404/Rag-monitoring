# src/monitoring/tracer.py
# Ovvoru function-um evlo time edukuthunnu measure panrom
# Udharanam: stopwatch mathiri - start, stop, record

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TraceContext:
    """
    # Oru query-oda ella timing info store panna
    # @dataclass = automatic __init__ undagum
    """
    query: str = ""

    # Start times - eppo start aachunnu record
    _start_time: float = field(default_factory=time.time)
    _retrieval_start: Optional[float] = None
    _reranking_start: Optional[float] = None
    _generation_start: Optional[float] = None

    # Latencies - evlo time aachunnu record (ms)
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

    def start_retrieval(self):
        """Search start aaguthu"""
        self._retrieval_start = time.time()

    def end_retrieval(self):
        """Search mudinjathu - time calculate pannu"""
        if self._retrieval_start:
            # milliseconds-ah convert panna * 1000
            self.retrieval_latency_ms = (time.time() - self._retrieval_start) * 1000

    def start_reranking(self):
        """Reranking start aaguthu"""
        self._reranking_start = time.time()

    def end_reranking(self):
        """Reranking mudinjathu"""
        if self._reranking_start:
            self.reranking_latency_ms = (time.time() - self._reranking_start) * 1000

    def start_generation(self):
        """LLM generation start aaguthu"""
        self._generation_start = time.time()

    def end_generation(self):
        """LLM generation mudinjathu"""
        if self._generation_start:
            self.generation_latency_ms = (time.time() - self._generation_start) * 1000

    def finish(self):
        """
        # Motha time calculate pannu
        # Query start-la irunthu answer ready aagum varai
        """
        self.total_latency_ms = (time.time() - self._start_time) * 1000