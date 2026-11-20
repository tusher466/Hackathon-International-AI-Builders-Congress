import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useBottlenecks = () => {
  return useQuery({
    queryKey: ['bottlenecks'],
    queryFn: () => api.getBottlenecks(),
    staleTime: 10000,
  })
}
