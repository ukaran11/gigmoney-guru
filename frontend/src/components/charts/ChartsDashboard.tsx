/**
 * Charts Dashboard Component
 * 
 * Main dashboard that displays all financial charts.
 */
import { useEffect, useState } from 'react';
import { BarChart3, RefreshCw, Expand, Minimize } from 'lucide-react';
import CashflowForecastChart from './CashflowForecastChart';
import BucketProgressChart from './BucketProgressChart';
import IncomeTrendChart from './IncomeTrendChart';
import ExpenseBreakdownChart from './ExpenseBreakdownChart';
import RiskGaugeChart from './RiskGaugeChart';
import GoalProgressChart from './GoalProgressChart';
import api from '../../lib/api';

interface ChartData {
  forecast?: {
    data: any[];
    summary: any;
  };
  buckets?: {
    data: any[];
    summary: any;
  };
  incomeTrend?: {
    data: any[];
    summary: any;
    platformBreakdown: any[];
  };
  expenses?: {
    categoryBreakdown: any[];
    summary: any;
  };
  goals?: {
    data: any[];
    summary: any;
  };
  riskGauge?: any;
  generatedAt?: string;
}

interface Props {
  compact?: boolean; // For showing in dashboard vs full page
}

export default function ChartsDashboard({ compact = false }: Props) {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchChartData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/charts/all');
      if (response.data.success) {
        setChartData(response.data.charts);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load charts');
      console.error('Chart fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChartData();
    // Refresh every 5 minutes
    const interval = setInterval(fetchChartData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Financial Charts
          </h2>
        </div>
        <div className="text-center py-8 text-red-400">
          <p>{error}</p>
          <button 
            onClick={fetchChartData}
            className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (compact) {
    // Compact view - show only key charts
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-purple-400" />
            Financial Insights
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchChartData}
              disabled={loading}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title={expanded ? "Collapse" : "Expand"}
            >
              {expanded ? <Minimize className="w-5 h-5" /> : <Expand className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {expanded ? (
          // Expanded view - show all charts
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="lg:col-span-2">
              <CashflowForecastChart 
                data={chartData?.forecast?.data || []}
                summary={chartData?.forecast?.summary || {}}
                loading={loading}
              />
            </div>
            <BucketProgressChart 
              data={chartData?.buckets?.data || []}
              summary={chartData?.buckets?.summary || {}}
              loading={loading}
            />
            <RiskGaugeChart 
              data={chartData?.riskGauge}
              loading={loading}
            />
            <IncomeTrendChart 
              data={chartData?.incomeTrend?.data || []}
              summary={chartData?.incomeTrend?.summary || {}}
              platformBreakdown={chartData?.incomeTrend?.platformBreakdown || []}
              loading={loading}
            />
            <ExpenseBreakdownChart 
              categoryBreakdown={chartData?.expenses?.categoryBreakdown || []}
              summary={chartData?.expenses?.summary || {}}
              loading={loading}
            />
            <div className="lg:col-span-2">
              <GoalProgressChart 
                data={chartData?.goals?.data || []}
                summary={chartData?.goals?.summary || {}}
                loading={loading}
              />
            </div>
          </div>
        ) : (
          // Compact view - show mini versions
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Risk Score Mini */}
            <div className="bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Risk Score</span>
                <span 
                  className="text-xl font-bold"
                  style={{ color: chartData?.riskGauge?.color || '#9CA3AF' }}
                >
                  {chartData?.riskGauge?.score || 0}
                </span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    width: `${chartData?.riskGauge?.score || 0}%`,
                    backgroundColor: chartData?.riskGauge?.color || '#9CA3AF'
                  }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2 capitalize">
                {chartData?.riskGauge?.level || 'Unknown'} risk
              </p>
            </div>

            {/* Bucket Progress Mini */}
            <div className="bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Buckets</span>
                <span className="text-xl font-bold text-green-400">
                  {chartData?.buckets?.summary?.overallPercentage || 0}%
                </span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 rounded-full transition-all duration-500"
                  style={{ width: `${chartData?.buckets?.summary?.overallPercentage || 0}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {chartData?.buckets?.summary?.bucketsOnTrack || 0} of {chartData?.buckets?.data?.length || 0} on track
              </p>
            </div>

            {/* Income Mini */}
            <div className="bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Daily Avg Income</span>
                <span className="text-xl font-bold text-blue-400">
                  ₹{chartData?.incomeTrend?.summary?.dailyAverage?.toLocaleString() || 0}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {chartData?.incomeTrend?.summary?.activeDays || 0} active days
              </p>
              <p className="text-xs text-green-400 mt-1">
                Best: {chartData?.incomeTrend?.summary?.bestDay || 'N/A'}
              </p>
            </div>
          </div>
        )}

        {chartData?.generatedAt && (
          <p className="text-xs text-gray-500 text-center">
            Last updated: {new Date(chartData.generatedAt).toLocaleTimeString()}
          </p>
        )}
      </div>
    );
  }

  // Full page view
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <BarChart3 className="w-7 h-7 text-purple-400" />
          Financial Dashboard
        </h2>
        <button
          onClick={fetchChartData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Top Row - Forecast and Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CashflowForecastChart 
            data={chartData?.forecast?.data || []}
            summary={chartData?.forecast?.summary || {}}
            loading={loading}
          />
        </div>
        <RiskGaugeChart 
          data={chartData?.riskGauge}
          loading={loading}
        />
      </div>

      {/* Middle Row - Buckets and Goals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BucketProgressChart 
          data={chartData?.buckets?.data || []}
          summary={chartData?.buckets?.summary || {}}
          loading={loading}
        />
        <GoalProgressChart 
          data={chartData?.goals?.data || []}
          summary={chartData?.goals?.summary || {}}
          loading={loading}
        />
      </div>

      {/* Bottom Row - Income and Expenses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <IncomeTrendChart 
          data={chartData?.incomeTrend?.data || []}
          summary={chartData?.incomeTrend?.summary || {}}
          platformBreakdown={chartData?.incomeTrend?.platformBreakdown || []}
          loading={loading}
        />
        <ExpenseBreakdownChart 
          categoryBreakdown={chartData?.expenses?.categoryBreakdown || []}
          summary={chartData?.expenses?.summary || {}}
          loading={loading}
        />
      </div>

      {chartData?.generatedAt && (
        <p className="text-sm text-gray-500 text-center">
          Data as of {new Date(chartData.generatedAt).toLocaleString()}
        </p>
      )}
    </div>
  );
}
