import { useState } from 'react'
import { Bot, TrendingUp, AlertTriangle, PiggyBank, CreditCard, Target, MessageSquare, ChevronDown, ChevronUp, Brain, Wrench, Route, Lightbulb, History } from 'lucide-react'

interface AgentActivity {
  agent: string
  status: 'running' | 'completed' | 'error'
  message: string
  tools_called?: number
  tools_used?: string[]
  iterations?: number
  reasoning?: string
  reasoning_chain?: Array<{ iteration: number; thought: string }>
  urgency?: string
  timestamp: string
  // Enhanced mode fields
  features?: string[]
  reflections_count?: number
  plan_revisions?: number
  debate_held?: boolean
  debate_confidence?: number
  advisors_consulted?: string[]
  learnings_applied?: boolean
}

interface ToolCall {
  tool: string
  arguments: any
  timestamp: string
  sequence?: number
}

interface ReasoningStep {
  iteration: number
  thought: string
}

interface AgentActivityLogProps {
  agentActivity?: AgentActivity[]
  toolCalls?: ToolCall[]
  agenticMode?: string
  reactIterations?: number
  totalToolCalls?: number
  reasoningChain?: ReasoningStep[]
  confidenceScore?: number
  isRunning?: boolean
}

const AGENT_INFO: Record<string, { icon: React.ReactNode; color: string; name: string }> = {
  // Enhanced agentic agent
  EnhancedReActAgent: { icon: <Brain size={16} />, color: 'bg-gradient-to-r from-purple-600 to-pink-600', name: 'Enhanced AI (Plan+Reflect+Debate+Learn)' },
  
  // New agentic agents
  ReActAgent: { icon: <Brain size={16} />, color: 'bg-purple-600', name: 'ReAct Agent' },
  AgentRouter: { icon: <Route size={16} />, color: 'bg-blue-600', name: 'Agent Router' },
  
  // Specialist agents
  INCOME_ANALYZER: { icon: <TrendingUp size={16} />, color: 'bg-green-500', name: 'Income Analyzer' },
  EXPENSE_ANALYZER: { icon: <TrendingUp size={16} />, color: 'bg-red-500', name: 'Expense Analyzer' },
  OBLIGATION_RISK_ANALYZER: { icon: <AlertTriangle size={16} />, color: 'bg-orange-500', name: 'Risk Detector' },
  RISK_CALCULATOR: { icon: <AlertTriangle size={16} />, color: 'bg-red-600', name: 'Risk Calculator' },
  CASHFLOW_FORECASTER: { icon: <TrendingUp size={16} />, color: 'bg-blue-500', name: 'Cashflow Planner' },
  BUCKET_ALLOCATOR: { icon: <PiggyBank size={16} />, color: 'bg-purple-500', name: 'Smart Allocator' },
  ADVANCE_EVALUATOR: { icon: <CreditCard size={16} />, color: 'bg-yellow-500', name: 'Advance Advisor' },
  GOAL_TRACKER: { icon: <Target size={16} />, color: 'bg-pink-500', name: 'Goal Tracker' },
  
  // Legacy agents
  income_pattern: { icon: <TrendingUp size={16} />, color: 'bg-green-500', name: 'Income Analyzer' },
  expense_analyzer: { icon: <TrendingUp size={16} />, color: 'bg-red-500', name: 'Expense Analyzer' },
  obligation_risk: { icon: <AlertTriangle size={16} />, color: 'bg-orange-500', name: 'Risk Detector' },
  risk_calculator: { icon: <AlertTriangle size={16} />, color: 'bg-red-600', name: 'Risk Calculator' },
  cashflow_planner: { icon: <TrendingUp size={16} />, color: 'bg-blue-500', name: 'Cashflow Planner' },
  bucket_allocation: { icon: <PiggyBank size={16} />, color: 'bg-purple-500', name: 'Smart Allocator' },
  smart_allocator: { icon: <PiggyBank size={16} />, color: 'bg-purple-600', name: 'Smart Allocator' },
  micro_advance: { icon: <CreditCard size={16} />, color: 'bg-yellow-500', name: 'Advance Advisor' },
  goal_scenario: { icon: <Target size={16} />, color: 'bg-pink-500', name: 'Goal Tracker' },
  conversation: { icon: <MessageSquare size={16} />, color: 'bg-indigo-500', name: 'Message Generator' },
  explainability: { icon: <Bot size={16} />, color: 'bg-gray-500', name: 'Explainer' },
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  get_bucket_balances: <PiggyBank size={14} />,
  get_upcoming_obligations: <AlertTriangle size={14} />,
  get_income_history: <TrendingUp size={14} />,
  get_expense_history: <TrendingUp size={14} />,
  allocate_to_bucket: <PiggyBank size={14} />,
  calculate_shortfall: <AlertTriangle size={14} />,
  suggest_advance: <CreditCard size={14} />,
  get_goals_progress: <Target size={14} />,
  send_message_to_user: <MessageSquare size={14} />,
  set_risk_score: <AlertTriangle size={14} />,
  complete_analysis: <Bot size={14} />,
  // New agentic tools
  get_past_decisions: <History size={14} />,
  save_decision: <History size={14} />,
  create_alert: <AlertTriangle size={14} />,
  analyze_spending_pattern: <TrendingUp size={14} />,
  calculate_goal_trajectory: <Target size={14} />,
  simulate_scenario: <Lightbulb size={14} />,
  update_bucket_balance_persistent: <PiggyBank size={14} />,
}

