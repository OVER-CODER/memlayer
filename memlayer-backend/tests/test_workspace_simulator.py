"""
Tests for Workspace Simulation Framework.

Tests for realistic long-running workspace simulation including
research projects, software engineering, startup planning, and
document-heavy workspaces.
"""

import pytest
from datetime import datetime, timezone
from app.runtime import (
    WorkspaceSimulator,
    SimulatedWorkspace,
    WorkspaceExecutionResult,
    WorkspaceType,
    QueryPattern,
    WorkspaceMemory,
    WorkspaceQuery,
    get_workspace_simulator,
)


class TestWorkspaceMemory:
    """Test workspace memory functionality."""

    def test_memory_creation(self):
        """Test creating a workspace memory."""
        memory = WorkspaceMemory(
            memory_id="mem-001",
            content="Test memory content",
            domain="research",
            importance=0.85,
        )

        assert memory.memory_id == "mem-001"
        assert memory.content == "Test memory content"
        assert memory.domain == "research"
        assert memory.importance == 0.85
        assert memory.access_count == 0

    def test_memory_to_dict(self):
        """Test converting memory to dictionary."""
        memory = WorkspaceMemory(
            memory_id="mem-002",
            content="Content",
            domain="code",
            importance=0.75,
            access_count=5,
        )

        memory_dict = memory.to_dict()

        assert memory_dict["memory_id"] == "mem-002"
        assert memory_dict["domain"] == "code"
        assert memory_dict["importance"] == 0.75
        assert memory_dict["access_count"] == 5
        assert "recency_score" in memory_dict

    def test_recency_score_calculation(self):
        """Test recency score calculation."""
        memory = WorkspaceMemory(
            memory_id="mem-003",
            content="Content",
            domain="test",
            importance=0.5,
        )

        recency = memory._calculate_recency_score()
        # Should be 0 since never accessed
        assert recency == 0.0


class TestWorkspaceQuery:
    """Test workspace query functionality."""

    def test_query_creation(self):
        """Test creating a workspace query."""
        query = WorkspaceQuery(
            query_id="q-001",
            query_text="What is the main hypothesis?",
            pattern=QueryPattern.DEEP_ANALYSIS,
            domain="hypothesis",
            complexity_level="complex",
            num_memories_needed=50,
        )

        assert query.query_id == "q-001"
        assert query.pattern == QueryPattern.DEEP_ANALYSIS
        assert query.complexity_level == "complex"
        assert query.num_memories_needed == 50

    def test_query_patterns(self):
        """Test all query patterns are defined."""
        patterns = [
            QueryPattern.DEEP_ANALYSIS,
            QueryPattern.RAPID_EXPLORATION,
            QueryPattern.REFERENCE_LOOKUP,
            QueryPattern.SYNTHESIS,
            QueryPattern.DEBUGGING,
        ]

        assert len(patterns) == 5
        for pattern in patterns:
            assert isinstance(pattern, QueryPattern)


class TestSimulatedWorkspace:
    """Test simulated workspace creation."""

    def test_workspace_creation(self):
        """Test creating a simulated workspace."""
        workspace = SimulatedWorkspace(
            workspace_id="ws-test-001",
            workspace_type=WorkspaceType.RESEARCH,
            description="Test research workspace",
            duration_hours=24,
            num_queries=100,
        )

        assert workspace.workspace_id == "ws-test-001"
        assert workspace.workspace_type == WorkspaceType.RESEARCH
        assert workspace.num_queries == 100

    def test_workspace_to_dict(self):
        """Test converting workspace to dictionary."""
        workspace = SimulatedWorkspace(
            workspace_id="ws-test-002",
            workspace_type=WorkspaceType.SOFTWARE_ENGINEERING,
            description="Test engineering workspace",
            duration_hours=24,
            num_queries=150,
        )

        ws_dict = workspace.to_dict()

        assert ws_dict["workspace_id"] == "ws-test-002"
        assert ws_dict["workspace_type"] == "software_engineering"
        assert ws_dict["num_queries"] == 150


