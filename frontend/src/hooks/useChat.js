import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useChat = () => {
  const [history, setHistory] = useState([])
  const mutation = useMutation({
    mutationFn: (body) => api.chat(body),
    onSuccess: (data, variables) => {
      setHistory(h => [...h, { role: 'user', content: variables.question }, { role: 'assistant', ...data }])
    }
  })

  const send = (question) => {
    if (!question.trim()) return
    mutation.mutate({ question, history: history.slice(-6) })
  }

  return { history, send, isLoading: mutation.isPending, error: mutation.error, setHistory }
}
