/**
 * Bucket Progress Chart Component
 * 
 * Shows progress of each financial bucket (rent, EMI, savings, etc.)
 */
import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Wallet, CheckCircle, AlertCircle } from 'lucide-react';

interface BucketDataPoint {
  name: string;
  target: number;
  current: number;
  percentage: number;
  color: string;
  gap: number;
}

interface BucketSummary {
  totalTarget: number;
  totalCurrent: number;
  overallPercentage: number;
  bucketsOnTrack: number;
}

interface Props {
  data: BucketDataPoint[];
  summary: BucketSummary;
  loading?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold mb-2">{data.name}</p>
        <div className="space-y-1 text-sm">
          <p className="text-green-400">Current: ₹{data.current.toLocaleString()}</p>
          <p className="text-gray-400">Target: ₹{data.target.toLocaleString()}</p>
          <p className={`font-medium ${data.percentage >= 80 ? 'text-green-400' : data.percentage >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
            Progress: {data.percentage}%
          </p>
          {data.gap > 0 && (
            <p className="text-orange-400">Gap: ₹{data.gap.toLocaleString()}</p>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export default function BucketProgressChart({ data, summary, loading }: Props) {
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
        <h3 className="text-lg font-semibold text-white mb-4">Bucket Progress</h3>
        <div className="h-64 flex items-center justify-center text-gray-400">
          No bucket data available
        </div>
      </div>
    );
  }

  const healthyBuckets = data.filter(b => b.percentage >= 80).length;
  const totalBuckets = data.length;

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Bucket Progress</h3>
          <p className="text-sm text-gray-400 mt-1">
            {summary.overallPercentage}% overall funded
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
          healthyBuckets === totalBuckets ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          {healthyBuckets === totalBuckets ? (
            <>
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">All on track</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">{healthyBuckets}/{totalBuckets} on track</span>
            </>
          )}
        </div>
      </div>

      {/* Progress Bars */}
      <div className="space-y-4 mb-6">
        {data.map((bucket) => (
          <div key={bucket.name} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white font-medium">{bucket.name}</span>
              <span className={`font-semibold ${
                bucket.percentage >= 80 ? 'text-green-400' : 
                bucket.percentage >= 50 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {bucket.percentage}%
              </span>
            </div>
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all duration-500"
                style={{ 
                  width: `${Math.min(bucket.percentage, 100)}%`,
                  backgroundColor: bucket.color
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400">
              <span>₹{bucket.current.toLocaleString()}</span>
              <span>₹{bucket.target.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Saved</p>
          <p className="text-lg font-semibold text-green-400">₹{summary.totalCurrent.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Target</p>
          <p className="text-lg font-semibold text-blue-400">₹{summary.totalTarget.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
