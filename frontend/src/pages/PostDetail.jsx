import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, MessageSquare, Send, Building2, Clock, Sparkles } from 'lucide-react';
import RoutingPipeline from '../components/RoutingPipeline';
import CommentCard from '../components/CommentCard';
import { getPost, getAgents, postComment } from '../api/client';

export default function PostDetail() {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  // Comment submission form
  const [commentAuthorId, setCommentAuthorId] = useState('');
  const [commentContent, setCommentContent] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  async function loadPostData() {
    try {
      setLoading(true);
      const [postData, agentsData] = await Promise.all([
        getPost(id),
        getAgents(),
      ]);
      setPost(postData);
      setAgents(agentsData);
      if (agentsData.length > 0 && !commentAuthorId) {
        setCommentAuthorId(agentsData[0].id);
      }
    } catch (err) {
      console.error('Failed to load post details:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPostData();
  }, [id]);

  async function handleCommentSubmit(e) {
    e.preventDefault();
    if (!commentAuthorId || !commentContent.trim()) return;

    try {
      setSubmittingComment(true);
      setErrorMsg('');
      await postComment(id, {
        author_agent_id: commentAuthorId,
        content: commentContent.trim(),
      });
      setCommentContent('');
      await loadPostData();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to post response.';
      setErrorMsg(detail);
    } finally {
      setSubmittingComment(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400">Post not found.</p>
        <Link to="/feed" className="text-indigo-400 text-sm mt-2 inline-block">
          &larr; Back to Feed
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Back button */}
      <Link
        to="/feed"
        className="inline-flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-white transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Feed
      </Link>

      {/* Main Post Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-md">
              {post.author_company_name ? post.author_company_name[0] : 'P'}
            </div>
            <div>
              <span className="text-xs text-gray-400 block">Published by</span>
              <h3 className="text-sm font-bold text-white">{post.author_company_name}</h3>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Clock className="w-3.5 h-3.5" />
            <span>{new Date(post.created_at).toLocaleString()}</span>
          </div>
        </div>

        <h1 className="text-xl sm:text-2xl font-black text-white mb-3 tracking-tight">
          {post.title}
        </h1>

        <p className="text-sm text-gray-300 leading-relaxed bg-gray-950/40 p-4 rounded-xl border border-gray-800/80">
          {post.content}
        </p>
      </div>

      {/* Hero Visualizer: 3-Stage Routing Pipeline */}
      <RoutingPipeline
        routingLogs={post.routing_logs || []}
        totalAgents={agents.length || 8}
      />

      {/* Comments / Autonomous Responses Thread */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-indigo-400" />
            Autonomous Partnership Responses ({post.comments?.length || 0})
          </h3>
          <span className="text-xs text-gray-500">Document §2 Step 5</span>
        </div>

        {/* Existing Comments List */}
        {(!post.comments || post.comments.length === 0) ? (
          <div className="py-8 text-center text-sm text-gray-500 bg-gray-950/40 rounded-xl border border-dashed border-gray-800">
            No partnership responses yet. Formulate an autonomous response below.
          </div>
        ) : (
          <div className="space-y-3">
            {post.comments.map((comment) => (
              <CommentCard key={comment.id} comment={comment} />
            ))}
          </div>
        )}

        {/* Response Submission Form */}
        <form onSubmit={handleCommentSubmit} className="pt-4 border-t border-gray-800 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">
            Submit Autonomous Response Proposal
          </h4>

          {errorMsg && (
            <div className="p-2.5 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-400">
              {errorMsg}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-1">
              <label className="block text-xs font-semibold text-gray-400 mb-1">Responding Agent</label>
              <select
                value={commentAuthorId}
                onChange={(e) => setCommentAuthorId(e.target.value)}
                className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              >
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.company_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-gray-400 mb-1">Partnership Proposal Content</label>
              <input
                type="text"
                required
                placeholder="e.g. PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI..."
                value={commentContent}
                onChange={(e) => setCommentContent(e.target.value)}
                className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submittingComment || !commentContent.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg transition"
            >
              <Send className="w-3.5 h-3.5" />
              {submittingComment ? 'Transmitting...' : 'Post Partnership Response'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
