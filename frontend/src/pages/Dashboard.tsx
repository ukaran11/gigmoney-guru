import { useEffect, useState } from 'react'
import { useDashboardStore } from '../store/dashboardStore'
import { 
  TrendingUp, 
  AlertTriangle, 
  Wallet, 
  Calendar,
  RefreshCw,
  Zap,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  FileText,
  Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import AddIncomeModal from '../components/AddIncomeModal'
import AddExpenseModal from '../components/AddExpenseModal'
import AddObligationModal from '../components/AddObligationModal'
import AgentActivityLog from '../components/AgentActivityLog'
import { ChartsDashboard } from '../components/charts'

// Bucket Card Component
function BucketCard({ bucket }: { bucket: { name: string; display_name: string; icon: string; color: string; current_balance: number; target_amount: number } }) {
  const progress = bucket.target_amount > 0 
    ? Math.min(100, (bucket.current_balance / bucket.target_amount) * 100)
    : 100

  const colorClasses: Record<string, string> = {
    essentials: 'from-blue-500 to-blue-600',
    flex: 'from-purple-500 to-purple-600',
    goals: 'from-green-500 to-green-600',
    emergency: 'from-orange-500 to-orange-600',
    discretionary: 'from-pink-500 to-pink-600',
  }

  return (
    <div className={`rounded-xl p-4 text-white bg-gradient-to-br ${colorClasses[bucket.name] || 'from-gray-500 to-gray-600'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{bucket.icon}</span>
        <span className="font-semibold">{bucket.display_name}</span>
      </div>
      <div className="text-2xl font-bold mb-2">₹{bucket.current_balance.toLocaleString()}</div>
      {bucket.target_amount > 0 && (
        <>
          <div className="w-full bg-white/30 rounded-full h-2 mb-1">
            <div 
              className="bg-white rounded-full h-2 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-xs opacity-80">
            {progress.toFixed(0)}% of ₹{bucket.target_amount.toLocaleString()}
          </div>
        </>
      )}
    </div>
  )
}

// Obligation Card Component
function ObligationCard({ obligation, onMarkPaid }: { 
  obligation: { id: string; name: string; amount: number; due_date: string; days_until_due: number }
  onMarkPaid?: (id: string) => void
}) {
  const isUrgent = obligation.days_until_due <= 3

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg ${isUrgent ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
      <div>
        <div className="font-medium text-gray-900">{obligation.name}</div>
        <div className="text-sm text-gray-500">
          Due in {obligation.days_until_due} days
        </div>
      </div>
      <div className="text-right flex items-center gap-2">
        <div>
          <div className="font-bold text-gray-900">₹{obligation.amount.toLocaleString()}</div>
          {isUrgent && (
            <span className="text-xs text-red-600 font-medium">⚠️ Urgent</span>
          )}
        </div>
        {onMarkPaid && (
          <button
            onClick={() => onMarkPaid(obligation.id)}
            className="p-1.5 text-green-600 hover:bg-green-100 rounded-lg"
            title="Mark as paid"
          >
            ✓
          </button>
        )}
      </div>
    </div>
  )
}

// Quick Action Button
function QuickAction({ icon, label, onClick, color = 'gray' }: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  color?: 'green' | 'red' | 'orange' | 'gray'
}) {
  const colors = {
    green: 'bg-green-100 text-green-700 hover:bg-green-200 border-green-200',
    red: 'bg-red-100 text-red-700 hover:bg-red-200 border-red-200',
    orange: 'bg-orange-100 text-orange-700 hover:bg-orange-200 border-orange-200',
    gray: 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-200',
  }

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-colors border ${colors[color]}`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  )
}

function Dashboard() {
  const {
    totalBalance,
    safeToSpend,
    riskScore,
    riskLevel,
    keyInsight,
    recommendedAction,
    confidenceScore,
    buckets,
    upcomingObligations,
    messages,
    warnings,
    alerts,
    isLoading,
    isRunningAgents,
    agentActivity,
    toolCalls,
    agenticMode,
    reactIterations,
    totalToolCalls,
    reasoningChain,
    error,
    fetchDashboard,
    runDailyAgents,
    seedDemoData,
    simulateDay,
    resetData,
  } = useDashboardStore()

  const [showIncomeModal, setShowIncomeModal] = useState(false)
  const [showExpenseModal, setShowExpenseModal] = useState(false)
  const [showObligationModal, setShowObligationModal] = useState(false)

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  const handleSeedDemo = async () => {
    await seedDemoData()
    toast.success('Demo data loaded! 🎉')
  }

  const handleResetData = async () => {
    if (window.confirm('Are you sure you want to reset ALL your data? This cannot be undone.')) {
      await resetData()
      toast.success('All data cleared! 🗑️')
    }
  }

  const handleRunAgents = async (mode: string = 'react') => {
    await runDailyAgents(mode)
    toast.success('AI analysis complete! 🧠')
  }

  const handleSimulate = async (scenario: string) => {
    await simulateDay(scenario)
    toast.success(`Simulated ${scenario} scenario!`)
  }

  const handleMarkPaid = async (obligationId: string) => {
    try {
      const token = localStorage.getItem('token')
      await fetch(`/api/obligations/${obligationId}/mark-paid`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      toast.success('Marked as paid!')
      fetchDashboard()
    } catch (error) {
      toast.error('Failed to mark as paid')
    }
  }

  if (isLoading && buckets.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with Quick Actions */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Manage your gig income smartly</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => fetchDashboard()}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          </button>
          {/* Agent Mode Selection */}
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => handleRunAgents('react')}
              disabled={isRunningAgents}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors disabled:opacity-50 ${
                agenticMode === 'react' ? 'bg-purple-600 text-white' : 'hover:bg-gray-200'
              }`}
              title="ReAct Mode - Full autonomy with tool calling"
            >
              🧠 ReAct
            </button>
            <button
              onClick={() => handleRunAgents('routed')}
              disabled={isRunningAgents}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors disabled:opacity-50 ${
                agenticMode === 'routed' ? 'bg-blue-600 text-white' : 'hover:bg-gray-200'
              }`}
              title="Routed Mode - Router decides which agents run"
            >
              🔀 Routed
            </button>
            <button
              onClick={() => handleRunAgents('fast')}
              disabled={isRunningAgents}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors disabled:opacity-50 ${
                agenticMode === 'fast' ? 'bg-gray-600 text-white' : 'hover:bg-gray-200'
              }`}
              title="Fast Mode - No LLM, just calculations"
            >
              ⚡ Fast
            </button>
          </div>
          <button
            onClick={() => handleRunAgents()}
            disabled={isRunningAgents}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            <Zap size={18} />
            {isRunningAgents ? 'Thinking...' : 'Run AI'}
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Key Insight Banner (from AI) */}
      {keyInsight && (
        <div className={`rounded-xl p-4 border ${
          keyInsight.includes('⚠️') || keyInsight.includes('gap') 
            ? 'bg-gradient-to-r from-orange-100 to-red-100 border-orange-200' 
            : keyInsight.includes('✅') || keyInsight.includes('Accha')
            ? 'bg-gradient-to-r from-green-100 to-emerald-100 border-green-200'
            : 'bg-gradient-to-r from-purple-100 to-blue-100 border-purple-200'
        }`}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">🧠</span>
            <div className="flex-1">
              <p className={`font-semibold ${
                keyInsight.includes('⚠️') ? 'text-orange-900' : 
                keyInsight.includes('✅') ? 'text-green-900' : 'text-purple-900'
              }`}>{keyInsight}</p>
              {recommendedAction && (
                <p className="text-sm text-gray-700 mt-2 flex items-start gap-2">
                  <span className="text-lg">👉</span>
                  <span>{recommendedAction}</span>
                </p>
              )}
              {confidenceScore > 0 && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-1.5 max-w-[100px]">
                    <div 
                      className="bg-purple-600 h-1.5 rounded-full" 
                      style={{ width: `${confidenceScore}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">{confidenceScore}% confident</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Alerts from AI */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, i) => (
            <div 
              key={alert.id || i}
              className={`rounded-lg p-3 border flex items-start gap-3 ${
                alert.type === 'urgent' ? 'bg-red-50 border-red-200' :
                alert.type === 'warning' ? 'bg-orange-50 border-orange-200' :
                alert.type === 'success' ? 'bg-green-50 border-green-200' :
                alert.type === 'tip' ? 'bg-blue-50 border-blue-200' :
                'bg-gray-50 border-gray-200'
              }`}
            >
              <span className="text-xl">
                {alert.type === 'urgent' ? '🚨' :
                 alert.type === 'warning' ? '⚠️' :
                 alert.type === 'success' ? '✅' :
                 alert.type === 'tip' ? '💡' : 'ℹ️'}
              </span>
              <div>
                <p className={`font-medium ${
                  alert.type === 'urgent' ? 'text-red-800' :
                  alert.type === 'warning' ? 'text-orange-800' :
                  alert.type === 'success' ? 'text-green-800' :
                  'text-gray-800'
                }`}>{alert.title}</p>
                <p className="text-sm text-gray-600 mt-0.5">{alert.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <QuickAction
          icon={<ArrowUpRight size={20} />}
          label="Add Income"
          onClick={() => setShowIncomeModal(true)}
          color="green"
        />
        <QuickAction
          icon={<ArrowDownRight size={20} />}
          label="Add Expense"
          onClick={() => setShowExpenseModal(true)}
          color="red"
        />
        <QuickAction
          icon={<FileText size={20} />}
          label="Add Bill"
          onClick={() => setShowObligationModal(true)}
          color="orange"
        />
        <QuickAction
          icon={<Zap size={20} />}
          label="Load Demo"
          onClick={handleSeedDemo}
          color="gray"
        />
        <QuickAction
          icon={<Trash2 size={20} />}
          label="Reset All"
          onClick={handleResetData}
          color="red"
        />
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Wallet className="text-primary-600" size={24} />
            </div>
            <span className="text-gray-500 font-medium">Total Balance</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            ₹{totalBalance.toLocaleString()}
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="text-green-600" size={24} />
            </div>
            <span className="text-gray-500 font-medium">Safe to Spend</span>
          </div>
          <div className="text-3xl font-bold text-green-600">
            ₹{safeToSpend.toLocaleString()}
          </div>
          <p className="text-sm text-gray-500 mt-1">After bills & savings</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2 rounded-lg ${
              riskLevel === 'critical' ? 'bg-red-100' : 
              riskLevel === 'high' ? 'bg-orange-100' : 
              riskLevel === 'moderate' ? 'bg-yellow-100' : 'bg-green-100'
            }`}>
              <AlertTriangle className={
                riskLevel === 'critical' ? 'text-red-600' : 
                riskLevel === 'high' ? 'text-orange-600' : 
                riskLevel === 'moderate' ? 'text-yellow-600' : 'text-green-600'
              } size={24} />
            </div>
            <span className="text-gray-500 font-medium">Risk Score</span>
          </div>
          <div className={`text-3xl font-bold ${
            riskLevel === 'critical' ? 'text-red-600' : 
            riskLevel === 'high' ? 'text-orange-600' : 
            riskLevel === 'moderate' ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {riskScore}/100
          </div>
          <p className="text-sm text-gray-500 mt-1 capitalize">
            {riskLevel} risk
          </p>
        </div>
      </div>

      {/* Agent Activity Log */}
      <AgentActivityLog 
        isRunning={isRunningAgents}
        agentActivity={agentActivity || []}
        toolCalls={toolCalls || []}
        agenticMode={agenticMode}
        reactIterations={reactIterations}
        totalToolCalls={totalToolCalls}
        reasoningChain={reasoningChain}
        confidenceScore={confidenceScore}
      />

      {/* Financial Charts Dashboard */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <ChartsDashboard compact />
      </div>

      {/* AI Messages */}
      {(messages.length > 0 || warnings.length > 0) && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap className="text-primary-600" size={20} />
            AI Insights
          </h2>
          <div className="space-y-3">
            {warnings.map((warning, i) => (
              <div key={`w-${i}`} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
                <AlertTriangle className="text-red-500 mt-0.5 flex-shrink-0" size={18} />
                <p className="text-red-700">{warning}</p>
              </div>
            ))}
            {messages.map((message, i) => (
              <div key={`m-${i}`} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                <Zap className="text-blue-500 mt-0.5 flex-shrink-0" size={18} />
                <p className="text-blue-700">{typeof message === 'string' ? message : message.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Buckets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">💰 Your Buckets</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {buckets.map((bucket) => (
            <BucketCard key={bucket.name} bucket={bucket} />
          ))}
          {buckets.length === 0 && (
            <div className="col-span-full text-center py-8 bg-gray-50 rounded-xl">
              <p className="text-gray-500 mb-3">No buckets yet</p>
              <button
                onClick={handleSeedDemo}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm"
              >
                Load Demo Data
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Upcoming Obligations */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Calendar className="text-gray-500" size={20} />
            Upcoming Bills
          </h2>
          <button
            onClick={() => setShowObligationModal(true)}
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
          >
            <Plus size={16} /> Add Bill
          </button>
        </div>
        <div className="space-y-3">
          {upcomingObligations.slice(0, 5).map((obligation) => (
            <ObligationCard 
              key={obligation.id} 
              obligation={obligation}
              onMarkPaid={handleMarkPaid}
            />
          ))}
          {upcomingObligations.length === 0 && (
            <p className="text-gray-500 text-center py-4">No upcoming bills - add your first one!</p>
          )}
        </div>
      </div>

      {/* Demo Scenarios */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-xl border border-purple-200">
        <h3 className="font-semibold text-purple-800 mb-3">🎮 Test Scenarios</h3>
        <p className="text-sm text-purple-600 mb-3">Simulate different situations to see how AI adapts</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleSimulate('normal')}
            className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm border"
          >
            📅 Normal Day
          </button>
          <button
            onClick={() => handleSimulate('rain')}
            className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm border"
          >
            🌧️ Rainy Day
          </button>
          <button
            onClick={() => handleSimulate('festival')}
            className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm border"
          >
            🎉 Festival
          </button>
          <button
            onClick={() => handleSimulate('payday')}
            className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm border"
          >
            💸 Payday
          </button>
        </div>
      </div>

      {/* Modals */}
      <AddIncomeModal
        isOpen={showIncomeModal}
        onClose={() => setShowIncomeModal(false)}
        onSuccess={fetchDashboard}
      />
      <AddExpenseModal
        isOpen={showExpenseModal}
        onClose={() => setShowExpenseModal(false)}
        onSuccess={fetchDashboard}
      />
      <AddObligationModal
        isOpen={showObligationModal}
        onClose={() => setShowObligationModal(false)}
        onSuccess={fetchDashboard}
      />
    </div>
  )
}

export default Dashboard
