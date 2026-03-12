'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { GROWTH_STAGES } from '@/lib/assessment';
import { useProgress, ACHIEVEMENTS } from '@/hooks/use-progress';

export default function GrowthPathPage() {
  const {
    progress,
    percentage,
    unlockedAchievements,
    toggleStage,
    resetProgress,
    getCurrentStage,
    getNextStage,
    getCompletedStages,
    getEstimatedCompletion,
    isComplete,
    totalStages,
    completedStages,
  } = useProgress();

  const currentStage = getCurrentStage();
  const nextStage = getNextStage();
  const completedStagesList = getCompletedStages();
  const estimatedDays = getEstimatedCompletion();

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white">
      <nav className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
            ← 返回首页
          </Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* 标题 */}
        <div className="text-center mb-8">
          <span className="text-6xl">📖</span>
          <h1 className="text-3xl font-bold text-gray-900 mt-4 mb-2">
            跨境电商业主养成记
          </h1>
          <p className="text-gray-600">从小白到卖家的12阶段成长地图</p>
        </div>

        {/* 统计卡片 */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="p-5 border-t-4" style={{ borderTopColor: '#f97316' }}>
            <div className="text-sm text-gray-500 mb-1">总体进度</div>
            <div className="text-3xl font-bold text-orange-600">{percentage}%</div>
          </Card>

          <Card className="p-5 border-t-4" style={{ borderTopColor: '#22c55e' }}>
            <div className="text-sm text-gray-500 mb-1">已完成</div>
            <div className="text-3xl font-bold text-green-600">{completedStages}/{totalStages}</div>
          </Card>

          <Card className="p-5 border-t-4" style={{ borderTopColor: '#a855f7' }}>
            <div className="text-sm text-gray-500 mb-1">当前阶段</div>
            <div className="text-lg font-bold text-purple-600 truncate">{currentStage?.title}</div>
          </Card>

          <Card className="p-5 border-t-4" style={{ borderTopColor: '#3b82f6' }}>
            <div className="text-sm text-gray-500 mb-1">预计剩余</div>
            <div className="text-lg font-bold text-blue-600">{estimatedDays ? `${estimatedDays}天` : '-'}</div>
          </Card>
        </div>

        {/* 成就展示 */}
        {unlockedAchievements.length > 0 && (
          <Card className="p-6 mb-8 bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🏆</span>
              <h2 className="text-lg font-bold text-gray-900">已解锁成就 ({unlockedAchievements.length}/{ACHIEVEMENTS.length})</h2>
            </div>
            <div className="grid md:grid-cols-5 gap-3">
              {ACHIEVEMENTS.map((achievement) => {
                const isUnlocked = unlockedAchievements.some(a => a.id === achievement.id);
                return (
                  <div
                    key={achievement.id}
                    className={`
                      p-3 rounded-lg text-center transition-all
                      ${isUnlocked
                        ? 'bg-white shadow-sm'
                        : 'bg-gray-100 opacity-50'
                      }
                    `}
                  >
                    <div className={`text-3xl mb-2 ${isUnlocked ? '' : 'grayscale'}`}>
                      {achievement.icon}
                    </div>
                    <div className={`text-sm font-medium mb-1 ${isUnlocked ? 'text-gray-900' : 'text-gray-400'}`}>
                      {achievement.title}
                    </div>
                    <div className={`text-xs ${isUnlocked ? 'text-gray-600' : 'text-gray-400'}`}>
                      {achievement.description}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* 进度条 */}
        <Card className="p-6 mb-8 border-t-4" style={{ borderTopColor: '#f97316' }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-lg font-bold text-gray-900">成长进度</h2>
              <p className="text-sm text-gray-500">
                {isComplete ? '🎉 恭喜！你已完成所有成长阶段！' : `下一步: ${nextStage?.title || '完成所有阶段'}`}
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-orange-600">{percentage}%</div>
            </div>
          </div>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 transition-all duration-500 relative"
              style={{ width: `${percentage}%` }}
            >
              {percentage > 0 && percentage < 100 && (
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              )}
            </div>
          </div>
          {completedStagesList.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500">已完成:</span>
              {completedStagesList.map((stage) => (
                <span key={stage.id} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                  {stage.emoji} {stage.title}
                </span>
              ))}
            </div>
          )}
        </Card>

        {/* 成长阶段列表 */}
        <div className="space-y-3">
          {GROWTH_STAGES.map((stage, idx) => {
            const isCompleted = progress[stage.id]?.completed;
            const isCurrent = currentStage?.id === stage.id && !isCompleted;
            const isLocked = idx > 0 && !progress[GROWTH_STAGES[idx - 1].id]?.completed;

            return (
              <Card
                key={stage.id}
                className={`
                  p-4 border-l-4 transition-all
                  ${isCompleted ? 'border-green-500 bg-green-50/50' : ''}
                  ${isCurrent ? 'border-orange-500 bg-orange-50/50' : ''}
                  ${isLocked && !isCompleted ? 'opacity-50' : 'hover:shadow-md'}
                `}
              >
                <div className="flex items-center gap-4">
                  {/* 序号/状态 */}
                  <div className={`
                    w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold flex-shrink-0
                    ${isCompleted ? 'bg-green-500 text-white' : ''}
                    ${isCurrent ? 'bg-orange-500 text-white' : ''}
                    ${!isCompleted && !isCurrent ? 'bg-gray-200 text-gray-500' : ''}
                  `}>
                    {isCompleted ? '✓' : idx + 1}
                  </div>

                  {/* 内容 */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{stage.emoji}</span>
                      <h3 className="text-lg font-semibold text-gray-900">{stage.title}</h3>
                      {isCompleted && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">已完成</span>
                      )}
                      {isCurrent && (
                        <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full">进行中</span>
                      )}
                      {isLocked && !isCompleted && (
                        <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">待解锁</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{stage.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>⏱️ 预计: {stage.estimatedDays}天</span>
                      {progress[stage.id]?.completedAt && (
                        <span>✅ 完成于: {new Date(progress[stage.id].completedAt!).toLocaleDateString('zh-CN')}</span>
                      )}
                    </div>
                  </div>

                  {/* 勾选按钮 */}
                  {!isLocked && (
                    <button
                      onClick={() => toggleStage(stage.id)}
                      className={`
                        w-14 h-12 rounded-lg flex items-center justify-center transition-all font-medium text-sm
                        ${isCompleted
                          ? 'bg-green-500 text-white hover:bg-green-600'
                          : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                        }
                      `}
                    >
                      {isCompleted ? '完成' : '标记'}
                    </button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>

        {/* 提示信息 */}
        <Card className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-start gap-4">
            <span className="text-3xl">💡</span>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">成长提示</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 按顺序完成各阶段，每个阶段都是下一阶段的基础</li>
                <li>• 实际时间因人而异，预计时间仅供参考</li>
                <li>• 进度自动保存在浏览器中，随时可以回来继续</li>
                <li>• 完成所有阶段后，你将具备跨境电商的基本运营能力</li>
                <li>• 完成特定阶段可解锁成就，记录你的成长里程碑</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 操作按钮 */}
        <div className="mt-8 flex gap-3 justify-center">
          <Link
            href="/assessment"
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
          >
            ← 能力评估
          </Link>
          {completedStages > 0 && (
            <button
              onClick={() => {
                if (confirm('确定要重置所有成长进度吗？此操作不可撤销。')) {
                  resetProgress();
                }
              }}
              className="px-6 py-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition"
            >
              重置进度
            </button>
          )}
          <Link href="/" className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition">
            返回首页
          </Link>
        </div>
      </div>
    </div>
  );
}
