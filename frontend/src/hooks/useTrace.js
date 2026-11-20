import { useQuery } from '@tanstack/react-query'
import { api } from '../api/endpoints'

export const useTrace = (alertId) => {
  return useQuery({
    queryKey: ['trace', alertId],
    queryFn: () => api.getTrace(alertId),
    enabled: !!alertId,
  })
}
