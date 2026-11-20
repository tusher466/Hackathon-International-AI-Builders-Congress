import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useAuditLog = (params={}) => {
  return useQuery({
    queryKey: ['audit', params],
    queryFn: () => api.getAuditLog(params),
    staleTime: 5000,
  })
}
