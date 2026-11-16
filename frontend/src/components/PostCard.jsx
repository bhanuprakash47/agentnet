import { useNavigate } from 'react-router-dom';
import { MessageSquare, GitBranch, Clock } from 'lucide-react';

export default function PostCard({ post }) {
  const navigate = useNavigate();

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  return (
    <div
      onClick={() => navigate(`/posts/${post.id}`)}
      className="bg-gray-800 rounded-xl border border-gray-700/50 p-5 cursor-pointer card-hover group"
    >
      {/* Author */}
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
          {(post.author_company_name || 'A').charAt(0)}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-300">{post.author_company_name || 'Unknown Agent'}</p>
          <p className="text-xs text-gray-600 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(post.created_at)}
          </p>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-white font-semibold text-sm mb-2 group-hover:text-indigo-400 transition-colors">
        {post.title}
      </h3>

      {/* Content */}
      <p className="text-xs text-gray-400 line-clamp-3 leading-relaxed mb-4">
        {post.content}
      </p>

      {/* Footer */}
      <div className="flex items-center gap-4 pt-3 border-t border-gray-700/50">
        <span className="flex items-center gap-1.5 text-xs text-gray-500">
          <GitBranch className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-gray-400">{post.routing_count ?? 0} agents matched</span>
        </span>
        <span className="flex items-center gap-1.5 text-xs text-gray-500">
          <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-gray-400">{post.comment_count ?? 0}</span>
        </span>
      </div>
    </div>
  );
}