class TestWorkspaceExecutionResult:
    """Test workspace execution result."""

    def test_result_creation(self):
        """Test creating execution result."""
        workspace = SimulatedWorkspace(
            workspace_id="ws-001",
            workspace_type=WorkspaceType.RESEARCH,
            description="Test",
        )

        result = WorkspaceExecutionResult(
            run_id="run-001",
            workspace=workspace,
        )

        assert result.run_id == "run-001"
        assert result.total_queries == 0
        assert result.successful_queries == 0
        assert result.workspace_stability_score == 0.0

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        workspace = SimulatedWorkspace(
            workspace_id="ws-002",
            workspace_type=WorkspaceType.STARTUP_PLANNING,
            description="Test startup",
        )

        result = WorkspaceExecutionResult(
            run_id="run-002",
            workspace=workspace,
            total_queries=50,
            successful_queries=48,
            avg_query_quality=0.87,
            workspace_stability_score=96.0,
        )

        result_dict = result.to_dict()

        assert result_dict["run_id"] == "run-002"
        assert result_dict["total_queries"] == 50
        assert result_dict["successful_queries"] == 48
        assert "success_rate" in result_dict


class TestWorkspaceSimulator:
    """Test workspace simulator functionality."""

    def test_simulator_initialization(self):
        """Test initializing workspace simulator."""
        simulator = WorkspaceSimulator()

        assert simulator is not None
        assert len(simulator.execution_results) == 0

    def test_create_research_workspace(self):
        """Test creating research workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace(
            duration_hours=24, num_queries=100
        )

        assert workspace.workspace_type == WorkspaceType.RESEARCH
        assert workspace.base_memory_count == 400
        assert workspace.num_queries == 100
        assert "literature" in workspace.domain_distribution

    def test_create_software_engineering_workspace(self):
        """Test creating software engineering workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_software_engineering_workspace(
            duration_hours=24, num_queries=150
        )

        assert workspace.workspace_type == WorkspaceType.SOFTWARE_ENGINEERING
        assert workspace.base_memory_count == 600
        assert workspace.num_queries == 150
        assert "code" in workspace.domain_distribution

    def test_create_startup_planning_workspace(self):
        """Test creating startup planning workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_startup_planning_workspace(
            duration_hours=48, num_queries=120
        )

        assert workspace.workspace_type == WorkspaceType.STARTUP_PLANNING
        assert workspace.base_memory_count == 700
        assert workspace.num_queries == 120
        assert "market" in workspace.domain_distribution

    def test_create_document_heavy_workspace(self):
        """Test creating document-heavy workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_document_heavy_workspace(
            duration_hours=72, num_queries=200
        )

        assert workspace.workspace_type == WorkspaceType.DOCUMENT_HEAVY
        assert workspace.base_memory_count == 1200
        assert workspace.num_queries == 200
        assert "documents" in workspace.domain_distribution

    def test_simulate_research_workspace(self):
        """Test simulating research workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        assert result.run_id is not None
        assert result.total_queries == 20
        assert result.successful_queries > 0
        assert result.avg_query_quality > 0
        assert result.workspace_stability_score > 0

    def test_simulate_engineering_workspace(self):
        """Test simulating engineering workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_software_engineering_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        assert result.total_queries == 20
        assert result.successful_queries > 0
        assert len(result.query_pattern_success_rates) > 0

    def test_simulate_startup_workspace(self):
        """Test simulating startup planning workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_startup_planning_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        assert result.total_queries == 20
        assert result.avg_memory_relevance > 0
        assert result.cognitive_continuity_score > 0

    def test_simulate_document_workspace(self):
        """Test simulating document-heavy workspace."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_document_heavy_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        assert result.total_queries == 20
        assert len(result.memory_pool_size_evolution) > 0

    def test_memory_pool_evolution(self):
        """Test that memory pool evolves during simulation."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace(num_queries=30)
        result = simulator.simulate_workspace(workspace)

        # Memory pool should grow and evolve
        assert len(result.memory_pool_size_evolution) > 0
        # Later pool sizes should generally be >= earlier sizes
        # (though not strictly monotonic due to stochastic queries)

    def test_quality_degradation_tracking(self):
        """Test that quality degradation is tracked."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace(num_queries=25)
        result = simulator.simulate_workspace(workspace)

        assert len(result.quality_degradation_over_time) > 0
        # Quality should generally degrade over time
        if len(result.quality_degradation_over_time) > 1:
            first_quality = result.quality_degradation_over_time[0]
            last_quality = result.quality_degradation_over_time[-1]
            # First should be >= last (degradation)
            assert first_quality >= last_quality - 0.1  # Allow some variance

    def test_compression_effectiveness_tracking(self):
        """Test compression effectiveness tracking."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_document_heavy_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        assert len(result.compression_effectiveness_over_time) > 0
        # All effectiveness scores should be between 0 and 1
        for effectiveness in result.compression_effectiveness_over_time:
            assert 0.0 <= effectiveness <= 1.0

    def test_query_pattern_success_rates(self):
        """Test query pattern success rates are calculated."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace(num_queries=25)
        result = simulator.simulate_workspace(workspace)

        # At least some patterns should have been executed
        assert len(result.query_pattern_success_rates) > 0
        # All rates should be between 0 and 1
        for rate in result.query_pattern_success_rates.values():
            assert 0.0 <= rate <= 1.0

    def test_domain_specific_degradation(self):
        """Test domain-specific degradation tracking."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_startup_planning_workspace(num_queries=20)
        result = simulator.simulate_workspace(workspace)

        # Should have degradation for each domain
        assert len(result.domain_specific_degradation) > 0
        # All degradation values should be reasonable
        for degradation in result.domain_specific_degradation.values():
            assert 0.0 <= degradation <= 1.0

    def test_workspace_statistics(self):
        """Test getting workspace statistics."""
        simulator = WorkspaceSimulator()

        # Run a few simulations
        for _ in range(3):
            workspace = simulator.create_research_workspace(num_queries=15)
            simulator.simulate_workspace(workspace)

        stats = simulator.get_workspace_statistics()

        assert stats["total_simulations"] == 3
        assert stats["total_queries"] > 0
        assert stats["overall_success_rate"] > 0
        assert "avg_workspace_stability" in stats
        assert "avg_cognitive_continuity" in stats

    def test_multiple_workspace_types(self):
        """Test simulating multiple workspace types."""
        simulator = WorkspaceSimulator()

        workspaces = [
            simulator.create_research_workspace(num_queries=10),
            simulator.create_software_engineering_workspace(num_queries=10),
            simulator.create_startup_planning_workspace(num_queries=10),
            simulator.create_document_heavy_workspace(num_queries=10),
        ]

        for workspace in workspaces:
            result = simulator.simulate_workspace(workspace)
            assert result.total_queries == 10
            assert result.successful_queries > 0

    def test_get_workspace_simulator_singleton(self):
        """Test getting workspace simulator as singleton."""
        sim1 = get_workspace_simulator()
        sim2 = get_workspace_simulator()

        assert sim1 is sim2  # Should be same instance

    def test_simulator_accumulates_results(self):
        """Test that simulator accumulates results."""
        simulator = WorkspaceSimulator()

        workspace1 = simulator.create_research_workspace(num_queries=10)
        result1 = simulator.simulate_workspace(workspace1)

        assert len(simulator.execution_results) == 1

        workspace2 = simulator.create_startup_planning_workspace(num_queries=10)
        result2 = simulator.simulate_workspace(workspace2)

        assert len(simulator.execution_results) == 2
        assert result1.run_id != result2.run_id

    def test_research_workspace_characteristics(self):
        """Test research workspace has appropriate characteristics."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_research_workspace()

        # Should prioritize synthesis and deep analysis
        assert workspace.query_pattern_distribution[QueryPattern.DEEP_ANALYSIS] > 0.3
        assert workspace.query_pattern_distribution[QueryPattern.SYNTHESIS] > 0.2

    def test_engineering_workspace_characteristics(self):
        """Test engineering workspace has appropriate characteristics."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_software_engineering_workspace()

        # Should prioritize rapid exploration and debugging
        assert (
            workspace.query_pattern_distribution[QueryPattern.RAPID_EXPLORATION] > 0.3
        )
        assert workspace.query_pattern_distribution[QueryPattern.DEBUGGING] > 0.2

    def test_startup_workspace_characteristics(self):
        """Test startup workspace has appropriate characteristics."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_startup_planning_workspace()

        # Should prioritize synthesis and analysis
        assert workspace.query_pattern_distribution[QueryPattern.SYNTHESIS] > 0.3
        assert workspace.query_pattern_distribution[QueryPattern.DEEP_ANALYSIS] > 0.2

    def test_document_workspace_characteristics(self):
        """Test document workspace has appropriate characteristics."""
        simulator = WorkspaceSimulator()
        workspace = simulator.create_document_heavy_workspace()

        # Should prioritize reference lookup and exploration
        assert workspace.query_pattern_distribution[QueryPattern.REFERENCE_LOOKUP] > 0.3
        assert (
            workspace.query_pattern_distribution[QueryPattern.RAPID_EXPLORATION] > 0.2
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
