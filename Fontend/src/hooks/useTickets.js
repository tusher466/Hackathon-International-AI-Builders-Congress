import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useTickets = (params={}) => {
  return useQuery({
    queryKey: ['tickets', params],
    queryFn: () => api.getTickets(params),
    staleTime: 5000,
  })
}

export const useTicket = (id) => {
  return useQuery({
    queryKey: ['ticket', id],
    queryFn: () => api.getTicket(id),
    enabled: !!id
  })
}
