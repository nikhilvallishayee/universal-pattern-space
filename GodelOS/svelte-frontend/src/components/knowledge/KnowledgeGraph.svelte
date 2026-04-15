<script>
  import { onMount, onDestroy } from 'svelte';
  import { knowledgeState } from '../../stores/cognitive.js';
  import { GödelOSAPI } from '../../utils/api.js';
  import * as d3 from 'd3';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  
  // Import our new advanced components
  import KnowledgeGraphAnalytics from './KnowledgeGraphAnalytics.svelte';
  import KnowledgeGraphPerformanceManager from './KnowledgeGraphPerformanceManager.svelte';
  import KnowledgeGraphCollaborativeManager from './KnowledgeGraphCollaborativeManager.svelte';
  
  let graphContainer;
  let controlsContainer;
  let width = 800;
  let height = 600;
  let svg;
  let simulation;
  let unsubscribe;
  
  // Graph data and state
  let graphData = { nodes: [], edges: [] };
  let selectedNode = null;
  let searchQuery = '';
  let layoutMode = '2d';
  let colorMode = 'category';
  let showLabels = true;
  let showEdgeLabels = true;
  let showOnlyStrongRelations = false;
  let showStatistics = true;
  let enableWordWrap = true;
  let linkStrength = 0.2;
  let chargeStrength = -400;
  let centerForce = 0.1;
  let collisionRadius = 35;
  let alphaDecay = 0.0228;
  let velocityDecay = 0.4;
  let nodeSize = 1.0;
  let linkDistance = 120;
  let loading = true;
  let error = null;
  let lastLoadTime = 0;
  let isLoading = false;
  let isRedrawing = false; // New state for redraw operations
  let parameterUpdateTimeout; // For debouncing parameter updates
  
  // Advanced features state
  let advancedMode = false;
  let performanceMode = true;
  let collaborativeMode = false;
  let analyticsVisible = true;
  let currentUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  let sessionId = null;
  
  // Advanced component references
  let analyticsComponent;
  let performanceManager;
  let collaborativeManager;
  
  // Three.js for 3D mode
  let scene, camera, renderer, controls3d;
  let nodeObjects = [];
  let edgeObjects = [];
  
  // Graph visualization modes
  const layoutModes = [
    { id: '2d', name: '2D Force', icon: '🕸️', description: 'Dynamic force-directed layout with natural clustering' },
    { id: '3d', name: '3D Network', icon: '🌐', description: 'Three-dimensional spatial visualization for complex relationships' },
    { id: 'hierarchical', name: 'Hierarchical', icon: '🌳', description: 'Tree-like structure showing clear parent-child relationships' },
    { id: 'circular', name: 'Circular', icon: '⭕', description: 'Circular arrangement emphasizing equal relationships' }
  ];
  
  const colorModes = [
    { id: 'category', name: 'By Category', icon: '🎨', description: 'Color nodes by semantic category type' },
    { id: 'importance', name: 'By Importance', icon: '⭐', description: 'Color intensity shows node importance and centrality' },
    { id: 'recency', name: 'By Recency', icon: '🕒', description: 'Warmer colors for recently updated content' },
    { id: 'confidence', name: 'By Confidence', icon: '🎯', description: 'Color depth reflects relationship confidence levels' }
  ];
  
  // Enhanced node categories with semantic analysis
  const nodeCategories = {
    // Core cognitive categories
    concept: { color: '#4CAF50', size: 8, icon: '💡', description: 'Core Concept' },
    entity: { color: '#2196F3', size: 6, icon: '🏷️', description: 'Named Entity' },
    document: { color: '#FF9800', size: 10, icon: '📄', description: 'Document' },
    relationship: { color: '#9C27B0', size: 4, icon: '🔗', description: 'Relationship' },
    topic: { color: '#00BCD4', size: 12, icon: '📚', description: 'Topic Area' },
    query: { color: '#F44336', size: 6, icon: '❓', description: 'Query' },
    principle: { color: '#8BC34A', size: 9, icon: '⚖️', description: 'Principle' },
    
    // Technical categories
    algorithm: { color: '#673AB7', size: 10, icon: '⚙️', description: 'Algorithm' },
    data_structure: { color: '#3F51B5', size: 8, icon: '🗂️', description: 'Data Structure' },
    mathematics: { color: '#E91E63', size: 9, icon: '🔢', description: 'Mathematical' },
    system: { color: '#607D8B', size: 11, icon: '🏗️', description: 'System' },
    programming: { color: '#795548', size: 7, icon: '💻', description: 'Programming' },
    security: { color: '#FF5722', size: 8, icon: '🔒', description: 'Security' }
  };
    
  // Enhanced semantic analysis functions
  function extractKeyPhrases(text) {
    if (!text) return [];
    
    // Clean the text first - remove UUIDs, file paths, and other noise
    let cleanedText = text
      .replace(/file-[a-f0-9-]{36}/gi, '') // Remove UUID patterns
      .replace(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, '') // Remove standalone UUIDs
      .replace(/\b(file|document|node|id|uuid)\b/gi, '') // Remove common noise words
      .replace(/https?:\/\/[^\s]+/gi, '') // Remove URLs
      .replace(/\/[^\s]+\.[a-z]{2,4}/gi, '') // Remove file paths
      .replace(/\.(pdf|txt|doc|docx|md|html|json|xml|py|js|ts|css)(?:\s|$)/gi, ' ') // Remove file extensions
      .replace(/[^\w\s.,!?;-]/g, ' ') // Keep only meaningful characters
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
    
    if (!cleanedText || cleanedText.length < 10) return [];
    
    // Enhanced stop words including technical noise
    const stopWords = new Set([
      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
      // Technical noise words
      'file', 'document', 'node', 'id', 'uuid', 'data', 'info', 'content', 'text', 'string', 'value', 'item', 'element', 'object', 'array', 'list'
    ]);
    
    // Extract meaningful phrases (2-4 words) and single important terms
    const phrases = [];
    const sentences = cleanedText.toLowerCase().split(/[.!?;]+/).filter(s => s.trim().length > 15);
    
    sentences.forEach(sentence => {
      const words = sentence.split(/\s+/)
        .filter(w => w.length > 2 && !stopWords.has(w))
        .filter(w => !/^\d+$/.test(w)) // Remove pure numbers
        .filter(w => !/-{2,}/.test(w)); // Remove multiple dashes
      
      // Extract single important terms (longer words only)
      words.forEach(word => {
        if (word.length > 5 && /^[a-z]+$/.test(word)) {
          phrases.push(word);
        }
      });
      
      // Extract 2-3 word phrases
      for (let i = 0; i < words.length - 1; i++) {
        const phrase2 = words[i] + ' ' + words[i + 1];
        if (phrase2.length > 10) phrases.push(phrase2);
        
        if (i < words.length - 2) {
          const phrase3 = words[i] + ' ' + words[i + 1] + ' ' + words[i + 2];
          if (phrase3.length > 15) phrases.push(phrase3);
        }
      }
    });
    
    if (phrases.length === 0) return [];
    
    // Return unique phrases sorted by frequency and meaningfulness
    const phraseCount = {};
    phrases.forEach(phrase => {
      // Score phrases based on length and uniqueness
      const score = phrase.length > 15 ? 2 : 1;
      phraseCount[phrase] = (phraseCount[phrase] || 0) + score;
    });
    
    return Object.entries(phraseCount)
      .filter(([phrase]) => phrase.length > 4) // Minimum meaningful length
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8) // Reduced to prevent clutter
      .map(([phrase]) => phrase);
  }

  function categorizeContent(content, node) {
    if (!content) return 'concept';
    
    const lowerContent = content.toLowerCase();
    
    // Technical patterns
    if (lowerContent.includes('algorithm') || lowerContent.includes('compute') || lowerContent.includes('process')) return 'algorithm';
    if (lowerContent.includes('data structure') || lowerContent.includes('array') || lowerContent.includes('tree')) return 'data_structure';
    if (lowerContent.includes('math') || lowerContent.includes('equation') || lowerContent.includes('formula')) return 'mathematics';
    if (lowerContent.includes('system') || lowerContent.includes('architecture') || lowerContent.includes('design')) return 'system';
    if (lowerContent.includes('program') || lowerContent.includes('code') || lowerContent.includes('function')) return 'programming';
    if (lowerContent.includes('security') || lowerContent.includes('crypto') || lowerContent.includes('auth')) return 'security';
    
    // Core categories
    if (lowerContent.includes('document') || node.type === 'document') return 'document';
    if (lowerContent.includes('topic') || lowerContent.includes('subject')) return 'topic';
    if (lowerContent.includes('principle') || lowerContent.includes('rule') || lowerContent.includes('law')) return 'principle';
    if (lowerContent.includes('entity') || lowerContent.includes('object')) return 'entity';
    if (lowerContent.includes('query') || lowerContent.includes('question')) return 'query';
    
    // Default
    return 'concept';
  }

  // Label sanitization function
  function sanitizeLabel(text) {
    if (!text) return 'Untitled';
    
    let cleaned = text;
    
    // Remove common file extensions
    cleaned = cleaned.replace(/\.(pdf|txt|doc|docx|md|html|json|xml|py|js|ts|css|scss|less)$/i, '');
    
    // Remove URL protocols and common prefixes
    cleaned = cleaned.replace(/^(https?:\/\/|www\.|file:\/\/)/i, '');
    
    // Replace hyphens, underscores, and dots with spaces
    cleaned = cleaned.replace(/[-_.]/g, ' ');
    
    // Remove excessive punctuation and special characters
    cleaned = cleaned.replace(/[^\w\s]/g, ' ');
    
    // Convert to title case and clean up spacing
    cleaned = cleaned
      .split(' ')
      .filter(word => word.length > 0) // Remove empty words
      .map(word => {
        // Don't capitalize small connecting words unless they're at the start
        const smallWords = ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
        return smallWords.includes(word.toLowerCase()) && cleaned.indexOf(word) !== 0 
          ? word.toLowerCase() 
          : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
    
    // Limit length for better display
    if (cleaned.length > 40) {
      const words = cleaned.split(' ');
      if (words.length > 5) {
        cleaned = words.slice(0, 5).join(' ') + '...';
      } else {
        cleaned = cleaned.substring(0, 40) + '...';
      }
    }
    
    return cleaned || 'Untitled';
  }

  // Enhanced relationship types with semantic meaning
  const relationshipTypes = {
    'is_a': { color: '#4CAF50', strength: 0.8, label: 'is a', description: 'Type/subtype relationship' },
    'part_of': { color: '#2196F3', strength: 0.7, label: 'part of', description: 'Composition relationship' },
    'uses': { color: '#FF9800', strength: 0.6, label: 'uses', description: 'Usage relationship' },
    'implements': { color: '#9C27B0', strength: 0.8, label: 'implements', description: 'Implementation relationship' },
    'depends_on': { color: '#F44336', strength: 0.7, label: 'depends on', description: 'Dependency relationship' },
    'similar_to': { color: '#8BC34A', strength: 0.5, label: 'similar to', description: 'Similarity relationship' },
    'causes': { color: '#FF5722', strength: 0.8, label: 'causes', description: 'Causal relationship' },
    'follows': { color: '#795548', strength: 0.6, label: 'follows', description: 'Sequential relationship' },
    
    // Technical relationships
    'computes': { color: '#673AB7', strength: 0.7, label: 'computes', description: 'Computational relationship' },
    'proves': { color: '#E91E63', strength: 0.9, label: 'proves', description: 'Proof relationship' },
    'verifies': { color: '#00BCD4', strength: 0.8, label: 'verifies', description: 'Verification relationship' },
    'generates': { color: '#607D8B', strength: 0.6, label: 'generates', description: 'Generation relationship' },
    'transforms': { color: '#9E9E9E', strength: 0.7, label: 'transforms', description: 'Transformation relationship' },
    'optimizes': { color: '#FF6F00', strength: 0.8, label: 'optimizes', description: 'Optimization relationship' },
    
    // Default relationships
    'related_to': { color: '#999999', strength: 0.4, label: 'related to', description: 'General relationship' },
    'mentions': { color: '#CCCCCC', strength: 0.3, label: 'mentions', description: 'Mention relationship' },
    'derived_from': { color: '#AA00FF', strength: 0.8, label: 'derived from', description: 'Derivation relationship' }
  };

  onMount(() => {
    initializeGraph();
    loadGraphData();
    
    // Add window resize handler
    const handleResize = () => {
      if (graphContainer) {
        width = graphContainer.clientWidth;
        height = graphContainer.clientHeight;
        
        if (layoutMode === '3d' && renderer && camera) {
          // Update 3D renderer
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
          renderer.setSize(width, height);
        } else if (svg) {
          // Update 2D SVG
          svg.attr('width', width).attr('height', height);
        }
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    // Cleanup resize listener
    console.log('⚠️ Knowledge state subscription disabled to prevent reload loops');
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
    if (simulation) simulation.stop();
    
    // Clean up 3D resources
    cleanup3D();
  });

  async function loadGraphData() {
    // Prevent reload loops - only reload if enough time has passed
    const now = Date.now();
    if (isLoading || (now - lastLoadTime < 2000)) {
      console.log('⏸️ Skipping reload - too soon or already loading');
      return;
    }
    
    isLoading = true;
    loading = true;
    error = null;
    lastLoadTime = now;
    
    console.log('🔄 Loading knowledge graph data...');
    
    try {
      // Try to fetch real data from backend
      const apiData = await GödelOSAPI.fetchKnowledgeGraph();
      
      if (apiData && apiData.nodes && apiData.edges && apiData.nodes.length > 0) {
        // Enhanced node processing with semantic analysis
        const processedNodes = apiData.nodes.map((node, index) => {
          // Clean and normalize node data first
          const cleanNodeData = (text) => {
            if (!text) return '';
            return text
              .replace(/file-[a-f0-9-]{36}/gi, '') // Remove UUID patterns
              .replace(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, '') // Remove standalone UUIDs
              .replace(/\b(file|document|node|id|uuid)\s*-?\s*/gi, '') // Remove noise words with separators
              .replace(/\s+/g, ' ')
              .trim();
          };
          
          // Comprehensive content extraction with priority system
          const contentSources = {
            primary: cleanNodeData(node.concept || node.title || node.name || node.label),
            secondary: cleanNodeData(node.content || node.text || node.description),
            metadata: cleanNodeData(node.summary || node.abstract || (node.properties ? Object.values(node.properties).join(' ') : ''))
          };
          
          // Create comprehensive text for analysis (only non-empty sources)
          const allContent = Object.values(contentSources).filter(Boolean).join(' ');
          
          // Extract meaningful label with contextual awareness
          let label = contentSources.primary;
          if (!label || label.trim() === '') {
            if (contentSources.secondary) {
              // Extract the most meaningful sentence or phrase
              const sentences = contentSources.secondary.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 10);
              if (sentences.length > 0) {
                // Pick the sentence with the most meaningful content
                const scoredSentences = sentences.map(sentence => {
                  const meaningfulWords = sentence.toLowerCase().split(/\s+/).filter(word => 
                    word.length > 3 && !['this', 'that', 'they', 'there', 'where', 'when', 'what', 'which'].includes(word)
                  );
                  return { sentence, score: meaningfulWords.length };
                });
                
                const bestSentence = scoredSentences.sort((a, b) => b.score - a.score)[0];
                label = bestSentence.sentence.length > 80 ? bestSentence.sentence.substring(0, 80) + '...' : bestSentence.sentence;
              } else {
                label = contentSources.secondary.length > 60 ? contentSources.secondary.substring(0, 60) + '...' : contentSources.secondary;
              }
            } else {
              label = `Knowledge Node ${index + 1}`;
            }
          }
          
          // Sanitize the label to remove file extensions and clean up formatting
          label = sanitizeLabel(label);
          
          // Enhanced categorization using semantic analysis
          const category = categorizeContent(allContent, node);
          
          // Extract key phrases for relationship inference
          const keyPhrases = extractKeyPhrases(allContent);
          
          // Calculate importance based on multiple factors
          const importance = Math.max(0, Math.min(1, 
            (node.importance || 0) * 0.4 +
            (node.strength || 0) * 0.3 +
            (node.confidence || 0) * 0.2 +
            (keyPhrases.length / 20) * 0.1 // More key phrases = higher importance
          )) || 0.7;
          
          return {
            ...node,
            id: String(node.node_id || node.id || node.concept_id || `node_${index}`),
            label: sanitizeLabel(label),
            category: category,
            importance: importance,
            confidence: Math.max(0, Math.min(1, node.confidence || 0.8)),
            timestamp: node.creation_time || node.timestamp || node.last_updated || Date.now(),
            recency: Math.max(0, Math.min(1, node.recency ||
              (node.last_updated ? Math.max(0, 1 - (Date.now() - node.last_updated * 1000) / (24 * 60 * 60 * 1000)) : 0.6))),
            
            // Enhanced content for display
            content: contentSources.secondary || '',
            summary: node.summary || (contentSources.secondary ? contentSources.secondary.substring(0, 200) + '...' : ''),
            keyPhrases: keyPhrases,
            
            // Store original data for detail view
            originalData: node
          };
        });

        // Enhanced edge processing with proper relationship inference
        let processedEdges = [];
        
        if (apiData.edges && apiData.edges.length > 0) {
          processedEdges = apiData.edges.map(edge => {
            // Clean edge labels
            let cleanLabel = edge.label || relationshipTypes[edge.relationship_type || edge.type]?.label || 'related';
            cleanLabel = cleanLabel
              .replace(/file-[a-f0-9-]{36}/gi, '') // Remove UUID patterns
              .replace(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, '') // Remove UUIDs
              .replace(/\b(file|document|node|id|uuid)\s*-?\s*/gi, '') // Remove noise words
              .replace(/[-_]+/g, ' ') // Replace separators with spaces
              .replace(/\s+/g, ' ')
              .trim();
            
            // If label becomes empty or too short, use type or default
            if (!cleanLabel || cleanLabel.length < 3) {
              cleanLabel = relationshipTypes[edge.relationship_type || edge.type]?.label || 'related';
            }
            
            return {
              ...edge,
              source: String(edge.source_id || edge.source || edge.from),
              target: String(edge.target_id || edge.target || edge.to),
              type: edge.relationship_type || edge.type || 'related',
              strength: Math.max(0, Math.min(1, edge.strength || edge.weight || 0.5)),
              confidence: Math.max(0, Math.min(1, edge.confidence || 0.7)),
              label: cleanLabel
            };
          });
        }
        
        // Generate additional relationships based on content similarity
        const inferredEdges = generateInferredRelationships(processedNodes);
        processedEdges = [...processedEdges, ...inferredEdges];
        
        // Filter out invalid edges (nodes that don't exist)
        const nodeIds = new Set(processedNodes.map(n => n.id));
        processedEdges = processedEdges.filter(edge => 
          nodeIds.has(String(edge.source)) && nodeIds.has(String(edge.target))
        );

        graphData = {
          nodes: processedNodes,
          edges: processedEdges
        };
        
        console.log(`✅ Loaded real knowledge graph: ${processedNodes.length} nodes, ${processedEdges.length} total edges (${processedEdges.filter(e => e.generated).length} generated)`);
      } else {
        // No backend data available
        console.error('❌ No knowledge graph data available from backend');
        graphData = { nodes: [], edges: [] };
        error = 'No knowledge data available';
      }
      
      updateGraph();
      loading = false;
      
    } catch (err) {
      console.error('❌ Error loading knowledge graph:', err);
      error = err.message;
      graphData = { nodes: [], links: [] };
      updateGraph();
      loading = false;
    } finally {
      isLoading = false;
    }
  }

  function generateInferredRelationships(nodes, existingLinks = []) {
    const inferredLinks = [];
    const existingLinkSet = new Set();
    
    // Track existing relationships to avoid duplicates
    existingLinks.forEach(link => {
      existingLinkSet.add(`${link.source}-${link.target}`);
      existingLinkSet.add(`${link.target}-${link.source}`); // Bidirectional check
    });
    
    // Generate relationships based on content similarity and semantic analysis
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i];
        const nodeB = nodes[j];
        const linkKey = `${nodeA.id}-${nodeB.id}`;
        
        if (existingLinkSet.has(linkKey)) continue;
        
        // Calculate content similarity
        const textA = (nodeA.label + ' ' + (nodeA.content || '') + ' ' + (nodeA.text || '')).toLowerCase();
        const textB = (nodeB.label + ' ' + (nodeB.content || '') + ' ' + (nodeB.text || '')).toLowerCase();
        
        const phrasesA = extractKeyPhrases(textA);
        const phrasesB = extractKeyPhrases(textB);
        
        // Calculate Jaccard similarity
        const setA = new Set(phrasesA);
        const setB = new Set(phrasesB);
        const intersection = new Set([...setA].filter(x => setB.has(x)));
        const union = new Set([...setA, ...setB]);
        const similarity = union.size > 0 ? intersection.size / union.size : 0;
        
        // Create relationship if similarity is above threshold OR if categories are related
        const shouldCreateLink = similarity > 0.15 || 
                                (nodeA.category === nodeB.category && Math.random() > 0.7) ||
                                (nodeA.category === 'concept' && nodeB.category === 'entity' && Math.random() > 0.8);
        
        if (shouldCreateLink) {
          // Infer relationship type based on content
          let relationshipType = 'similar_to';
          
          if (nodeA.category === nodeB.category && similarity > 0.3) {
            relationshipType = 'is_a';
          } else if (nodeA.category === 'algorithm' && nodeB.category === 'data_structure') {
            relationshipType = 'uses';
          } else if (nodeA.category === 'concept' && nodeB.category === 'document') {
            relationshipType = 'mentions';
          } else if (nodeA.category === 'concept' && nodeB.category === 'entity') {
            relationshipType = 'includes';
          }
          
          const strength = Math.max(0.3, Math.min(0.8, similarity * 2 + 0.2)); // Ensure minimum strength
          
          inferredLinks.push({
            source: nodeA.id,
            target: nodeB.id,
            type: relationshipType,
            strength: strength,
            confidence: Math.max(0.3, similarity),
            generated: true,
            label: relationshipTypes[relationshipType]?.label || relationshipType
          });
        }
      }
    }
    
    console.log(`🔗 Generated ${inferredLinks.length} inferred relationships`);
    return inferredLinks;
  }

  function initializeGraph() {
    if (!graphContainer) return;
    
    const rect = graphContainer.getBoundingClientRect();
    width = Math.max(800, rect.width - 40);
    height = Math.max(600, rect.height - 40);
    
    if (layoutMode === '2d') {
      initialize2DGraph();
    } else if (layoutMode === '3d') {
      initialize3DGraph();
    }
  }

  function initialize2DGraph() {
    // Clear any existing content
    d3.select(graphContainer).selectAll("*").remove();
    
    svg = d3.select(graphContainer)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', 'rgba(0, 0, 0, 0.05)')
      .style('border-radius', '8px');
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        svg.select('.graph-group').attr('transform', event.transform);
      });
    
    svg.call(zoom);
    
    // Create main group for graph elements
    const graphGroup = svg.append('g').attr('class', 'graph-group');
    
    // Initialize force simulation with enhanced parameters
    simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).strength(linkStrength).distance(linkDistance))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2).strength(centerForce))
      .force('collision', d3.forceCollide().radius(collisionRadius))
      .alphaDecay(alphaDecay)
      .velocityDecay(velocityDecay);
  }

  function initialize3DGraph() {
    console.log('🌐 Initializing 3D Network visualization...');
    if (!graphContainer) return;
    
    // Clean up any existing 2D elements
    if (svg) {
      svg.remove();
      svg = null;
    }
    
    // Initialize Three.js scene
    init3DVisualization();
  }

  function init3DVisualization() {
    // Create Three.js scene
    scene = new THREE.Scene();
    
    // Create gradient background that matches the theme
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const context = canvas.getContext('2d');
    
    // Create gradient matching the main theme: #667eea to #764ba2
    const gradient = context.createLinearGradient(0, 0, 0, 512);
    gradient.addColorStop(0, '#667eea'); // Blue
    gradient.addColorStop(1, '#764ba2'); // Purple
    
    context.fillStyle = gradient;
    context.fillRect(0, 0, 512, 512);
    
    // Apply as scene background
    const texture = new THREE.CanvasTexture(canvas);
    scene.background = texture;
    
    // Setup camera
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 2000);
    camera.position.set(0, 0, 500);
    
    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Clear container and add renderer
    graphContainer.innerHTML = '';
    graphContainer.appendChild(renderer.domElement);
    
    // Add orbital controls for navigation
    controls3d = new OrbitControls(camera, renderer.domElement);
    controls3d.enableDamping = true;
    controls3d.dampingFactor = 0.05;
    controls3d.enableZoom = true;
    controls3d.enablePan = true;
    
    // Add ambient lighting (softer to match theme)
    const ambientLight = new THREE.AmbientLight(0x8888ff, 0.4);
    scene.add(ambientLight);
    
    // Add directional light (warmer tone to complement gradient)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(100, 100, 50);
    scene.add(directionalLight);
    
    // Add subtle colored lights to enhance the theme
    const blueLight = new THREE.PointLight(0x667eea, 0.3, 1000);
    blueLight.position.set(-200, 200, 200);
    scene.add(blueLight);
    
    const purpleLight = new THREE.PointLight(0x764ba2, 0.3, 1000);
    purpleLight.position.set(200, -200, 200);
    scene.add(purpleLight);
    
    // Create 3D graph from current data
    create3DNodes();
    create3DLinks();
    
    // Start animation loop
    animate3D();
  }

  function create3DNodes() {
    // Clear existing node objects
    nodeObjects.forEach(obj => scene.remove(obj));
    nodeObjects = [];
    
    if (!graphData.nodes) return;
    
    graphData.nodes.forEach(node => {
      // Create sphere geometry for nodes
      const geometry = new THREE.SphereGeometry(
        (nodeCategories[node.category]?.size || 8) * nodeSize, 
        16, 
        16
      );
      
      // Create material with category color
      const color = nodeCategories[node.category]?.color || '#4CAF50';
      const material = new THREE.MeshLambertMaterial({ 
        color: color,
        transparent: true,
        opacity: 0.8
      });
      
      // Create mesh
      const sphere = new THREE.Mesh(geometry, material);
      
      // Position randomly in 3D space initially
      sphere.position.set(
        (Math.random() - 0.5) * 400,
        (Math.random() - 0.5) * 400,
        (Math.random() - 0.5) * 400
      );
      
      // Store reference to original node data
      sphere.userData = node;
      
      // Add to scene and tracking array
      scene.add(sphere);
      nodeObjects.push(sphere);
      
      // Add text label with better visibility
      if (showLabels) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // Calculate canvas size based on text
        const text = node.label || node.id;
        context.font = 'bold 20px Arial';
        const textMetrics = context.measureText(text);
        const textWidth = textMetrics.width;
        
        // Set canvas size with padding
        canvas.width = textWidth + 20;
        canvas.height = 30;
        
        // Clear and set font again (canvas resize clears context)
        context.font = 'bold 20px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        
        // Add background with rounded corners for better contrast
        context.fillStyle = 'rgba(0, 0, 0, 0.8)';
        context.roundRect = context.roundRect || function(x, y, w, h, r) {
          this.beginPath();
          this.moveTo(x + r, y);
          this.arcTo(x + w, y, x + w, y + h, r);
          this.arcTo(x + w, y + h, x, y + h, r);
          this.arcTo(x, y + h, x, y, r);
          this.arcTo(x, y, x + w, y, r);
          this.closePath();
        };
        context.beginPath();
        context.roundRect(2, 2, canvas.width - 4, canvas.height - 4, 8);
        context.fill();
        
        // Add white outline for better visibility
        context.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        context.lineWidth = 2;
        context.stroke();
        
        // Draw text with white color and shadow
        context.shadowColor = 'rgba(0, 0, 0, 0.8)';
        context.shadowBlur = 4;
        context.shadowOffsetX = 1;
        context.shadowOffsetY = 1;
        context.fillStyle = '#ffffff';
        context.fillText(text, canvas.width / 2, canvas.height / 2);
        
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({ 
          map: texture,
          transparent: true,
          depthTest: false // Always render on top
        });
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.position.copy(sphere.position);
        sprite.position.y += 25;
        sprite.scale.set(canvas.width * 0.8, canvas.height * 0.8, 1);
        
        // Associate sprite with its node
        sprite.userData = { ...node, parentNode: sphere, isLabel: true };
        
        scene.add(sprite);
        nodeObjects.push(sprite);
      }
    });
  }

  function create3DLinks() {
    // Clear existing link objects
    edgeObjects.forEach(obj => scene.remove(obj));
    edgeObjects = [];
    
    if (!graphData.edges) return;
    
    graphData.edges.forEach(edge => {
      // Find source and target node objects
      const sourceNode = nodeObjects.find(obj => 
        obj.userData && obj.userData.id === (edge.source.id || edge.source)
      );
      const targetNode = nodeObjects.find(obj => 
        obj.userData && obj.userData.id === (edge.target.id || edge.target)
      );
      
      if (sourceNode && targetNode) {
        // Calculate distance and direction for cylindrical link
        const direction = new THREE.Vector3().subVectors(targetNode.position, sourceNode.position);
        const distance = direction.length();
        const midpoint = new THREE.Vector3().addVectors(sourceNode.position, targetNode.position).multiplyScalar(0.5);
        
        // Create cylinder geometry for thicker, more visible links
        const linkRadius = (link.weight || 0.6) * 2; // Scale thickness based on link weight
        const geometry = new THREE.CylinderGeometry(linkRadius, linkRadius, distance, 8);
        
        // Create material with enhanced visibility
        const material = new THREE.MeshLambertMaterial({
          color: link.color || '#888888',
          transparent: true,
          opacity: Math.max(0.4, link.weight || 0.6) // Ensure minimum visibility
        });
        
        // Create mesh
        const cylinder = new THREE.Mesh(geometry, material);
        
        // Position and orient the cylinder between nodes
        cylinder.position.copy(midpoint);
        cylinder.lookAt(targetNode.position);
        cylinder.rotateX(Math.PI / 2); // Align with direction
        
        cylinder.userData = { source: sourceNode, target: targetNode, link: link, isCylinder: true };
        
        scene.add(cylinder);
        edgeObjects.push(cylinder);
      }
    });
  }

  function animate3D() {
    if (!renderer || !scene || !camera) return;
    
    requestAnimationFrame(animate3D);
    
    // Update controls
    if (controls3d) {
      controls3d.update();
    }
    
    // Update edge positions and orientations
    edgeObjects.forEach(edgeObj => {
      const { source, target, isCylinder } = edgeObj.userData;
      if (source && target) {
        if (isCylinder) {
          // Update cylindrical link position and orientation
          const direction = new THREE.Vector3().subVectors(target.position, source.position);
          const distance = direction.length();
          const midpoint = new THREE.Vector3().addVectors(source.position, target.position).multiplyScalar(0.5);
          
          // Update position
          linkObj.position.copy(midpoint);
          
          // Update scale to match distance
          linkObj.scale.y = distance / linkObj.geometry.parameters.height;
          
          // Update orientation
          linkObj.lookAt(target.position);
          linkObj.rotateX(Math.PI / 2);
        } else {
          // Legacy line update (fallback)
          const positions = linkObj.geometry.attributes.position.array;
          positions[0] = source.position.x;
          positions[1] = source.position.y;
          positions[2] = source.position.z;
          positions[3] = target.position.x;
          positions[4] = target.position.y;
          positions[5] = target.position.z;
          linkObj.geometry.attributes.position.needsUpdate = true;
        }
      }
    });
    
    // Update label positions to follow their nodes
    nodeObjects.forEach(obj => {
      if (obj.userData && obj.userData.isLabel && obj.userData.parentNode) {
        obj.position.copy(obj.userData.parentNode.position);
        obj.position.y += 25; // Offset above the node
      }
    });
    
    // Apply force simulation to 3D positions
    apply3DForces();
    
    // Render the scene
    renderer.render(scene, camera);
  }

  function apply3DForces() {
    if (!nodeObjects.length) return;
    
    // Improved 3D force simulation with damping and collision detection
    const damping = 0.95; // Velocity damping to reduce jitter
    const minDistance = 50; // Minimum distance between nodes
    const maxForce = 2; // Maximum force magnitude to prevent extreme movements
    
    nodeObjects.forEach(node => {
      if (!node.userData) return;
      
      // Initialize velocity if not exists
      if (!node.velocity) {
        node.velocity = { x: 0, y: 0, z: 0 };
      }
      
      let forceX = 0, forceY = 0, forceZ = 0;
      
      // Apply repulsion forces between nodes
      nodeObjects.forEach(otherNode => {
        if (node === otherNode || !otherNode.userData) return;
        
        const dx = node.position.x - otherNode.position.x;
        const dy = node.position.y - otherNode.position.y;
        const dz = node.position.z - otherNode.position.z;
        let distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
        
        // Prevent division by zero and enforce minimum distance
        if (distance < 0.1) distance = 0.1;
        
        if (distance < minDistance * 2) {
          const repulsion = (chargeStrength * 0.0001) / (distance * distance);
          const normalizedDx = dx / distance;
          const normalizedDy = dy / distance;
          const normalizedDz = dz / distance;
          
          forceX += normalizedDx * repulsion;
          forceY += normalizedDy * repulsion;
          forceZ += normalizedDz * repulsion;
        }
      });
      
      // Apply attraction forces for connected nodes
      graphData.edges.forEach(edge => {
        const sourceId = edge.source.id || edge.source;
        const targetId = edge.target.id || edge.target;
        
        if (node.userData.id === sourceId || node.userData.id === targetId) {
          const partnerId = node.userData.id === sourceId ? targetId : sourceId;
          const partnerNode = nodeObjects.find(obj => 
            obj.userData && obj.userData.id === partnerId
          );
          
          if (partnerNode) {
            const dx = partnerNode.position.x - node.position.x;
            const dy = partnerNode.position.y - node.position.y;
            const dz = partnerNode.position.z - node.position.z;
            let distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
            
            if (distance > linkDistance) {
              const attraction = linkStrength * 0.1;
              const normalizedDx = dx / distance;
              const normalizedDy = dy / distance;
              const normalizedDz = dz / distance;
              
              forceX += normalizedDx * attraction;
              forceY += normalizedDy * attraction;
              forceZ += normalizedDz * attraction;
            }
          }
        }
      });
      
      // Apply center force (weaker)
      const centerDist = Math.sqrt(
        node.position.x * node.position.x + 
        node.position.y * node.position.y + 
        node.position.z * node.position.z
      );
      if (centerDist > 0 && centerDist > 200) {
        const centerForceStrength = centerForce * 0.0005;
        forceX -= node.position.x * centerForceStrength;
        forceY -= node.position.y * centerForceStrength;
        forceZ -= node.position.z * centerForceStrength;
      }
      
      // Limit force magnitude to prevent instability
      const forceMagnitude = Math.sqrt(forceX * forceX + forceY * forceY + forceZ * forceZ);
      if (forceMagnitude > maxForce) {
        const scale = maxForce / forceMagnitude;
        forceX *= scale;
        forceY *= scale;
        forceZ *= scale;
      }
      
      // Update velocity with forces
      node.velocity.x = (node.velocity.x + forceX) * damping;
      node.velocity.y = (node.velocity.y + forceY) * damping;
      node.velocity.z = (node.velocity.z + forceZ) * damping;
      
      // Apply velocity to position with collision detection
      node.position.x += node.velocity.x;
      node.position.y += node.velocity.y;
      node.position.z += node.velocity.z;
      
      // Constrain nodes to stay within reasonable bounds
      const maxBounds = 300;
      node.position.x = Math.max(-maxBounds, Math.min(maxBounds, node.position.x));
      node.position.y = Math.max(-maxBounds, Math.min(maxBounds, node.position.y));
      node.position.z = Math.max(-maxBounds, Math.min(maxBounds, node.position.z));
    });
  }

  function cleanup3D() {
    if (scene) {
      // Remove all objects from scene
      while(scene.children.length > 0) {
        scene.remove(scene.children[0]);
      }
    }
    
    if (renderer) {
      renderer.dispose();
      renderer = null;
    }
    
    if (controls3d) {
      controls3d.dispose();
      controls3d = null;
    }
    
    scene = null;
    camera = null;
    nodeObjects = [];
    edgeObjects = [];
    
    // Clear the container
    if (graphContainer) {
      graphContainer.innerHTML = '';
    }
  }

  function updateGraph() {
    if (!simulation || !svg) {
      console.warn('❌ Simulation or SVG not initialized');
      return;
    }
    
    // Validate graph data
    if (!graphData || !graphData.nodes || !graphData.edges) {
      console.warn('❌ Invalid graph data structure');
      return;
    }
    
    console.log(`🔄 Updating graph: ${graphData.nodes.length} nodes, ${graphData.edges.length} edges`);
    
    // Filter edges based on settings
    const filteredEdges = showOnlyStrongRelations 
      ? graphData.edges.filter(edge => (edge.strength || 0.5) > 0.6)
      : graphData.edges;
    
    // Get the graph group for appending elements
    const graphGroup = svg.select('.graph-group');
    if (graphGroup.empty()) {
      console.warn('❌ Graph group not found');
      return;
    }
    
    // Update node colors based on color mode
    const getNodeColor = (node) => {
      const categoryProps = nodeCategories[node.category] || nodeCategories.concept;
      
      switch (colorMode) {
        case 'importance':
          const importanceIntensity = node.importance || 0.5;
          return d3.interpolateViridis(importanceIntensity);
        case 'recency':
          const recencyIntensity = node.recency || 0.5;
          return d3.interpolateWarm(recencyIntensity);
        case 'confidence':
          const confidenceIntensity = node.confidence || 0.5;
          return d3.interpolateCool(confidenceIntensity);
        default:
          return categoryProps.color;
      }
    };
    
    // Update links
    const links = graphGroup.selectAll('.link')
      .data(filteredEdges, d => `${d.source}-${d.target}`);
    
    links.exit().remove();
    
    const linksEnter = links.enter()
      .append('g')
      .attr('class', 'link-group')
      .on('mouseenter', function(event, d) {
        // Highlight edge label on hover
        d3.select(this).select('.edge-label')
          .style('opacity', 1)
          .style('font-size', '11px')
          .style('font-weight', '700');
      })
      .on('mouseleave', function(event, d) {
        // Reset edge label on mouse leave
        const strength = d.strength || 0.5;
        d3.select(this).select('.edge-label')
          .style('opacity', strength > 0.6 ? 1 : 0.4)
          .style('font-size', '9px')
          .style('font-weight', '600');
      });
    
    // Add lines to link groups
    linksEnter.append('line')
      .attr('class', 'link')
      .attr('stroke', d => relationshipTypes[d.type]?.color || '#999')
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');
    
    // Add edge labels if enabled (with smart visibility)
    if (showEdgeLabels) {
      linksEnter.append('text')
        .attr('class', 'edge-label')
        .style('font-size', '9px')
        .style('fill', '#ffffff')
        .style('text-anchor', 'middle')
        .style('pointer-events', 'none')
        .style('font-weight', '600')
        .style('text-shadow', '1px 1px 2px rgba(0,0,0,0.8)')
        .style('opacity', d => {
          // Only show labels for strong relationships or on hover
          const strength = d.strength || 0.5;
          return strength > 0.7 ? 1 : 0.3;
        });
    }
    
    const linksUpdate = linksEnter.merge(links);
    
    // Update link lines
    linksUpdate.select('.link')
      .attr('stroke-width', d => Math.sqrt(d.strength * 8) + 1)
      .attr('stroke-opacity', d => 0.3 + (d.strength * 0.5))
      .attr('stroke', d => relationshipTypes[d.type]?.color || '#999');
    
    // Update edge labels with better positioning and filtering
    linksUpdate.select('.edge-label')
      .text(d => {
        if (!showEdgeLabels) return '';
        // Only show meaningful labels, not generic ones
        const label = d.label || d.type;
        if (!label || label.length < 3 || ['relates', 'connects', 'links'].includes(label.toLowerCase())) {
          return '';
        }
        return label.length > 15 ? label.substring(0, 15) + '...' : label;
      })
      .style('display', showEdgeLabels ? 'block' : 'none')
      .style('opacity', d => {
        const strength = d.strength || 0.5;
        return strength > 0.6 ? 1 : 0.4;
      });
    
    // Update nodes
    const nodes = graphGroup.selectAll('.node')
      .data(graphData.nodes, d => d.id);
    
    nodes.exit().remove();
    
    const nodesEnter = nodes.enter()
      .append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        selectNode(d);
      })
      .on('mouseenter', function(event, d) {
        // Highlight node on hover
        d3.select(this).select('.node-circle')
          .attr('stroke-width', 3)
          .attr('stroke', '#ffffff');
        d3.select(this).select('.label-background')
          .attr('stroke-width', 2)
          .attr('stroke', 'rgba(255, 255, 255, 0.9)');
      })
      .on('mouseleave', function(event, d) {
        // Reset node on mouse leave
        d3.select(this).select('.node-circle')
          .attr('stroke-width', 1.5)
          .attr('stroke', '#fff');
        d3.select(this).select('.label-background')
          .attr('stroke-width', 1)
          .attr('stroke', 'rgba(255, 255, 255, 0.6)');
      })
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
    
    // Add circles to nodes
    nodesEnter.append('circle')
      .attr('class', 'node-circle');
    
    // Add labels to nodes if enabled
    if (showLabels) {
      const labelGroup = nodesEnter.append('g')
        .attr('class', 'label-group');
        
      if (enableWordWrap) {
        // Multi-line labels with word wrapping
        labelGroup.append('rect')
          .attr('class', 'label-background')
          .attr('fill', 'rgba(0, 0, 0, 0.85)')
          .attr('stroke', 'rgba(255, 255, 255, 0.6)')
          .attr('stroke-width', 1)
          .attr('rx', 6);
          
        labelGroup.each(function(d) {
          const group = d3.select(this);
          const words = (d.label || '').split(/\s+/);
          const maxWidth = 80;
          const lineHeight = 12;
          let line = [];
          let lineNumber = 0;
          let lines = [];
          
          // Word wrap algorithm with better spacing
          words.forEach(word => {
            const testLine = line.concat(word).join(' ');
            if (testLine.length > 12 && line.length > 0) { // Reduced line length for better readability
              lines.push(line.join(' '));
              line = [word];
              lineNumber++;
            } else {
              line.push(word);
            }
          });
          if (line.length > 0) lines.push(line.join(' '));
          
          // Limit to maximum 3 lines to prevent overcrowding
          if (lines.length > 3) {
            const truncatedLines = lines.slice(0, 2);
            truncatedLines.push('...');
            lines = truncatedLines;
          }
          
          // Create text elements for each line with better styling
          lines.forEach((lineText, i) => {
            group.append('text')
              .attr('class', 'node-label-line')
              .attr('dy', (i - lines.length/2 + 0.5) * lineHeight)
              .attr('dx', 15)
              .style('font-size', '10px')
              .style('fill', '#ffffff')
              .style('font-weight', '600')
              .style('pointer-events', 'none')
              .style('text-shadow', '1px 1px 1px rgba(0,0,0,0.8)')
              .text(lineText);
          });
          
          // Update background rectangle with better padding
          const bbox = group.node().getBBox();
          group.select('.label-background')
            .attr('x', bbox.x - 6)
            .attr('y', bbox.y - 3)
            .attr('width', bbox.width + 12)
            .attr('height', bbox.height + 6);
        });
      } else {
        // Single line labels with background
        labelGroup.append('rect')
          .attr('class', 'label-background')
          .attr('fill', 'rgba(0, 0, 0, 0.85)')
          .attr('stroke', 'rgba(255, 255, 255, 0.6)')
          .attr('stroke-width', 1)
          .attr('rx', 6);
          
        labelGroup.append('text')
          .attr('class', 'node-label')
          .attr('dx', 12)
          .attr('dy', '.35em')
          .style('font-size', '11px')
          .style('fill', '#ffffff')
          .style('font-weight', '600')
          .style('pointer-events', 'none')
          .style('text-shadow', '1px 1px 1px rgba(0,0,0,0.8)');
      }
    }
    
    const nodesUpdate = nodesEnter.merge(nodes);
    
    // Update node circles
    nodesUpdate.select('.node-circle')
      .attr('r', getNodeSize)
      .attr('fill', getNodeColor)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);
    
    // Update node labels and backgrounds
    nodesUpdate.select('.node-label')
      .text(d => showLabels ? d.label : '')
      .style('display', showLabels ? 'block' : 'none')
      .each(function(d) {
        // Update background for single-line labels
        const textElement = d3.select(this);
        const bbox = textElement.node()?.getBBox();
        if (bbox) {
          const backgroundRect = d3.select(this.parentNode).select('.label-background');
          if (!backgroundRect.empty()) {
            backgroundRect
              .attr('x', bbox.x - 6)
              .attr('y', bbox.y - 3)
              .attr('width', bbox.width + 12)
              .attr('height', bbox.height + 6);
          }
        }
      });
    
    // Update and restart simulation with current parameters
    simulation
      .nodes(graphData.nodes);
    
    // Update all force parameters
    simulation.force('link')
      .links(filteredEdges)
      .strength(linkStrength)
      .distance(linkDistance);
    
    simulation.force('charge')
      .strength(chargeStrength);
    
    simulation.force('center')
      .strength(centerForce);
    
    simulation.force('collision')
      .radius(collisionRadius);
    
    simulation
      .alphaDecay(alphaDecay)
      .velocityDecay(velocityDecay)
      .alpha(1)
      .restart();
    
    // Update simulation tick with enhanced edge label positioning
    simulation.on('tick', () => {
      linksUpdate.select('.link')
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      // Position edge labels at the midpoint of links
      linksUpdate.select('.edge-label')
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)
        .attr('transform', d => {
          const dx = d.target.x - d.source.x;
          const dy = d.target.y - d.source.y;
          const angle = Math.atan2(dy, dx) * 180 / Math.PI;
          return `rotate(${angle > 90 || angle < -90 ? angle + 180 : angle} ${(d.source.x + d.target.x) / 2} ${(d.source.y + d.target.y) / 2})`;
        });
      
      nodesUpdate
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  // Enhanced cleanup function to prevent visual artifacts
  function cleanupGraph() {
    if (!svg) return;
    
    // Stop the current simulation completely
    if (simulation) {
      simulation.stop();
      simulation.alpha(0);
    }
    
    // Remove ALL existing elements to prevent artifacts
    const graphGroup = svg.select('.graph-group');
    if (!graphGroup.empty()) {
      // Remove all node elements and their children
      graphGroup.selectAll('.node').remove();
      graphGroup.selectAll('.node-circle').remove();
      graphGroup.selectAll('.node-label').remove();
      graphGroup.selectAll('.node-label-line').remove();
      graphGroup.selectAll('.label-group').remove();
      graphGroup.selectAll('.label-background').remove();
      
      // Remove all link elements and their children
      graphGroup.selectAll('.link-group').remove();
      graphGroup.selectAll('.link').remove();
      graphGroup.selectAll('.edge-label').remove();
      
      // Force a complete clear of any remaining elements
      graphGroup.selectAll('*').remove();
    }
    
    console.log('🧹 Graph completely cleaned up');
  }

  // Enhanced graph reinitialization with cleanup
  function reinitializeGraph() {
    cleanupGraph();
    
    // Small delay to ensure cleanup is complete
    setTimeout(() => {
      initializeGraph();
    }, 50);
  }

  // Force complete redraw function for when artifacts persist
  function forceRedraw() {
    console.log('🔄 Forcing complete redraw...');
    
    isRedrawing = true;
    
    // Complete cleanup
    cleanupGraph();
    
    // Reset any cached states
    selectedNode = null;
    
    // Clear and reinitialize SVG
    if (svg) {
      svg.selectAll('*').remove();
    }
    
    // Reinitialize from scratch
    setTimeout(() => {
      initializeGraph();
      isRedrawing = false;
    }, 200);
  }

  // Helper function to calculate node size
  function getNodeSize(node) {
    const baseSize = nodeCategories[node.category]?.size || 8;
    const importanceMultiplier = 1 + (node.importance || 0.5) * 0.5;
    return baseSize * importanceMultiplier * nodeSize;
  }

  // Drag functions
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
  
  function selectNode(node) {
    selectedNode = node;
    // Clear any existing highlights when selecting a new node
    clearHighlights();
    console.log('🔍 Selected node:', node);
  }

  function changeLayoutMode(newMode) {
    console.log(`🎛️ Changing layout mode: ${layoutMode} → ${newMode}`);
    
    if (layoutMode === newMode) return;
    
    layoutMode = newMode;
    
    // Apply different visual effects based on layout mode
    switch (newMode) {
      case '3d':
        // Switch to 3D visualization
        init3DVisualization();
        break;
      case 'hierarchical':
        // Apply hierarchical layout with specific physics
        linkStrength = 1.2;
        chargeStrength = -600;
        centerForce = 0.2;
        linkDistance = 100;
        break;
      case 'circular':
        // Apply circular layout
        linkStrength = 0.8;
        chargeStrength = -300;
        centerForce = 0.8;
        linkDistance = 150;
        break;
      case '2d':
      default:
        // Standard 2D force layout
        if (scene) {
          // Clean up 3D if switching back
          cleanup3D();
        }
        linkStrength = 0.8;
        chargeStrength = -400;
        centerForce = 0.1;
        linkDistance = 120;
        break;
    }
    
    updateGraph();
  }

  function changeColorMode(newMode) {
    console.log(`🎨 Changing color mode: ${colorMode} → ${newMode}`);
    colorMode = newMode;
    updateGraph();
  }
  
  function handleSearch() {
    loadGraphData();
  }
  
  // Collaborative event handlers
  function handleGraphDataSync(event) {
    console.log('📥 Syncing graph data from collaborative session');
    graphData = event.detail.graphData;
    // Redraw visualization with synced data
    if (layoutMode === '2d') {
      renderGraph2D();
    } else if (layoutMode === '3d') {
      renderGraph3D();
    }
  }
  
  function handleNodeCreate(event) {
    console.log('➕ Remote node created:', event.detail);
    const newNode = event.detail;
    graphData.nodes = [...graphData.nodes, newNode];
    // Update visualization
    if (layoutMode === '2d') {
      updateGraph2D();
    } else if (layoutMode === '3d') {
      updateGraph3D();
    }
  }
  
  function handleNodeUpdate(event) {
    console.log('✏️ Remote node updated:', event.detail);
    const { nodeId, updates } = event.detail;
    graphData.nodes = graphData.nodes.map(node => 
      node.id === nodeId ? { ...node, ...updates } : node
    );
    // Update visualization
    updateVisualization();
  }
  
  function handleNodeDelete(event) {
    console.log('🗑️ Remote node deleted:', event.detail);
    const nodeId = event.detail;
    graphData.nodes = graphData.nodes.filter(node => node.id !== nodeId);
    graphData.edges = graphData.edges.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    );
    // Update visualization
    updateVisualization();
  }
  
  function handleEdgeCreate(event) {
    console.log('🔗 Remote edge created:', event.detail);
    const newEdge = event.detail;
    graphData.edges = [...graphData.edges, newEdge];
    updateVisualization();
  }
  
  function handleEdgeUpdate(event) {
    console.log('✏️ Remote edge updated:', event.detail);
    const { edgeId, updates } = event.detail;
    graphData.edges = graphData.edges.map(edge => 
      edge.id === edgeId ? { ...edge, ...updates } : edge
    );
    updateVisualization();
  }
  
  function handleEdgeDelete(event) {
    console.log('🗑️ Remote edge deleted:', event.detail);
    const edgeId = event.detail;
    graphData.edges = graphData.edges.filter(edge => edge.id !== edgeId);
    updateVisualization();
  }
  
  function handleParticipantJoined(event) {
    console.log('👋 Participant joined:', event.detail);
    // Could show notification or update UI
  }
  
  function handleParticipantLeft(event) {
    console.log('👋 Participant left:', event.detail);
    // Could show notification or update UI
  }
  
  function handleRemoteOperation(event) {
    console.log('🔄 Remote operation applied:', event.detail);
    // Operation already applied by collaborative manager
  }
  
  function handleRemoteSelection(event) {
    console.log('🎯 Remote selection changed:', event.detail);
    // Could highlight remotely selected nodes/edges
    const { userId, selectedNodes, selectedEdges } = event.detail;
    // Update UI to show remote selections
  }
  
  function updateVisualization() {
    if (layoutMode === '2d') {
      updateGraph2D();
    } else if (layoutMode === '3d') {
      updateGraph3D();
    }
  }

  // Debounced function for parameter updates (variable declared at top)
  function debouncedParameterUpdate() {
    clearTimeout(parameterUpdateTimeout);
    parameterUpdateTimeout = setTimeout(() => {
      updateSimulationParameters();
    }, 300); // Increased delay to 300ms for better stability
  }

  // Reactive statements to handle parameter changes and prevent artifacts
  $: if (linkStrength !== undefined && simulation) {
    console.log('🔄 Link strength changed:', linkStrength);
    debouncedParameterUpdate();
  }
  
  $: if (chargeStrength !== undefined && simulation) {
    console.log('🔄 Charge strength changed:', chargeStrength);
    debouncedParameterUpdate();
  }
  
  $: if (linkDistance !== undefined && simulation) {
    console.log('🔄 Link distance changed:', linkDistance);
    debouncedParameterUpdate();
  }
  
  $: if (collisionRadius !== undefined && simulation) {
    console.log('🔄 Collision radius changed:', collisionRadius);
    debouncedParameterUpdate();
  }

  // Function to update simulation parameters with complete redraw to prevent artifacts
  function updateSimulationParameters() {
    if (!simulation || !graphData.nodes.length) return;
    
    console.log('🔄 Updating simulation parameters with cleanup');
    
    isRedrawing = true;
    
    // Complete cleanup and redraw to prevent artifacts
    cleanupGraph();
    
    // Reinitialize the graph with new parameters after cleanup
    setTimeout(() => {
      updateGraph();
      isRedrawing = false;
    }, 100);
  }

  // Physics preset configurations
  function applyPhysicsPreset(preset) {
    switch (preset) {
      case 'default':
        linkStrength = 0.2;
        chargeStrength = -400;
        centerForce = 0.1;
        linkDistance = 120;
        collisionRadius = 35;
        break;
      case 'tight':
        linkStrength = 1.5;
        chargeStrength = -800;
        centerForce = 0.3;
        linkDistance = 80;
        collisionRadius = 25;
        break;
      case 'loose':
        linkStrength = 0.3;
        chargeStrength = -200;
        centerForce = 0.05;
        linkDistance = 180;
        collisionRadius = 50;
        break;
      case 'clustered':
        linkStrength = 0.4;
        chargeStrength = -300;
        centerForce = 0.2;
        linkDistance = 90;
        collisionRadius = 40;
        break;
      case 'minimal':
        linkStrength = 0.1;
        chargeStrength = -800;
        centerForce = 0.05;
        linkDistance = 250;
        collisionRadius = 50;
        break;
    }
    
    // Clean up and reinitialize to prevent artifacts with longer delay
    console.log(`🔧 Applying physics preset: ${preset}`);
    cleanupGraph();
    
    // Reinitialize with new parameters after a longer delay for stability
    setTimeout(() => {
      updateGraph();
    }, 200);
  }

  // Calculate enhanced node statistics
  function getNodeStatistics(node) {
    const connectedEdges = graphData.edges.filter(edge => 
      edge.source.id === node.id || edge.target.id === node.id
    );
    
    const neighbors = new Set();
    const incomingEdges = [];
    const outgoingEdges = [];
    const neighborNodes = [];
    
    connectedEdges.forEach(edge => {
      if (edge.source.id === node.id) {
        neighbors.add(edge.target.id);
        outgoingEdges.push(edge);
        neighborNodes.push(edge.target);
      } else if (edge.target.id === node.id) {
        neighbors.add(edge.source.id);
        incomingEdges.push(edge);
        neighborNodes.push(edge.source);
      }
    });
    
    const relationshipTypes = [...new Set(connectedEdges.map(edge => edge.type))];
    const avgEdgeStrength = connectedEdges.length > 0 
      ? connectedEdges.reduce((sum, edge) => sum + (edge.strength || 0), 0) / connectedEdges.length 
      : 0;
    
    const centrality = neighbors.size / Math.max(1, graphData.nodes.length - 1);
    
    return {
      degree: connectedLinks.length,
      neighbors: neighbors.size,
      incomingConnections: incomingLinks.length,
      outgoingConnections: outgoingLinks.length,
      relationshipTypes: relationshipTypes,
      avgLinkStrength: avgLinkStrength,
      centrality: centrality,
      keyPhrases: node.keyPhrases || [],
      lastUpdated: node.timestamp ? new Date(node.timestamp).toLocaleDateString() : 'Unknown',
      
      // Detailed information for interactivity
      connectedLinks: connectedLinks,
      incomingLinks: incomingLinks,
      outgoingLinks: outgoingLinks,
      neighborNodes: neighborNodes,
      neighborNames: neighborNodes.map(n => n.label || n.id)
    };
  }

  // State for interactive statistics
  let highlightedConnections = new Set();
  let selectedStatistic = null;
  let showConnectionDetails = false;

  // Function to handle clicking on statistics
  function handleStatisticClick(statType, nodeStats) {
    console.log(`🔍 Clicked on ${statType} statistic`);
    
    // Clear previous highlights
    highlightedConnections.clear();
    
    // Set which statistic is selected
    selectedStatistic = statType;
    showConnectionDetails = true;
    
    // Highlight relevant connections based on statistic type
    switch (statType) {
      case 'totalConnections':
        nodeStats.connectedLinks.forEach(link => {
          highlightedConnections.add(link.source.id + '-' + link.target.id);
        });
        break;
      case 'incomingLinks':
        nodeStats.incomingLinks.forEach(link => {
          highlightedConnections.add(link.source.id + '-' + link.target.id);
        });
        break;
      case 'outgoingLinks':
        nodeStats.outgoingLinks.forEach(link => {
          highlightedConnections.add(link.source.id + '-' + link.target.id);
        });
        break;
      case 'neighbors':
        nodeStats.connectedLinks.forEach(link => {
          highlightedConnections.add(link.source.id + '-' + link.target.id);
        });
        break;
    }
    
    // Update the graph visualization
    updateGraphHighlights();
  }

  // Function to update graph highlights
  function updateGraphHighlights() {
    if (!svg) return;
    
    // Highlight links
    svg.selectAll('.link')
      .style('stroke', d => {
        const linkKey = d.source.id + '-' + d.target.id;
        const reverseKey = d.target.id + '-' + d.source.id;
        return highlightedConnections.has(linkKey) || highlightedConnections.has(reverseKey) 
          ? '#FFD700' 
          : relationshipTypes[d.type]?.color || '#999';
      })
      .style('stroke-width', d => {
        const linkKey = d.source.id + '-' + d.target.id;
        const reverseKey = d.target.id + '-' + d.source.id;
        return highlightedConnections.has(linkKey) || highlightedConnections.has(reverseKey) 
          ? Math.max(3, (d.strength || 0.5) * 6)
          : Math.max(1, (d.strength || 0.5) * 3);
      })
      .style('opacity', d => {
        const linkKey = d.source.id + '-' + d.target.id;
        const reverseKey = d.target.id + '-' + d.source.id;
        return highlightedConnections.has(linkKey) || highlightedConnections.has(reverseKey) 
          ? 1.0 
          : 0.4;
      });
    
    // Highlight connected nodes
    svg.selectAll('.node')
      .style('opacity', d => {
        if (d.id === selectedNode?.id) return 1.0;
        
        const hasHighlightedConnection = [...highlightedConnections].some(linkKey => {
          const [sourceId, targetId] = linkKey.split('-');
          return sourceId === d.id || targetId === d.id;
        });
        
        return hasHighlightedConnection ? 1.0 : 0.4;
      })
      .style('stroke', d => {
        const hasHighlightedConnection = [...highlightedConnections].some(linkKey => {
          const [sourceId, targetId] = linkKey.split('-');
          return sourceId === d.id || targetId === d.id;
        });
        
        return hasHighlightedConnection ? '#FFD700' : 'none';
      })
      .style('stroke-width', d => {
        const hasHighlightedConnection = [...highlightedConnections].some(linkKey => {
          const [sourceId, targetId] = linkKey.split('-');
          return sourceId === d.id || targetId === d.id;
        });
        
        return hasHighlightedConnection ? '3px' : '0px';
      });
  }

  // Function to clear highlights
  function clearHighlights() {
    highlightedConnections.clear();
    selectedStatistic = null;
    showConnectionDetails = false;
    
    if (!svg) return;
    
    // Reset link styles
    svg.selectAll('.link')
      .style('stroke', d => relationshipTypes[d.type]?.color || '#999')
      .style('stroke-width', d => Math.max(1, (d.strength || 0.5) * 3))
      .style('opacity', d => showOnlyStrongRelations ? (d.strength || 0) * 2 : Math.max(0.3, (d.strength || 0.5)));
    
    // Reset node styles
    svg.selectAll('.node')
      .style('opacity', 1.0)
      .style('stroke', 'none')
      .style('stroke-width', '0px');
  }

  // Reactive statements to handle parameter changes and prevent artifacts
  $: if (linkStrength !== undefined && simulation) {
    debouncedParameterUpdate();
  }
  
  $: if (chargeStrength !== undefined && simulation) {
    debouncedParameterUpdate();
  }
  
  $: if (linkDistance !== undefined && simulation) {
    debouncedParameterUpdate();
  }
  
  $: if (collisionRadius !== undefined && simulation) {
    debouncedParameterUpdate();
  }

  // Reactive statements for display options that might cause artifacts
  $: if (showLabels !== undefined && svg) {
    debouncedDisplayUpdate();
  }
  
  $: if (showEdgeLabels !== undefined && svg) {
    debouncedDisplayUpdate();
  }
  
  $: if (enableWordWrap !== undefined && svg) {
    debouncedDisplayUpdate();
  }

  // Debounced display update function
  function debouncedDisplayUpdate() {
    clearTimeout(parameterUpdateTimeout);
    parameterUpdateTimeout = setTimeout(() => {
      if (graphData.nodes.length > 0) {
        console.log('🎨 Updating display options with cleanup');
        cleanupGraph();
        setTimeout(() => {
          updateGraph();
        }, 100);
      }
    }, 200); // Slightly longer delay for display updates
  }
