import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useOee = () => {
  return useQuery({
    queryKey: ['oee'],
    queryFn: () => api.getOee(),
    staleTime: 10000,
  })
}
