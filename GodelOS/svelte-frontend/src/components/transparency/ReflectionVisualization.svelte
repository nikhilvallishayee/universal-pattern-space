<script>
  import { onMount } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import * as d3 from 'd3';

  export let width = 600;
  export let height = 400;

  let svgElement;
  let reflectionData = [];
  
  $: {
    // Update visualization when cognitive state changes
    if ($cognitiveState.manifestConsciousness) {
      updateReflectionData();
    }
  }

  function updateReflectionData() {
    const consciousness = $cognitiveState.manifestConsciousness;
    
    reflectionData = [
      {
        id: 'attention',
        label: 'Attention Focus',
        value: consciousness.attentionFocus?.intensity || 0,
        connections: consciousness.attentionFocus?.targets || [],
        color: '#64B5F6'
      },
      {
        id: 'awareness',
        label: 'Self-Awareness',
        value: consciousness.selfAwareness?.level || 0,
        connections: consciousness.selfAwareness?.aspects || [],
        color: '#81C784'
      },
      {
        id: 'reflection',
        label: 'Meta-Reflection',
        value: consciousness.metaReflection?.depth || 0,
        connections: consciousness.metaReflection?.layers || [],
        color: '#FFB74D'
      },
      {
        id: 'monitoring',
        label: 'Process Monitoring',
        value: consciousness.processMonitoring?.coverage || 0,
        connections: consciousness.processMonitoring?.processes || [],
        color: '#F06292'
      }
    ];
    
    if (svgElement) {
      renderVisualization();
    }
  }

  function renderVisualization() {
    const svg = d3.select(svgElement);
    svg.selectAll("*").remove();

    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create radial layout for reflection aspects
    const angleStep = (2 * Math.PI) / reflectionData.length;
    const centerX = innerWidth / 2;
    const centerY = innerHeight / 2;
    const maxRadius = Math.min(innerWidth, innerHeight) / 3;

    // Draw connections between aspects
    const connections = g.append('g').attr('class', 'connections');
    
    reflectionData.forEach((aspect, i) => {
      const angle1 = i * angleStep;
      const x1 = centerX + Math.cos(angle1) * (maxRadius * aspect.value);
      const y1 = centerY + Math.sin(angle1) * (maxRadius * aspect.value);
      
      reflectionData.forEach((otherAspect, j) => {
        if (i !== j && aspect.connections.some(conn => 
          otherAspect.connections.includes(conn))) {
          const angle2 = j * angleStep;
          const x2 = centerX + Math.cos(angle2) * (maxRadius * otherAspect.value);
          const y2 = centerY + Math.sin(angle2) * (maxRadius * otherAspect.value);
          
          connections.append('line')
            .attr('x1', x1)
            .attr('y1', y1)
            .attr('x2', x2)
            .attr('y2', y2)
            .attr('stroke', '#666')
            .attr('stroke-width', 1)
            .attr('opacity', 0.3);
        }
      });
    });

    // Draw central consciousness core
    g.append('circle')
      .attr('cx', centerX)
      .attr('cy', centerY)
      .attr('r', 20)
      .attr('fill', '#BB86FC')
      .attr('opacity', 0.8);

    g.append('text')
      .attr('x', centerX)
      .attr('y', centerY)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '10px')
      .text('Core');

    // Draw reflection aspects
    const aspects = g.selectAll('.aspect')
      .data(reflectionData)
      .enter().append('g')
      .attr('class', 'aspect');

    aspects.each(function(d, i) {
      const aspect = d3.select(this);
      const angle = i * angleStep;
      const radius = maxRadius * d.value;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;

      // Draw connection line to center
      aspect.append('line')
        .attr('x1', centerX)
        .attr('y1', centerY)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', d.color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.6);

      // Draw aspect circle
      aspect.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 15 + d.value * 10)
        .attr('fill', d.color)
        .attr('opacity', 0.7)
        .on('mouseover', function() {
          d3.select(this).attr('opacity', 1);
        })
        .on('mouseout', function() {
          d3.select(this).attr('opacity', 0.7);
        });

      // Add aspect label
      const labelX = centerX + Math.cos(angle) * (radius + 30);
      const labelY = centerY + Math.sin(angle) * (radius + 30);
      
      aspect.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '12px')
        .text(d.label);

      // Add value indicator
      aspect.append('text')
        .attr('x', labelX)
        .attr('y', labelY + 15)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#ccc')
        .attr('font-size', '10px')
        .text(`${(d.value * 100).toFixed(0)}%`);
    });
  }

  onMount(() => {
    updateReflectionData();
  });
</script>

<div class="reflection-container">
  <div class="header">
    <h3>Cognitive Reflection Visualization</h3>
    <p>Real-time mapping of consciousness aspects and their interconnections</p>
  </div>
  
  <div class="visualization">
    <svg bind:this={svgElement} {width} {height}></svg>
  </div>
  
  <div class="metrics">
    {#each reflectionData as aspect}
      <div class="metric">
        <div class="metric-label" style="color: {aspect.color}">
          {aspect.label}
        </div>
        <div class="metric-value">
          {(aspect.value * 100).toFixed(1)}%
        </div>
        <div class="metric-connections">
          {aspect.connections.length} connections
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .reflection-container {
    background: rgba(18, 18, 18, 0.95);
    border: 1px solid rgba(187, 134, 252, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .header {
    margin-bottom: 1.5rem;
  }

  .header h3 {
    margin: 0 0 0.5rem 0;
    color: #BB86FC;
    font-size: 1.2rem;
  }

  .header p {
    margin: 0;
    color: #B0BEC5;
    font-size: 0.9rem;
  }

  .visualization {
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }

  .metric {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
  }

  .metric-label {
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .metric-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    margin-bottom: 0.25rem;
  }

  .metric-connections {
    font-size: 0.8rem;
    color: #B0BEC5;
  }
</style>
