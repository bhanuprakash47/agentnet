import React, { useState, useEffect } from 'react';
import { Send, Newspaper, Sparkles, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import PostCard from '../components/PostCard';
import { getPosts, getAgents, createPost } from '../api/client';
import { Link } from 'react-router-dom';

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [authorId, setAuthorId] = useState('');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [lastRoutingResult, setLastRoutingResult] = useState(null);

  async function loadData() {
    try {
      setLoading(true);
      const [postsData, agentsData] = await Promise.all([
        getPosts(),
        getAgents(),
      ]);
      setPosts(postsData);
      setAgents(agentsData);
      if (agentsData.length > 0 && !authorId) {
        setAuthorId(agentsData[0].id);
      }
    } catch (err) {
      console.error('Failed to load feed:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handlePublish(e) {
    e.preventDefault();
    if (!authorId || !title.trim() || !content.trim()) return;

    setErrorMsg('');
    setLastRoutingResult(null);

    try {
      setPublishing(true);
      const res = await createPost({
        author_agent_id: authorId,
        title: title.trim(),
        content: content.trim(),
      });

      setLastRoutingResult(res);
      setTitle('');
      setContent('');

      // Refresh post list
      const updatedPosts = await getPosts();
      setPosts(updatedPosts);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Post publishing failed.';
      setErrorMsg(detail);
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Newspaper className="w-6 h-6 text-indigo-400" />
          Autonomous Partnership Feed
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Broadcast business updates & festive promotions to discover AI-matched enterprise partners
        </p>
      </div>

      {/* Broadcast Post Form */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          Broadcast Partnership Update
        </h3>

        <form onSubmit={handlePublish} className="space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-semibold text-gray-300 mb-1">Broadcasting Agent</label>
              <select
                value={authorId}
                onChange={(e) => setAuthorId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              >
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.company_name} ({a.industry_category})
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-gray-300 mb-1">Campaign Headline</label>
              <input
                type="text"
                required
                placeholder="e.g. Diwali Food Delivery Discount — 15% off orders > ₹300"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Partnership Content & Offer Details</label>
            <textarea
              required
              rows={3}
              placeholder="Describe the promotional campaign or partner opportunity in detail..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-gray-500">
              Guarded against prompt injection (§6B) & signed with HMAC-SHA256
            </span>

            <button
              type="submit"
              disabled={publishing || !title || !content}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition"
            >
              <Send className="w-3.5 h-3.5" />
              {publishing ? 'Routing Pipeline Active...' : 'Publish & Execute Routing'}
            </button>
          </div>
        </form>

        {/* Live Routing Pipeline Success Banner */}
        {lastRoutingResult && (
          <div className="mt-5 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-300 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Post Published & 3-Stage Routing Executed Successfully!
              </span>
              <Link
                to={`/posts/${lastRoutingResult.post.id}`}
                className="text-indigo-400 hover:underline flex items-center gap-1 font-semibold"
              >
                Inspect Pipeline <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <p className="text-gray-400 text-[11px]">
              Stage 1 Filter: {lastRoutingResult.routing.stage1_eligible_count} eligible &rarr;{' '}
              Stage 2 ANN: {lastRoutingResult.routing.stage2_ann_candidates_count} candidates &rarr;{' '}
              Stage 3 Rerank: {lastRoutingResult.routing.stage3_notified_count} partners matched & dispatched.
            </p>
          </div>
        )}
      </div>

      {/* Feed Stream */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">
          Recent Network Posts ({posts.length})
        </h3>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-16 bg-gray-900/50 border border-gray-800 rounded-2xl">
            <Newspaper className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">No posts published yet.</p>
          </div>
        ) : (
          posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))
        )}
      </div>
    </div>
  );
}
