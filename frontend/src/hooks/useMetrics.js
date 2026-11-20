import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useImpact = () => {
  return useQuery({
    queryKey: ['impact'],
    queryFn: () => api.getImpact(),
    staleTime: 10000,
  })
}

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    staleTime: 5000,
    refetchInterval: 10000,
  })
}
