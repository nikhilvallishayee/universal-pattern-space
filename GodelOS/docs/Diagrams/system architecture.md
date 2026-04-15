``` mermaid 
---
config:
  look: neo
  theme: neo-dark
---
classDiagram
    namespace Backend_Config {
        class Settings {
            <<backend/config.py>>
            +config_data: dict
            +load_config() dict
            +save_config(data) void
            +get(key) Any
            +set(key, value) void
        }
    }
    namespace Backend_Core {
        class CognitiveManager {
            <<backend/core/cognitive_manager.py>>
            -consciousness_engine: ConsciousnessEngine
            -llm_driver: LLMCognitiveDriver
            -websocket_manager: WebSocketManager
            -knowledge_graph: KnowledgeGraphEvolution
            -metacognitive_monitor: MetaCognitiveMonitor
            -phenomenal_generator: PhenomenalExperienceGenerator
            +process_query(query: str) dict
            +assess_consciousness(context: dict) dict
            +integrate_knowledge(data: dict) void
            +stream_cognitive_event(event: CognitiveEvent) void
            +monitor_metacognition() dict
            +generate_phenomenal_experience(stimulus: dict) dict
        }
        class ConsciousnessEngine {
            <<backend/core/consciousness_engine.py>>
            -llm_driver: LLMCognitiveDriver
            -metrics_collector: MetricsCollector
            -assessment_history: list
            +assess_consciousness_state(context: dict) dict
            +evaluate_awareness_level() float
            +analyze_self_reflection() int
            +identify_autonomous_goals() list
            +measure_cognitive_integration() float
            +get_consciousness_metrics() dict
        }
        class MetaCognitiveMonitor {
            <<backend/core/metacognitive_monitor.py>>
            -monitoring_state: dict
            -reflection_depth: int
            -cognitive_metrics: dict
            +monitor_cognitive_processes() dict
            +analyze_thinking_patterns() dict
            +evaluate_reasoning_quality() float
            +generate_self_reflection() dict
            +track_cognitive_evolution() list
            +assess_metacognitive_awareness() float
        }
        class PhenomenalExperienceGenerator {
            <<backend/core/phenomenal_experience.py>>
            -experience_history: list
            -qualia_patterns: dict
            -experience_cache: dict
            +generate_experience(stimulus: dict) dict
            +analyze_qualia(experience: dict) dict
            +integrate_phenomenal_data(data: dict) void
            +report_subjective_state() dict
            +track_experience_evolution() list
        }
        class CognitiveEvent {
            <<backend/core/cognitive_transparency.py>>
            +event_type: str
            +timestamp: float
            +data: dict
            +source: str
            +metadata: dict
            +process() dict
            +serialize() dict
            +validate() bool
        }
        class MetricsCollector {
            <<backend/core/enhanced_metrics.py>>
            -metrics: dict
            -history: list
            -aggregations: dict
            +collect_metric(name: str, value: float) void
            +get_metric(name: str) float
            +get_all_metrics() dict
            +compute_statistics() dict
            +export_metrics() dict
            +reset_metrics() void
        }
        class WebSocketManager {
            <<backend/core/enhanced_websocket_manager.py>>
            -active_connections: list~WebSocket~
            -event_queue: Queue
            -connection_metadata: dict
            +connect(websocket: WebSocket) void
            +disconnect(websocket: WebSocket) void
            +broadcast_cognitive_event(event_type: str, data: dict) void
            +broadcast_consciousness_update(state: dict) void
            +send_personal_message(message: str, websocket: WebSocket) void
            +get_active_connections_count() int
        }
        class ValidationError {
            <<backend/core/errors.py>>
            +message: str
            +field: str
            +value: Any
            +get_error_details() dict
        }
    }
    namespace Backend_Knowledge {
        class KnowledgeGraphEvolution {
            <<backend/core/knowledge_graph_evolution.py>>
            -graph: dict
            -vector_store: VectorStore
            -evolution_history: list
            -nodes: dict
            -edges: list
            +evolve_graph(trigger: str, context: dict) dict
            +add_node(node_data: dict) void
            +add_edge(source: str, target: str, relation: str) void
            +query_graph(query: str) list
            +analyze_structure() dict
            +get_subgraph(node_id: str, depth: int) dict
        }
        class KnowledgePipelineService {
            <<backend/knowledge_pipeline_service.py>>
            -pipeline_stages: list
            -processors: dict
            -knowledge_graph: KnowledgeGraphEvolution
            +process_knowledge(data: dict) dict
            +add_pipeline_stage(stage: Callable) void
            +execute_pipeline(input: dict) dict
            +validate_knowledge(knowledge: dict) bool
        }
        class EmbeddingModel {
            <<backend/core/vector_database.py>>
            -model_name: str
            -dimension: int
            -cache: dict
            +embed_text(text: str) ndarray
            +embed_batch(texts: list) list
            +get_dimension() int
        }
        class ClusterManager {
            <<backend/core/distributed_vector_search.py>>
            -clusters: dict
            -nodes: list
            -load_balancer: Any
            +add_cluster(cluster_id: str, config: dict) void
            +distribute_query(query: dict) list
            +balance_load() void
            +health_check() dict
        }
    }
    namespace Backend_NLP {
        class NLSemanticParser {
            <<backend/core/nl_semantic_parser.py>>
            -inference_engine: InferenceEngine
            -ontology_manager: OntologyManager
            -entity_cache: dict
            +parse(text: str) dict
            +extract_semantics(text: str) dict
            +process_natural_language(input: str) dict
            +identify_entities(text: str) list
            +extract_relations(text: str) list
            +resolve_references(text: str) dict
        }
        class InferenceEngine {
            <<backend/core/nl_semantic_parser.py>>
            -rules: list
            -knowledge_base: dict
            -inference_cache: dict
            +infer(facts: list) list
            +apply_rules(data: dict) dict
            +derive_conclusions(premises: list) list
            +validate_inference(conclusion: dict) bool
            +backward_chain(goal: dict) list
            +forward_chain(facts: list) list
        }
    }
    namespace Backend_LLM {
        class LLMCognitiveDriver {
            <<backend/llm_cognitive_driver.py>>
            -api_key: str
            -model: str
            -client: OpenAI
            -temperature: float
            +generate_consciousness_assessment(context: dict) dict
            +process_cognitive_query(query: str) str
            +analyze_phenomenal_experience(data: dict) dict
            +stream_thought_process() AsyncIterator
            +chat_completion(messages: list) dict
        }
        class ToolResult {
            <<backend/llm_tool_integration.py>>
            +success: bool
            +result: Any
            +error: str
            +metadata: dict
            +execution_time: float
        }
    }
    namespace Backend_Models {
        class QueryRequest {
            <<backend/models.py>>
            +query: str
            +context: dict
            +parameters: dict
            +timestamp: float
            +validate() bool
        }
        class QueryResponse {
            <<backend/models.py>>
            +result: str
            +confidence: float
            +metadata: dict
            +processing_time: float
            +sources: list
        }
        class WebSocketMessage {
            <<backend/models.py>>
            +type: str
            +data: dict
            +timestamp: float
            +sender: str
            +priority: int
            +validate() bool
            +to_json() str
        }
        class KnowledgeGraphRequest {
            <<backend/cognitive_transparency_integration.py>>
            +query: str
            +depth: int
            +filters: dict
            +include_metadata: bool
        }
        class KnowledgeGraphResponse {
            <<backend/api/unified_api.py>>
            +nodes: list
            +edges: list
            +metadata: dict
            +query_context: dict
        }
        class ResponseFormatter {
            <<backend/response_formatter.py>>
            -format_type: str
            -templates: dict
            +format_response(data: dict) str
            +apply_template(template: str, data: dict) str
            +validate_format(response: str) bool
        }
    }
    namespace Core_Agent {
        class UnifiedAgentCore {
            <<godelOS/unified_agent_core/core.py>>
            -cognitive_engine: CognitiveEngine
            -memory_manager: MemoryManager
            -performance_monitor: PerformanceMonitor
            -interaction_engine: InteractionEngine
            +initialize() void
            +process_input(input: dict) dict
            +execute_action(action: dict) dict
            +shutdown() void
            +get_status() dict
        }
        class CognitiveEngine {
            <<godelOS/unified_agent_core/cognitive_engine/engine.py>>
            -thought_stream: ThoughtStream
            -reasoning_state: dict
            -decision_history: list
            +process_thought(thought: dict) dict
            +reason(context: dict) dict
            +decide(options: list) dict
            +plan(goal: dict) list
            +execute_plan(plan: list) dict
            +reflect(experience: dict) dict
        }
        class ThoughtStream {
            <<godelOS/unified_agent_core/cognitive_engine/thought_stream.py>>
            -stream: list~CognitiveEvent~
            -current_thought: dict
            -stream_metadata: dict
            +add_thought(thought: dict) void
            +get_stream() list
            +process_stream() dict
            +filter_thoughts(criteria: dict) list
            +analyze_flow() dict
            +clear_stream() void
        }
        class InteractionEngine {
            <<godelOS/unified_agent_core/interaction_engine/engine.py>>
            -interfaces: list
            -handlers: dict
            -context: dict
            +process_interaction(input: dict) dict
            +register_interface(interface: Any) void
            +handle_request(request: dict) Response
        }
        class Response {
            <<godelOS/unified_agent_core/interaction_engine/interfaces.py>>
            +content: str
            +type: str
            +metadata: dict
            +timestamp: float
            +format() str
        }
    }
    namespace Core_Memory {
        class MemoryManager {
            <<godelOS/unified_agent_core/resource_manager/memory_manager.py>>
            -working_memory: WorkingMemory
            -episodic_memory: EpisodicMemory
            -semantic_memory: SemanticMemory
            -allocation_table: dict
            +allocate(size: int) bool
            +deallocate(reference: str) void
            +optimize() void
            +get_usage() dict
            +consolidate_memories() void
            +transfer_to_long_term(data: dict) void
        }
        class WorkingMemory {
            <<godelOS/unified_agent_core/knowledge_store/store.py>>
            -buffer: dict
            -capacity: int
            -current_load: int
            -access_history: list
            +store(key: str, value: Any) void
            +retrieve(key: str) Any
            +update(key: str, value: Any) void
            +clear() void
            +get_available_capacity() int
            +evict_least_used() void
        }
        class EpisodicMemory {
            <<godelOS/unified_agent_core/knowledge_store/episodic_memory.py>>
            -episodes: list
            -index: dict
            -temporal_index: dict
            +add_episode(episode: dict) void
            +recall_episode(query: dict) dict
            +search_episodes(criteria: dict) list
            +consolidate_episodes() void
            +prune_old_episodes() void
            +get_timeline() list
        }
        class SemanticMemory {
            <<godelOS/unified_agent_core/knowledge_store/semantic_memory.py>>
            -concepts: dict
            -semantic_network: dict
            -association_strengths: dict
            +add_concept(concept: dict) void
            +get_concept(name: str) dict
            +relate_concepts(c1: str, c2: str, relation: str) void
            +query_semantic_network(query: str) list
            +strengthen_association(c1: str, c2: str) void
            +spread_activation(seed: str) dict
        }
    }
    namespace Core_Monitoring {
        class PerformanceMonitor {
            <<godelOS/unified_agent_core/monitoring/performance_monitor.py>>
            -metrics_collector: MetricsCollector
            -thresholds: dict
            -alerts: list
            +monitor() dict
            +check_performance() bool
            +log_performance(data: dict) void
            +alert_on_threshold(metric: str) void
            +get_performance_report() dict
        }
    }
    namespace Core_Semantic {
        class VectorStore {
            <<godelOS/semantic_search/vector_store.py>>
            -vectors: dict
            -index: Any
            -dimension: int
            -metadata: dict
            +add_vector(id: str, vector: ndarray) void
            +search(query_vector: ndarray, k: int) list
            +delete_vector(id: str) void
            +update_vector(id: str, vector: ndarray) void
            +get_vector(id: str) ndarray
            +rebuild_index() void
        }
        class QueryEngine {
            <<godelOS/semantic_search/query_engine.py>>
            -vector_store: VectorStore
            -parser: NLSemanticParser
            -query_cache: dict
            +query(text: str) list
            +semantic_search(query: str) list
            +hybrid_search(query: str) list
            +rank_results(results: list) list
            +expand_query(query: str) str
        }
        class OntologyManager {
            <<godelOS/ontology/ontology_manager.py>>
            -ontology: dict
            -concepts: dict
            -relations: list
            -hierarchy: dict
            +load_ontology(path: str) void
            +query_ontology(query: str) dict
            +update_ontology(data: dict) void
            +get_concept(name: str) dict
            +add_relation(source: str, target: str, type: str) void
            +get_hierarchy() dict
        }
    }
    namespace Core_NLU_NLG {
        class Entity {
            <<godelOS/nlu_nlg/nlu/lexical_analyzer_parser.py>>
            +text: str
            +type: str
            +start: int
            +end: int
            +confidence: float
            +metadata: dict
        }
        class DialogueState {
            <<godelOS/nlu_nlg/nlu/discourse_manager.py>>
            -current_turn: int
            -history: list
            -context: dict
            -goals: list
            +update_state(input: dict) void
            +get_context() dict
            +track_turn() void
        }
    }
    namespace Core_Actions {
        class ActionExecutor {
            <<godelOS/symbol_grounding/action_executor.py>>
            -action_registry: dict
            -execution_context: dict
            +execute_action(action: dict) ToolResult
            +register_action(name: str, handler: Callable) void
            +validate_action(action: dict) bool
            +get_available_actions() list
        }
    }
    namespace Tests {
        class TestRunner {
            <<godelOS/test_runner/test_runner.py>>
            -test_suites: list
            -config: dict
            -results: dict
            +run_tests() dict
            +add_test_suite(suite: TestSuite) void
            +generate_report() dict
        }
        class TestSuite {
            <<backups/unified_test_runner_backup.py>>
            -tests: list
            -setup: Callable
            -teardown: Callable
            +add_test(test: Callable) void
            +run() dict
        }
    }
    CognitiveManager *-- "1" ConsciousnessEngine : owns
    CognitiveManager *-- "1" LLMCognitiveDriver : owns
    CognitiveManager *-- "1" WebSocketManager : owns
    CognitiveManager *-- "1" KnowledgeGraphEvolution : owns
    CognitiveManager *-- "1" MetaCognitiveMonitor : owns
    CognitiveManager *-- "1" PhenomenalExperienceGenerator : owns
    ConsciousnessEngine --> "1" LLMCognitiveDriver : uses
    ConsciousnessEngine --> "1" MetricsCollector : collects from
    WebSocketManager --> "0..*" WebSocketMessage : broadcasts
    KnowledgeGraphEvolution *-- "1" VectorStore : uses
    KnowledgePipelineService *-- "1" KnowledgeGraphEvolution : owns
    NLSemanticParser *-- "1" InferenceEngine : owns
    NLSemanticParser *-- "1" OntologyManager : owns
    InferenceEngine --> "1" OntologyManager : queries
    NLSemanticParser --> "0..*" Entity : extracts
    UnifiedAgentCore *-- "1" CognitiveEngine : owns
    UnifiedAgentCore *-- "1" MemoryManager : owns
    UnifiedAgentCore *-- "1" PerformanceMonitor : owns
    UnifiedAgentCore *-- "1" InteractionEngine : owns
    CognitiveEngine *-- "1" ThoughtStream : owns
    CognitiveEngine --> "1" NLSemanticParser : uses
    CognitiveEngine --> "1" MemoryManager : accesses
    ThoughtStream --> "0..*" CognitiveEvent : contains
    InteractionEngine --> "0..*" Response : generates
    MemoryManager *-- "1" WorkingMemory : manages
    MemoryManager *-- "1" EpisodicMemory : manages
    MemoryManager *-- "1" SemanticMemory : manages
    WorkingMemory o-- "0..*" Entity : stores
    EpisodicMemory o-- "0..*" CognitiveEvent : stores
    SemanticMemory o-- "0..*" Entity : stores
    QueryEngine *-- "1" VectorStore : owns
    QueryEngine *-- "1" NLSemanticParser : owns
    PerformanceMonitor *-- "1" MetricsCollector : owns
    ActionExecutor --> "0..*" ToolResult : produces
    ActionExecutor --> "0..*" Response : generates
    QueryRequest ..> QueryResponse : produces
    KnowledgeGraphRequest ..> KnowledgeGraphResponse : produces
    CognitiveManager ..> QueryRequest : processes
    CognitiveManager ..> QueryResponse : returns
    Settings ..> CognitiveManager : configures
    Settings ..> UnifiedAgentCore : configures
    Settings ..> ConsciousnessEngine : configures
    Settings ..> WebSocketManager : configures
    MetaCognitiveMonitor ..> CognitiveEngine : observes
    PhenomenalExperienceGenerator ..> CognitiveEvent : generates
    click Settings call linkCallback("/Users/oli/code/GodelOS/backend/config.py#L11")
    click CognitiveManager call linkCallback("/Users/oli/code/GodelOS/backend/core/cognitive_manager.py#L85")
    click ConsciousnessEngine call linkCallback("/Users/oli/code/GodelOS/backend/core/consciousness_engine.py#L62")
    click MetaCognitiveMonitor call linkCallback("/Users/oli/code/GodelOS/backend/core/metacognitive_monitor.py#L51")
    click PhenomenalExperienceGenerator call linkCallback("/Users/oli/code/GodelOS/backend/core/phenomenal_experience.py#L126")
    click CognitiveEvent call linkCallback("/Users/oli/code/GodelOS/backend/core/cognitive_transparency.py#L20")
    click MetricsCollector call linkCallback("/Users/oli/code/GodelOS/backend/core/enhanced_metrics.py#L91")
    click WebSocketManager call linkCallback("/Users/oli/code/GodelOS/backend/core/enhanced_websocket_manager.py#L25")
    click ValidationError call linkCallback("/Users/oli/code/GodelOS/backend/core/errors.py#L31")
    click KnowledgeGraphEvolution call linkCallback("/Users/oli/code/GodelOS/backend/core/knowledge_graph_evolution.py#L158")
    click KnowledgePipelineService call linkCallback("/Users/oli/code/GodelOS/backend/knowledge_pipeline_service.py#L26")
    click EmbeddingModel call linkCallback("/Users/oli/code/GodelOS/backend/core/vector_database.py#L69")
    click ClusterManager call linkCallback("/Users/oli/code/GodelOS/backend/core/distributed_vector_search.py#L202")
    click NLSemanticParser call linkCallback("/Users/oli/code/GodelOS/backend/core/nl_semantic_parser.py#L191")
    click InferenceEngine call linkCallback("/Users/oli/code/GodelOS/backend/core/nl_semantic_parser.py#L262")
    click LLMCognitiveDriver call linkCallback("/Users/oli/code/GodelOS/backend/llm_cognitive_driver.py#L41")
    click ToolResult call linkCallback("/Users/oli/code/GodelOS/backend/llm_tool_integration.py#L28")
    click QueryRequest call linkCallback("/Users/oli/code/GodelOS/backend/models.py#L19")
    click QueryResponse call linkCallback("/Users/oli/code/GodelOS/backend/models.py#L36")
    click WebSocketMessage call linkCallback("/Users/oli/code/GodelOS/backend/models.py#L229")
    click KnowledgeGraphRequest call linkCallback("/Users/oli/code/GodelOS/backend/cognitive_transparency_integration.py#L58")
    click KnowledgeGraphResponse call linkCallback("/Users/oli/code/GodelOS/backend/api/unified_api.py#L76")
    click ResponseFormatter call linkCallback("/Users/oli/code/GodelOS/backend/response_formatter.py#L13")
    click UnifiedAgentCore call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/core.py#L21")
    click CognitiveEngine call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/cognitive_engine/engine.py#L37")
    click ThoughtStream call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/cognitive_engine/thought_stream.py#L25")
    click InteractionEngine call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/interaction_engine/engine.py#L26")
    click Response call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/interaction_engine/interfaces.py#L46")
    click MemoryManager call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/resource_manager/memory_manager.py#L114")
    click WorkingMemory call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/knowledge_store/store.py#L437")
    click EpisodicMemory call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/knowledge_store/episodic_memory.py#L27")
    click SemanticMemory call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/knowledge_store/semantic_memory.py#L26")
    click PerformanceMonitor call linkCallback("/Users/oli/code/GodelOS/godelOS/unified_agent_core/monitoring/performance_monitor.py#L22")
    click VectorStore call linkCallback("/Users/oli/code/GodelOS/godelOS/semantic_search/vector_store.py#L12")
    click QueryEngine call linkCallback("/Users/oli/code/GodelOS/godelOS/semantic_search/query_engine.py#L17")
    click OntologyManager call linkCallback("/Users/oli/code/GodelOS/godelOS/ontology/ontology_manager.py#L14")
    click Entity call linkCallback("/Users/oli/code/GodelOS/godelOS/nlu_nlg/nlu/lexical_analyzer_parser.py#L98")
    click DialogueState call linkCallback("/Users/oli/code/GodelOS/godelOS/nlu_nlg/nlu/discourse_manager.py#L140")
    click ActionExecutor call linkCallback("/Users/oli/code/GodelOS/godelOS/symbol_grounding/action_executor.py#L94")
    click TestRunner call linkCallback("/Users/oli/code/GodelOS/godelOS/test_runner/test_runner.py#L28")
    click TestSuite call linkCallback("/Users/oli/code/GodelOS/backups/unified_test_runner_backup.py#L170")
```