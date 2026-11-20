import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useApprovals = () => {
  return useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: () => api.getPendingApprovals(),
    staleTime: 5000,
  })
}

export const useApprove = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ alertId, body }) => api.approve(alertId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals'] })
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['tickets'] })
      qc.invalidateQueries({ queryKey: ['audit'] })
    }
  })
}

export const useReject = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ alertId, body }) => api.reject(alertId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals'] })
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['tickets'] })
      qc.invalidateQueries({ queryKey: ['audit'] })
    }
  })
}
