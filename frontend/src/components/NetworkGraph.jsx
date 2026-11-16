import React, { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useNavigate } from 'react-router-dom';
import { Share2 } from 'lucide-react';

const INDUSTRY_COLORS = {
  'Food Delivery': '#f97316',
  'Payments & Fintech': '#3b82f6',
  'E-commerce': '#a855f7',
  'Banking & Finance': '#10b981',
  'Automotive': '#ef4444',
  'Travel & Hospitality': '#06b6d4',
  'Digital Payments': '#6366f1',
};

export default function NetworkGraph({ nodes = [], links = [] }) {
  const containerRef = useRef(null);
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });
  const navigate = useNavigate();

  useEffect(() => {
    function updateDimensions() {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 600,
          height: 420,
        });
      }
    }
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Format data for ForceGraph
  const graphData = {
    nodes: nodes.map((n) => ({
      ...n,
      val: Math.max(8, (n.trust_score || 1) * 12),
      color: INDUSTRY_COLORS[n.industry_category] || '#6366f1',
    })),
    links: links.map((l) => ({
      ...l,
      color: l.status === 'ENGAGED' ? '#10b981' : '#475569',
    })),
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl" ref={containerRef}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Share2 className="w-5 h-5 text-indigo-400" />
            Autonomous Agent Interaction Network
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Real-time topology of cross-company partnership proposals and routing connections
          </p>
        </div>

        {/* Legend */}
        <div className="hidden lg:flex items-center gap-3 text-xs">
          {Object.entries(INDUSTRY_COLORS).slice(0, 4).map(([industry, color]) => (
            <div key={industry} className="flex items-center gap-1.5 text-gray-400">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span>{industry}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl overflow-hidden bg-gray-950 border border-gray-800/80">
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          backgroundColor="#030712"
          nodeLabel={(n) => `${n.company_name} (${n.industry_category})`}
          nodeColor={(n) => n.color}
          nodeRelSize={6}
          linkColor={(l) => l.color}
          linkWidth={(l) => (l.status === 'ENGAGED' ? 2 : 1)}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleWidth={2}
          onNodeClick={(node) => navigate(`/agents/${node.id}`)}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.company_name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;

            // Draw circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.color;
            ctx.fill();
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();

            // Draw label
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#f3f4f6';
            ctx.fillText(label, node.x, node.y + 14);
          }}
        />
      </div>
    </div>
  );
}
