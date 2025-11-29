/**
 * Cashflow Forecast Chart Component
 * 
 * Shows 30-day projected cashflow with balance, income, and obligations.
 */
import {
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { TrendingUp, AlertTriangle } from 'lucide-react';

interface ForecastDataPoint {
  date: string;
  displayDate: string;
  balance: number;
  income: number;
  expenses: number;
  obligations: number;
  status: 'safe' | 'tight' | 'shortfall';
  statusColor: string;
}

interface ForecastSummary {
  totalIncome: number;
  totalExpenses: number;
  totalObligations: number;
  shortfallDays: number;
  projectedBalance: number;
}

interface Props {
  data: ForecastDataPoint[];
  summary: ForecastSummary;
  loading?: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold mb-2">{data.displayDate}</p>
        <div className="space-y-1 text-sm">
          <p className="text-purple-400">Balance: ₹{data.balance.toLocaleString()}</p>
          <p className="text-blue-400">Income: ₹{data.income.toLocaleString()}</p>
          <p className="text-orange-400">Obligations: ₹{data.obligations.toLocaleString()}</p>
          <p className={`font-medium ${
            data.status === 'safe' ? 'text-green-400' : 
            data.status === 'tight' ? 'text-yellow-400' : 'text-red-400'
          }`}>
            Status: {data.status.charAt(0).toUpperCase() + data.status.slice(1)}
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export default function CashflowForecastChart({ data, summary, loading }: Props) {
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
        <h3 className="text-lg font-semibold text-white mb-4">30-Day Cashflow Forecast</h3>
        <div className="h-64 flex items-center justify-center text-gray-400">
          No forecast data available
        </div>
      </div>
    );
  }

  const isPositiveOutlook = summary.projectedBalance > 0 && summary.shortfallDays === 0;

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">30-Day Cashflow Forecast</h3>
          <p className="text-sm text-gray-400 mt-1">
            Projected balance: ₹{summary.projectedBalance.toLocaleString()}
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
          isPositiveOutlook ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {isPositiveOutlook ? (
            <>
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm font-medium">Healthy</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">{summary.shortfallDays} shortfall days</span>
            </>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Income</p>
          <p className="text-lg font-semibold text-blue-400">₹{summary.totalIncome.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Total Expenses</p>
          <p className="text-lg font-semibold text-orange-400">₹{summary.totalExpenses.toLocaleString()}</p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400">Obligations</p>
          <p className="text-lg font-semibold text-purple-400">₹{summary.totalObligations.toLocaleString()}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="displayDate" 
              stroke="#9CA3AF" 
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis 
              stroke="#9CA3AF" 
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              iconType="rect"
            />
            <ReferenceLine y={0} stroke="#EF4444" strokeDasharray="5 5" />
            <Area
              type="monotone"
              dataKey="balance"
              name="Balance"
              stroke="#9333EA"
              fill="url(#balanceGradient)"
              strokeWidth={2}
            />
            <Bar 
              dataKey="income" 
              name="Income" 
              fill="#3B82F6" 
              opacity={0.6}
              radius={[2, 2, 0, 0]}
            />
            <defs>
              <linearGradient id="balanceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9333EA" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#9333EA" stopOpacity={0}/>
              </linearGradient>
            </defs>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
