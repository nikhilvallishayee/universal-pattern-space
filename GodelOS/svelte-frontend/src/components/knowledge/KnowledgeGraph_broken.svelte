<script>
  import { onMount, onDestroy } from 'svelte';
  import { knowledgeState } from '../../stores/cognitive.js';
  import { GödelOSAPI } from '../../utils/api.js';
  import * as d3 from 'd3';
  import * as THREE from 'three';
  
  let graphContainer;
  let controlsContainer;
  let width = 800;
  let height = 600;
  let svg;
  let simulation;
  let unsubscribe;
  
  // Graph data and state
  let graphData = { nodes: [], links: [] };
  let selectedNode = null;
  let searchQuery = '';
  let layoutMode = '2d';
  let colorMode = 'category';
  let showLabels = true;
  let linkStrength = 0.3;
  let chargeStrength = -300;
  let loading = true;
  let error = null;
  let lastLoadTime = 0;
  let isLoading = false;
  
  // Three.js for 3D mode
  let scene, camera, renderer, controls3d;
  let nodeObjects = [];
  let linkObjects = [];
  
  // Graph visualization modes
  const layoutModes = [
    { id: '2d', name: '2D Force Layout', icon: '🕸️' },
    { id: '3d', name: '3D Network', icon: '🌐' },
    { id: 'hierarchical', name: 'Hierarchical', icon: '🌳' },
    { id: 'circular', name: 'Circular', icon: '⭕' }
  ];
  
  const colorModes = [
    { id: 'category', name: 'By Category', icon: '🎨' },
    { id: 'importance', name: 'By Importance', icon: '⭐' },
    { id: 'recency', name: 'By Recency', icon: '🕒' },
    { id: 'confidence', name: 'By Confidence', icon: '🎯' }
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
    
    // Remove common stop words and extract meaningful phrases
    const stopWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those']);
    
    // Extract meaningful phrases (2-4 words) and single important terms
    const phrases = [];
    const sentences = text.toLowerCase().split(/[.!?;]+/).filter(s => s.trim().length > 10);
    
    sentences.forEach(sentence => {
      const words = sentence.split(/\s+/).filter(w => w.length > 2 && !stopWords.has(w));
      
      // Extract single important terms
      words.forEach(word => {
        if (word.length > 4 && /^[a-z]+$/.test(word)) {
          phrases.push(word);
        }
      });
      
      // Extract 2-3 word phrases
      for (let i = 0; i < words.length - 1; i++) {
        const phrase2 = words[i] + ' ' + words[i + 1];
        if (phrase2.length > 8) phrases.push(phrase2);
        
        if (i < words.length - 2) {
          const phrase3 = words[i] + ' ' + words[i + 1] + ' ' + words[i + 2];
          if (phrase3.length > 12) phrases.push(phrase3);
        }
      }
    });
    
    // Return unique phrases sorted by frequency
    const phraseCount = {};
    phrases.forEach(phrase => phraseCount[phrase] = (phraseCount[phrase] || 0) + 1);
    
    return Object.entries(phraseCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
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
  onMount(() => {
    initializeGraph();
    loadGraphData();
    
    // Temporarily disable subscription to prevent reload loops
    // unsubscribe = knowledgeState.subscribe((state) => {
    //   // Only reload if there's actually new knowledge data
    //   if (state && state.lastUpdate && state.lastUpdate !== lastLoadTime) {
    //     console.log('📡 Knowledge state updated, reloading graph');
    //     loadGraphData();
    //   }
    // });
    
    console.log('⚠️ Knowledge state subscription disabled to prevent reload loops');
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
    if (simulation) simulation.stop();
    if (renderer) {
      renderer.dispose();
      controlsContainer?.removeChild(renderer.domElement);
    }
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
      
      if (apiData && apiData.nodes && apiData.links && apiData.nodes.length > 0) {
        // Enhanced node processing with semantic analysis
        const processedNodes = apiData.nodes.map((node, index) => {
          // Comprehensive content extraction with priority system
          const contentSources = {
            primary: node.concept || node.title || node.name || node.label,
            secondary: node.content || node.text || node.description,
            metadata: node.summary || node.abstract || (node.properties ? Object.values(node.properties).join(' ') : '')
          };
          
          // Create comprehensive text for analysis
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
            label: label,
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
        
        // Validate and process links with enhanced relationship inference
        const validNodeIds = new Set(processedNodes.map(n => n.id));
        const linkData = apiData.links || apiData.edges || [];
        
        const processedLinks = linkData
          .filter(link => {
            const sourceId = String(link.source || link.source_id || link.from);
            const targetId = String(link.target || link.target_id || link.to);
            return validNodeIds.has(sourceId) && validNodeIds.has(targetId);
          })
          .map(link => {
            const sourceId = String(link.source || link.source_id || link.from);
            const targetId = String(link.target || link.target_id || link.to);
            const sourceNode = processedNodes.find(n => n.id === sourceId);
            const targetNode = processedNodes.find(n => n.id === targetId);
            
            // Infer relationship type using semantic analysis
            const relationshipType = inferRelationshipType(sourceNode, targetNode, link);
            
            return {
              source: sourceId,
              target: targetId,
              type: relationshipType,
              label: relationshipTypes[relationshipType]?.label || relationshipType,
              strength: Math.max(0.1, Math.min(1, link.strength || link.weight || relationshipTypes[relationshipType]?.strength || 0.5)),
              confidence: Math.max(0, Math.min(1, link.confidence || 0.8)),
              generated: false,
              description: relationshipTypes[relationshipType]?.description || 'Relationship between concepts'
            };
          });
        
        // Generate additional inferred relationships
        const inferredLinks = generateInferredRelationships(processedNodes);
        const allLinks = [...processedLinks, ...inferredLinks];
        
        graphData = {
          nodes: processedNodes,
          links: allLinks
        };
        
        console.log(`✅ Enhanced knowledge graph loaded: ${processedNodes.length} nodes, ${allLinks.length} links (${inferredLinks.length} inferred)`);
        
      } else {
        // NO SAMPLE DATA FALLBACK - Show empty state
        console.warn('⚠️ No backend data available - showing empty graph');
        graphData = { nodes: [], links: [] };
        error = "No knowledge graph data available. Please ensure the backend has processed documents.";
      }
      
      updateGraph();
      loading = false;
      
    } catch (err) {
      console.error('❌ Error loading knowledge graph:', err);
      error = err.message;
      // NO SAMPLE DATA FALLBACK - Show error state
      graphData = { nodes: [], links: [] };
      updateGraph();
      loading = false;
    } finally {
      isLoading = false;
    }
  }
  function generateInferredRelationships(nodes) {
    const inferredLinks = [];
    const existingLinks = new Set();
    
    // Track existing relationships to avoid duplicates
    graphData.links.forEach(link => {
      existingLinks.add(`${link.source}-${link.target}`);
      existingLinks.add(`${link.target}-${link.source}`); // Bidirectional check
    });
    
    // Generate relationships based on content similarity and semantic analysis
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i];
        const nodeB = nodes[j];
        const linkKey = `${nodeA.id}-${nodeB.id}`;
        
        if (existingLinks.has(linkKey)) continue;
        
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
        
        // Create relationship if similarity is above threshold
        if (similarity > 0.2) {
          const relationshipType = inferRelationshipType(nodeA, nodeB, {});
          const strength = Math.min(0.8, similarity * 2); // Cap at 0.8 for inferred relationships
          
          inferredLinks.push({
            source: nodeA.id,
            target: nodeB.id,
            type: relationshipType,
            strength: strength,
            confidence: similarity,
            generated: true,
            label: relationshipTypes[relationshipType]?.label || relationshipType
          });
        }
      }
    }
    
    console.log(`🔗 Generated ${inferredLinks.length} inferred relationships`);
    return inferredLinks;
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
    
    // Temporarily disable subscription to prevent reload loops
    // unsubscribe = knowledgeState.subscribe((state) => {
    //   // Only reload if there's actually new knowledge data
    //   if (state && state.lastUpdate && state.lastUpdate !== lastLoadTime) {
    //     console.log('📡 Knowledge state updated, reloading graph');
    //     loadGraphData();
    //   }
    // });
    
    console.log('⚠️ Knowledge state subscription disabled to prevent reload loops');
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
    if (simulation) simulation.stop();
    if (renderer) {
      renderer.dispose();
      controlsContainer?.removeChild(renderer.domElement);
    }
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
      
      if (apiData && apiData.nodes && apiData.links && apiData.nodes.length > 0) {
        // Use real data from backend with proper validation
        const processedNodes = apiData.nodes.map((node, index) => {
          // PRIORITY 1: Use the 'concept' field - this contains the actual meaningful content from backend
          let label = node.concept;
          
          // PRIORITY 2: Check other meaningful fields if concept is not available
          if (!label || label.trim() === '') {
            label = node.label || node.name || node.concept_name || node.title;
          }
          
          // PRIORITY 3: Extract from properties if available
          if (!label && node.properties) {
            // Look for meaningful content in properties
            const meaningfulKeys = ['title', 'name', 'content', 'summary', 'description', 'text'];
            for (const key of meaningfulKeys) {
              if (node.properties[key] && typeof node.properties[key] === 'string' && node.properties[key].trim()) {
                const content = node.properties[key].toString().trim();
                if (content.length > 0) {
                  label = content.length > 80 ? content.substring(0, 80) + '...' : content;
                  break;
                }
              }
            }
          }
          
          // PRIORITY 4: Try to extract meaningful content from other fields
          if (!label && node.content) {
            // Look for meaningful phrases in content
            const content = node.content.toString();
            const sentences = content.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 5);
            if (sentences.length > 0) {
              label = sentences[0].length > 80 ? sentences[0].substring(0, 80) + '...' : sentences[0];
            } else {
              label = content.length > 60 ? content.substring(0, 60) + '...' : content;
            }
          }
          
          if (!label && node.text) {
            const text = node.text.toString();
            // Extract meaningful phrases instead of just words
            const sentences = text.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 10);
            if (sentences.length > 0) {
              label = sentences[0].length > 80 ? sentences[0].substring(0, 80) + '...' : sentences[0];
            } else {
              const words = text.split(/\s+/).filter(w => w.length > 2);
              if (words.length > 0) {
                // Take first few meaningful words
                label = words.slice(0, 8).join(' ');
                if (text.length > label.length) label += '...';
              }
            }
          }
          
          if (!label && node.description) {
            label = node.description.length > 80 ? node.description.substring(0, 80) + '...' : node.description;
          }
          
          // Intelligent categorization based on content
          let category = node.category || node.type || node.node_type;
          if (!category) {
            // Create comprehensive text for analysis from all available sources
            const textSources = [
              label,
              node.concept,
              node.content,
              node.text,
              node.description,
              // Check properties for additional context
              ...(node.properties ? Object.values(node.properties).filter(v => typeof v === 'string') : [])
            ];
            const allText = textSources.filter(t => t).join(' ').toLowerCase();
            
            // Enhanced categorization with Cairo STARK document context
            if (/stark|cairo|cpu|architecture|instruction|processor|virtual machine|vm/.test(allText)) {
              category = 'system';
            }
            // Technical/Algorithm concepts (enhanced for STARK proofs)
            else if (/algorithm|function|method|computation|process|execution|proof|verification|polynomial/.test(allText)) {
              category = 'algorithm';
            }
            // Data structures and types
            else if (/data|structure|type|field|variable|parameter|register|memory|trace/.test(allText)) {
              category = 'data_structure';
            }
            // Mathematical concepts (enhanced for cryptography)
            else if (/theorem|proof|equation|formula|mathematical|number|finite field|constraint|polynomial/.test(allText)) {
              category = 'mathematics';
            }
            // System/Architecture concepts (enhanced for CPU architecture)
            else if (/system|architecture|design|framework|model|virtual|cpu|instruction set|turing/.test(allText)) {
              category = 'system';
            }
            // Programming concepts
            else if (/code|program|language|instruction|compile|runtime|assembly|opcodes/.test(allText)) {
              category = 'programming';
            }
            // Security/Cryptography (enhanced for STARK context)
            else if (/security|crypto|hash|signature|verification|proof|stark|snark|zero.knowledge/.test(allText)) {
              category = 'security';
            }
            // Documentation/Reference
            else if (/paper|document|reference|section|chapter|appendix|specification/.test(allText)) {
              category = 'document';
            }
            // Default to concept for unknown types
            else {
              category = 'concept';
            }
          }
          
          // Ultimate fallback - use node_id or create meaningful label from available data
          if (!label || label.trim() === '') {
            // Try to use node_id if it contains meaningful information
            if (node.node_id && typeof node.node_id === 'string' && !node.node_id.match(/^[0-9a-f-]{36}$/i)) {
              // Not a UUID, might be meaningful
              label = node.node_id.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
            } else if (node.id && typeof node.id === 'string' && !node.id.match(/^[0-9a-f-]{36}$/i)) {
              // Not a UUID, might be meaningful
              label = node.id.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
            } else {
              // Create descriptive label based on category and timestamp
              const categoryNames = {
                'algorithm': 'Algorithm Concept',
                'data_structure': 'Data Structure',
                'mathematics': 'Mathematical Concept',
                'system': 'System Component',
                'programming': 'Programming Element',
                'security': 'Security Feature',
                'document': 'Document Content',
                'concept': 'Knowledge Concept',
                'entity': 'Knowledge Entity',
                'topic': 'Topic Area',
                'principle': 'Core Principle'
              };
              
              // Use creation time or timestamp to make unique but still meaningful
              const timeRef = node.creation_time || node.timestamp || Date.now();
              const shortTime = new Date(timeRef * (timeRef < 1e12 ? 1000 : 1)).toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
              });
              
              label = `${categoryNames[category] || 'Knowledge Element'} (${shortTime})`;
            }
          }
          
          return {
            ...node,
            id: String(node.node_id || node.id || node.concept_id || `node_${index}`),
            label: label,
            category: category,
            importance: Math.max(0, Math.min(1, node.importance || node.strength || node.confidence || 0.7)),
            confidence: Math.max(0, Math.min(1, node.confidence || 0.8)),
            timestamp: node.creation_time || node.timestamp || node.last_updated || Date.now(),
            recency: Math.max(0, Math.min(1, node.recency ||
              (node.last_updated ? Math.max(0, 1 - (Date.now() - node.last_updated * 1000) / (24 * 60 * 60 * 1000)) : 0.6))),
            // Store original data for detail view
            originalData: node
          };
        });
        
        // Create a Set of valid node IDs for link validation
        const validNodeIds = new Set(processedNodes.map(n => n.id));
        
        // Process and validate links (backend uses 'edges' in the data structure)
        const linkData = apiData.links || apiData.edges || [];
        
        // Debug: Log the raw data from backend and processed results
        console.log('🔍 FULL RAW BACKEND RESPONSE:', JSON.stringify(apiData, null, 2));
        console.log('🔍 Raw backend nodes (first 3):', apiData.nodes.slice(0, 3));
        console.log('🔍 Raw backend links/edges (first 3):', linkData.slice(0, 3));
        
        // Log each individual node's content in detail
        apiData.nodes.slice(0, 5).forEach((node, i) => {
          console.log(`🔍 Node ${i} detailed content:`, {
            allFields: Object.keys(node),
            concept: node.concept,
            content: node.content,
            text: node.text,
            title: node.title,
            label: node.label,
            name: node.name,
            description: node.description,
            properties: node.properties,
            metadata: node.metadata,
            fullNode: node
          });
        });
        
        console.log('🔍 Processed node labels (first 5):', processedNodes.slice(0, 5).map(n => ({
          id: n.id,
          label: n.label,
          concept: n.originalData.concept,
          category: n.category,
          allOriginalFields: Object.keys(n.originalData)
        })));
        console.log('🔍 Valid node IDs:', Array.from(validNodeIds).slice(0, 5));
        const processedLinks = linkData
          .map(link => {
            // Handle backend edge structure: source_node_id, target_node_id, relation_type
            const source = String(link.source_node_id || link.source || link.from_concept || link.from_id || link.source_id || '');
            const target = String(link.target_node_id || link.target || link.to_concept || link.to_id || link.target_id || '');
            
            return {
              ...link,
              source: source,
              target: target,
              strength: Math.max(0, Math.min(1, link.strength || link.weight || link.confidence || 0.5)),
              type: link.relation_type || link.type || 'related'
            };
          })
          .filter(link => {
            // Only include links where both source and target nodes exist
            const hasValidSource = link.source && link.source !== '' && validNodeIds.has(link.source);
            const hasValidTarget = link.target && link.target !== '' && validNodeIds.has(link.target);
            const notSelfLoop = link.source !== link.target;
            
            const isValid = hasValidSource && hasValidTarget && notSelfLoop;
            
            if (!isValid) {
              console.warn('❌ Invalid link detected and filtered out:', link);
            }
            
            return isValid;
          });
        
        graphData = {
          nodes: processedNodes,
          links: processedLinks
        };
        
        console.log(`✅ Loaded real knowledge graph: ${processedNodes.length} nodes, ${processedLinks.length} total links (${processedLinks.filter(l => l.generated).length} generated)`);
      } else {
        // NO FALLBACK TO SAMPLE DATA - Show empty state instead
        console.warn('⚠️ No backend data available - showing empty state');
        graphData = { nodes: [], links: [] };
        error = "No knowledge graph data available. Please ensure the backend is running and has processed some documents.";
      }
      
    } catch (err) {
      console.error('❌ Failed to load knowledge graph data:', err);
      error = err.message;
      // NO FALLBACK TO SAMPLE DATA - Show error state
      graphData = { nodes: [], links: [] };
    }
    
    // Always call updateGraph after data is set
    updateGraph();
    loading = false;
    isLoading = false;
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
    
    // Initialize force simulation
    simulation = d3.forceSimulation()
      .force('link', d3.forceLink().id(d => d.id).strength(linkStrength))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => getNodeSize(d) + 2));
    
    updateGraph();
  }
  
  function initialize3DGraph() {
    // Clear existing content
    d3.select(graphContainer).selectAll("*").remove();
    
    // Initialize Three.js scene
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ alpha: true });
    
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0.05);
    graphContainer.appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);
    
    // Position camera
    camera.position.z = 50;
    
    // Add orbit controls (would need to import OrbitControls)
    // controls3d = new THREE.OrbitControls(camera, renderer.domElement);
    
    update3DGraph();
    animate3D();
    }
  
  // generateSampleData function removed - no more sample data fallbacks
  
  async function performSearch() {
    if (!searchQuery.trim()) {
      await loadGraphData(); // Reset to all data
      return;
    }
    
    try {
      // Search through API if available
      const searchResults = await GödelOSAPI.searchKnowledge(searchQuery);
      
      if (searchResults && searchResults.results) {
        // Convert search results to graph format
        const searchNodes = searchResults.results.map((result, index) => ({
          id: result.id || `search_${index}`,
          label: result.title || result.content?.substring(0, 50) || 'Unknown',
          category: result.category || 'search_result',
          importance: result.relevance_score || 0.5,
          confidence: result.confidence || 0.5,
          timestamp: Date.now(),
          recency: 1.0,
          searchResult: true
        }));
        
        // Add the search query as a central node
        const queryNode = {
          id: `query_${Date.now()}`,
          label: `"${searchQuery}"`,
          category: 'query',
          importance: 1.0,
          confidence: 1.0,
          timestamp: Date.now(),
          recency: 1.0,
          isQueryNode: true
        };
        
        // Create links from query to each result based on relevance
        const searchLinks = searchNodes.map(node => ({
          source: queryNode.id,
          target: node.id,
          strength: node.importance || 0.5,
          type: 'query_result',
          label: `relevance: ${(node.importance * 100).toFixed(0)}%`
        }));
        
        // Add semantic links between results if they share categories or topics
        for (let i = 0; i < searchNodes.length; i++) {
          for (let j = i + 1; j < searchNodes.length; j++) {
            const nodeA = searchNodes[i];
            const nodeB = searchNodes[j];
            
            // Link nodes with same category or high relevance similarity
            const relevanceDiff = Math.abs((nodeA.importance || 0.5) - (nodeB.importance || 0.5));
            const categoryMatch = nodeA.category === nodeB.category;
            
            if (categoryMatch || relevanceDiff < 0.2) {
              searchLinks.push({
                source: nodeA.id,
                target: nodeB.id,
                strength: categoryMatch ? 0.4 : (0.3 - relevanceDiff),
                type: categoryMatch ? 'category_related' : 'relevance_related',
                label: categoryMatch ? `shared: ${nodeA.category}` : 'similar relevance'
              });
            }
          }
        }
        
        // Combine query node with search result nodes
        const allNodes = [queryNode, ...searchNodes];
        
        graphData = { nodes: allNodes, links: searchLinks };
        console.log(`✅ Search visualization: 1 query + ${searchNodes.length} results with ${searchLinks.length} relationships`);
      } else {
        // No fallback to sample data - show empty results
        console.warn('⚠️ No search results available from backend');
        graphData = { nodes: [], links: [] };
        error = "No search results found. Please try a different search term or ensure the backend has processed some documents.";
      }
    } catch (error) {
      console.warn('Search failed:', error);
      graphData = { nodes: [], links: [] };
      error = `Search failed: ${error.message}`;
    }
    
    updateGraph();
  }

  function handleSearch() {
    performSearch();
  }
  
  function changeLayoutMode(mode) {
    layoutMode = mode;
    initializeGraph();
  }
  
  function changeColorMode(mode) {
    colorMode = mode;
    updateGraph();
  }
  
  function updateGraph() {
    if (!simulation || !svg) {
      console.warn('❌ Simulation or SVG not initialized');
      return;
    }
    
    // Validate graph data
    if (!graphData || !graphData.nodes || !graphData.links) {
      console.warn('❌ Invalid graph data structure');
      return;
    }
    
    console.log(`🔄 Updating graph: ${graphData.nodes.length} nodes, ${graphData.links.length} links`);
    
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
      .data(graphData.links, d => `${d.source}-${d.target}`);
    
    links.exit().remove();
    
    const linksEnter = links.enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6);
    
    const linksUpdate = linksEnter.merge(links)
      .attr('stroke-width', d => Math.sqrt(d.strength * 10))
      .attr('stroke-opacity', d => 0.4 + (d.strength * 0.4));
    
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
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));
    
    // Add circles to nodes
    nodesEnter.append('circle')
      .attr('class', 'node-circle');
    
    // Add labels to nodes if enabled
    if (showLabels) {
      nodesEnter.append('text')
        .attr('class', 'node-label')
        .attr('dx', 12)
        .attr('dy', '.35em')
        .style('font-size', '12px')
        .style('fill', 'white')
        .style('pointer-events', 'none');
    }
    
    const nodesUpdate = nodesEnter.merge(nodes);
    
    // Update node circles
    nodesUpdate.select('.node-circle')
      .attr('r', getNodeSize)
      .attr('fill', getNodeColor)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);
    
    // Update node labels
    nodesUpdate.select('.node-label')
      .text(d => showLabels ? d.label : '')
      .style('display', showLabels ? 'block' : 'none');
    
    // Update and restart simulation
    simulation
      .nodes(graphData.nodes);
    
    // Update force links with validation
    const linkForce = simulation.force('link');
    if (linkForce) {
      linkForce.links(graphData.links);
      linkForce.strength(linkStrength);
      console.log(`🔗 Updated ${graphData.links.length} links in force simulation`);
    } else {
      console.warn('❌ Link force not found in simulation');
    }
    
    // Update simulation forces
    const chargeForce = simulation.force('charge');
    if (chargeForce) {
      chargeForce.strength(chargeStrength);
    }
    
    // Set up tick function for animation with error handling
    simulation.on('tick', () => {
      // Update links with safety checks
      linksUpdate
        .attr('x1', d => {
          if (!d.source || typeof d.source.x !== 'number') {
            console.warn('Invalid link source:', d);
            return 0;
          }
          return d.source.x;
        })
        .attr('y1', d => {
          if (!d.source || typeof d.source.y !== 'number') return 0;
          return d.source.y;
        })
        .attr('x2', d => {
          if (!d.target || typeof d.target.x !== 'number') {
            console.warn('Invalid link target:', d);
            return 0;
          }
          return d.target.x;
        })
        .attr('y2', d => {
          if (!d.target || typeof d.target.y !== 'number') return 0;
          return d.target.y;
        });
      
      // Update nodes with safety checks
      nodesUpdate
        .attr('transform', d => {
          if (typeof d.x !== 'number' || typeof d.y !== 'number') {
            console.warn('Invalid node position:', d);
            return 'translate(0,0)';
          }
          return `translate(${d.x},${d.y})`;
        });
    });
    
    // Restart simulation with new data
    simulation.alpha(1).restart();
  }
  
  // Drag functions for node interaction
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
    console.log('🔍 Selected node:', node);
    
    // Log all available data from the node
    console.log('📋 Node details:', {
      id: node.id,
      label: node.label,
      category: node.category,
      importance: node.importance,
      confidence: node.confidence,
      originalData: node.originalData
    });
  }
  
  async function reAnalyzeData() {
    if (loading) return;
    
    loading = true;
    error = null;
    
    try {
      console.log('🧠 Triggering re-analysis of uploaded documents...');
      
      // Call backend to re-process all uploaded documents
      const response = await GödelOSAPI.reAnalyzeKnowledge();
      
      if (response.success) {
        if (response.fallback) {
          console.log('⚠️ Using fallback re-analysis method');
          console.log('🔄 Forcing data refresh with enhanced processing...');
          
          // For fallback, we force a fresh load with cache busting
          lastLoadTime = 0; // Reset to force reload
          await loadGraphData();
          
          console.log('✅ Knowledge graph refreshed with current data');
        } else {
          console.log('✅ Re-analysis triggered successfully');
          
          // Wait for backend processing
          await new Promise(resolve => setTimeout(resolve, 3000));
          
          // Reload the graph data to get updated results
          lastLoadTime = 0; // Reset to force reload
          await loadGraphData();
          
          console.log('🎉 Knowledge graph updated with re-analyzed data');
        }
        
        // Show success notification
        selectedNode = null; // Clear selection to show updated view
        
      } else {
        throw new Error(response.message || 'Re-analysis failed');
      }
      
    } catch (err) {
      console.error('❌ Failed to re-analyze data:', err);
      error = `Re-analysis failed: ${err.message}`;
    } finally {
      loading = false;
    }
  }

  // Helper function to calculate node size
  function getNodeSize(node) {
    const baseSize = nodeCategories[node.category]?.size || 8;
    const importanceMultiplier = 1 + (node.importance || 0.5) * 0.5;
    return baseSize * importanceMultiplier;
  }

  // 3D Graph functions (placeholder implementations)
  function update3DGraph() {
    if (!scene || !renderer) return;
    
    // Clear existing objects
    nodeObjects.forEach(obj => scene.remove(obj));
    linkObjects.forEach(obj => scene.remove(obj));
    nodeObjects = [];
    linkObjects = [];
    
    // Create 3D nodes
    graphData.nodes.forEach((node, i) => {
      const geometry = new THREE.SphereGeometry(getNodeSize(node) / 5, 16, 16);
      const material = new THREE.MeshLambertMaterial({ 
        color: nodeCategories[node.category]?.color || '#4CAF50' 
      });
      const mesh = new THREE.Mesh(geometry, material);
      
      // Position nodes in a sphere
      const phi = Math.acos(-1 + (2 * i) / graphData.nodes.length);
      const theta = Math.sqrt(graphData.nodes.length * Math.PI) * phi;
      const radius = 30;
      
      mesh.position.x = radius * Math.cos(theta) * Math.sin(phi);
      mesh.position.y = radius * Math.sin(theta) * Math.sin(phi);
      mesh.position.z = radius * Math.cos(phi);
      
      scene.add(mesh);
      nodeObjects.push(mesh);
    });
    
    // Create 3D links (simplified)
    graphData.links.forEach(link => {
      const sourceIndex = graphData.nodes.findIndex(n => n.id === (link.source.id || link.source));
      const targetIndex = graphData.nodes.findIndex(n => n.id === (link.target.id || link.target));
      
      if (sourceIndex >= 0 && targetIndex >= 0 && nodeObjects[sourceIndex] && nodeObjects[targetIndex]) {
        const geometry = new THREE.BufferGeometry().setFromPoints([
          nodeObjects[sourceIndex].position,
          nodeObjects[targetIndex].position
        ]);
        const material = new THREE.LineBasicMaterial({ color: 0x999999, opacity: 0.6, transparent: true });
        const line = new THREE.Line(geometry, material);
        
        scene.add(line);
        linkObjects.push(line);
      }
    });
  }
  
  function animate3D() {
    if (!renderer || !scene || !camera) return;
    
    function render() {
      requestAnimationFrame(render);
      
      // Simple rotation animation
      scene.rotation.y += 0.005;
      
      renderer.render(scene, camera);
    }
    
    render();
  }
