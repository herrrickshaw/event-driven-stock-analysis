import { configureStore } from '@reduxjs/toolkit'
import dashboardReducer from './slices/dashboardSlice'

export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['dashboard/updatePerformance'],
        ignoredPaths: ['dashboard.last_updated'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