</script>

<!-- Main Knowledge Graph Component -->
<div class="knowledge-graph-container">
  <!-- Header -->
  <div class="graph-header">
    <div class="title-section">
      <h2 class="graph-title">
        <span class="title-icon">🧠</span>
        Knowledge Graph Explorer
        <span class="version-badge">Enhanced</span>
      </h2>
      <p class="subtitle">Interactive semantic knowledge visualization with intelligent relationship inference</p>
    </div>
    
    <div class="status-indicators">
      <div class="status-item">
        <span class="status-value">{graphData.nodes.length}</span>
        <span class="status-label">Concepts</span>
      </div>
      <div class="status-item">
        <span class="status-value">{graphData.edges.length}</span>
        <span class="status-label">Relationships</span>
      </div>
      <div class="status-item">
        <span class="status-value">{graphData.edges.filter(e => e.generated).length}</span>
        <span class="status-label">Inferred</span>
      </div>
      <div class="status-health {loading ? 'loading' : error ? 'error' : 'healthy'}">
        {loading ? '🔄' : error ? '❌' : '✅'}
      </div>
    </div>
  </div>

  <!-- Controls Panel -->
  <div class="controls-panel">
    <div class="control-section">
      <div class="section-title">🔍 Discovery & Search</div>
      <div class="search-enhanced">
        <div class="search-input-container">
          <input 
            type="text" 
            placeholder="Search concepts, relationships, or content..." 
            bind:value={searchQuery}
            on:input={handleSearch}
            class="search-input-enhanced"
          />
          <button class="search-button" on:click={handleSearch}>
            <span class="search-icon">🔍</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="control-section">
      <div class="section-title">🎛️ Visualization Settings</div>
      <div class="control-grid">
        <div class="control-group">
          <div class="control-label">
            <span class="label-icon">🏗️</span>
            Layout Mode
            <span class="mode-preview">{layoutModes.find(m => m.id === layoutMode)?.description || ''}</span>
          </div>
          <div class="mode-selector">
            {#each layoutModes as mode}
              <button 
                class="modern-mode-button {layoutMode === mode.id ? 'active' : ''}"
                on:click={() => changeLayoutMode(mode.id)}
                title="{mode.name} - {mode.description}"
              >
                <span class="mode-icon-large">{mode.icon}</span>
                <div class="mode-details">
                  <span class="mode-name">{mode.name}</span>
                  <span class="mode-description">{mode.description}</span>
                </div>
                {#if layoutMode === mode.id}
                  <span class="active-indicator">✓</span>
                {/if}
              </button>
            {/each}
          </div>
        </div>
        
        <div class="control-group">
          <div class="control-label">
            <span class="label-icon">🎨</span>
            Color Scheme
            <span class="mode-preview">{colorModes.find(m => m.id === colorMode)?.description || ''}</span>
          </div>
          <div class="mode-selector">
            {#each colorModes as mode}
              <button 
                class="modern-mode-button {colorMode === mode.id ? 'active' : ''}"
                on:click={() => changeColorMode(mode.id)}
                title="{mode.name} - {mode.description}"
              >
                <span class="mode-icon-large">{mode.icon}</span>
                <div class="mode-details">
                  <span class="mode-name">{mode.name}</span>
                  <span class="mode-description">{mode.description}</span>
                </div>
                {#if colorMode === mode.id}
                  <span class="active-indicator">✓</span>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      </div>
    </div>
    
    <div class="control-section">
      <div class="section-title">⚙️ Display & Behavior</div>
      <div class="control-grid">
        <div class="display-toggles">
          <label class="modern-toggle">
            <input type="checkbox" bind:checked={showLabels} on:change={updateGraph} />
            <span class="toggle-slider modern"></span>
            <div class="toggle-content">
              <span class="toggle-icon">🏷️</span>
              <div class="toggle-text">
                <span class="toggle-title">Node Labels</span>
                <span class="toggle-desc">Show concept names</span>
              </div>
            </div>
          </label>
          
          <label class="modern-toggle">
            <input type="checkbox" bind:checked={showEdgeLabels} on:change={updateGraph} />
            <span class="toggle-slider modern"></span>
            <div class="toggle-content">
              <span class="toggle-icon">🔗</span>
              <div class="toggle-text">
                <span class="toggle-title">Relationship Labels</span>
                <span class="toggle-desc">Show connection types</span>
              </div>
            </div>
          </label>
          
          <label class="modern-toggle">
            <input type="checkbox" bind:checked={showOnlyStrongRelations} on:change={updateGraph} />
            <span class="toggle-slider modern"></span>
            <div class="toggle-content">
              <span class="toggle-icon">💪</span>
              <div class="toggle-text">
                <span class="toggle-title">Strong Links Only</span>
                <span class="toggle-desc">Filter weak connections</span>
              </div>
            </div>
          </label>
          
          <label class="modern-toggle">
            <input type="checkbox" bind:checked={showStatistics} on:change={updateGraph} />
            <span class="toggle-slider modern"></span>
            <div class="toggle-content">
              <span class="toggle-icon">📊</span>
              <div class="toggle-text">
                <span class="toggle-title">Interactive Stats</span>
                <span class="toggle-desc">Show clickable metrics</span>
              </div>
            </div>
          </label>
        </div>
        
        <div class="physics-presets">
          <div class="control-label">
            <span class="label-icon">🎯</span>
            Graph Behavior
          </div>
          <div class="preset-buttons">
            <button class="preset-button" on:click={() => applyPhysicsPreset('tight')}>
              <span class="preset-icon">🔗</span>
              <div class="preset-details">
                <span class="preset-name">Tight Clustering</span>
                <span class="preset-desc">Dense, connected groups</span>
              </div>
            </button>
            <button class="preset-button" on:click={() => applyPhysicsPreset('loose')}>
              <span class="preset-icon">🌌</span>
              <div class="preset-details">
                <span class="preset-name">Loose Spread</span>
                <span class="preset-desc">Spacious, clear layout</span>
              </div>
            </button>
            <button class="preset-button" on:click={() => applyPhysicsPreset('balanced')}>
              <span class="preset-icon">⚖️</span>
              <div class="preset-details">
                <span class="preset-name">Balanced</span>
                <span class="preset-desc">Optimal for most graphs</span>
              </div>
            </button>
          </div>
          
          <div class="fine-tune-controls" style="margin-top: 16px;">
            <label class="modern-slider">
              <div class="slider-header">
                <span class="slider-icon">📏</span>
                <span class="slider-title">Node Size</span>
                <span class="slider-value">{nodeSize.toFixed(1)}x</span>
              </div>
              <input 
                type="range" 
                min="0.5" 
                max="3.0" 
                step="0.1" 
                bind:value={nodeSize} 
                on:input={updateGraph}
                class="modern-range"
              />
            </label>
            
            <label class="modern-slider">
              <div class="slider-header">
                <span class="slider-icon">🔗</span>
                <span class="slider-title">Connection Strength</span>
                <span class="slider-value">{Math.round(linkStrength * 100)}%</span>
              </div>
              <input 
                type="range" 
                min="0.1" 
                max="2.0" 
                step="0.1" 
                bind:value={linkStrength} 
                on:input={updateGraph}
                class="modern-range"
              />
            </label>
          </div>
        </div>
        
        <!-- Advanced Features Control Section -->
        <div class="control-group advanced-features">
          <div class="control-label">
            <span class="label-icon">⚡</span>
            Advanced Features
            <span class="mode-preview">Enhanced performance, analytics & collaboration</span>
          </div>
          <div class="advanced-toggles">
            <label class="toggle-control">
              <input type="checkbox" bind:checked={advancedMode} />
              <span class="toggle-slider"></span>
              <span class="toggle-label">Advanced Mode</span>
            </label>
            
            {#if advancedMode}
              <label class="toggle-control secondary">
                <input type="checkbox" bind:checked={performanceMode} />
                <span class="toggle-slider"></span>
                <span class="toggle-label">3D Performance Optimization</span>
              </label>
              
              <label class="toggle-control secondary">
                <input type="checkbox" bind:checked={analyticsVisible} />
                <span class="toggle-slider"></span>
                <span class="toggle-label">Knowledge Analytics</span>
              </label>
              
              <label class="toggle-control secondary">
                <input type="checkbox" bind:checked={collaborativeMode} />
                <span class="toggle-slider"></span>
                <span class="toggle-label">Collaborative Editing</span>
              </label>
              
              {#if collaborativeMode}
                <div class="collaboration-settings">
                  <div class="mini-control">
                    <label>Session ID:</label>
                    <input type="text" bind:value={sessionId} placeholder="Enter session ID or leave empty">
                  </div>
                </div>
              {/if}
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Main Visualization Area -->
  <div class="visualization-container">
    <div class="graph-area">
      <div class="graph-viewport" bind:this={graphContainer}>
        {#if loading}
          <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">Loading knowledge graph...</div>
          </div>
        {/if}
        
        {#if error}
          <div class="error-overlay">
            <div class="error-icon">⚠️</div>
            <div class="error-text">{error}</div>
            <button class="retry-button" on:click={() => loadGraphData()}>Retry</button>
          </div>
        {/if}
      </div>
      
      <!-- Advanced Features Integration -->
      {#if advancedMode}
        <!-- Analytics Overlay -->
        <KnowledgeGraphAnalytics 
          bind:this={analyticsComponent}
          {graphData}
          {selectedNode}
          isVisible={analyticsVisible}
        />
        
        <!-- Performance Manager for 3D optimization -->
        {#if layoutMode === '3d' && performanceMode}
          <KnowledgeGraphPerformanceManager
            bind:this={performanceManager}
            {scene}
            {camera}
            {renderer}
            {graphData}
            isPerformanceMode={performanceMode}
          />
        {/if}
        
        <!-- Collaborative Manager -->
        {#if collaborativeMode}
          <KnowledgeGraphCollaborativeManager
            bind:this={collaborativeManager}
            {graphData}
            userId={currentUserId}
            {sessionId}
            isEnabled={collaborativeMode}
            on:graphDataSync={handleGraphDataSync}
            on:nodeCreate={handleNodeCreate}
            on:nodeUpdate={handleNodeUpdate}
            on:nodeDelete={handleNodeDelete}
            on:edgeCreate={handleEdgeCreate}
            on:edgeUpdate={handleEdgeUpdate}
            on:edgeDelete={handleEdgeDelete}
            on:participantJoined={handleParticipantJoined}
            on:participantLeft={handleParticipantLeft}
            on:remoteOperation={handleRemoteOperation}
            on:remoteSelection={handleRemoteSelection}
          />
        {/if}
      {/if}
    </div>

    <!-- Information Panel -->
    <div class="info-panel">
      {#if selectedNode}
        <div class="node-details-card">
          <div class="card-header">
            <div class="node-title-area">
              <span class="node-category-icon">
                {nodeCategories[selectedNode.category]?.icon || '•'}
              </span>
              <div class="node-title-text">
                <h3 class="node-title">{selectedNode.label}</h3>
                <span class="node-category-badge">
                  {nodeCategories[selectedNode.category]?.description || selectedNode.category}
                </span>
              </div>
            </div>
            <button class="close-button" on:click={() => selectedNode = null}>✕</button>
          </div>
          
          <div class="card-content">
            <!-- Enhanced Metrics Display -->
            <div class="metrics-grid">
              <div class="metric-item">
                <div class="metric-label">Importance</div>
                <div class="metric-bar">
                  <div class="metric-fill importance" style="width: {(selectedNode.importance || 0) * 100}%"></div>
                </div>
                <div class="metric-value">{Math.round((selectedNode.importance || 0) * 100)}%</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-label">Confidence</div>
                <div class="metric-bar">
                  <div class="metric-fill confidence" style="width: {(selectedNode.confidence || 0) * 100}%"></div>
                </div>
                <div class="metric-value">{Math.round((selectedNode.confidence || 0) * 100)}%</div>
              </div>
              
              <div class="metric-item">
                <div class="metric-label">Recency</div>
                <div class="metric-bar">
                  <div class="metric-fill recency" style="width: {(selectedNode.recency || 0) * 100}%"></div>
                </div>
                <div class="metric-value">{Math.round((selectedNode.recency || 0) * 100)}%</div>
              </div>
            </div>
            
            <!-- Enhanced Statistics Display -->
            {#if showStatistics}
              {@const stats = getNodeStatistics(selectedNode)}
              <div class="statistics-section">
                <div class="section-header">
                 
                  <h4 class="section-title">📊 Network Statistics</h4>
                  {#if selectedStatistic}
                    <button class="clear-highlights-btn" on:click={clearHighlights}>
                      Clear Highlights
                    </button>
                  {/if}
                </div>
                
                <div class="stats-grid">
                  <button 
                    class="stat-item clickable {selectedStatistic === 'totalConnections' ? 'selected' : ''}"
                    on:click={() => handleStatisticClick('totalConnections', stats)}
                    title="Click to highlight all connections in the graph"
                  >
                    <div class="stat-icon">🔗</div>
                    <div class="stat-info">
                      <div class="stat-value">{stats.degree}</div>
                      <div class="stat-label">Total Connections</div>
                    </div>
                  </button>
                  
                  <button 
                    class="stat-item clickable {selectedStatistic === 'neighbors' ? 'selected' : ''}"
                    on:click={() => handleStatisticClick('neighbors', stats)}
                    title="Click to highlight unique neighbors"
                  >
                    <div class="stat-icon">👥</div>
                    <div class="stat-info">
                      <div class="stat-value">{stats.neighbors}</div>
                      <div class="stat-label">Unique Neighbors</div>
                    </div>
                  </button>
                  
                  <button 
                    class="stat-item clickable {selectedStatistic === 'incomingLinks' ? 'selected' : ''}"
                    on:click={() => handleStatisticClick('incomingLinks', stats)}
                    title="Click to highlight incoming connections"
                  >
                    <div class="stat-icon">⬇️</div>
                    <div class="stat-info">
                      <div class="stat-value">{stats.incomingConnections}</div>
                      <div class="stat-label">Incoming Links</div>
                    </div>
                  </button>
                  
                  <button 
                    class="stat-item clickable {selectedStatistic === 'outgoingLinks' ? 'selected' : ''}"
                    on:click={() => handleStatisticClick('outgoingLinks', stats)}
                    title="Click to highlight outgoing connections"
                  >
                    <div class="stat-icon">⬆️</div>
                    <div class="stat-info">
                      <div class="stat-value">{stats.outgoingConnections}</div>
                      <div class="stat-label">Outgoing Links</div>
                    </div>
                  </button>
                  
                  <div class="stat-item">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-info">
                      <div class="stat-value">{Math.round(stats.centrality * 100)}%</div>
                      <div class="stat-label">Centrality</div>
                    </div>
                  </div>
                  
                  <div class="stat-item">
                    <div class="stat-icon">💪</div>
                    <div class="stat-info">
                      <div class="stat-value">{stats.avgLinkStrength.toFixed(2)}</div>
                      <div class="stat-label">Avg Link Strength</div>
                    </div>
                  </div>
                </div>
                
                <!-- Connection Details Panel -->
                {#if showConnectionDetails && selectedStatistic}
                  <div class="connection-details">
                    <h5 class="details-title">
                      {#if selectedStatistic === 'totalConnections'}
                        🔗 All {stats.degree} Connections
                      {:else if selectedStatistic === 'incomingLinks'}
                        ⬇️ {stats.incomingConnections} Incoming Links
                      {:else if selectedStatistic === 'outgoingLinks'}
                        ⬆️ {stats.outgoingConnections} Outgoing Links
                      {:else if selectedStatistic === 'neighbors'}
                        👥 {stats.neighbors} Unique Neighbors
                      {/if}
                    </h5>
                    
                    <div class="connection-list">
                      {#if selectedStatistic === 'totalConnections'}
                        {#each stats.connectedLinks as link}
                          <div class="connection-item">
                            <div class="connection-nodes">
                              <span class="node-name">{link.source.label || link.source.id}</span>
                              <span class="connection-arrow">
                                {#if link.source.id === selectedNode.id}→{:else}←{/if}
                              </span>
                              <span class="node-name">{link.target.label || link.target.id}</span>
                            </div>
                            <div class="connection-meta">
                              <span class="connection-type">{relationshipTypes[link.type]?.label || link.type}</span>
                              <span class="connection-strength">{Math.round((link.strength || 0) * 100)}%</span>
                            </div>
                          </div>
                        {/each}
                      {:else if selectedStatistic === 'incomingLinks'}
                        {#each stats.incomingLinks as link}
                          <div class="connection-item">
                            <div class="connection-nodes">
                              <span class="node-name">{link.source.label || link.source.id}</span>
                              <span class="connection-arrow">→</span>
                              <span class="node-name">{selectedNode.label}</span>
                            </div>
                            <div class="connection-meta">
                              <span class="connection-type">{relationshipTypes[link.type]?.label || link.type}</span>
                              <span class="connection-strength">{Math.round((link.strength || 0) * 100)}%</span>
                            </div>
                          </div>
                        {/each}
                      {:else if selectedStatistic === 'outgoingLinks'}
                        {#each stats.outgoingLinks as link}
                          <div class="connection-item">
                            <div class="connection-nodes">
                              <span class="node-name">{selectedNode.label}</span>
                              <span class="connection-arrow">→</span>
                              <span class="node-name">{link.target.label || link.target.id}</span>
                            </div>
                            <div class="connection-meta">
                              <span class="connection-type">{relationshipTypes[link.type]?.label || link.type}</span>
                              <span class="connection-strength">{Math.round((link.strength || 0) * 100)}%</span>
                            </div>
                          </div>
                        {/each}
                      {:else if selectedStatistic === 'neighbors'}
                        <div class="neighbor-list">
                          {#each stats.neighborNames as neighborName, index}
                            <span class="neighbor-tag">{neighborName}</span>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  </div>
                {/if}
                
                <!-- Relationship Types -->
                {#if stats.relationshipTypes.length > 0}
                  <div class="relationship-types">
                    <h5 class="subsection-title">🔗 Relationship Types</h5>
                    <div class="relationship-tags">
                      {#each stats.relationshipTypes as relType}
                        <span class="relationship-tag" style="background-color: {relationshipTypes[relType]?.color || '#999'}">
                          {relationshipTypes[relType]?.label || relType}
                        </span>
                      {/each}
                    </div>
                  </div>
                {/if}
                
                <!-- Key Phrases -->
                {#if stats.keyPhrases.length > 0}
                  <div class="key-phrases">
                    <h5 class="subsection-title">🔍 Key Phrases</h5>
                    <div class="phrase-tags">
                      {#each stats.keyPhrases.slice(0, 6) as phrase}
                        <span class="phrase-tag">{phrase}</span>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            {/if}
            
            <!-- Content Preview -->
            {#if selectedNode.content || selectedNode.summary}
              <div class="content-section">
                <h4 class="section-title">📄 Content</h4>
                <div class="content-preview">
                  {selectedNode.summary || selectedNode.content || 'No content available'}
                </div>
              </div>
            {/if}
            
            <!-- Metadata -->
            <div class="metadata-section">
              <h4 class="section-title">ℹ️ Metadata</h4>
              <div class="metadata-grid">
                <div class="metadata-item">
                  <span class="metadata-label">Node ID:</span>
                  <span class="metadata-value">{selectedNode.id}</span>
                </div>
                <div class="metadata-item">
                  <span class="metadata-label">Category:</span>
                  <span class="metadata-value">{selectedNode.category}</span>
                </div>
                <div class="metadata-item">
                  <span class="metadata-label">Last Updated:</span>
                  <span class="metadata-value">{getNodeStatistics(selectedNode).lastUpdated}</span>
                </div>
                {#if selectedNode.originalData}
                  <div class="metadata-item">
                    <span class="metadata-label">Source:</span>
                    <span class="metadata-value">{selectedNode.originalData.source || 'Knowledge Base'}</span>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {:else}
        <div class="welcome-panel">
          <div class="welcome-icon">🎯</div>
          <h3 class="welcome-title">Explore Knowledge</h3>
          <p class="welcome-text">Click on any node to view detailed information, relationships, and semantic analysis.</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .knowledge-graph-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 800px;
  }

  /* Header Styles */
  .graph-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  .title-section h2 {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .title-icon {
    font-size: 32px;
  }

  .version-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }

  .subtitle {
    margin: 8px 0 0 0;
    opacity: 0.8;
    font-size: 14px;
    line-height: 1.5;
  }

  .status-indicators {
    display: flex;
    gap: 20px;
    align-items: center;
  }

  .status-item {
    text-align: center;
    background: rgba(255, 255, 255, 0.1);
    padding: 12px 16px;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .status-value {
    display: block;
    font-size: 24px;
    font-weight: 700;
    line-height: 1;
  }

  .status-label {
    display: block;
    font-size: 12px;
    opacity: 0.8;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .status-health {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  /* Controls Panel */
  .controls-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 24px;
    margin-bottom: 24px;
  }

  .control-section {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .search-enhanced {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .search-input-container {
    display: flex;
    gap: 8px;
  }

  .search-input-enhanced {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    font-size: 14px;
    transition: all 0.3s ease;
  }

  .search-input-enhanced::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  .search-input-enhanced:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2);
  }

  .search-button {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    border: none;
    border-radius: 12px;
    color: white;
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .search-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
  }

  .control-grid {
    display: grid;
    gap: 20px;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .control-label {
    font-size: 14px;
    font-weight: 600;
    opacity: 0.9;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .label-icon {
    font-size: 16px;
  }

  .mode-preview {
    font-size: 12px;
    opacity: 0.7;
    font-weight: 400;
    margin-left: auto;
  }

  /* Modern Mode Buttons */
  .mode-selector {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .modern-mode-button {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: left;
    position: relative;
    overflow: hidden;
  }

  .modern-mode-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(46, 125, 50, 0.1));
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .modern-mode-button:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }

  .modern-mode-button:hover::before {
    opacity: 1;
  }

  .modern-mode-button.active {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(46, 125, 50, 0.2));
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.3);
  }

  .modern-mode-button.active::before {
    opacity: 1;
  }

  .mode-icon-large {
    font-size: 24px;
    min-width: 24px;
    z-index: 1;
  }

  .mode-details {
    flex: 1;
    z-index: 1;
  }

  .mode-name {
    display: block;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 2px;
  }

  .mode-description {
    display: block;
    font-size: 12px;
    opacity: 0.7;
    line-height: 1.3;
  }

  .active-indicator {
    font-size: 18px;
    color: #4CAF50;
    z-index: 1;
  }

  /* Modern Toggles */
  .display-toggles {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .modern-toggle {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .modern-toggle:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
  }

  .toggle-slider.modern {
    position: relative;
    width: 44px;
    height: 24px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    transition: all 0.3s ease;
    flex-shrink: 0;
  }

  .toggle-slider.modern::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  input[type="checkbox"]:checked + .toggle-slider.modern {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
  }

  input[type="checkbox"]:checked + .toggle-slider.modern::before {
    transform: translateX(20px);
  }

  .toggle-content {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
  }

  .toggle-icon {
    font-size: 18px;
    min-width: 18px;
  }

  .toggle-text {
    flex: 1;
  }

  .toggle-title {
    display: block;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.2;
  }

  .toggle-desc {
    display: block;
    font-size: 12px;
    opacity: 0.7;
    line-height: 1.2;
  }

  /* Physics Presets */
  .physics-presets {
    margin-top: 20px;
  }

  .preset-buttons {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .preset-button {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: left;
  }

  .preset-button:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
  }

  .preset-icon {
    font-size: 20px;
    min-width: 20px;
  }

  .preset-details {
    flex: 1;
  }

  .preset-name {
    display: block;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 2px;
  }

  .preset-desc {
    display: block;
    font-size: 11px;
    opacity: 0.7;
    line-height: 1.2;
  }

  /* Modern Sliders */
  .fine-tune-controls {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .modern-slider {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .slider-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .slider-icon {
    font-size: 14px;
  }

  .slider-title {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
  }

  .slider-value {
    font-size: 12px;
    font-weight: 600;
    color: #4CAF50;
  }

  .modern-range {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    outline: none;
    appearance: none;
    cursor: pointer;
    transition: background 0.3s ease;
  }

  .modern-range:hover {
    background: rgba(255, 255, 255, 0.25);
  }

  .modern-range::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
  }

  .modern-range::-webkit-slider-thumb:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  }

  .modern-range::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }

  input[type="checkbox"] {
    display: none;
  }

  /* Visualization Area */
  .visualization-container {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 24px;
    height: 600px;
    position: relative;
    z-index: 1;
  }

  .graph-area {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    background: rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .graph-viewport {
    width: 100%;
    height: 100%;
    position: relative;
  }

  .loading-overlay,
  .error-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    z-index: 10;
  }

  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top: 4px solid #4CAF50;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }

  .loading-text,
  .error-text {
    color: white;
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 16px;
  }

  .error-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .retry-button {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
  }

  .retry-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
  }

  /* Information Panel */
  .info-panel {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .node-details-card {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .card-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .node-title-area {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
  }

  .node-category-icon {
    font-size: 24px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .node-title-text {
    flex: 1;
  }

  .node-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.2;
  }

  .node-category-badge {
    background: rgba(255, 255, 255, 0.15);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
    display: inline-block;
  }

  .close-button {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.1);
  }

  .card-content {
    padding: 20px;
    flex: 1;
    overflow-y: auto;
  }

  .metrics-grid {
    display: grid;
    gap: 16px;
    margin-bottom: 24px;
  }

  .metric-item {
    display: grid;
    grid-template-columns: 80px 1fr 40px;
    align-items: center;
    gap: 12px;
  }

  .metric-label {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.8;
  }

  .metric-bar {
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .metric-fill {
    height: 100%;
    border-radius: 4px;
    transition: all 0.3s ease;
  }

  .metric-fill.importance {
    background: linear-gradient(90deg, #4CAF50, #2E7D32);
  }

  .metric-fill.confidence {
    background: linear-gradient(90deg, #2196F3, #1565C0);
  }

  .metric-fill.recency {
    background: linear-gradient(90deg, #FF9800, #F57C00);
  }

  .metric-value {
    font-size: 12px;
    font-weight: 600;
    text-align: right;
  }

  .content-section {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 16px;
  }

  .section-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .content-preview {
    background: rgba(255, 255, 255, 0.05);
    padding: 12px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.5;
    border-left: 3px solid #4CAF50;
  }

  .welcome-panel {
    padding: 40px 20px;
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .welcome-icon {
    font-size: 64px;
    margin-bottom: 20px;
    opacity: 0.7;
  }

  .welcome-title {
    margin: 0 0 16px 0;
    font-size: 20px;
    font-weight: 600;
  }

  .welcome-text {
    margin: 0;
    opacity: 0.8;
    line-height: 1.5;
    max-width: 300px;
  }

  /* Animations */
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .visualization-container {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
      height: auto;
    }
    
    .controls-panel {
      grid-template-columns: 1fr;
    }
    
    .graph-area {
      height: 500px;
    }
  }

  /* Physics Controls */
  .physics-controls {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .slider-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 16px;
  }

  .slider-label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
  }

  .physics-slider {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    outline: none;
    appearance: none;
    cursor: pointer;
  }

  .physics-slider::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: #4CAF50;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .physics-slider::-moz-range-thumb {
    width:  16px;
    height: 16px;
    background: #4CAF50;
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .physics-presets {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .preset-button {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 11px;
    font-weight: 500;
    transition: all 0.3s ease;
    text-align: center;
  }

  .preset-button:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-1px);
  }

  .redraw-button {
    background: rgba(76, 175, 80, 0.2) !important;
    border: 1px solid rgba(76, 175, 80, 0.4) !important;
    color: #4CAF50 !important;
    font-weight: 600 !important;
  }

  .redraw-button:hover {
    background: rgba(76, 175, 80, 0.3) !important;
    border: 1px solid rgba(76, 175, 80, 0.6) !important;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }

  /* Enhanced Statistics */
  .statistics-section {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 16px;
    margin-top: 16px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.05);
    padding: 10px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }

  .stat-item.clickable {
    cursor: pointer;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .stat-item.clickable:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 215, 0, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .stat-item.selected {
    background: rgba(255, 215, 0, 0.15);
    border-color: rgba(255, 215, 0, 0.6);
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.3);
  }

  .stat-icon {
    font-size: 16px;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
  }

  .stat-info {
    flex: 1;
  }

  .stat-value {
    font-size: 16px;
    font-weight: 700;
    line-height: 1;
  }

  .stat-label {
    font-size: 10px;
    opacity: 0.8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
  }

  .subsection-title {
    margin: 16px 0 8px 0;
    font-size: 13px;
    font-weight: 600;
    opacity: 0.9;
  }

  .relationship-tags, .phrase-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .relationship-tag {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 500;
    color: white;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .phrase-tag {
    background: rgba(255, 255, 255, 0.15);
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .metadata-section {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 16px;
    margin-top: 16px;
  }

  .metadata-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  /* Interactive Statistics Styles */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .clear-highlights-btn {
    background: rgba(255, 100, 100, 0.8);
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .clear-highlights-btn:hover {
    background: rgba(255, 100, 100, 1);
    transform: scale(1.05);
  }

  /* Connection details panel */
  .connection-details {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
    border-left: 3px solid #FFD700;
    animation: slideIn 0.3s ease-out;
  }

  .details-title {
    margin: 0 0 12px 0;
    font-size: 13px;
    font-weight: 600;
    color: #FFD700;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .connection-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
  }

  .connection-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 8px;
    border-left: 2px solid #4CAF50;
    transition: all 0.2s ease;
  }

  .connection-item:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(2px);
  }

  .connection-nodes {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    flex-wrap: wrap;
  }

  .node-name {
    font-size: 12px;
    font-weight: 500;
    color: #E3F2FD;
    background: rgba(0, 0, 0, 0.2);
    padding: 2px 6px;
    border-radius: 4px;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .node-name.current {
    background: rgba(255, 215, 0, 0.3);
    color: #FFD700;
    font-weight: 600;
  }

  .connection-arrow {
    font-size: 12px;
    color: #4CAF50;
    font-weight: bold;
    flex-shrink: 0;
  }

  .connection-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    gap: 8px;
  }

  .connection-type {
    background: rgba(76, 175, 80, 0.2);
    color: #4CAF50;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 500;
    font-size: 10px;
  }

  .connection-strength {
    color: #FFF9C4;
    font-weight: 600;
    flex-shrink: 0;
  }

  .neighbor-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    max-height: 120px;
    overflow-y: auto;
  }

  .neighbor-tag {
    background: rgba(33, 150, 243, 0.2);
    color: #2196F3;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid rgba(33, 150, 243, 0.3);
    transition: all 0.2s ease;
  }

  .neighbor-tag:hover {
    background: rgba(33, 150, 243, 0.3);
    transform: scale(1.05);
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .metadata-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    font-size: 12px;
  }

  .metadata-label {
    font-weight: 500;
    opacity: 0.8;
  }

  .metadata-value {
    font-weight: 600;
    font-family: 'Monaco', 'Consolas', monospace;
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
  }

  @media (max-width: 1200px) {
    .visualization-container {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
      height: auto;
    }
    
    .controls-panel {
      grid-template-columns: 1fr;
    }
    
    .graph-area {
      height: 500px;
    }
  }

  @media (max-width: 768px) {
    .knowledge-graph-container {
      padding: 16px;
    }
    
    .graph-header {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
    }
    
    .status-indicators {
      justify-content: space-between;
    }
    
    .button-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  /* Advanced Features Styles */
  .advanced-features {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(33, 150, 243, 0.1));
    border: 2px solid rgba(76, 175, 80, 0.3);
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
  }
  
  .advanced-toggles {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 16px;
  }
  
  .toggle-control {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    padding: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .toggle-control:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-1px);
  }
  
  .toggle-control.secondary {
    margin-left: 20px;
    background: rgba(33, 150, 243, 0.1);
    border-color: rgba(33, 150, 243, 0.3);
  }
  
  .toggle-control input[type="checkbox"] {
    display: none;
  }
  
  .toggle-slider {
    position: relative;
    width: 50px;
    height: 24px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    transition: all 0.3s ease;
    cursor: pointer;
  }
  
  .toggle-slider::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .toggle-control input[type="checkbox"]:checked + .toggle-slider {
    background: #4CAF50;
  }
  
  .toggle-control input[type="checkbox"]:checked + .toggle-slider::before {
    transform: translateX(26px);
  }
  
  .toggle-label {
    font-weight: 500;
    color: #E3F2FD;
    font-size: 14px;
  }
  
  .collaboration-settings {
    margin-top: 12px;
    padding: 12px;
    background: rgba(33, 150, 243, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(33, 150, 243, 0.3);
  }
  
  .mini-control {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .mini-control label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
  }
  
  .mini-control input[type="text"] {
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    color: white;
    font-size: 12px;
    outline: none;
    transition: all 0.3s ease;
  }
  
  .mini-control input[type="text"]:focus {
    border-color: #4CAF50;
    background: rgba(0, 0, 0, 0.5);
  }
  
  .mini-control input[type="text"]::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  
  /* Version badge enhancement */
  .version-badge {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    color: white;
    font-size: 10px;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 12px;
    margin-left: 8px;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
    animation: pulse-glow 2s infinite;
  }
  
  @keyframes pulse-glow {
    0%, 100% {
      box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
    }
    50% {
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.6);
    }
  }
</style>