</script>

<div class="knowledge-graph-container">
  <!-- Enhanced Header Section -->
  <div class="header-section">
    <div class="title-area">
      <h2 class="main-title">
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
        <span class="status-value">{graphData.links.length}</span>
        <span class="status-label">Relationships</span>
      </div>
      <div class="status-item">
        <span class="status-value">{graphData.links.filter(l => l.generated).length}</span>
        <span class="status-label">Inferred</span>
      </div>
      <div class="status-health {loading ? 'loading' : error ? 'error' : 'healthy'}">
        {loading ? '🔄' : error ? '❌' : '✅'}
      </div>
    </div>
  </div>

  <!-- Advanced Controls Panel -->
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
        {#if searchQuery}
          <div class="search-info">
            Searching across {graphData.nodes.length} concepts and {graphData.links.length} relationships
          </div>
        {/if}
      </div>
    </div>
    
    <div class="control-section">
      <div class="section-title">🎛️ Visualization Settings</div>
      <div class="control-grid">
        <div class="control-group">
          <label class="control-label">Layout Mode</label>
          <div class="button-grid">
            {#each layoutModes as mode}
              <button 
                class="mode-button {layoutMode === mode.id ? 'active' : ''}"
                on:click={() => changeLayoutMode(mode.id)}
                title={mode.name}
              >
                <span class="mode-icon">{mode.icon}</span>
                <span class="mode-name">{mode.name}</span>
              </button>
            {/each}
          </div>
        </div>
        
        <div class="control-group">
          <label class="control-label">Color Scheme</label>
          <div class="button-grid">
            {#each colorModes as mode}
              <button 
                class="mode-button {colorMode === mode.id ? 'active' : ''}"
                on:click={() => changeColorMode(mode.id)}
                title={mode.description}
              >
                <span class="mode-icon">{mode.icon}</span>
                <span class="mode-name">{mode.name}</span>
              </button>
            {/each}
          </div>
        </div>
      </div>
    </div>
    
    <div class="control-section">
      <div class="section-title">⚙️ Physics & Display</div>
      <div class="physics-grid">
        <div class="slider-group">
          <label class="slider-label">
            Link Strength: <span class="slider-value">{linkStrength}</span>
          </label>
          <input 
            type="range" 
            min="0.1" 
            max="1" 
            step="0.1" 
            bind:value={linkStrength}
            class="enhanced-slider"
            on:input={() => {
              if (simulation) {
                simulation.force('link').strength(linkStrength);
                simulation.alpha(1).restart();
              }
            }}
          />
        </div>
        
        <div class="slider-group">
          <label class="slider-label">
            Node Repulsion: <span class="slider-value">{Math.abs(chargeStrength)}</span>
          </label>
          <input 
            type="range" 
            min="-1000" 
            max="-50" 
            step="50" 
            bind:value={chargeStrength}
            class="enhanced-slider"
            on:input={() => {
              if (simulation) {
                simulation.force('charge').strength(chargeStrength);
                simulation.alpha(1).restart();
              }
            }}
          />
        </div>
        
        <div class="toggle-group">
          <label class="toggle-label">
            <input type="checkbox" bind:checked={showLabels} on:change={updateGraph} />
            <span class="toggle-slider"></span>
            Show Node Labels
          </label>
        </div>
      </div>
    </div>
    
    <div class="control-section">
      <div class="section-title">🧠 Intelligence & Analysis</div>
      <div class="action-buttons">
        <button
          class="action-button primary"
          on:click={reAnalyzeData}
          disabled={loading}
          title="Re-process knowledge base with enhanced semantic analysis"
        >
          {#if loading}
            <span class="button-icon spinning">🔄</span>
            <span class="button-text">Analyzing...</span>
          {:else}
            <span class="button-icon">🧠</span>
            <span class="button-text">Re-analyze Knowledge</span>
          {/if}
        </button>
        
        <button class="action-button secondary" on:click={() => loadGraphData()}>
          <span class="button-icon">🔄</span>
          <span class="button-text">Refresh Data</span>
        </button>
        
        <button class="action-button secondary" on:click={() => initializeGraph()}>
          <span class="button-icon">🎯</span>
          <span class="button-text">Reset View</span>
        </button>
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
      
      <!-- Graph Navigation Controls -->
      <div class="graph-controls">
        <button class="graph-control-btn" title="Zoom In">🔍+</button>
        <button class="graph-control-btn" title="Zoom Out">🔍-</button>
        <button class="graph-control-btn" title="Fit to Screen">📐</button>
        <button class="graph-control-btn" title="Full Screen">⛶</button>
      </div>
    </div>

    <!-- Enhanced Information Panel -->
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
            
            <!-- Content Preview -->
            {#if selectedNode.content || selectedNode.summary}
              <div class="content-section">
                <h4 class="section-title">📄 Content</h4>
                <div class="content-preview">
                  {selectedNode.summary || selectedNode.content || 'No content available'}
                </div>
              </div>
            {/if}
            
            <!-- Key Phrases -->
            {#if selectedNode.keyPhrases && selectedNode.keyPhrases.length > 0}
              <div class="phrases-section">
                <h4 class="section-title">🏷️ Key Concepts</h4>
                <div class="phrases-container">
                  {#each selectedNode.keyPhrases.slice(0, 8) as phrase}
                    <span class="phrase-tag">{phrase}</span>
                  {/each}
                </div>
              </div>
            {/if}
            
            <!-- Enhanced Connections -->
            <div class="connections-section">
              <h4 class="section-title">🔗 Relationships ({graphData.links.filter(l => (l.source.id || l.source) === selectedNode.id || (l.target.id || l.target) === selectedNode.id).length})</h4>
              <div class="connections-list">
                {#each graphData.links.filter(l => (l.source.id || l.source) === selectedNode.id || (l.target.id || l.target) === selectedNode.id).slice(0, 5) as link}
                  <div class="connection-card">
                    <div class="connection-header">
                      <span class="relationship-type {link.generated ? 'inferred' : 'explicit'}">
                        {relationshipTypes[link.type]?.label || link.type}
                        {#if link.generated}<span class="inferred-badge">inferred</span>{/if}
                      </span>
                      <span class="connection-strength-badge">
                        {Math.round((link.strength || 0) * 100)}%
                      </span>
                    </div>
                    <div class="connection-target">
                      {(link.source.id || link.source) === selectedNode.id 
                        ? (graphData.nodes.find(n => n.id === (link.target.id || link.target))?.label || 'Unknown')
                        : (graphData.nodes.find(n => n.id === (link.source.id || link.source))?.label || 'Unknown')
                      }
                    </div>
                    {#if link.description}
                      <div class="connection-description">{link.description}</div>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
            
            <!-- Raw Data Explorer (Collapsible) -->
            <details class="raw-data-section">
              <summary class="raw-data-toggle">
                <span class="toggle-icon">📊</span>
                Raw Data Explorer
              </summary>
              <div class="raw-data-content">
                <pre class="raw-data-viewer">{JSON.stringify(selectedNode.originalData || selectedNode, null, 2)}</pre>
              </div>
            </details>
          </div>
        </div>
      {:else}
        <div class="welcome-panel">
          <div class="welcome-icon">🎯</div>
          <h3 class="welcome-title">Explore Knowledge</h3>
          <p class="welcome-text">Click on any node to view detailed information, relationships, and semantic analysis.</p>
          <div class="welcome-features">
            <div class="feature-item">🧠 Intelligent relationship inference</div>
            <div class="feature-item">📊 Semantic content analysis</div>
            <div class="feature-item">🔍 Interactive exploration</div>
          </div>
        </div>
      {/if}
      
      <!-- Enhanced Legend -->
      <div class="legend-section">
        <h4 class="legend-title">🎨 Category Legend</h4>
        <div class="legend-grid">
          {#each Object.entries(nodeCategories) as [category, props]}
            <div class="legend-item">
              <div class="legend-color-indicator" style="background-color: {props.color}"></div>
              <span class="legend-icon">{props.icon}</span>
              <span class="legend-text">{props.description}</span>
            </div>
          {/each}
        </div>
        
        <div class="relationship-legend">
          <h5 class="legend-subtitle">Relationship Types</h5>
          <div class="relationship-types">
            {#each Object.entries(relationshipTypes).slice(0, 6) as [type, props]}
              <div class="relationship-item">
                <div class="relationship-line" style="background-color: {props.color}"></div>
                <span class="relationship-label">{props.label}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Enhanced Knowledge Graph Container */
  .knowledge-graph-container {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #667eea 100%);
    border-radius: 16px;
    padding: 24px;
    color: white;
    min-height: 900px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  }

  .knowledge-graph-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 70% 80%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
    pointer-events: none;
  }

  /* Header Section */
  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
    position: relative;
    z-index: 2;
  }

  .title-area {
    flex: 1;
  }

  .main-title {
    display: flex;
    align-items: center;
    gap: 16px;
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #ffffff, #e3f2fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .title-icon {
    font-size: 32px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  }

  .version-badge {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
  }

  .subtitle {
    margin: 0;
    opacity: 0.9;
    font-size: 16px;
    font-weight: 400;
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
    font-size: 20px;
    transition: all 0.3s ease;
  }

  .status-health.healthy {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
  }

  .status-health.loading {
    background: linear-gradient(135deg, #FF9800, #F57C00);
    animation: pulse 2s infinite;
  }

  .status-health.error {
    background: linear-gradient(135deg, #F44336, #C62828);
    box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
  }

  /* Controls Panel */
  .controls-panel {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    position: relative;
    z-index: 2;
  }

  .control-section {
    margin-bottom: 24px;
  }

  .control-section:last-child {
    margin-bottom: 0;
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: rgba(255, 255, 255, 0.95);
  }

  /* Enhanced Search */
  .search-enhanced {
    width: 100%;
  }

  .search-input-container {
    display: flex;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
  }

  .search-input-container:focus-within {
    background: rgba(255, 255, 255, 0.18);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
  }

  .search-input-enhanced {
    flex: 1;
    background: transparent;
    border: none;
    padding: 12px 16px;
    color: white;
    font-size: 14px;
    border-radius: 8px;
  }

  .search-input-enhanced::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }

  .search-button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    padding: 12px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .search-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  }

  .search-info {
    margin-top: 8px;
    font-size: 12px;
    opacity: 0.8;
    font-style: italic;
  }

  /* Control Grid */
  .control-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .control-label {
    font-size: 14px;
    font-weight: 500;
    opacity: 0.9;
  }

  .button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
  }

  .mode-button {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 12px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    text-align: center;
  }

  .mode-button:hover {
    background: rgba(255, 255, 255, 0.18);
    transform: translateY(-2px);
  }

  .mode-button.active {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    border-color: #4CAF50;
    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
  }

  .mode-icon {
    font-size: 18px;
    margin-bottom: 2px;
  }

  .mode-name {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Physics Controls */
  .physics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    align-items: end;
  }

  .slider-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .slider-label {
    font-size: 13px;
    font-weight: 500;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .slider-value {
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 8px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 11px;
  }

  .enhanced-slider {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.2);
    outline: none;
    cursor: pointer;
  }

  .enhanced-slider::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.4);
    transition: all 0.2s ease;
  }

  .enhanced-slider::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }

  /* Toggle Controls */
  .toggle-group {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }

  .toggle-label input[type="checkbox"] {
    display: none;
  }

  .toggle-slider {
    width: 48px;
    height: 24px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    position: relative;
    transition: all 0.3s ease;
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
  }

  .toggle-label input[type="checkbox"]:checked + .toggle-slider {
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
  }

  .toggle-label input[type="checkbox"]:checked + .toggle-slider::before {
    transform: translateX(24px);
  }

  /* Action Buttons */
  .action-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .action-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 14px;
  }

  .action-button.primary {
    background: linear-gradient(135deg, #FF6B6B, #EE5A24);
    color: white;
  }

  .action-button.secondary {
    background: rgba(255, 255, 255, 0.12);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .action-button:hover:not(:disabled) {
    transform: translateY(-2px);
  }

  .action-button.primary:hover:not(:disabled) {
    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
  }

  .action-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .button-icon {
    font-size: 16px;
  }

  .button-icon.spinning {
    animation: spin 1s linear infinite;
  }

  /* Visualization Container */
  .visualization-container {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 24px;
    height: 600px;
    position: relative;
    z-index: 1;
  }

  /* Graph Area */
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

  /* Graph Controls */
  .graph-controls {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 5;
  }

  .graph-control-btn {
    width: 40px;
    height: 40px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
  }

  .graph-control-btn:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.05);
  }

  /* Information Panel */
  .info-panel {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(15px);
    display: flex;
    flex-direction: column;
  }

  /* Node Details Card */
  .node-details-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .card-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .node-title-area {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;
  }

  .node-category-icon {
    font-size: 24px;
    margin-top: 2px;
  }

  .node-title-text {
    flex: 1;
  }

  .node-title {
    margin: 0 0 4px 0;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.3;
    color: white;
  }

  .node-category-badge {
    background: rgba(255, 255, 255, 0.2);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .close-button {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .card-content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }

  /* Metrics Grid */
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

  /* Content Sections */
  .content-section,
  .phrases-section,
  .connections-section {
    margin-bottom: 20px;
  }

  .section-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .content-preview {
    background: rgba(255, 255, 255, 0.05);
    padding: 12px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.5;
    border-left: 3px solid #4CAF50;
  }

  /* Key Phrases */
  .phrases-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .phrase-tag {
    background: rgba(255, 255, 255, 0.12);
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  /* Connections */
  .connections-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
  }

  .connection-card {
    background: rgba(255, 255, 255, 0.05);
    padding: 10px;
    border-radius: 8px;
    border-left: 3px solid #2196F3;
  }

  .connection-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  .relationship-type {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .relationship-type.inferred {
    opacity: 0.8;
  }

  .inferred-badge {
    background: rgba(255, 193, 7, 0.3);
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 9px;
  }

  .connection-strength-badge {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 600;
  }

  .connection-target {
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 2px;
  }

  .connection-description {
    font-size: 11px;
    opacity: 0.7;
    font-style: italic;
  }

  /* Raw Data Section */
  .raw-data-section {
    margin-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 16px;
  }

  .raw-data-toggle {
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 0;
    transition: all 0.3s ease;
  }

  .raw-data-toggle:hover {
    opacity: 0.8;
  }

  .toggle-icon {
    font-size: 14px;
  }

  .raw-data-content {
    margin-top: 12px;
  }

  .raw-data-viewer {
    background: rgba(0, 0, 0, 0.3);
    padding: 12px;
    border-radius: 8px;
    font-size: 10px;
    line-height: 1.4;
    max-height: 200px;
    overflow: auto;
    border: 1px solid rgba(255, 255, 255, 0.1);
    font-family: 'Courier New', monospace;
  }

  /* Welcome Panel */
  .welcome-panel {
    padding: 40px 20px;
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }

  .welcome-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.8;
  }

  .welcome-title {
    margin: 0 0 12px 0;
    font-size: 20px;
    font-weight: 600;
  }

  .welcome-text {
    margin: 0 0 24px 0;
    opacity: 0.8;
    font-size: 14px;
    line-height: 1.5;
  }

  .welcome-features {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .feature-item {
    font-size: 12px;
    opacity: 0.7;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* Legend Section */
  .legend-section {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.02);
  }

  .legend-title {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
  }

  .legend-grid {
    display: grid;
    gap: 6px;
    margin-bottom: 16px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
  }

  .legend-color-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .legend-icon {
    font-size: 12px;
    width: 16px;
    text-align: center;
  }

  .legend-text {
    font-weight: 500;
  }

  .legend-subtitle {
    margin: 0 0 8px 0;
    font-size: 12px;
    font-weight: 600;
    opacity: 0.9;
  }

  .relationship-types {
    display: grid;
    gap: 4px;
  }

  .relationship-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
  }

  .relationship-line {
    width: 16px;
    height: 2px;
    border-radius: 1px;
  }

  .relationship-label {
    font-weight: 500;
  }

  /* Animations */
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .visualization-container {
      grid-template-columns: 1fr;
      height: auto;
    }
    
    .info-panel {
      height: 400px;
    }
  }

  @media (max-width: 768px) {
    .knowledge-graph-container {
      padding: 16px;
    }
    
    .header-section {
      flex-direction: column;
      gap: 16px;
    }
    
    .status-indicators {
      flex-wrap: wrap;
      gap: 12px;
    }
    
    .control-grid,
    .physics-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
    
    .button-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .reanalyze-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .reanalyze-btn:active {
    transform: translateY(0px);
  }
  
  .graph-stats {
    display: flex;
    gap: 20px;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .stat-value {
    font-size: 18px;
    font-weight: bold;
    color: #FFD700;
  }
  
  .stat-label {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .controls-section {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    align-items: center;
  }
  
  .search-controls {
    display: flex;
    gap: 10px;
    flex: 1;
    min-width: 200px;
  }
  
  .search-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 8px 12px;
    font-size: 14px;
  }
  
  .search-input::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  
  .search-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 8px 12px;
    cursor: pointer;
  }
  
  .layout-controls {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .control-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .control-group label,
  .control-group .control-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
    min-width: 40px;
  }
  
  .button-group {
    display: flex;
    gap: 4px;
  }
  
  .mode-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    color: white;
    padding: 6px 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s ease;
  }
  
  .mode-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  .mode-btn.active {
    background: rgba(255, 255, 255, 0.3);
    border-color: #FFD700;
  }
  
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    cursor: pointer;
  }
  
  .physics-controls {
    display: flex;
    gap: 20px;
    align-items: center;
  }
  
  .slider-control {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  
  .slider-control label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .slider-control input[type="range"] {
    width: 80px;
  }
  
  .main-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
    min-height: 600px;
  }
  
  .graph-section {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    overflow: hidden;
  }
  
  .graph-container {
    width: 100%;
    height: 100%;
    min-height: 600px;
  }
  
  .info-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .node-details h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .node-card {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .node-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .node-icon {
    font-size: 20px;
  }
  
  .node-title {
    font-weight: bold;
    font-size: 14px;
  }
  
  .node-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 15px;
  }
  
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .info-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .info-value {
    font-size: 11px;
    font-weight: bold;
  }
  
  .node-description h5 {
    margin: 0 0 5px 0;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .node-description p {
    margin: 0;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.4;
  }
  
  .node-connections h5 {
    margin: 15px 0 8px 0;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .connections-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .connection-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 10px;
  }
  
  .connection-type {
    color: #FFD700;
    font-weight: bold;
  }
  
  .connection-target {
    flex: 1;
    text-align: center;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .connection-strength {
    color: rgba(255, 255, 255, 0.6);
  }
  
  .no-selection {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 2px dashed rgba(255, 255, 255, 0.2);
  }
  
  .selection-hint {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
  }
  
  .graph-legend h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .legend-items {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }
  
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }
  
  .legend-icon {
    font-size: 14px;
  }
  
  .legend-label {
    color: rgba(255, 255, 255, 0.8);
    text-transform: capitalize;
  }
  
  .graph-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
  }
  
  .action-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 10px 15px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .action-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
</style>
