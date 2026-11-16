import { useNavigate } from 'react-router-dom';
import { Shield, Calendar } from 'lucide-react';

const industryColors = {
  'Food Delivery': { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', bar: 'bg-orange-500' },
  'Payments & Fintech': { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30', bar: 'bg-blue-500' },
  'E-commerce': { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30', bar: 'bg-purple-500' },
  'Banking & Finance': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', bar: 'bg-emerald-500' },
  'Automotive': { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30', bar: 'bg-red-500' },
  'Travel & Hospitality': { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30', bar: 'bg-cyan-500' },
  'Digital Payments': { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/30', bar: 'bg-indigo-500' },
};

const defaultColor = { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/30', bar: 'bg-gray-500' };

export default function AgentCard({ agent }) {
  const navigate = useNavigate();
  const colors = industryColors[agent.industry_category] || defaultColor;
  const trustPercent = Math.round((agent.trust_score ?? 0) * 100);

  return (
    <div
      onClick={() => navigate(`/agents/${agent.id}`)}
      className="bg-gray-800 rounded-xl border border-gray-700/50 p-5 cursor-pointer card-hover group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-white font-semibold text-sm group-hover:text-indigo-400 transition-colors truncate pr-2">
          {agent.company_name}
        </h3>
        <div className={`${agent.is_active ? 'bg-emerald-500' : 'bg-gray-600'} w-2 h-2 rounded-full shrink-0 mt-1.5`} />
      </div>

      {/* Industry badge */}
      <span
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${colors.bg} ${colors.text} ${colors.border}`}
      >
        {agent.industry_category}
      </span>

      {/* Trust Score */}
      <div className="mt-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <Shield className="w-3 h-3" />
            Trust Score
          </span>
          <span className="text-xs font-medium text-gray-300">{trustPercent}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full ${colors.bar} transition-all duration-500`}
            style={{ width: `${trustPercent}%` }}
          />
        </div>
      </div>

      {/* Manifesto */}
      {agent.interest_manifesto && (
        <p className="text-xs text-gray-400 mt-3 line-clamp-2 leading-relaxed">
          {agent.interest_manifesto}
        </p>
      )}

      {/* Date */}
      <div className="flex items-center gap-1 mt-3 text-xs text-gray-600">
        <Calendar className="w-3 h-3" />
        {new Date(agent.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
