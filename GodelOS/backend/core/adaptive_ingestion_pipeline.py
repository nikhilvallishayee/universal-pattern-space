"""
Adaptive Knowledge Ingestion Pipeline

Implements a CPU-optimized ingestion pipeline with user-selectable analysis levels,
layout-aware chunking, autotuning, and integration with custom vector database.
"""

import asyncio
import hashlib
import logging
import os
import psutil
import tempfile
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Use aiofiles for async file operations
import aiofiles

# PDF and document processing
try:
    import pypdf
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from python_docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# NLP and chunking
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

logger = logging.getLogger(__name__)


class AnalysisLevel(Enum):
    """User-selectable analysis levels with different performance characteristics."""
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


@dataclass
class AnalysisLevelConfig:
    """Configuration for each analysis level."""
    chunk_tokens_min: int
    chunk_tokens_max: int
    overlap_tokens: int
    embedding_model: str
    top_k: int
    dedup_threshold: float
    use_layout_analysis: bool
    use_semantic_chunking: bool
    max_batch_size: int
    
    
# Analysis level configurations
ANALYSIS_CONFIGS = {
    AnalysisLevel.FAST: AnalysisLevelConfig(
        chunk_tokens_min=650,
        chunk_tokens_max=800,
        overlap_tokens=75,
        embedding_model="all-MiniLM-L6-v2",
        top_k=10,
        dedup_threshold=0.92,
        use_layout_analysis=False,
        use_semantic_chunking=False,
        max_batch_size=64
    ),
    AnalysisLevel.BALANCED: AnalysisLevelConfig(
        chunk_tokens_min=750,
        chunk_tokens_max=900,
        overlap_tokens=110,
        embedding_model="all-MiniLM-L6-v2",
        top_k=15,
        dedup_threshold=0.88,
        use_layout_analysis=True,
        use_semantic_chunking=True,
        max_batch_size=32
    ),
    AnalysisLevel.DEEP: AnalysisLevelConfig(
        chunk_tokens_min=500,
        chunk_tokens_max=700,
        overlap_tokens=140,
        embedding_model="all-mpnet-base-v2",
        top_k=20,
        dedup_threshold=0.85,
        use_layout_analysis=True,
        use_semantic_chunking=True,
        max_batch_size=16
    )
}


@dataclass
class SystemResources:
    """Current system resource state."""
    cpu_cores: int
    available_memory_gb: float
    current_memory_usage_percent: float
    cpu_usage_percent: float
    

@dataclass
class AutotuneConfig:
    """Dynamic configuration determined by autotuner."""
    num_workers: int
    batch_size: int
    queue_depth: int
    memory_limit_gb: float
    enable_spill_to_disk: bool


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    document_id: str
    chunk_index: int
    start_offset: int
    end_offset: int
    token_count: int
    has_heading: bool
    heading_level: int
    punctuation_ratio: float
    quality_score: float
    simhash: Optional[str] = None


@dataclass
class ProcessedChunk:
    """A processed chunk ready for embedding."""
    metadata: ChunkMetadata
    text: str
    embedding: Optional[np.ndarray] = None


@dataclass
class IngestionJob:
    """Represents an ingestion job with progress tracking."""
    job_id: str
    file_path: str
    file_name: str
    analysis_level: AnalysisLevel
    status: str  # queued, processing, completed, failed, cancelled
    total_chunks: int
    processed_chunks: int
    start_time: float
    estimated_completion_time: Optional[float] = None
    error_message: Optional[str] = None
    document_id: Optional[str] = None
    
    
@dataclass
class PreflightEstimate:
    """Preflight estimation for different analysis levels."""
    estimated_chunks: int
    estimated_tokens: int
    eta_p50_seconds: float
    eta_p90_seconds: float
    memory_usage_mb: float
    

