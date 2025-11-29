/**
 * Expense Breakdown Chart Component
 * 
 * Shows expense categories as a pie chart with summary.
 */
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

interface CategoryData {
  name: string;
  value: number;
  percentage: number;
}

interface ExpenseSummary {
  totalExpenses: number;
  dailyAverage: number;
  topCategory: string;
  categoryCount: number;
}

interface Props {
  categoryBreakdown: CategoryData[];
  summary: ExpenseSummary;
  loading?: boolean;
}

const CATEGORY_COLORS = [
  '#EF4444', // Red
  '#F59E0B', // Amber
  '#10B981', // Emerald
  '#3B82F6', // Blue
  '#8B5CF6', // Violet
  '#EC4899', // Pink
  '#6B7280', // Gray
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-white font-semibold">{data.name}</p>
        <p className="text-green-400">₹{data.value.toLocaleString()}</p>
        <p className="text-gray-400 text-sm">{data.percentage}% of total</p>
      </div>
    );
  }
  return null;
};

const CustomLegend = ({ payload }: any) => {
  return (
    <div className="flex flex-wrap justify-center gap-3 mt-4">
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-1.5">
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-xs text-gray-300">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function ExpenseBreakdownChart({ categoryBreakdown, summary, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="h-64 bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (!categoryBreakdown || categoryBreakdown.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Expense Breakdown</h3>
        <div className="h-64 flex items-center justify-center text-gray-400">
          No expense data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Expense Breakdown</h3>
          <p className="text-sm text-gray-400 mt-1">
            Where your money goes
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Total Spent</p>
          <p className="text-lg font-semibold text-red-400">₹{summary.totalExpenses.toLocaleString()}</p>
        </div>
      </div>

      {/* Pie Chart */}
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={categoryBreakdown}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              nameKey="name"
            >
              {categoryBreakdown.map((_, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Category List */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="space-y-3">
          {categoryBreakdown.slice(0, 5).map((category, index) => (
            <div key={category.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }}
                />
                <span className="text-sm text-white">{category.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-400">₹{category.value.toLocaleString()}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  category.percentage > 30 ? 'bg-red-500/20 text-red-400' :
                  category.percentage > 20 ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-700 text-gray-400'
                }`}>
                  {category.percentage}%
                </span>
              </div>
            </div>
          ))}
        </div>
        
        {/* Daily Average */}
        <div className="mt-4 p-3 bg-gray-700/50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Daily Average</span>
            <span className="text-sm font-semibold text-white">₹{summary.dailyAverage.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
