import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// 型定義
interface ExampleState {
  // State
  count: number
  user: {
    id: string
    name: string
  } | null
  isLoading: boolean

  // Actions
  increment: () => void
  decrement: () => void
  setUser: (user: { id: string; name: string }) => void
  clearUser: () => void
  setLoading: (loading: boolean) => void
  reset: () => void
}

// 初期状態
const initialState = {
  count: 0,
  user: null,
  isLoading: false,
}

// ストアの作成
export const useExampleStore = create<ExampleState>()(
  devtools(
    persist(
      immer((set) => ({
        // 初期状態
        ...initialState,

        // アクション
        increment: () =>
          set((state) => {
            state.count++
          }),

        decrement: () =>
          set((state) => {
            state.count--
          }),

        setUser: (user) =>
          set((state) => {
            state.user = user
          }),

        clearUser: () =>
          set((state) => {
            state.user = null
          }),

        setLoading: (loading) =>
          set((state) => {
            state.isLoading = loading
          }),

        reset: () => set(initialState),
      })),
      {
        name: 'example-store', // localStorage key
        partialize: (state) => ({ // 永続化するプロパティを選択
          count: state.count,
          user: state.user,
        }),
      }
    ),
    {
      name: 'ExampleStore', // Redux DevTools用の名前
    }
  )
)

// セレクター（オプション）
export const selectCount = (state: ExampleState) => state.count
export const selectUser = (state: ExampleState) => state.user
export const selectIsLoading = (state: ExampleState) => state.isLoading