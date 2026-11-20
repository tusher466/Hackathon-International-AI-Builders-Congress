import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useMachines = () => {
  return useQuery({
    queryKey: ['machines'],
    queryFn: () => api.getMachines(),
    staleTime: 10000,
  })
}

export const useMachine = (id) => {
  return useQuery({
    queryKey: ['machine', id],
    queryFn: () => api.getMachine(id),
    enabled: !!id,
  })
}

export const useMachineReadings = (id, limit=100) => {
  return useQuery({
    queryKey: ['readings', id, limit],
    queryFn: () => api.getReadings(id, limit),
    enabled: !!id,
    staleTime: 5000,
  })
}
