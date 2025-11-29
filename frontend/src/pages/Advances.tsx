import { useState, useEffect } from 'react'
import { CreditCard, Clock, CheckCircle } from 'lucide-react'
import { advancesAPI } from '../lib/api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

interface Advance {
  id: string
  amount: number
  fee: number
  total_repayment: number
  status: string
  reason: string | null
  due_date: string | null
  approved_at: string | null
  repaid_at: string | null
  created_at: string
}

interface AdvanceStats {
  total_advances_taken: number
  total_amount_taken: number
  total_fees_paid: number
  currently_outstanding: number
  total_repaid: number
  on_time_repayment_rate: number
}

function Advances() {
  const [advances, setAdvances] = useState<Advance[]>([])
  const [stats, setStats] = useState<AdvanceStats | null>(null)
  const [available, setAvailable] = useState<{ max_advance_amount: number; can_request: boolean; reason?: string } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showRequestModal, setShowRequestModal] = useState(false)
  const [requestAmount, setRequestAmount] = useState('')
  const [requestReason, setRequestReason] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [advancesRes, statsRes, availableRes] = await Promise.all([
        advancesAPI.list(),
        advancesAPI.getStats(),
        advancesAPI.getAvailable(),
      ])
      setAdvances(advancesRes.data.advances || [])
      setStats(statsRes.data)
      setAvailable(availableRes.data)
    } catch (error) {
      toast.error('Failed to load advances data')
    } finally {
      setIsLoading(false)
    }
  }

  const requestAdvance = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await advancesAPI.request(
        parseFloat(requestAmount),
        requestReason || undefined
      )
      toast.success(response.data.message)
      setShowRequestModal(false)
      setRequestAmount('')
      setRequestReason('')
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Request failed')
    }
  }

  const repayAdvance = async (advanceId: string) => {
    try {
      const response = await advancesAPI.repay(advanceId)
      toast.success(response.data.message)
      loadData()
    } catch (error) {
      toast.error('Failed to mark as repaid')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">💸 Micro-Advances</h1>
          <p className="text-gray-600">Small advances to tide you over</p>
        </div>
        {available?.can_request && (
          <button
            onClick={() => setShowRequestModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <CreditCard size={20} />
            Request Advance
          </button>
        )}
      </div>

      {/* Available Advance Card */}
      <div className={`rounded-xl p-6 ${available?.can_request ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white' : 'bg-gray-100'}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className={`text-lg font-medium ${available?.can_request ? 'text-white/80' : 'text-gray-600'}`}>
              Available Advance
            </h2>
            <p className={`text-3xl font-bold ${available?.can_request ? 'text-white' : 'text-gray-900'}`}>
              ₹{available?.max_advance_amount?.toLocaleString() || 0}
            </p>
            {!available?.can_request && available?.reason && (
              <p className="text-sm text-gray-500 mt-2">{available.reason}</p>
            )}
          </div>
          {available?.can_request && (
            <div className="text-right">
              <p className="text-white/80 text-sm">Fee: Just 1%</p>
              <p className="text-white/60 text-xs">Repay within 3 days</p>
            </div>
          )}
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Total Advances</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_advances_taken}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Total Borrowed</p>
            <p className="text-2xl font-bold text-gray-900">₹{stats.total_amount_taken.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Outstanding</p>
            <p className="text-2xl font-bold text-orange-600">₹{stats.currently_outstanding.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">On-time Rate</p>
            <p className="text-2xl font-bold text-green-600">{stats.on_time_repayment_rate.toFixed(0)}%</p>
          </div>
        </div>
      )}

      {/* Advances List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Advance History</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {advances.map((advance) => (
            <div key={advance.id} className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${
                  advance.status === 'repaid' ? 'bg-green-100' : 
                  advance.status === 'approved' ? 'bg-orange-100' : 'bg-gray-100'
                }`}>
                  {advance.status === 'repaid' ? (
                    <CheckCircle className="text-green-600" size={20} />
                  ) : (
                    <Clock className="text-orange-600" size={20} />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900">₹{advance.amount.toLocaleString()}</p>
                  <p className="text-sm text-gray-500">
                    {advance.approved_at && format(new Date(advance.approved_at), 'MMM d, yyyy')}
                    {advance.status === 'approved' && advance.due_date && (
                      <span className="text-orange-600 ml-2">
                        Due: {format(new Date(advance.due_date), 'MMM d')}
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                  advance.status === 'repaid' ? 'bg-green-100 text-green-700' :
                  advance.status === 'approved' ? 'bg-orange-100 text-orange-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {advance.status}
                </span>
                {advance.status === 'approved' && (
                  <button
                    onClick={() => repayAdvance(advance.id)}
                    className="block mt-2 text-sm text-primary-600 hover:text-primary-700"
                  >
                    Mark as Repaid
                  </button>
                )}
              </div>
            </div>
          ))}
          {advances.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              <CreditCard className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p>No advances yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Request Modal */}
      {showRequestModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md animate-slide-up">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Request Advance</h2>
            
            <form onSubmit={requestAdvance} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  value={requestAmount}
                  onChange={(e) => setRequestAmount(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="1000"
                  min="100"
                  max={available?.max_advance_amount || 5000}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Max: ₹{available?.max_advance_amount?.toLocaleString()} | Fee: ₹{(parseFloat(requestAmount || '0') * 0.01).toFixed(0)}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason (Optional)</label>
                <input
                  type="text"
                  value={requestReason}
                  onChange={(e) => setRequestReason(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., Fuel for tomorrow"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRequestModal(false)}
                  className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Advances
