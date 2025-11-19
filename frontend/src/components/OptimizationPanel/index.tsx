import React, { useState, useEffect, useCallback } from 'react'
import { Card, Button, Progress, Steps, Typography, Space, Alert, Divider, Row, Col, Statistic, Tag, Tooltip, Badge } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FireOutlined,
  TrophyOutlined,
  SettingOutlined,
  RocketOutlined
} from '@ant-design/icons'
import type { OptimizationTask, OptimizationStage } from '@/types'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

export interface OptimizationPanelProps {
  onTaskStart?: (parameters: any) => void
  onTaskPause?: (taskId: string) => void
  onTaskStop?: (taskId: string) => void
  onTaskComplete?: (task: OptimizationTask) => void
}

export const OptimizationPanel: React.FC<OptimizationPanelProps> = ({
  onTaskStart,
  onTaskPause,
  onTaskStop,
  onTaskComplete,
}) => {
  const [currentTask, setCurrentTask] = useState<OptimizationTask | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(0)

  // 优化阶段配置
  const optimizationStages = [
    {
      key: 'data_preprocessing',
      title: '数据预处理',
      description: '验证和清洗输入数据',
      duration: 30, // 占总进度的30%
      icon: <SettingOutlined />,
    },
    {
      key: '3d_packing',
      title: '3D装箱计算',
      description: '执行三维装箱优化算法',
      duration: 30, // 占总进度的30%
      icon: <FireOutlined />,
    },
    {
      key: 'route_planning',
      title: '路径规划优化',
      description: '计算最优配送路径',
      duration: 30, // 占总进度的30%
      icon: <TrophyOutlined />,
    },
    {
      key: 'result_generation',
      title: '结果生成',
      description: '生成优化报告和可视化',
      duration: 10, // 占总进度的10%
      icon: <RocketOutlined />,
    },
  ]

  // 模拟优化参数
  const optimizationParameters = {
    vehicles: ['LARGE_TRUCK_000', 'MEDIUM_TRUCK_001', 'LTL_TRUCK_002'],
    orders: ['ORDER_001', 'ORDER_002', 'ORDER_003'],
    objectives: [
      { name: 'minimize_distance', weight: 0.4 },
      { name: 'minimize_time', weight: 0.3 },
      { name: 'maximize_utilization', weight: 0.3 },
    ],
    constraints: {
      timeWindows: true,
      capacity: true,
      driverHours: true,
    },
    timeLimit: 300, // 5分钟
  }

  // 计时器效果
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isRunning && !isPaused) {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1)
        if (estimatedTimeRemaining > 0) {
          setEstimatedTimeRemaining((prev) => Math.max(0, prev - 1))
        }
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isRunning, isPaused, estimatedTimeRemaining])

  // 开始优化任务
  const startOptimization = useCallback(() => {
    const newTask: OptimizationTask = {
      id: `task_${Date.now()}`,
      name: `物流优化任务_${new Date().toLocaleString()}`,
      type: 'hybrid',
      status: 'running',
      progress: {
        current: 0,
        stage: {
          name: 'data_preprocessing',
          progress: 0,
          status: 'running',
          startTime: new Date().toISOString(),
        },
        estimatedTimeRemaining: 300, // 5分钟
      },
      parameters: optimizationParameters,
      createdAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    }

    setCurrentTask(newTask)
    setIsRunning(true)
    setIsPaused(false)
    setElapsedTime(0)
    setEstimatedTimeRemaining(300)

    // 启动进度模拟
    simulateOptimizationProgress(newTask)

    onTaskStart?.(newTask)
  }, [onTaskStart])

  // 模拟优化进度
  const simulateOptimizationProgress = (task: OptimizationTask) => {
    let currentStageIndex = 0
    let currentStageProgress = 0

    const progressInterval = setInterval(() => {
      currentStageProgress += Math.random() * 5 // 随机进度增量

      if (currentStageProgress >= 100) {
        currentStageProgress = 100
        currentStageIndex++

        if (currentStageIndex >= optimizationStages.length) {
          // 所有阶段完成
          clearInterval(progressInterval)
          completeOptimization()
          return
        }
      }

      // 更新当前任务状态
      setCurrentTask((prev) => {
        if (!prev) return null

        const totalProgress = (currentStageIndex * 100 + currentStageProgress) / optimizationStages.length
        const currentStage = optimizationStages[currentStageIndex]

        return {
          ...prev,
          progress: {
            ...prev.progress,
            current: Math.round(totalProgress),
            stage: {
              name: currentStage.key,
              progress: Math.round(currentStageProgress),
              status: currentStageProgress >= 100 ? 'completed' : 'running',
              startTime: currentStageIndex === 0 ? prev.progress.stage.startTime : undefined,
              endTime: currentStageProgress >= 100 ? new Date().toISOString() : undefined,
            },
            estimatedTimeRemaining: Math.max(0, 300 - elapsedTime),
          },
        }
      })
    }, 200)
  }

  // 完成优化任务
  const completeOptimization = () => {
    const completedTask = {
      ...currentTask!,
      status: 'completed' as const,
      progress: {
        current: 100,
        stage: {
          name: 'result_generation',
          progress: 100,
          status: 'completed' as const,
          startTime: currentTask?.progress.stage.startTime,
          endTime: new Date().toISOString(),
        },
        estimatedTimeRemaining: 0,
      },
      completedAt: new Date().toISOString(),
      results: {
        totalDistance: 145.8,
        totalTime: 480,
        totalCost: 2850.5,
        vehicleUtilization: [
          { vehicleId: 'LARGE_TRUCK_000', utilizationRate: 92.5, routeDistance: 85.2, routeTime: 280, ordersCount: 8 },
          { vehicleId: 'MEDIUM_TRUCK_001', utilizationRate: 87.3, routeDistance: 60.6, routeTime: 200, ordersCount: 6 },
        ],
        kpis: {
          costPerKm: 19.54,
          costPerOrder: 178.16,
          averageUtilization: 89.9,
          onTimeDeliveryRate: 95.5,
        },
      },
    }

    setCurrentTask(completedTask)
    setIsRunning(false)
    setIsPaused(false)

    onTaskComplete?.(completedTask)
  }

  // 暂停优化任务
  const pauseOptimization = () => {
    setIsPaused(true)
    onTaskPause?.(currentTask?.id || '')
  }

  // 停止优化任务
  const stopOptimization = () => {
    setCurrentTask(null)
    setIsRunning(false)
    setIsPaused(false)
    setElapsedTime(0)
    setEstimatedTimeRemaining(0)

    onTaskStop?.(currentTask?.id || '')
  }

  // 重新开始优化任务
  const restartOptimization = () => {
    stopOptimization()
    setTimeout(startOptimization, 500)
  }

  // 格式化时间
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  // 获取当前步骤状态
  const getStepStatus = (stageKey: string) => {
    if (!currentTask) return 'wait'

    const currentStageIndex = optimizationStages.findIndex(s => s.key === currentTask.progress.stage.name)
    const stageIndex = optimizationStages.findIndex(s => s.key === stageKey)

    if (stageIndex < currentStageIndex) return 'finish'
    if (stageIndex === currentStageIndex) {
      return currentTask.status === 'running' ? 'process' : currentTask.status === 'completed' ? 'finish' : 'wait'
    }
    return 'wait'
  }

  const currentStep = optimizationStages.findIndex(s => s.key === currentTask?.progress.stage.name)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <Title level={2}>优化执行面板</Title>

      {/* 主要控制区域 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card className="h-full">
            <div className="space-y-6">
              {/* 标题和控制按钮 */}
              <div className="flex items-center justify-between">
                <div>
                  <Title level={3} className="mb-2">
                    智能物流优化引擎
                  </Title>
                  <Text type="secondary">
                    基于3D装箱与路径规划的混合优化算法
                  </Text>
                </div>

                <Space size="large">
                  {!isRunning ? (
                    <Button
                      type="primary"
                      size="large"
                      icon={<PlayCircleOutlined />}
                      onClick={startOptimization}
                      className="btn-primary"
                    >
                      开始优化
                    </Button>
                  ) : (
                    <>
                      {!isPaused ? (
                        <Button
                          size="large"
                          icon={<PauseCircleOutlined />}
                          onClick={pauseOptimization}
                        >
                          暂停
                        </Button>
                      ) : (
                        <Button
                          type="primary"
                          size="large"
                          icon={<PlayCircleOutlined />}
                          onClick={() => setIsPaused(false)}
                        >
                          继续
                        </Button>
                      )}
                      <Button
                        size="large"
                        icon={<StopOutlined />}
                        onClick={stopOptimization}
                        danger
                      >
                        停止
                      </Button>
                    </>
                  )}
                </Space>
              </div>

              <Divider />

              {/* 优化进度步骤 */}
              {currentTask && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <Title level={4}>优化进度</Title>
                    <div className="flex items-center space-x-4">
                      <Tag color="blue">
                        <ClockCircleOutlined /> 已用时间: {formatTime(elapsedTime)}
                      </Tag>
                      {estimatedTimeRemaining > 0 && (
                        <Tag color="green">
                          <ClockCircleOutlined /> 剩余时间: {formatTime(estimatedTimeRemaining)}
                        </Tag>
                      )}
                    </div>
                  </div>

                  <Steps
                    current={currentStep}
                    items={optimizationStages.map((stage, index) => ({
                      title: stage.title,
                      description: stage.description,
                      status: getStepStatus(stage.key) as any,
                      icon: stage.icon,
                    }))}
                  />

                  {/* 总体进度条 */}
                  <div className="mt-6">
                    <div className="flex items-center justify-between mb-2">
                      <Text strong>总体进度</Text>
                      <Text strong>{currentTask.progress.current}%</Text>
                    </div>
                    <Progress
                      percent={currentTask.progress.current}
                      strokeColor={{
                        '0%': '#108ee9',
                        '30%': '#87d068',
                        '60%': '#faad14',
                        '100%': '#52c41a',
                      }}
                      format={(percent) => (
                        <span className="font-medium">{percent}%</span>
                      )}
                    />
                  </div>
                </div>
              )}

              {/* 实时状态信息 */}
              {currentTask && (
                <AnimatePresence>
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Alert
                      message={
                        <div className="flex items-center space-x-2">
                          <Badge status={isRunning && !isPaused ? 'processing' : currentTask.status === 'completed' ? 'success' : 'default'} />
                          <span>
                            {isRunning && !isPaused
                              ? `正在执行: ${optimizationStages[currentStep]?.title}`
                              : currentTask.status === 'completed'
                              ? '优化任务已完成'
                              : '任务已暂停'}
                          </span>
                        </div>
                      }
                      description={
                        isRunning && !isPaused
                          ? `${currentTask.progress.stage.progress}% 完成，预计剩余时间 ${formatTime(estimatedTimeRemaining)}`
                          : currentTask.status === 'completed'
                          ? '优化结果已生成，可查看详细报告和可视化结果'
                          : '点击继续按钮恢复优化进程'
                      }
                      type={currentTask.status === 'completed' ? 'success' : 'info'}
                      showIcon
                    />
                  </motion.div>
                </AnimatePresence>
              )}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Space direction="vertical" size="large" className="w-full">
            {/* 优化参数配置 */}
            <Card title="优化参数" size="small">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Text type="secondary">车辆数量:</Text>
                  <Text strong>{optimizationParameters.vehicles.length}</Text>
                </div>
                <div className="flex justify-between">
                  <Text type="secondary">订单数量:</Text>
                  <Text strong>{optimizationParameters.orders.length}</Text>
                </div>
                <div className="flex justify-between">
                  <Text type="secondary">时间限制:</Text>
                  <Text strong>{optimizationParameters.timeLimit}秒</Text>
                </div>
                <div className="flex justify-between">
                  <Text type="secondary">优化类型:</Text>
                  <Tag color="blue">混合优化</Tag>
                </div>
              </div>
            </Card>

            {/* 优化目标权重 */}
            <Card title="优化目标" size="small">
              <div className="space-y-3">
                {optimizationParameters.objectives.map((objective, index) => (
                  <div key={index}>
                    <div className="flex justify-between mb-1">
                      <Text type="secondary">
                        {objective.name === 'minimize_distance' ? '最短距离' :
                         objective.name === 'minimize_time' ? '最短时间' :
                         '最高利用率'}
                      </Text>
                      <Text strong>{(objective.weight * 100).toFixed(0)}%</Text>
                    </div>
                    <Progress
                      percent={objective.weight * 100}
                      size="small"
                      strokeColor="#1890ff"
                      showInfo={false}
                    />
                  </div>
                ))}
              </div>
            </Card>

            {/* 任务历史 */}
            <Card title="最近任务" size="small">
              <div className="text-center py-4">
                <Text type="secondary">暂无历史任务</Text>
              </div>
            </Card>
          </Space>
        </Col>
      </Row>
    </motion.div>
  )
}

export default OptimizationPanel