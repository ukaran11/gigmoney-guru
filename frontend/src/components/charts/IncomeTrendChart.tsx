/**
 * Income Trend Chart Component
 * 
 * Shows daily income trend with platform breakdown.
 */
import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { TrendingUp, Calendar, Zap } from 'lucide-react';

interface IncomeDataPoint {
  date: string;
  displayDate: string;
  dayOfWeek: string;
  total: number;
  platforms: Record<string, number>;
}

interface IncomeSummary {
  totalIncome: number;
  dailyAverage: number;
  bestDay: string;
  bestAmount: number;
  activeDays: number;
}

interface PlatformBreakdown {
  platform: string;
  amount: number;
  percentage: number;
}

interface Props {
  data: IncomeDataPoint[];
  summary: IncomeSummary;
  platformBreakdown: PlatformBreakdown[];
  loading?: boolean;
}

const PLATFORM_COLORS: Record<string, string> = {
  uber: '#000000',
  ola: '#4CAF50',
  swiggy: '#FC8019',
  zomato: '#E23744',
  rapido: '#FFD54F',
  dunzo: '#00C6AE',
  other: '#9CA3AF'
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold mb-2">{data.displayDate} ({data.dayOfWeek})</p>
        <div className="space-y-1 text-sm">
          <p className="text-green-400 font-semibold">Total: ₹{data.total.toLocaleString()}</p>
          {Object.entries(data.platforms || {}).map(([platform, amount]) => (
            <p key={platform} className="text-gray-300">
              <span className="capitalize">{platform}</span>: ₹{(amount as number).toLocaleString()}
            </p>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export default function IncomeTrendChart({ data, summary, platformBreakdown, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="h-64 bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Income Trend</h3>
        <div className="h-64 flex items-center justify-center text-gray-400">
          No income data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Income Trend</h3>
          <p className="text-sm text-gray-400 mt-1">
            Last 30 days earning pattern
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/20 text-blue-400">
          <TrendingUp className="w-4 h-4" />
          <span className="text-sm font-medium">₹{summary.dailyAverage.toLocaleString()}/day avg</span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-green-400" />
            <p className="text-xs text-gray-400">Total Earned</p>
          </div>
          <p className="text-lg font-semibold text-green-400">₹{summary.totalIncome.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <p className="text-xs text-gray-400">Best Day</p>
          </div>
          <p className="text-lg font-semibold text-blue-400">{summary.bestDay}</p>
          <p className="text-xs text-gray-400">₹{summary.bestAmount.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-4 h-4 text-purple-400" />
            <p className="text-xs text-gray-400">Active Days</p>
          </div>
          <p className="text-lg font-semibold text-purple-400">{summary.activeDays} days</p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-48 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="displayDate" 
              stroke="#9CA3AF" 
              fontSize={10}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis 
              stroke="#9CA3AF" 
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine 
              y={summary.dailyAverage} 
              stroke="#60A5FA" 
              strokeDasharray="5 5" 
              label={{ value: 'Avg', fill: '#60A5FA', fontSize: 10 }}
            />
            <Area
              type="monotone"
              dataKey="total"
              stroke="#10B981"
              fill="url(#incomeGradient)"
              strokeWidth={2}
            />
            <defs>
              <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Platform Breakdown */}
      {platformBreakdown && platformBreakdown.length > 0 && (
        <div className="pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400 mb-3">Platform Breakdown</p>
          <div className="flex flex-wrap gap-2">
            {platformBreakdown.map((p) => (
              <div 
                key={p.platform}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-700/50 rounded-lg"
              >
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: PLATFORM_COLORS[p.platform.toLowerCase()] || PLATFORM_COLORS.other }}
                />
                <span className="text-sm text-white capitalize">{p.platform}</span>
                <span className="text-xs text-gray-400">₹{p.amount.toLocaleString()} ({p.percentage}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
