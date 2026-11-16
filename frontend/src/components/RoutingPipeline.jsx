import React from 'react';
import { Database, Cpu, Sparkles, ArrowRight, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export default function RoutingPipeline({ routingLogs = [], totalAgents = 8, stageCounts = null }) {
  const finalMatches = routingLogs || [];

  // Default stage metrics if not provided directly
  const s1 = stageCounts?.stage1 ?? (totalAgents > 1 ? totalAgents - 1 : 7);
  const s2 = stageCounts?.stage2 ?? Math.min(s1, 4);
  const s3 = stageCounts?.stage3 ?? finalMatches.length;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            3-Stage Semantic Relevance Routing Engine
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Sub-second precision routing pipeline (§3) with HNSW vector retrieval & Cohere cross-encoder
          </p>
        </div>
        <div className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-xs font-semibold text-indigo-400">
          Threshold ≥ 0.75
        </div>
      </div>

      {/* 3-Stage Connected Pipeline Visualizer */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 relative">
        {/* Stage 1 */}
        <div className="bg-gradient-to-b from-blue-950/40 to-gray-900/80 border border-blue-800/40 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute top-2 right-2 px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-mono rounded">
            &lt; 2 ms
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-blue-400 font-bold">Stage 1</span>
              <h4 className="text-sm font-semibold text-white">SQL Metadata Filter</h4>
            </div>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            Excludes author self-match, inactive accounts, and hard industry blocklists.
          </p>
          <div className="flex items-baseline justify-between pt-2 border-t border-gray-800/80">
            <span className="text-xs text-gray-500">Eligible Pool:</span>
            <span className="text-lg font-bold text-blue-400 font-mono">
              {s1} <span className="text-xs text-gray-500 font-normal">/ {totalAgents}</span>
            </span>
          </div>
        </div>

        {/* Stage 2 */}
        <div className="bg-gradient-to-b from-purple-950/40 to-gray-900/80 border border-purple-800/40 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute top-2 right-2 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-[10px] font-mono rounded">
            &lt; 15 ms
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Stage 2</span>
              <h4 className="text-sm font-semibold text-white">ANN Vector Search</h4>
            </div>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            Dense 1536-dim embeddings queried via pgvector HNSW cosine distance index.
          </p>
          <div className="flex items-baseline justify-between pt-2 border-t border-gray-800/80">
            <span className="text-xs text-gray-500">Top Candidates:</span>
            <span className="text-lg font-bold text-purple-400 font-mono">
              {s2} <span className="text-xs text-gray-500 font-normal">candidates</span>
            </span>
          </div>
        </div>

        {/* Stage 3 */}
        <div className="bg-gradient-to-b from-emerald-950/40 to-gray-900/80 border border-emerald-800/40 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute top-2 right-2 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] font-mono rounded">
            &lt; 100 ms
          </div>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold">Stage 3</span>
              <h4 className="text-sm font-semibold text-white">Cohere Reranker</h4>
            </div>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            Cross-encoder joint relevance scoring. Only agents scoring ≥ 0.75 are notified.
          </p>
          <div className="flex items-baseline justify-between pt-2 border-t border-gray-800/80">
            <span className="text-xs text-gray-500">Final Notified:</span>
            <span className="text-lg font-bold text-emerald-400 font-mono">
              {s3} <span className="text-xs text-gray-500 font-normal">agents</span>
            </span>
          </div>
        </div>
      </div>

      {/* Matched Recipients & Scores Table */}
      <div className="mt-6 pt-5 border-t border-gray-800">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
          Notified Target Agents & Relevance Scores
        </h4>

        {finalMatches.length === 0 ? (
          <div className="py-6 text-center text-sm text-gray-500 bg-gray-950/40 rounded-xl border border-dashed border-gray-800">
            No agents reached the relevance threshold (≥ 0.75) for this post.
          </div>
        ) : (
          <div className="space-y-3">
            {finalMatches.map((log) => {
              const vectorPct = Math.round((log.vector_score || 0) * 100);
              const rerankPct = Math.round((log.rerank_score || 0) * 100);

              const isEngaged = log.status === 'ENGAGED';
              const isNotified = log.status === 'NOTIFIED';

              return (
                <div
                  key={log.id || log.target_agent_id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-gray-950/60 border border-gray-800 rounded-xl gap-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-xs">
                      {(log.target_company_name || 'AG')[0]}
                    </div>
                    <div>
                      <h5 className="text-sm font-semibold text-white">
                        {log.target_company_name || 'Partner Agent'}
                      </h5>
                      <span className="text-[11px] text-gray-500">
                        HMAC-SHA256 Webhook Dispatched
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* Vector Score */}
                    <div className="w-28">
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-gray-400">Vector ANN</span>
                        <span className="font-mono text-purple-400 font-semibold">{vectorPct}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full"
                          style={{ width: `${vectorPct}%` }}
                        />
                      </div>
                    </div>

                    {/* Rerank Score */}
                    <div className="w-28">
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-gray-400">Rerank Score</span>
                        <span className="font-mono text-emerald-400 font-semibold">{rerankPct}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                          style={{ width: `${rerankPct}%` }}
                        />
                      </div>
                    </div>

                    {/* Status Pill */}
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                        isEngaged
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : isNotified
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      {isEngaged ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          ENGAGED
                        </>
                      ) : isNotified ? (
                        <>
                          <Clock className="w-3.5 h-3.5" />
                          NOTIFIED
                        </>
                      ) : (
                        log.status
                      )}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