class Autotuner:
    """Autotuning system for mid-range CPU efficiency."""
    
    def __init__(self):
        self.base_workers = min(max(psutil.cpu_count() - 2, 1), 8)
        self.current_config = AutotuneConfig(
            num_workers=self.base_workers,
            batch_size=32,
            queue_depth=100,
            memory_limit_gb=12.0,
            enable_spill_to_disk=False
        )
        self.performance_history = []
        self.adjustment_interval = 10.0  # seconds
        self.last_adjustment = time.time()
        
    def get_system_resources(self) -> SystemResources:
        """Get current system resource utilization."""
        memory = psutil.virtual_memory()
        return SystemResources(
            cpu_cores=psutil.cpu_count(),
            available_memory_gb=memory.available / (1024**3),
            current_memory_usage_percent=memory.percent,
            cpu_usage_percent=psutil.cpu_percent(interval=1)
        )
        
    def should_adjust(self) -> bool:
        """Check if it's time to adjust configuration."""
        return time.time() - self.last_adjustment > self.adjustment_interval
        
    def adjust_configuration(self, throughput_chunks_per_sec: float, memory_pressure: bool):
        """Adjust configuration based on performance metrics."""
        if not self.should_adjust():
            return
            
        resources = self.get_system_resources()
        
        # Memory pressure handling
        if memory_pressure or resources.current_memory_usage_percent > 85:
            self.current_config.batch_size = max(8, self.current_config.batch_size // 2)
            self.current_config.enable_spill_to_disk = True
            logger.info(f"Memory pressure detected, reducing batch size to {self.current_config.batch_size}")
            
        # CPU utilization optimization
        elif resources.cpu_usage_percent < 60 and self.current_config.num_workers < 16:
            self.current_config.num_workers += 1
            logger.info(f"Increasing workers to {self.current_config.num_workers}")
            
        elif resources.cpu_usage_percent > 90 and self.current_config.num_workers > 1:
            self.current_config.num_workers -= 1
            logger.info(f"Decreasing workers to {self.current_config.num_workers}")
            
        # Throughput optimization
        if throughput_chunks_per_sec > 0:
            self.performance_history.append(throughput_chunks_per_sec)
            if len(self.performance_history) > 10:
                self.performance_history.pop(0)
                
        self.last_adjustment = time.time()


class LayoutAwareChunker:
    """Layout and sentence-aware chunking strategy."""
    
    def __init__(self, config: AnalysisLevelConfig):
        self.config = config
        self.nlp = None
        if HAS_SPACY and config.use_semantic_chunking:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, falling back to basic chunking")
                
    def _calculate_simhash(self, text: str) -> str:
        """Calculate simhash for deduplication."""
        # Simple simhash implementation
        hash_val = hashlib.md5(text.encode()).hexdigest()
        return hash_val[:16]
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return len(text.split()) * 1.3  # Conservative estimate
        
    def _calculate_quality_score(self, text: str, has_heading: bool) -> float:
        """Calculate chunk quality score."""
        score = 1.0
        
        # Length penalty for very short or very long chunks
        word_count = len(text.split())
        if word_count < 50:
            score *= 0.7
        elif word_count > 1000:
            score *= 0.8
            
        # Heading bonus
        if has_heading:
            score *= 1.2
            
        # Punctuation ratio
        punct_chars = sum(1 for c in text if c in '.,!?;:')
        punct_ratio = punct_chars / max(len(text), 1)
        if 0.02 <= punct_ratio <= 0.08:  # Good punctuation range
            score *= 1.1
            
        return min(score, 2.0)
        
    def chunk_text(self, text: str, document_id: str) -> List[ProcessedChunk]:
        """Chunk text using layout and sentence awareness."""
        chunks = []
        
        if self.nlp and self.config.use_semantic_chunking:
            chunks = self._semantic_chunk(text, document_id)
        else:
            chunks = self._basic_chunk(text, document_id)
            
        # Apply deduplication
        unique_chunks = self._deduplicate_chunks(chunks)
        
        return unique_chunks
        
    def _semantic_chunk(self, text: str, document_id: str) -> List[ProcessedChunk]:
        """Semantic chunking using spaCy."""
        doc = self.nlp(text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if not sentence_text:
                continue
                
            # Check if adding this sentence would exceed token limit
            potential_chunk = current_chunk + " " + sentence_text if current_chunk else sentence_text
            estimated_tokens = self._estimate_tokens(potential_chunk)
            
            if estimated_tokens > self.config.chunk_tokens_max and current_chunk:
                # Create chunk from current content
                chunk = self._create_chunk(
                    current_chunk, document_id, chunk_index, current_start, len(current_chunk)
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_tokens = self.config.overlap_tokens
                overlap_text = self._get_overlap_text(current_chunk, overlap_tokens)
                current_chunk = overlap_text + " " + sentence_text if overlap_text else sentence_text
                current_start = len(current_chunk) - len(sentence_text)
            else:
                current_chunk = potential_chunk
                
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, document_id, chunk_index, current_start, len(current_chunk)
            )
            chunks.append(chunk)
            
        return chunks
        
    def _basic_chunk(self, text: str, document_id: str) -> List[ProcessedChunk]:
        """Basic sliding window chunking."""
        chunks = []
        words = text.split()
        chunk_index = 0
        
        # Estimate words per token
        words_per_token = 0.75
        words_per_chunk = int(self.config.chunk_tokens_max * words_per_token)
        overlap_words = int(self.config.overlap_tokens * words_per_token)
        
        start_idx = 0
        while start_idx < len(words):
            end_idx = min(start_idx + words_per_chunk, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)
            
            chunk = self._create_chunk(
                chunk_text, document_id, chunk_index, start_idx, end_idx
            )
            chunks.append(chunk)
            chunk_index += 1
            
            # Move window with overlap
            start_idx = max(start_idx + words_per_chunk - overlap_words, start_idx + 1)
            
        return chunks
        
    def _create_chunk(self, text: str, document_id: str, chunk_index: int, 
                     start_offset: int, end_offset: int) -> ProcessedChunk:
        """Create a ProcessedChunk with metadata."""
        chunk_id = f"{document_id}_chunk_{chunk_index}"
        
        # Detect headings (simple heuristic)
        has_heading = any(line.strip() and (
            line.strip().isupper() or 
            line.strip().endswith(':') or
            len(line.strip().split()) <= 8
        ) for line in text.split('\n')[:3])
        
        # Calculate punctuation ratio
        punct_chars = sum(1 for c in text if c in '.,!?;:')
        punct_ratio = punct_chars / max(len(text), 1)
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_index=chunk_index,
            start_offset=start_offset,
            end_offset=end_offset,
            token_count=int(self._estimate_tokens(text)),
            has_heading=has_heading,
            heading_level=1 if has_heading else 0,
            punctuation_ratio=punct_ratio,
            quality_score=self._calculate_quality_score(text, has_heading),
            simhash=self._calculate_simhash(text)
        )
        
        return ProcessedChunk(metadata=metadata, text=text)
        
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text for chunk boundaries."""
        words = text.split()
        overlap_words = int(overlap_tokens * 0.75)  # Conservative estimate
        if len(words) <= overlap_words:
            return text
        return " ".join(words[-overlap_words:])
        
    def _deduplicate_chunks(self, chunks: List[ProcessedChunk]) -> List[ProcessedChunk]:
        """Remove duplicate chunks based on simhash."""
        seen_hashes = set()
        unique_chunks = []
        
        for chunk in chunks:
            if chunk.metadata.simhash not in seen_hashes:
                seen_hashes.add(chunk.metadata.simhash)
                unique_chunks.append(chunk)
            else:
                logger.debug(f"Skipping duplicate chunk: {chunk.metadata.chunk_id}")
                
        return unique_chunks


class AdaptiveIngestionPipeline:
    """Main adaptive ingestion pipeline."""
    
    def __init__(self, vector_database=None):
        self.vector_database = vector_database
        self.autotuner = Autotuner()
        self.embedding_models = {}
        self.active_jobs = {}
        self.job_queue = asyncio.Queue()
        self.worker_tasks = []
        self.chunker_cache = {}
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize embedding models for each analysis level."""
        for level, config in ANALYSIS_CONFIGS.items():
            try:
                if config.embedding_model not in self.embedding_models:
                    logger.info(f"Loading embedding model: {config.embedding_model}")
                    model = SentenceTransformer(config.embedding_model)
                    self.embedding_models[config.embedding_model] = model
            except Exception as e:
                logger.error(f"Failed to load model {config.embedding_model}: {e}")
                
    def get_chunker(self, analysis_level: AnalysisLevel) -> LayoutAwareChunker:
        """Get cached chunker for analysis level."""
        if analysis_level not in self.chunker_cache:
            config = ANALYSIS_CONFIGS[analysis_level]
            self.chunker_cache[analysis_level] = LayoutAwareChunker(config)
        return self.chunker_cache[analysis_level]
        
    async def estimate_workload(self, file_path: str) -> Dict[AnalysisLevel, PreflightEstimate]:
        """Provide preflight estimation for all analysis levels."""
        estimates = {}
        
        # Extract actual text content for more accurate estimation
        try:
            # Use the same text extraction method as actual processing
            full_text = await self._extract_text(file_path)
            if not full_text:
                # Fallback to sampling if full extraction fails
                full_text = await self._sample_file(file_path, max_chars=8192)
        except Exception as e:
            logger.warning(f"Failed to extract full text for estimation, using sample: {e}")
            full_text = await self._sample_file(file_path, max_chars=8192)
        
        # Calculate actual token count using the same method as chunking
        estimated_total_tokens = len(full_text.split()) * 1.3  # More conservative multiplier
        
        for level, config in ANALYSIS_CONFIGS.items():
            # Create a chunker instance to simulate actual chunking
            chunker = self.get_chunker(level)
            
            # Estimate chunks using actual chunking logic on a sample
            if len(full_text) > 10000:
                # For large documents, use representative sample
                sample_text = full_text[:5000] + full_text[len(full_text)//2:len(full_text)//2+2500] + full_text[-2500:]
            else:
                sample_text = full_text
                
            # Actually chunk the sample to get realistic count
            sample_chunks = chunker.chunk_text(sample_text, "sample_doc")
            sample_tokens = len(sample_text.split()) * 1.3
            
            # Extrapolate to full document
            if sample_tokens > 0:
                chunks_per_token = len(sample_chunks) / sample_tokens
                estimated_chunks = max(1, int(estimated_total_tokens * chunks_per_token))
                
                # Apply deduplication factor (estimated 10-30% reduction)
                dedup_factor = 0.8  # Conservative estimate for deduplication impact
                estimated_chunks = max(1, int(estimated_chunks * dedup_factor))
            else:
                # Fallback calculation
                avg_chunk_tokens = (config.chunk_tokens_min + config.chunk_tokens_max) / 2
                estimated_chunks = max(1, int(estimated_total_tokens / avg_chunk_tokens))
            
            # Estimate processing time based on model and hardware
            base_time_per_chunk = self._estimate_processing_time(level)
            eta_p50 = estimated_chunks * base_time_per_chunk
            eta_p90 = eta_p50 * 1.5  # Add variance buffer
            
            # Estimate memory usage
            embedding_dim = 384 if "MiniLM" in config.embedding_model else 768
            memory_usage_mb = estimated_chunks * embedding_dim * 4 / (1024 * 1024)  # float32
            
            estimates[level] = PreflightEstimate(
                estimated_chunks=estimated_chunks,
                estimated_tokens=int(estimated_total_tokens),
                eta_p50_seconds=eta_p50,
                eta_p90_seconds=eta_p90,
                memory_usage_mb=memory_usage_mb
            )
            
        return estimates
        
    async def _sample_file(self, file_path: str, max_chars: int = 2048) -> str:
        """Sample beginning of file for estimation."""
        try:
            if file_path.lower().endswith('.pdf') and HAS_PYPDF:
                reader = PdfReader(file_path)
                if reader.pages:
                    return reader.pages[0].extract_text()[:max_chars]
            elif file_path.lower().endswith('.docx') and HAS_DOCX:
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs[:5]])
                return text[:max_chars]
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(max_chars)
        except Exception as e:
            logger.warning(f"Failed to sample file {file_path}: {e}")
            return ""
            
    def _estimate_processing_time(self, level: AnalysisLevel) -> float:
        """Estimate processing time per chunk for analysis level."""
        config = ANALYSIS_CONFIGS[level]
        
        # Base time estimates (seconds per chunk)
        base_times = {
            AnalysisLevel.FAST: 0.1,
            AnalysisLevel.BALANCED: 0.25,
            AnalysisLevel.DEEP: 0.5
        }
        
        # Adjust for current system performance
        resources = self.autotuner.get_system_resources()
        cpu_factor = max(0.5, 2.0 - (resources.cpu_usage_percent / 100))
        memory_factor = max(0.7, 1.5 - (resources.current_memory_usage_percent / 100))
        
        return base_times[level] * cpu_factor * memory_factor
        
    async def start_ingestion_job(self, file_path: str, analysis_level: AnalysisLevel, file_name: Optional[str] = None) -> str:
        """Start a new ingestion job."""
        if file_name is None:
            file_name = Path(file_path).name
            
        job_id = f"job_{int(time.time())}_{hash(file_path) % 10000}"
        document_id = f"doc_{int(time.time())}_{hash(file_name) % 10000}"
        
        job = IngestionJob(
            job_id=job_id,
            file_path=file_path,
            file_name=file_name,
            analysis_level=analysis_level,
            status="queued",
            total_chunks=0,
            processed_chunks=0,
            start_time=time.time(),
            document_id=document_id
        )
        
        self.active_jobs[job_id] = job
        await self.job_queue.put(job)
        
        # Start worker if needed
        if not self.worker_tasks:
            await self._start_workers()
            
        logger.info(f"Started ingestion job {job_id} for {file_path} at level {analysis_level.value}")
        return job_id
        
    async def _start_workers(self):
        """Start worker tasks for processing jobs."""
        num_workers = self.autotuner.current_config.num_workers
        
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker_{i}"))
            self.worker_tasks.append(task)
            
        logger.info(f"Started {num_workers} ingestion workers")
        
    async def _worker(self, worker_id: str):
        """Worker task for processing ingestion jobs."""
        logger.info(f"Ingestion worker {worker_id} started")
        
        while True:
            try:
                job = await self.job_queue.get()
                await self._process_job(job, worker_id)
                self.job_queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                
    async def _process_job(self, job: IngestionJob, worker_id: str):
        """Process a single ingestion job."""
        try:
            job.status = "processing"
            logger.info(f"Worker {worker_id} processing job {job.job_id}")
            
            # Extract text from file
            text = await self._extract_text(job.file_path)
            if not text:
                raise ValueError("No text could be extracted from file")
                
            # Chunk the text
            chunker = self.get_chunker(job.analysis_level)
            chunks = chunker.chunk_text(text, job.job_id)
            job.total_chunks = len(chunks)
            
            # Process chunks in batches
            config = ANALYSIS_CONFIGS[job.analysis_level]
            model = self.embedding_models.get(config.embedding_model)
            
            if not model:
                raise ValueError(f"Embedding model {config.embedding_model} not available")
                
            batch_size = min(config.max_batch_size, self.autotuner.current_config.batch_size)
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await self._process_chunk_batch(batch, model, job)
                
                # Update progress
                job.processed_chunks = min(i + batch_size, len(chunks))
                
                # Check for cancellation
                if job.status == "cancelled":
                    logger.info(f"Job {job.job_id} cancelled")
                    return
                    
                # Autotune if needed
                throughput = job.processed_chunks / (time.time() - job.start_time)
                memory_pressure = psutil.virtual_memory().percent > 80
                self.autotuner.adjust_configuration(throughput, memory_pressure)
                
            job.status = "completed"
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed: {e}")
            
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from various file formats."""
        try:
            if file_path.lower().endswith('.pdf') and HAS_PYPDF:
                return await self._extract_pdf_text(file_path)
            elif file_path.lower().endswith('.docx') and HAS_DOCX:
                return await self._extract_docx_text(file_path)
            else:
                return await self._extract_plain_text(file_path)
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""
            
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        def extract():
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)
            
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, extract)
            
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        def extract():
            doc = Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, extract)
            
    async def _extract_plain_text(self, file_path: str) -> str:
        """Extract text from plain text file."""
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return await f.read()
            
    async def _process_chunk_batch(self, chunks: List[ProcessedChunk], 
                                  model: SentenceTransformer, job: IngestionJob):
        """Process a batch of chunks for embedding and storage."""
        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        
        def generate_embeddings():
            return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            embeddings = await loop.run_in_executor(executor, generate_embeddings)
            
        # Store in vector database
        if self.vector_database:
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                await self._store_chunk(chunk, job)
                
    async def _store_chunk(self, chunk: ProcessedChunk, job: IngestionJob):
        """Store chunk in vector database and build knowledge graph."""
        try:
            # Store in vector database using the correct method
            if self.vector_database and hasattr(self.vector_database, 'add_items'):
                # Convert chunk to vector database format
                items = [(chunk.metadata.chunk_id, chunk.text)]
                metadata = [chunk.metadata.__dict__]
                
                result = self.vector_database.add_items(
                    items=items,
                    metadata=metadata,
                    model_name=None  # Use default model
                )
                
                # Handle both boolean and dict returns from vector database
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if not success:
                        logger.error(f"Failed to store chunk in vector DB: {result.get('message', 'Unknown error')}")
                        return
                elif isinstance(result, bool):
                    if not result:
                        logger.error(f"Failed to store chunk in vector DB: add_items returned False")
                        return
                else:
                    logger.error(f"Unexpected result type from vector DB: {type(result)}")
                    return
                    
                logger.debug(f"Stored chunk {chunk.metadata.chunk_id} in vector database")
            
            # Create concept in knowledge graph
            await self._create_knowledge_concept(chunk, job)
            
            # Build knowledge graph relationships
            await self._build_knowledge_relationships(chunk, job)
            
        except Exception as e:
            logger.error(f"Failed to store chunk {chunk.metadata.chunk_id}: {e}")
            
    async def _create_knowledge_concept(self, chunk: ProcessedChunk, job: IngestionJob):
        """Create a knowledge concept for this chunk."""
        if not hasattr(self, 'knowledge_graph_evolution'):
            # Initialize knowledge graph if not available
            try:
                from backend.core.knowledge_graph_evolution import KnowledgeGraphEvolution
                self.knowledge_graph_evolution = KnowledgeGraphEvolution()
            except ImportError:
                logger.warning("Knowledge graph evolution not available")
                return
                
        try:
            concept_data = {
                "name": f"Chunk_{chunk.metadata.chunk_id[:8]}",
                "description": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "type": "document_chunk",
                "properties": {
                    "document_id": job.document_id,
                    "chunk_index": chunk.metadata.chunk_index,
                    "token_count": chunk.metadata.token_count,
                    "quality_score": chunk.metadata.quality_score,
                    "file_name": job.file_name,
                    "analysis_level": job.analysis_level.value
                },
                "confidence": chunk.metadata.quality_score,
                "embedding": chunk.embedding.tolist() if chunk.embedding is not None else None,
                "evidence": [f"Extracted from {job.file_name}"]
            }
            
            concept = await self.knowledge_graph_evolution.add_concept(
                concept_data, auto_connect=False  # We'll handle connections manually
            )
            
            # Store concept ID in chunk metadata for relationship building
            chunk.metadata.concept_id = concept.id
            
            # Track concept mapping in job for later lookups
            if not hasattr(job, 'chunk_concepts'):
                job.chunk_concepts = {}
            job.chunk_concepts[chunk.metadata.chunk_id] = concept.id
            
            logger.debug(f"Created knowledge concept {concept.id} for chunk {chunk.metadata.chunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to create knowledge concept for chunk {chunk.metadata.chunk_id}: {e}")
            
    async def _build_knowledge_relationships(self, chunk: ProcessedChunk, job: IngestionJob):
        """Build knowledge graph relationships from vector similarities."""
        if not self.vector_database or not hasattr(self.vector_database, 'search'):
            return
            
        if not hasattr(chunk.metadata, 'concept_id'):
            logger.warning(f"No concept ID for chunk {chunk.metadata.chunk_id}, skipping relationships")
            return
            
        try:
            # Find similar chunks using vector database search
            config = ANALYSIS_CONFIGS[job.analysis_level]
            
            # Use the chunk text to search for similar content
            similar_results = self.vector_database.search(
                query_text=chunk.text,
                k=config.top_k,
                similarity_threshold=0.3  # Lower threshold for initial search
            )
            
            # Filter out self and create relationships
            relationship_count = 0
            similarity_threshold = {
                AnalysisLevel.FAST: 0.6,
                AnalysisLevel.BALANCED: 0.7, 
                AnalysisLevel.DEEP: 0.8
            }.get(job.analysis_level, 0.7)
            
            for similar_result in similar_results:
                # Handle both tuple (id, score) and dict formats
                if isinstance(similar_result, tuple):
                    result_id, similarity_score = similar_result
                elif isinstance(similar_result, dict):
                    result_id = similar_result.get('id')
                    similarity_score = similar_result.get('similarity_score', similar_result.get('score', 0))
                else:
                    logger.warning(f"Unexpected result format: {type(similar_result)}")
                    continue
                
                # Skip self-matches
                if result_id == chunk.metadata.chunk_id:
                    continue
                    
                if similarity_score > similarity_threshold:
                    # Create SIMILAR_TO relationship
                    await self._create_knowledge_relationship(
                        chunk.metadata.concept_id,
                        result_id,
                        'SIMILAR_TO',
                        similarity_score
                    )
                    relationship_count += 1
                    
                    # Limit relationships to avoid graph explosion
                    if relationship_count >= 5:
                        break
                    
            logger.debug(f"Created {relationship_count} relationships for chunk {chunk.metadata.chunk_id}")
                    
        except Exception as e:
            logger.error(f"Failed to build relationships for chunk {chunk.metadata.chunk_id}: {e}")
            
    async def _create_knowledge_relationship(self, source_concept_id: str, target_chunk_id: str, 
                                           relation_type: str, strength: float):
        """Create a knowledge graph relationship between concepts."""
        if not hasattr(self, 'knowledge_graph_evolution'):
            return
            
        try:
            # Find the target concept ID from the chunk ID
            target_concept_id = await self._find_concept_by_chunk_id(target_chunk_id)
            if not target_concept_id:
                logger.debug(f"Could not find target concept for chunk {target_chunk_id}")
                return
                
            from backend.core.knowledge_graph_evolution import RelationshipType
            
            relationship = await self.knowledge_graph_evolution.create_relationship(
                source_id=source_concept_id,
                target_id=target_concept_id,
                relationship_type=RelationshipType.SIMILAR_TO,
                strength=min(strength, 1.0),  # Ensure strength is <= 1.0
                evidence=[f"Vector similarity: {strength:.3f}"]
            )
            
            logger.debug(f"Created knowledge relationship: {source_concept_id} --{relation_type}:{strength:.3f}--> {target_concept_id}")
            
        except Exception as e:
            logger.error(f"Failed to create knowledge relationship: {e}")
            
    async def _find_concept_by_chunk_id(self, chunk_id: str) -> Optional[str]:
        """Find knowledge concept ID by chunk ID."""
        # Search through active jobs to find the concept ID
        for job in self.active_jobs.values():
            if hasattr(job, 'chunk_concepts') and chunk_id in job.chunk_concepts:
                return job.chunk_concepts[chunk_id]
        return None
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status and progress."""
        if job_id not in self.active_jobs:
            return None
            
        job = self.active_jobs[job_id]
        progress_percent = 0.0
        if job.total_chunks > 0:
            progress_percent = (job.processed_chunks / job.total_chunks) * 100
            
        elapsed_time = time.time() - job.start_time
        eta_seconds = None
        
        if job.processed_chunks > 0 and job.status == "processing":
            chunks_per_second = job.processed_chunks / elapsed_time
            remaining_chunks = job.total_chunks - job.processed_chunks
            eta_seconds = remaining_chunks / chunks_per_second if chunks_per_second > 0 else None
            
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress_percent": progress_percent,
            "processed_chunks": job.processed_chunks,
            "total_chunks": job.total_chunks,
            "elapsed_time_seconds": elapsed_time,
            "eta_seconds": eta_seconds,
            "error_message": job.error_message,
            "analysis_level": job.analysis_level.value
        }
        
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in ["queued", "processing"]:
                job.status = "cancelled"
                logger.info(f"Job {job_id} cancelled")
                return True
        return False
        
    async def cleanup_completed_jobs(self, max_age_seconds: int = 3600):
        """Clean up old completed jobs."""
        current_time = time.time()
        to_remove = []
        
        for job_id, job in self.active_jobs.items():
            if (job.status in ["completed", "failed", "cancelled"] and 
                current_time - job.start_time > max_age_seconds):
                to_remove.append(job_id)
                
        for job_id in to_remove:
            del self.active_jobs[job_id]
            logger.debug(f"Cleaned up job {job_id}")
            
    async def shutdown(self):
        """Shutdown the ingestion pipeline."""
        logger.info("Shutting down adaptive ingestion pipeline")
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
            
        # Wait for workers to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
        self.worker_tasks.clear()
        logger.info("Adaptive ingestion pipeline shutdown complete")