import React from 'react';

const GRADIENTS = {
  indigo: 'from-indigo-500 to-blue-600',
  blue: 'from-blue-500 to-cyan-500',
  emerald: 'from-emerald-500 to-teal-500',
  purple: 'from-purple-500 to-pink-500',
  amber: 'from-amber-500 to-orange-500',
};

export default function StatsCard({ icon: Icon, label, value, trend, color = 'indigo' }) {
  const gradientClass = GRADIENTS[color] || color;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 relative overflow-hidden shadow-lg group hover:border-gray-700 transition">
      {/* Accent border bar */}
      <div className={`absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b ${gradientClass}`} />

      <div className="flex items-start justify-between">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 block mb-1">
            {label}
          </span>
          <span className="text-2xl font-black text-white font-mono tracking-tight">
            {value}
          </span>
          {trend && (
            <span className="text-[11px] text-gray-400 block mt-1.5 font-medium">
              {trend}
            </span>
          )}
        </div>

        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${gradientClass} flex items-center justify-center text-white shadow-md shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
