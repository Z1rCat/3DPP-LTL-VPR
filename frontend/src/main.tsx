import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import App from './App.tsx'
import './styles/index.css'

// 设置dayjs中文语言
dayjs.locale('zh-cn')

// 创建React Query客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5分钟
      gcTime: 10 * 60 * 1000, // 10分钟
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

// Ant Design主题配置
const antdTheme = {
  token: {
    colorPrimary: '#1890ff', // 主色调 - 科技蓝
    colorSuccess: '#52c41a', // 成功绿
    colorWarning: '#faad14', // 警告橙
    colorError: '#f5222d',   // 错误红
    colorInfo: '#1890ff',    // 信息蓝
    borderRadius: 8,
    wireframe: false,
    fontFamily: 'Inter, PingFang SC, Microsoft YaHei, sans-serif',
    fontSize: 14,
    fontSizeHeading1: 32,
    fontSizeHeading2: 24,
    fontSizeHeading3: 18,
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
    },
    Card: {
      borderRadius: 12,
      paddingLG: 24,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Select: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Table: {
      borderRadius: 8,
      headerBg: '#fafafa',
    },
    Modal: {
      borderRadius: 12,
    },
    Tabs: {
      borderRadius: 8,
    },
  },
  algorithm: undefined, // 使用默认算法
}

// 隐藏加载动画
const hideLoading = () => {
  const loading = document.getElementById('loading')
  if (loading) {
    document.body.classList.add('loaded')
    setTimeout(() => {
      loading.remove()
    }, 300)
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={antdTheme}
      >
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)

// 页面加载完成后隐藏加载动画
window.addEventListener('load', hideLoading)

// 如果页面已经加载完成，立即隐藏加载动画
if (document.readyState === 'complete') {
  hideLoading()
}