export default function AgentActivityLog({ 
  agentActivity = [], 
  toolCalls = [],
  agenticMode = 'react',
  reactIterations = 0,
  totalToolCalls = 0,
  reasoningChain = [],
  confidenceScore = 0,
  isRunning = false 
}: AgentActivityLogProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [showTools, setShowTools] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)

  const effectiveToolCalls = totalToolCalls || toolCalls.length

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg ${isRunning ? 'bg-purple-100 animate-pulse' : 'bg-gray-100'}`}>
            <Brain className={isRunning ? 'text-purple-600' : 'text-gray-600'} size={20} />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">AI Agent Activity</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                agenticMode === 'enhanced' ? 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700' :
                agenticMode === 'react' ? 'bg-purple-100 text-purple-700' : 
                agenticMode === 'routed' ? 'bg-blue-100 text-blue-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {agenticMode === 'enhanced' ? '🚀 Enhanced Mode' :
                 agenticMode === 'react' ? '🧠 ReAct Mode' : 
                 agenticMode === 'routed' ? '🔀 Routed Mode' : 
                 '⚡ Fast Mode'}
              </span>
            </div>
            <p className="text-sm text-gray-500">
              {isRunning ? 'AI is reasoning and taking actions...' : 
               agentActivity.length > 0 ? `${reactIterations || agentActivity.length} reasoning cycles, ${effectiveToolCalls} tools called${confidenceScore > 0 ? ` • ${confidenceScore}% confident` : ''}` : 
               'Run AI to see agent activity'}
            </p>
          </div>
        </div>
        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4">
          {/* Agent Activity Timeline */}
          {agentActivity.length > 0 ? (
            <div className="space-y-2 mb-4">
              {/* Deduplicate: show only latest status per agent */}
              {(() => {
                // Get the latest activity for each agent
                const latestByAgent = new Map<string, typeof agentActivity[0]>()
                for (const activity of agentActivity) {
                  const existing = latestByAgent.get(activity.agent)
                  // Keep the completed/error status over running
                  if (!existing || activity.status !== 'running' || existing.status === 'running') {
                    latestByAgent.set(activity.agent, activity)
                  }
                }
                return Array.from(latestByAgent.values())
              })().map((activity, i) => {
                const info = AGENT_INFO[activity.agent] || { icon: <Bot size={16} />, color: 'bg-gray-500', name: activity.agent }
                
                // If not running anymore (API complete), don't show pulse animation
                const showPulse = isRunning && activity.status === 'running'
                
                return (
                  <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${
                    showPulse ? 'bg-purple-50 animate-pulse' :
                    activity.status === 'error' ? 'bg-red-50' :
                    activity.status === 'completed' ? 'bg-green-50' :
                    'bg-gray-50'
                  }`}>
                    <div className={`p-1.5 rounded-lg ${info.color} text-white flex-shrink-0`}>
                      {info.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-gray-900">{info.name}</span>
                        {activity.status === 'completed' && (
                          <span className="text-xs text-green-600">✓ Complete</span>
                        )}
                        {activity.status === 'running' && !isRunning && (
                          <span className="text-xs text-green-600">✓ Complete</span>
                        )}
                        {activity.status === 'running' && isRunning && (
                          <span className="text-xs text-purple-600">Running...</span>
                        )}
                        {activity.status === 'error' && (
                          <span className="text-xs text-red-600">Error</span>
                        )}
                        {activity.tools_called && (
                          <span className="text-xs text-gray-400 flex items-center gap-1">
                            <Wrench size={12} /> {activity.tools_called} tools
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-0.5">{activity.message}</p>
                      {activity.reasoning && (
                        <p className="text-xs text-gray-500 mt-1 italic">"{activity.reasoning}"</p>
                      )}
                      {activity.urgency && (
                        <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full ${
                          activity.urgency === 'critical' ? 'bg-red-100 text-red-700' :
                          activity.urgency === 'high' ? 'bg-orange-100 text-orange-700' :
                          activity.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          Urgency: {activity.urgency}
                        </span>
                      )}
                      {/* Enhanced Mode Features */}
                      {activity.features && activity.features.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {activity.features.map((feature, idx) => (
                            <span key={idx} className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                              {feature === 'planning' ? '📋 Planning' :
                               feature === 'self-reflection' ? '🪞 Reflection' :
                               feature === 'debate' ? '🗣️ Debate' :
                               feature === 'learning' ? '📚 Learning' : feature}
                            </span>
                          ))}
                        </div>
                      )}
                      {activity.reflections_count != null && activity.reflections_count > 0 && (
                        <span className="inline-block mt-1 mr-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                          🪞 {activity.reflections_count} reflections
                        </span>
                      )}
                      {activity.plan_revisions != null && activity.plan_revisions > 0 && (
                        <span className="inline-block mt-1 mr-2 text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full">
                          📋 {activity.plan_revisions} plan revisions
                        </span>
                      )}
                      {activity.debate_held && (
                        <div className="mt-2 p-2 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg">
                          <div className="flex items-center gap-2 text-xs">
                            <span className="font-medium text-purple-700">🗣️ Debate held</span>
                            {activity.debate_confidence && (
                              <span className="text-gray-600">({Math.round(activity.debate_confidence * 100)}% consensus)</span>
                            )}
                          </div>
                          {activity.advisors_consulted && activity.advisors_consulted.length > 0 && (
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {activity.advisors_consulted.map((advisor, idx) => (
                                <span key={idx} className="text-[10px] px-1.5 py-0.5 bg-white text-gray-600 rounded">
                                  {advisor}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                      {activity.learnings_applied && (
                        <span className="inline-block mt-1 text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                          📚 Past learnings applied
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : !isRunning ? (
            <div className="text-center py-6 text-gray-400">
              <Brain size={32} className="mx-auto mb-2" />
              <p className="text-sm">Click "Run AI" to see autonomous agent activity</p>
              <p className="text-xs mt-1">ReAct pattern: Think → Act → Observe → Repeat</p>
            </div>
          ) : null}

          {/* Tool Calls Section */}
          {toolCalls.length > 0 && (
            <div className="border-t pt-3">
              <button
                onClick={() => setShowTools(!showTools)}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
              >
                <Wrench size={16} />
                <span>{effectiveToolCalls} Tool Calls</span>
                <span className="text-xs text-gray-400">
                  (click to {showTools ? 'hide' : 'see'} details)
                </span>
                {showTools ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              
              {showTools && (
                <div className="mt-2 space-y-1 max-h-60 overflow-y-auto">
                  {toolCalls.map((call, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs p-2 bg-gray-100 rounded">
                      <span className="text-gray-600 mt-0.5">
                        {TOOL_ICONS[call.tool] || <Wrench size={14} />}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-gray-800 font-medium">{call.tool}</span>
                          {call.sequence && (
                            <span className="text-gray-400">#{call.sequence}</span>
                          )}
                        </div>
                        {Object.keys(call.arguments || {}).length > 0 && (
                          <pre className="text-gray-500 mt-0.5 text-[10px] bg-gray-50 p-1 rounded overflow-x-auto">
                            {JSON.stringify(call.arguments, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Reasoning Chain Section */}
          {reasoningChain.length > 0 && (
            <div className="border-t pt-3">
              <button
                onClick={() => setShowReasoning(!showReasoning)}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
              >
                <Lightbulb size={16} />
                <span>{reasoningChain.length} Reasoning Steps</span>
                {showReasoning ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              
              {showReasoning && (
                <div className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                  {reasoningChain.map((step, i) => (
                    <div key={i} className="p-2 bg-purple-50 rounded text-xs">
                      <span className="text-purple-600 font-medium">Cycle {step.iteration}:</span>
                      <p className="text-gray-700 mt-1 italic">"{step.thought}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
