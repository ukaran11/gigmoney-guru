import { create } from 'zustand'
import { stateAPI, agentAPI, demoAPI } from '../lib/api'

interface Bucket {
  name: string
  display_name: string
  icon: string
  color: string
  current_balance: number
  target_amount: number
  allocation_percent: number
}

interface Obligation {
  id: string
  name: string
  amount: number
  due_date: string
  days_until_due: number
  is_critical: boolean
}

interface IncomeEvent {
  source: string
  amount: number
  time: string
}

interface Message {
  content: string
  message_type: string
  quick_replies?: string[]
  priority?: string
}

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
}

interface ToolCall {
  tool: string
  arguments: any
  timestamp: string
  sequence?: number
}

interface Alert {
  id: string
  type: 'urgent' | 'warning' | 'info' | 'success' | 'tip'
  title: string
  message: string
  action_url?: string
  created_at: string
  expires_at: string
  read: boolean
}

interface DecisionMade {
  type: string
  value: string
  reasoning: string
  impact?: number
  timestamp: string
  persisted?: boolean
}

interface BucketChange {
  bucket: string
  change: number
  new_balance: number
  reason: string
  persisted: boolean
  timestamp: string
}

interface DashboardState {
  // Data
  totalBalance: number
  safeToSpend: number
  riskScore: number
  riskLevel: string
  keyInsight: string
  recommendedAction: string
  confidenceScore: number
  buckets: Bucket[]
  upcomingObligations: Obligation[]
  todayIncome: IncomeEvent[]
  messages: Message[]
  warnings: string[]
  forecastImage: string | null
  
  // Agentic data
  agentActivity: AgentActivity[]
  toolCalls: ToolCall[]
  agenticMode: string
  reactIterations: number
  totalToolCalls: number
  routingDecision: any
  reasoningChain: Array<{ iteration: number; thought: string }>
  alerts: Alert[]
  decisionsMade: DecisionMade[]
  bucketChanges: BucketChange[]
  
  // Loading states
  isLoading: boolean
  isRunningAgents: boolean
  error: string | null
  
  // Actions
  fetchDashboard: () => Promise<void>
  runDailyAgents: (mode?: string) => Promise<any>
  seedDemoData: () => Promise<void>
  simulateDay: (scenario: string) => Promise<void>
  resetData: () => Promise<void>
}

export const useDashboardStore = create<DashboardState>()((set, get) => ({
  // Initial state
  totalBalance: 0,
  safeToSpend: 0,
  riskScore: 0,
  riskLevel: 'unknown',
  keyInsight: '',
  recommendedAction: '',
  confidenceScore: 0,
  buckets: [],
  upcomingObligations: [],
  todayIncome: [],
  messages: [],
  warnings: [],
  forecastImage: null,
  
  // Agentic data
  agentActivity: [],
  toolCalls: [],
  agenticMode: 'react',
  reactIterations: 0,
  totalToolCalls: 0,
  routingDecision: null,
  reasoningChain: [],
  alerts: [],
  decisionsMade: [],
  bucketChanges: [],
  
  isLoading: false,
  isRunningAgents: false,
  error: null,

  fetchDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await stateAPI.getToday()
      const data = response.data
      
      // Keep existing agentic data (from agent run), only update dashboard data
      set({
        totalBalance: data.total_balance || 0,
        safeToSpend: data.safe_to_spend || 0,
        riskScore: data.risk_score || 0,
        buckets: data.buckets || [],
        upcomingObligations: data.upcoming_obligations || [],
        todayIncome: data.today_income || [],
        // Warnings from state API are strings
        warnings: data.warnings || [],
        isLoading: false,
      })
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to load dashboard',
        isLoading: false 
      })
    }
  },

  runDailyAgents: async (mode = 'react') => {
    set({ 
      isRunningAgents: true, 
      error: null, 
      agentActivity: [],
      toolCalls: [],
      agenticMode: mode,
      reasoningChain: [],
      alerts: [],
      decisionsMade: [],
      bucketChanges: [],
    })
    
    try {
      const response = await agentAPI.runDaily(mode)
      const data = response.data
      
      // Update state with agentic data
      set({
        // Agentic info
        agentActivity: data.agent_activity || [],
        toolCalls: data.tool_calls_log || [],
        agenticMode: data.agentic_mode || mode,
        reactIterations: data.react_iterations || 0,
        totalToolCalls: data.total_tool_calls || (data.tool_calls_log?.length || 0),
        routingDecision: data.routing_decision || null,
        reasoningChain: data.reasoning_chain || [],
        
        // Key insights from agent
        safeToSpend: data.safe_to_spend || 0,
        keyInsight: data.key_insight || '',
        recommendedAction: data.recommended_action || '',
        confidenceScore: data.confidence_score || 0,
        riskScore: data.risk_score || 0,
        riskLevel: data.risk_level || 'unknown',
        
        // Messages, alerts, and decisions from agent
        messages: data.messages || [],
        warnings: data.warnings || [],
        alerts: data.alerts || [],
        decisionsMade: data.decisions_made || [],
        bucketChanges: data.bucket_changes || [],
        
        isRunningAgents: false,
      })
      
      // Refresh dashboard to get updated bucket balances
      await get().fetchDashboard()
      
      return data
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to run agents',
        isRunningAgents: false 
      })
      return null
    }
  },

  seedDemoData: async () => {
    set({ isLoading: true, error: null })
    try {
      await demoAPI.seedRavi()
      await get().fetchDashboard()
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to seed demo data',
        isLoading: false 
      })
    }
  },

  simulateDay: async (scenario: string) => {
    set({ isLoading: true, error: null })
    try {
      await demoAPI.simulateDay(scenario)
      await get().fetchDashboard()
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to simulate day',
        isLoading: false 
      })
    }
  },

  resetData: async () => {
    set({ isLoading: true, error: null })
    try {
      await demoAPI.reset()
      set({
        totalBalance: 0,
        safeToSpend: 0,
        riskScore: 0,
        riskLevel: 'unknown',
        keyInsight: '',
        recommendedAction: '',
        buckets: [],
        upcomingObligations: [],
        todayIncome: [],
        messages: [],
        warnings: [],
        agentActivity: [],
        toolCalls: [],
        agenticMode: 'react',
        reactIterations: 0,
        routingDecision: null,
        isLoading: false,
      })
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to reset data',
        isLoading: false 
      })
    }
  },
}))
