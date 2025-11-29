import { useState } from 'react'
import { X, Plus, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface AddIncomeModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const PLATFORMS = [
  { id: 'uber', name: 'Uber', icon: '🚗' },
  { id: 'ola', name: 'Ola', icon: '🚕' },
  { id: 'swiggy', name: 'Swiggy', icon: '🍔' },
  { id: 'zomato', name: 'Zomato', icon: '🍕' },
  { id: 'zepto', name: 'Zepto', icon: '📦' },
  { id: 'blinkit', name: 'Blinkit', icon: '🛒' },
  { id: 'rapido', name: 'Rapido', icon: '🏍️' },
  { id: 'dunzo', name: 'Dunzo', icon: '📬' },
  { id: 'freelance', name: 'Freelance', icon: '💼' },
  { id: 'other', name: 'Other', icon: '💰' },
]

export default function AddIncomeModal({ isOpen, onClose, onSuccess }: AddIncomeModalProps) {
  const [platform, setPlatform] = useState('')
  const [amount, setAmount] = useState('')
  const [notes, setNotes] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!platform || !amount) {
      toast.error('Please select platform and enter amount')
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/income/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          source_name: platform,
          amount: parseFloat(amount),
          notes: notes || undefined,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to add income')
      }

      const data = await response.json()
      toast.success(`₹${amount} added! ${data.allocation_summary || ''}`)
      
      // Reset form
      setPlatform('')
      setAmount('')
      setNotes('')
      onSuccess()
      onClose()
    } catch (error) {
      toast.error('Failed to add income')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Add Earnings 💰</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Platform / Source
            </label>
            <div className="grid grid-cols-5 gap-2">
              {PLATFORMS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setPlatform(p.name)}
                  className={`flex flex-col items-center p-2 rounded-lg border-2 transition-all ${
                    platform === p.name
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xl">{p.icon}</span>
                  <span className="text-xs mt-1 text-gray-600">{p.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount (₹)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0"
                className="w-full pl-8 pr-4 py-3 text-2xl font-bold border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            {/* Quick amounts */}
            <div className="flex gap-2 mt-2">
              {[100, 250, 500, 1000].map((amt) => (
                <button
                  key={amt}
                  type="button"
                  onClick={() => setAmount(amt.toString())}
                  className="px-3 py-1 text-sm bg-gray-100 rounded-full hover:bg-gray-200"
                >
                  ₹{amt}
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes (optional)
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Airport trip, Late night bonus"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* AI Info */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm text-blue-700">
              🤖 <strong>AI will automatically:</strong> Allocate this to your buckets based on priorities and upcoming obligations.
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !platform || !amount}
            className="w-full py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus size={20} />
                Add ₹{amount || '0'}
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
