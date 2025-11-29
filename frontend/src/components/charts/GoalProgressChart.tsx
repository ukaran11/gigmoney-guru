/**
 * Goal Progress Chart Component
 * 
 * Shows progress towards financial goals.
 */
import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Target, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

interface GoalDataPoint {
  name: string;
  target: number;
  current: number;
  percentage: number;
  daysLeft: number;
  dailyNeeded: number;
  onTrack: boolean;
}

interface GoalSummary {
  totalGoals: number;
  goalsOnTrack: number;
  totalTarget: number;
  totalSaved: number;
}

interface Props {
  data: GoalDataPoint[];
  summary: GoalSummary;
  loading?: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold mb-2">{data.name}</p>
        <div className="space-y-1 text-sm">
          <p className="text-green-400">Saved: ₹{data.current.toLocaleString()}</p>
          <p className="text-blue-400">Target: ₹{data.target.toLocaleString()}</p>
          <p className="text-gray-400">{data.daysLeft} days left</p>
          <p className="text-purple-400">Need ₹{data.dailyNeeded.toLocaleString()}/day</p>
          <p className={data.onTrack ? 'text-green-400' : 'text-red-400'}>
            {data.onTrack ? '✓ On Track' : '✗ Behind Schedule'}
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export default function GoalProgressChart({ data, summary, loading }: Props) {
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
        <h3 className="text-lg font-semibold text-white mb-4">Goal Progress</h3>
        <div className="h-64 flex flex-col items-center justify-center text-gray-400">
          <Target className="w-12 h-12 mb-3 opacity-50" />
          <p>No goals set yet</p>
          <p className="text-sm">Create a goal to start tracking</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Goal Progress</h3>
          <p className="text-sm text-gray-400 mt-1">
            Track your savings goals
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
          summary.goalsOnTrack === summary.totalGoals 
            ? 'bg-green-500/20 text-green-400' 
            : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          {summary.goalsOnTrack === summary.totalGoals ? (
            <>
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">All on track</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">{summary.goalsOnTrack}/{summary.totalGoals} on track</span>
            </>
          )}
        </div>
      </div>

      {/* Goal Cards */}
      <div className="space-y-4 mb-6">
        {data.map((goal) => (
          <div key={goal.name} className="bg-gray-700/50 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Target className={`w-5 h-5 ${goal.onTrack ? 'text-green-400' : 'text-yellow-400'}`} />
                <div>
                  <p className="text-white font-medium">{goal.name}</p>
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {goal.daysLeft} days left
                  </p>
                </div>
              </div>
              <div className={`text-sm font-semibold ${
                goal.percentage >= 80 ? 'text-green-400' :
                goal.percentage >= 50 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {goal.percentage}%
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="h-2 bg-gray-600 rounded-full overflow-hidden mb-2">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  goal.onTrack ? 'bg-green-500' : 'bg-yellow-500'
                }`}
                style={{ width: `${Math.min(goal.percentage, 100)}%` }}
              />
            </div>
            
            <div className="flex justify-between text-xs">
              <span className="text-green-400">₹{goal.current.toLocaleString()}</span>
              <span className="text-gray-400">₹{goal.target.toLocaleString()}</span>
            </div>
            
            {goal.daysLeft > 0 && goal.dailyNeeded > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-600">
                <p className="text-xs text-gray-400">
                  Save <span className="text-purple-400 font-medium">₹{goal.dailyNeeded.toLocaleString()}</span> daily to reach goal
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Saved</p>
          <p className="text-lg font-semibold text-green-400">₹{summary.totalSaved.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Target</p>
          <p className="text-lg font-semibold text-blue-400">₹{summary.totalTarget.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
