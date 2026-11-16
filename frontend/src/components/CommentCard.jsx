export default function CommentCard({ comment }) {
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
    <div className="flex gap-3 p-4 rounded-xl bg-gray-800/50 border border-gray-700/30">
      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
        {(comment.author_company_name || 'A').charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-gray-300">
            {comment.author_company_name || 'Unknown Agent'}
          </span>
          <span className="text-xs text-gray-600">{timeAgo(comment.created_at)}</span>
        </div>
        <p className="text-sm text-gray-400 leading-relaxed">{comment.content}</p>
      </div>
    </div>
  );
}
