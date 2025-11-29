/**
 * Risk Gauge Chart Component
 * 
 * Shows financial risk score as a gauge meter.
 */
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { AlertTriangle, XCircle, CheckCircle } from 'lucide-react';

interface RiskData {
  score: number;
  level: 'low' | 'moderate' | 'high';
  color: string;
  message: string;
  factors: string[];
  gaugeData: { name: string; value: number }[];
}

interface Props {
  data: RiskData;
  loading?: boolean;
}

export default function RiskGaugeChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="h-40 bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Financial Risk</h3>
        <div className="h-40 flex items-center justify-center text-gray-400">
          No risk data available
        </div>
      </div>
    );
  }

  const RiskIcon = data.level === 'low' ? CheckCircle : 
                   data.level === 'moderate' ? AlertTriangle : XCircle;

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Financial Risk</h3>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
          data.level === 'low' ? 'bg-green-500/20 text-green-400' :
          data.level === 'moderate' ? 'bg-yellow-500/20 text-yellow-400' :
          'bg-red-500/20 text-red-400'
        }`}>
          <RiskIcon className="w-4 h-4" />
          <span className="text-sm font-medium capitalize">{data.level} Risk</span>
        </div>
      </div>

      {/* Gauge */}
      <div className="relative h-36">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.gaugeData}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={60}
              outerRadius={90}
              paddingAngle={0}
              dataKey="value"
            >
              <Cell fill={data.color} />
              <Cell fill="#374151" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        
        {/* Score Display */}
        <div className="absolute inset-0 flex items-end justify-center pb-2">
          <div className="text-center">
            <p className="text-3xl font-bold" style={{ color: data.color }}>
              {data.score}
            </p>
            <p className="text-xs text-gray-400">/ 100</p>
          </div>
        </div>
      </div>

      {/* Message */}
      <div className="mt-4 p-3 bg-gray-700/50 rounded-lg">
        <p className="text-sm text-center" style={{ color: data.color }}>
          {data.message}
        </p>
      </div>

      {/* Risk Factors */}
      {data.factors && data.factors.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400 mb-2">Risk Factors:</p>
          <div className="space-y-2">
            {data.factors.slice(0, 3).map((factor, index) => (
              <div key={index} className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-300">{factor}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
