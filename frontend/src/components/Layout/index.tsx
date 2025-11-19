import React, { useState } from 'react'
import { Layout, Menu, Button, Avatar, Dropdown, Badge, Space, Typography } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  CarOutlined,
  UploadOutlined,
  BarChartOutlined,
  SettingOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CubeOutlined,
  ShareAltOutlined
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout
const { Text } = Typography

export interface AppLayoutProps {
  children: React.ReactNode
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  // 菜单配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/import',
      icon: <UploadOutlined />,
      label: '数据导入',
    },
    {
      key: '/optimization',
      icon: <CubeOutlined />,
      label: '优化执行',
    },
    {
      key: '/vehicles',
      icon: <CarOutlined />,
      label: '车辆管理',
    },
    {
      key: '/visualization',
      icon: <BarChartOutlined />,
      label: '可视化',
    },
  ]

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        // 跳转到个人资料页面
        break
      case 'settings':
        // 跳转到设置页面
        break
      case 'logout':
        // 处理退出登录
        localStorage.removeItem('auth_token')
        navigate('/login')
        break
    }
  }

  // 处理通知点击
  const handleNotificationClick = () => {
    // 显示通知面板
  }

  return (
    <Layout className="min-h-screen">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        className="bg-white shadow-lg border-r border-gray-100"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        {/* Logo区域 */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              巧
            </div>
            {!collapsed && (
              <div className="ml-3">
                <div className="font-semibold text-gray-900">巧满装载</div>
                <div className="text-xs text-gray-500">智能物流优化</div>
              </div>
            )}
          </div>
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="border-r-0"
          style={{ background: 'transparent' }}
        />
      </Sider>

      {/* 主内容区域 */}
      <Layout style={{ marginLeft: collapsed ? 80 : 240 }}>
        {/* 顶部导航栏 */}
        <Header className="bg-white shadow-sm border-b border-gray-100 px-6 flex items-center justify-between sticky top-0 z-50">
          <div className="flex items-center">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-lg hover:bg-gray-100"
            />
          </div>

          <div className="flex items-center space-x-4">
            {/* 通知按钮 */}
            <Button
              type="text"
              icon={<BellOutlined />}
              onClick={handleNotificationClick}
              className="text-lg hover:bg-gray-100 relative"
            >
              <Badge
                count={3}
                size="small"
                className="absolute -top-1 -right-1"
              />
            </Button>

            {/* 用户下拉菜单 */}
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
              arrow
            >
              <div className="flex items-center cursor-pointer hover:bg-gray-50 rounded-lg px-3 py-2 transition-colors">
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  className="bg-primary-500"
                />
                <div className="ml-2 hidden sm:block">
                  <div className="text-sm font-medium text-gray-900">管理员</div>
                  <div className="text-xs text-gray-500">admin@logistics.com</div>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 页面内容 */}
        <Content className="flex-1 bg-gray-50">
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout