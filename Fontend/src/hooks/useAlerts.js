import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useAlerts = (params={}) => {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => api.getAlerts(params),
    staleTime: 5000,
  })
}

export const useAlert = (id) => {
  return useQuery({
    queryKey: ['alert', id],
    queryFn: () => api.getAlert(id),
    enabled: !!id,
  })
}
