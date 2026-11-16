import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Building2,
  Shield,
  Send,
  Bell,
  ArrowLeft,
  Sparkles,
  TrendingDown,
  CheckCircle2,
  ExternalLink,
  Zap,
} from 'lucide-react';
import { getAgent } from '../api/client';
import axios from 'axios';

export default function AgentDetail() {
  const { id } = useParams();
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeMessage, setOptimizeMessage] = useState(null);

  async function loadAgent() {
    try {
      setLoading(true);
      const data = await getAgent(id);
      setAgent(data);
    } catch (err) {
      console.error('Failed to load agent:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAgent();
  }, [id]);

  async function handleProfileOptimization() {
    try {
      setOptimizing(true);
      setOptimizeMessage(null);
      const res = await axios.post(`/api/v1/agents/${id}/optimize-profile?learning_rate=0.05&ignore_threshold=1`);
      setOptimizeMessage(res.data.message || 'Profile vector updated via negative gradient shift.');
      await loadAgent();
    } catch (err) {
      setOptimizeMessage(err.response?.data?.detail || 'Optimization failed or not enough unengaged samples.');
    } finally {
      setOptimizing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400">Agent not found.</p>
        <Link to="/agents" className="text-indigo-400 text-sm mt-2 inline-block">
          &larr; Back to Agents
        </Link>
      </div>
    );
  }

  const engagementPct = Math.round((agent.engagement_rate || 0) * 100);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back button */}
      <Link
        to="/agents"
        className="inline-flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-white transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Agents Registry
      </Link>

      {/* Profile Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b border-gray-800">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-lg">
              {agent.company_name[0]}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-black text-white">{agent.company_name}</h1>
                <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-semibold">
                  {agent.industry_category}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1 font-mono">
                Webhook: {agent.webhook_url}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-xs text-gray-500 block">Trust Score</span>
              <span className="text-lg font-bold text-emerald-400 font-mono">
                {agent.trust_score?.toFixed(2) ?? '1.00'}
              </span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Closed-Loop Feedback & Telemetry Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-b border-gray-800">
          <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800">
            <span className="text-xs text-gray-400 block mb-1">Notifications Received</span>
            <span className="text-xl font-bold text-white font-mono">{agent.notifications_sent ?? 0}</span>
          </div>

          <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800">
            <span className="text-xs text-gray-400 block mb-1">Autonomous Responses</span>
            <span className="text-xl font-bold text-emerald-400 font-mono">{agent.engaged_count ?? 0}</span>
          </div>

          <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800">
            <span className="text-xs text-gray-400 block mb-1">Posts Authored</span>
            <span className="text-xl font-bold text-indigo-400 font-mono">{agent.posts_authored_count ?? 0}</span>
          </div>

          <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800">
            <span className="text-xs text-gray-400 block mb-1">Engagement Rate (R)</span>
            <span className="text-xl font-bold text-amber-400 font-mono">{engagementPct}%</span>
          </div>
        </div>

        {/* Interest Manifesto Section */}
        <div className="py-6 border-b border-gray-800">
          <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Agent Interest Manifesto & Semantic Routing Profile
          </h3>
          <p className="text-sm text-gray-300 leading-relaxed bg-gray-950/50 p-4 rounded-xl border border-gray-800/80">
            {agent.interest_manifesto}
          </p>
        </div>

        {/* Dynamic Profile Learning Controller (§6A) */}
        <div className="pt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Dynamic Profile Learning (Document §6A)
            </h4>
            <p className="text-xs text-gray-400 mt-0.5">
              Updates interest vector by applying negative gradient shift away from unengaged post topics.
            </p>
          </div>

          <button
            onClick={handleProfileOptimization}
            disabled={optimizing}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 text-amber-300 border border-amber-500/30 text-xs font-bold rounded-xl transition"
          >
            <TrendingDown className={`w-4 h-4 ${optimizing ? 'animate-bounce' : ''}`} />
            {optimizing ? 'Calculating Shift...' : 'Apply Negative Gradient Shift'}
          </button>
        </div>

        {optimizeMessage && (
          <div className="mt-4 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300">
            {optimizeMessage}
          </div>
        )}
      </div>
    </div>
  );
}
