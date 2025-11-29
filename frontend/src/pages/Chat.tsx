import { useState, useEffect, useRef } from 'react'
import { Send, Trash2, Loader } from 'lucide-react'
import { chatAPI } from '../lib/api'
import toast from 'react-hot-toast'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  message_type?: string
  created_at: string
}

function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadHistory = async () => {
    setIsLoading(true)
    try {
      const response = await chatAPI.getHistory(50)
      setMessages(response.data.messages || [])
    } catch (error) {
      console.error('Failed to load chat history:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSending) return

    const userMessage = input.trim()
    setInput('')
    
    // Optimistically add user message
    const tempUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMsg])
    
    setIsSending(true)
    try {
      const response = await chatAPI.sendMessage(userMessage)
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.message,
        message_type: response.data.message_type,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      toast.error('Failed to send message')
      // Remove optimistic message
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id))
    } finally {
      setIsSending(false)
    }
  }

  const handleQuickAction = async (action: string) => {
    setIsSending(true)
    try {
      const response = await chatAPI.quickAction(action)
      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.data.message,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      toast.error('Action failed')
    } finally {
      setIsSending(false)
    }
  }

  const clearHistory = async () => {
    if (!confirm('Clear all chat history?')) return
    try {
      await chatAPI.clearHistory()
      setMessages([])
      toast.success('Chat history cleared')
    } catch (error) {
      toast.error('Failed to clear history')
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] lg:h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">💬 Chat with Guru</h1>
          <p className="text-gray-600">Ask me anything about your finances!</p>
        </div>
        <button
          onClick={clearHistory}
          className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          title="Clear chat history"
        >
          <Trash2 size={20} />
        </button>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        <button
          onClick={() => handleQuickAction('check_status')}
          disabled={isSending}
          className="px-4 py-2 bg-primary-50 text-primary-700 rounded-full whitespace-nowrap hover:bg-primary-100 transition-colors disabled:opacity-50"
        >
          📊 Check Status
        </button>
        <button
          onClick={() => handleQuickAction('get_advice')}
          disabled={isSending}
          className="px-4 py-2 bg-blue-50 text-blue-700 rounded-full whitespace-nowrap hover:bg-blue-100 transition-colors disabled:opacity-50"
        >
          💡 Get Advice
        </button>
        <button
          onClick={() => handleQuickAction('check_advance')}
          disabled={isSending}
          className="px-4 py-2 bg-purple-50 text-purple-700 rounded-full whitespace-nowrap hover:bg-purple-100 transition-colors disabled:opacity-50"
        >
          💸 Check Advance
        </button>
        <button
          onClick={() => handleQuickAction('view_goals')}
          disabled={isSending}
          className="px-4 py-2 bg-orange-50 text-orange-700 rounded-full whitespace-nowrap hover:bg-orange-100 transition-colors disabled:opacity-50"
        >
          🎯 View Goals
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 rounded-xl p-4 space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader className="animate-spin text-primary-600" size={32} />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <p className="text-4xl mb-4">👋</p>
              <p className="font-medium">Namaste! I'm GigMoney Guru</p>
              <p className="text-sm mt-2">Ask me about budgeting, savings, or anything money-related!</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white rounded-br-none'
                      : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-500 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="mt-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message... (Hindi/English both work!)"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            disabled={isSending}
          />
          <button
            type="submit"
            disabled={!input.trim() || isSending}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  )
}

export default Chat
