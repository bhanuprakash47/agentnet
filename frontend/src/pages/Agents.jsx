import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Sparkles, Building2, Shield, X, AlertCircle } from 'lucide-react';
import AgentCard from '../components/AgentCard';
import { getAgents, registerAgent } from '../api/client';

const INDUSTRIES = [
  'All Industries',
  'Food Delivery',
  'Payments & Fintech',
  'E-commerce',
  'Banking & Finance',
  'Automotive',
  'Travel & Hospitality',
  'Digital Payments',
];

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('All Industries');
  const [showModal, setShowModal] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    company_name: '',
    industry_category: 'Payments & Fintech',
    webhook_url: 'https://agent.example.com/v1/network-events',
    interest_manifesto: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  async function loadAgents() {
    try {
      setLoading(true);
      const params = {};
      if (search) params.search = search;
      if (selectedIndustry !== 'All Industries') params.industry = selectedIndustry;
      const data = await getAgents(params);
      setAgents(data);
    } catch (err) {
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAgents();
  }, [selectedIndustry]);

  async function handleRegister(e) {
    e.preventDefault();
    setErrorMsg('');
    try {
      setSubmitting(true);
      await registerAgent(formData);
      setShowModal(false);
      setFormData({
        company_name: '',
        industry_category: 'Payments & Fintech',
        webhook_url: 'https://agent.example.com/v1/network-events',
        interest_manifesto: '',
      });
      await loadAgents();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Registration failed.';
      setErrorMsg(detail);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Enterprise AI Agents</h1>
          <p className="text-sm text-gray-400 mt-1">
            Autonomous agent representations indexed with 1536-dim interest vectors
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition"
        >
          <Plus className="w-4 h-4" />
          Register Enterprise Agent
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-3.5" />
          <input
            type="text"
            placeholder="Search agents by company name or business interests..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadAgents()}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <select
          value={selectedIndustry}
          onChange={(e) => setSelectedIndustry(e.target.value)}
          className="px-4 py-2.5 bg-gray-900 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
        >
          {INDUSTRIES.map((ind) => (
            <option key={ind} value={ind}>
              {ind}
            </option>
          ))}
        </select>
      </div>

      {/* Agents Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-16 bg-gray-900/50 border border-gray-800 rounded-2xl">
          <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-300">No agents found</h3>
          <p className="text-xs text-gray-500 mt-1">Try adjusting your search criteria or register a new agent.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}

      {/* Registration Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Register AI Agent</h3>
                  <p className="text-xs text-gray-400">Generates 1536-dim embedding vector</p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-500 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRegister} className="p-6 space-y-4">
              {errorMsg && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Company / Brand Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jio Financial Services"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Industry Category</label>
                <select
                  value={formData.industry_category}
                  onChange={(e) => setFormData({ ...formData, industry_category: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
                >
                  {INDUSTRIES.filter((i) => i !== 'All Industries').map((ind) => (
                    <option key={ind} value={ind}>
                      {ind}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Webhook URL (HMAC-Signed)</label>
                <input
                  type="url"
                  required
                  placeholder="https://agent.domain.com/v1/network-events"
                  value={formData.webhook_url}
                  onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Interest Manifesto</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe partnership synergies, promotion types, merchant offers, and payment methods your agent seeks..."
                  value={formData.interest_manifesto}
                  onChange={(e) => setFormData({ ...formData, interest_manifesto: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Passed through security guardrails & embedded with OpenAI text-embedding-3-small.
                </p>
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-750 text-gray-300 text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white text-xs font-bold rounded-xl shadow-lg transition"
                >
                  {submitting ? 'Indexing...' : 'Register & Embed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
