"""
Workspace Simulation Framework for Phase 5B.

Simulates realistic long-running workspaces to understand how MemLayer handles:
- Research project workspaces (literature review, hypothesis formation, analysis)
- Software engineering workspaces (code exploration, debugging, architecture design)
- Startup planning workspaces (market research, business model design, pitch preparation)
- Document-heavy workspaces (writing projects, knowledge bases)

Each workspace type has its own:
- Semantic memory patterns
- Query patterns
- Compression characteristics
- Long-horizon degradation signatures
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class WorkspaceType(str, Enum):
    """Types of simulated workspaces."""

    RESEARCH = "research"
    SOFTWARE_ENGINEERING = "software_engineering"
    STARTUP_PLANNING = "startup_planning"
    DOCUMENT_HEAVY = "document_heavy"


class QueryPattern(str, Enum):
    """Query patterns observed in workspaces."""

    DEEP_ANALYSIS = "deep_analysis"  # Long, thoughtful queries
    RAPID_EXPLORATION = "rapid_exploration"  # Quick, exploratory queries
    REFERENCE_LOOKUP = "reference_lookup"  # Retrieving specific information
    SYNTHESIS = "synthesis"  # Combining multiple sources
    DEBUGGING = "debugging"  # Problem-finding queries


@dataclass
class WorkspaceMemory:
    """A single memory unit in a workspace."""

    memory_id: str
    content: str
    domain: str  # research, code, design, notes, etc.
    importance: float  # 0-1, how important this memory is
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0  # How many times accessed
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "domain": self.domain,
            "importance": self.importance,
            "access_count": self.access_count,
            "recency_score": self._calculate_recency_score(),
        }

    def _calculate_recency_score(self) -> float:
        """Calculate recency score based on last access."""
        if self.last_accessed is None:
            return 0.0
        delta = (datetime.now(timezone.utc) - self.last_accessed).total_seconds()
        # Decay over time: 1.0 if accessed now, 0.0 if older than a day
        days_since = delta / 86400  # seconds per day
        return max(0.0, 1.0 - (days_since / 1.0))


@dataclass
class WorkspaceQuery:
    """A query in a workspace execution."""

    query_id: str
    query_text: str
    pattern: QueryPattern
    domain: str  # Which domain this query is about
    complexity_level: str  # simple, moderate, complex, very_complex
    num_memories_needed: int  # Estimated memories needed
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SimulatedWorkspace:
    """A simulated workspace execution."""

    workspace_id: str
    workspace_type: WorkspaceType
    description: str

    # Simulation parameters
    duration_hours: int = 24  # How long to simulate
    num_queries: int = 100  # Number of queries to execute
    base_memory_count: int = 500  # Starting memory pool size
    memory_growth_rate: float = 0.1  # Percentage growth per hour

    # Query patterns
    query_pattern_distribution: Dict[QueryPattern, float] = field(
        default_factory=lambda: {
            QueryPattern.DEEP_ANALYSIS: 0.3,
            QueryPattern.RAPID_EXPLORATION: 0.3,
            QueryPattern.REFERENCE_LOOKUP: 0.2,
            QueryPattern.SYNTHESIS: 0.1,
            QueryPattern.DEBUGGING: 0.1,
        }
    )

    # Domain distribution (varies by workspace type)
    domain_distribution: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "workspace_id": self.workspace_id,
            "workspace_type": self.workspace_type.value,
            "description": self.description,
            "duration_hours": self.duration_hours,
            "num_queries": self.num_queries,
            "base_memory_count": self.base_memory_count,
            "memory_growth_rate": self.memory_growth_rate,
            "query_pattern_distribution": {
                k.value: v for k, v in self.query_pattern_distribution.items()
            },
            "domain_distribution": self.domain_distribution,
        }


@dataclass
class WorkspaceExecutionResult:
    """Result of simulated workspace execution."""

    run_id: str
    workspace: SimulatedWorkspace
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Execution metrics
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    # Quality metrics
    avg_query_quality: float = 0.0
    quality_degradation_over_time: List[float] = field(default_factory=list)

    # Memory metrics
    memory_pool_size_evolution: List[int] = field(default_factory=list)
    domain_coverage_evolution: List[Dict[str, float]] = field(default_factory=list)
    avg_memory_relevance: float = 0.0

    # Workspace-specific insights
    query_pattern_success_rates: Dict[str, float] = field(default_factory=dict)
    domain_specific_degradation: Dict[str, float] = field(default_factory=dict)
    compression_effectiveness_over_time: List[float] = field(default_factory=list)

    # Overall assessment
    workspace_stability_score: float = 0.0  # 0-100
    cognitive_continuity_score: float = 0.0  # 0-100
    sustained_productivity_score: float = 0.0  # 0-100

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "workspace": self.workspace.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "success_rate": (
                self.successful_queries / self.total_queries
                if self.total_queries > 0
                else 0.0
            ),
            "avg_query_quality": self.avg_query_quality,
            "avg_memory_relevance": self.avg_memory_relevance,
            "query_pattern_success_rates": self.query_pattern_success_rates,
            "domain_specific_degradation": self.domain_specific_degradation,
            "workspace_stability_score": self.workspace_stability_score,
            "cognitive_continuity_score": self.cognitive_continuity_score,
            "sustained_productivity_score": self.sustained_productivity_score,
        }


class WorkspaceSimulator:
    """
    Simulates realistic long-running workspace environments.

    Generates:
    - Realistic query patterns for different workspace types
    - Memory pools that grow and evolve
    - Domain-specific query distributions
    - Long-horizon quality and semantic degradation signatures
    """

    def __init__(self):
        """Initialize workspace simulator."""
        self.execution_results: List[WorkspaceExecutionResult] = []
        logger.info("Workspace Simulator initialized")

    def create_research_workspace(
        self,
        duration_hours: int = 24,
        num_queries: int = 100,
    ) -> SimulatedWorkspace:
        """
        Create a research project workspace.

        Characteristics:
        - Heavy synthesis queries
        - Literature/reference domain
        - Gradual understanding buildup
        - Higher semantic retention needs
        """
        return SimulatedWorkspace(
            workspace_id="ws-research-" + self._generate_id(),
            workspace_type=WorkspaceType.RESEARCH,
            description="Research project workspace with literature review and analysis",
            duration_hours=duration_hours,
            num_queries=num_queries,
            base_memory_count=400,
            memory_growth_rate=0.15,
            query_pattern_distribution={
                QueryPattern.DEEP_ANALYSIS: 0.4,
                QueryPattern.SYNTHESIS: 0.3,
                QueryPattern.REFERENCE_LOOKUP: 0.2,
                QueryPattern.RAPID_EXPLORATION: 0.1,
                QueryPattern.DEBUGGING: 0.0,
            },
            domain_distribution={
                "literature": 0.4,
                "hypothesis": 0.3,
                "methodology": 0.2,
                "data": 0.1,
            },
        )

    def create_software_engineering_workspace(
        self,
        duration_hours: int = 24,
        num_queries: int = 150,
    ) -> SimulatedWorkspace:
        """
        Create a software engineering workspace.

        Characteristics:
        - Mixed debugging and rapid exploration
        - Code/architecture domain
        - Fast context switching
        - High query volume
        """
        return SimulatedWorkspace(
            workspace_id="ws-eng-" + self._generate_id(),
            workspace_type=WorkspaceType.SOFTWARE_ENGINEERING,
            description="Software engineering workspace with code exploration and debugging",
            duration_hours=duration_hours,
            num_queries=num_queries,
            base_memory_count=600,
            memory_growth_rate=0.2,
            query_pattern_distribution={
                QueryPattern.RAPID_EXPLORATION: 0.4,
                QueryPattern.DEBUGGING: 0.3,
                QueryPattern.REFERENCE_LOOKUP: 0.2,
                QueryPattern.SYNTHESIS: 0.1,
                QueryPattern.DEEP_ANALYSIS: 0.0,
            },
            domain_distribution={
                "code": 0.5,
                "architecture": 0.2,
                "dependencies": 0.15,
                "tests": 0.1,
                "deployment": 0.05,
            },
        )

    def create_startup_planning_workspace(
        self,
        duration_hours: int = 48,
        num_queries: int = 120,
    ) -> SimulatedWorkspace:
        """
        Create a startup planning workspace.

        Characteristics:
        - Heavy synthesis and strategy
        - Multiple business domains
        - Longer deliberation periods
        - Integration across domains
        """
        return SimulatedWorkspace(
            workspace_id="ws-startup-" + self._generate_id(),
            workspace_type=WorkspaceType.STARTUP_PLANNING,
            description="Startup planning workspace with market research and strategy",
            duration_hours=duration_hours,
            num_queries=num_queries,
            base_memory_count=700,
            memory_growth_rate=0.12,
            query_pattern_distribution={
                QueryPattern.SYNTHESIS: 0.35,
                QueryPattern.DEEP_ANALYSIS: 0.3,
                QueryPattern.REFERENCE_LOOKUP: 0.2,
                QueryPattern.RAPID_EXPLORATION: 0.15,
                QueryPattern.DEBUGGING: 0.0,
            },
            domain_distribution={
                "market": 0.25,
                "business_model": 0.25,
                "technology": 0.2,
                "funding": 0.15,
                "pitch": 0.15,
            },
        )

    def create_document_heavy_workspace(
        self,
        duration_hours: int = 72,
        num_queries: int = 200,
    ) -> SimulatedWorkspace:
        """
        Create a document-heavy workspace.

        Characteristics:
        - Large memory pools
        - Reference-heavy queries
        - Long session durations
        - High compression pressure
        """
        return SimulatedWorkspace(
            workspace_id="ws-doc-" + self._generate_id(),
            workspace_type=WorkspaceType.DOCUMENT_HEAVY,
            description="Document-heavy workspace with large knowledge bases",
            duration_hours=duration_hours,
            num_queries=num_queries,
            base_memory_count=1200,
            memory_growth_rate=0.25,
            query_pattern_distribution={
                QueryPattern.REFERENCE_LOOKUP: 0.4,
                QueryPattern.RAPID_EXPLORATION: 0.3,
                QueryPattern.SYNTHESIS: 0.2,
                QueryPattern.DEEP_ANALYSIS: 0.1,
                QueryPattern.DEBUGGING: 0.0,
            },
            domain_distribution={
                "documents": 0.4,
                "references": 0.3,
                "summaries": 0.2,
                "indexes": 0.1,
            },
        )

    def simulate_workspace(
        self, workspace: SimulatedWorkspace
    ) -> WorkspaceExecutionResult:
        """
        Simulate a workspace execution.

        Args:
            workspace: Workspace definition to simulate

        Returns:
            WorkspaceExecutionResult with execution metrics
        """
        run_id = f"ws-exec-{workspace.workspace_id[:12]}"
        result = WorkspaceExecutionResult(
            run_id=run_id,
            workspace=workspace,
        )

        logger.info(
            f"Starting workspace simulation {run_id}: "
            f"{workspace.workspace_type.value} ({workspace.num_queries} queries)"
        )

        # Initialize memory pool
        memory_pool = self._generate_memory_pool(
            workspace.base_memory_count, workspace.domain_distribution
        )

        # Simulate queries over time
        quality_scores = []
        memory_relevances = []
        query_successes = {pattern.value: [] for pattern in QueryPattern}

        for query_idx in range(workspace.num_queries):
            # Generate query based on patterns
            query = self._generate_query(workspace, query_idx, len(memory_pool))

            # Simulate query execution
            success = random.random() > 0.05  # 95% success rate baseline
            result.total_queries += 1

            if success:
                result.successful_queries += 1

                # Simulate quality degradation over time
                degradation_factor = query_idx / workspace.num_queries
                quality = max(0.5, 1.0 - (degradation_factor * 0.3))
                quality_scores.append(quality)

                # Simulate memory relevance
                relevance = random.uniform(0.6, 1.0)
                memory_relevances.append(relevance)

                # Track by pattern
                query_successes[query.pattern.value].append(quality)

                # Grow memory pool based on query type
                if query.pattern == QueryPattern.DEEP_ANALYSIS:
                    growth = int(len(memory_pool) * 0.02)
                    memory_pool.extend(
                        self._generate_memory_pool(
                            growth, workspace.domain_distribution
                        )
                    )

                # Record evolution
                result.memory_pool_size_evolution.append(len(memory_pool))
                result.compression_effectiveness_over_time.append(
                    random.uniform(0.75, 0.95)
                )

            else:
                result.failed_queries += 1

        # Calculate statistics
        if quality_scores:
            result.avg_query_quality = sum(quality_scores) / len(quality_scores)
            quality_degradation = quality_scores[0] - (
                quality_scores[-1] if quality_scores else 0
            )
            result.quality_degradation_over_time = quality_scores

        if memory_relevances:
            result.avg_memory_relevance = sum(memory_relevances) / len(
                memory_relevances
            )

        # Calculate pattern success rates
        for pattern, successes in query_successes.items():
            if successes:
                result.query_pattern_success_rates[pattern] = sum(successes) / len(
                    successes
                )

        # Calculate domain-specific degradation
        result.domain_specific_degradation = {
            domain: random.uniform(0.05, 0.25)
            for domain in workspace.domain_distribution.keys()
        }

        # Calculate overall scores
        result.workspace_stability_score = (
            result.successful_queries / result.total_queries * 100
            if result.total_queries > 0
            else 0.0
        )
        result.cognitive_continuity_score = result.avg_query_quality * 100
        result.sustained_productivity_score = result.avg_memory_relevance * 100

        self.execution_results.append(result)
        logger.info(
            f"Workspace simulation {run_id} completed: "
            f"{result.successful_queries}/{result.total_queries} successful"
        )

        return result

    def _generate_id(self, length: int = 8) -> str:
        """Generate a random ID."""
        import uuid

        return str(uuid.uuid4())[:length]

    def _generate_memory_pool(
        self, count: int, domain_distribution: Dict[str, float]
    ) -> List[WorkspaceMemory]:
        """Generate a pool of workspace memories."""
        memories = []
        for i in range(count):
            # Select domain based on distribution
            domain = random.choices(
                list(domain_distribution.keys()),
                weights=list(domain_distribution.values()),
                k=1,
            )[0]

            memory = WorkspaceMemory(
                memory_id=f"mem-{i:06d}",
                content=f"Memory content for {domain}",
                domain=domain,
                importance=random.uniform(0.3, 1.0),
            )
            memories.append(memory)

        return memories

    def _generate_query(
        self,
        workspace: SimulatedWorkspace,
        query_idx: int,
        memory_pool_size: int,
    ) -> WorkspaceQuery:
        """Generate a query based on workspace patterns."""
        # Select pattern based on distribution
        pattern = random.choices(
            list(workspace.query_pattern_distribution.keys()),
            weights=list(workspace.query_pattern_distribution.values()),
            k=1,
        )[0]

        # Select domain based on distribution
        domain = random.choices(
            list(workspace.domain_distribution.keys()),
            weights=list(workspace.domain_distribution.values()),
            k=1,
        )[0]

        # Determine complexity
        if pattern == QueryPattern.DEEP_ANALYSIS:
            complexity = "very_complex"
            num_memories = int(memory_pool_size * 0.3)
        elif pattern == QueryPattern.SYNTHESIS:
            complexity = "complex"
            num_memories = int(memory_pool_size * 0.25)
        elif pattern == QueryPattern.RAPID_EXPLORATION:
            complexity = "moderate"
            num_memories = int(memory_pool_size * 0.15)
        elif pattern == QueryPattern.REFERENCE_LOOKUP:
            complexity = "simple"
            num_memories = int(memory_pool_size * 0.05)
        else:  # DEBUGGING
            complexity = "moderate"
            num_memories = int(memory_pool_size * 0.1)

        return WorkspaceQuery(
            query_id=f"q-{query_idx:06d}",
            query_text=f"Query about {domain}",
            pattern=pattern,
            domain=domain,
            complexity_level=complexity,
            num_memories_needed=num_memories,
        )

    def get_workspace_statistics(self) -> Dict[str, Any]:
        """Get statistics across all simulated workspaces."""
        if not self.execution_results:
            return {}

        total_queries = sum(r.total_queries for r in self.execution_results)
        total_successful = sum(r.successful_queries for r in self.execution_results)

        return {
            "total_simulations": len(self.execution_results),
            "total_queries": total_queries,
            "total_successful": total_successful,
            "overall_success_rate": (
                total_successful / total_queries if total_queries > 0 else 0.0
            ),
            "avg_workspace_stability": (
                sum(r.workspace_stability_score for r in self.execution_results)
                / len(self.execution_results)
                if self.execution_results
                else 0.0
            ),
            "avg_cognitive_continuity": (
                sum(r.cognitive_continuity_score for r in self.execution_results)
                / len(self.execution_results)
                if self.execution_results
                else 0.0
            ),
            "avg_sustained_productivity": (
                sum(r.sustained_productivity_score for r in self.execution_results)
                / len(self.execution_results)
                if self.execution_results
                else 0.0
            ),
        }


# Global simulator instance
_workspace_simulator: Optional[WorkspaceSimulator] = None


def get_workspace_simulator() -> WorkspaceSimulator:
    """Get or create the global workspace simulator."""
    global _workspace_simulator
    if _workspace_simulator is None:
        _workspace_simulator = WorkspaceSimulator()
    return _workspace_simulator
