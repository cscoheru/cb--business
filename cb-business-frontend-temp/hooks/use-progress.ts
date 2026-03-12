import { useState, useEffect, useCallback } from 'react';
import { getGrowthProgress, saveGrowthProgress, getGrowthProgressPercentage, GROWTH_STAGES } from '@/lib/assessment';

// 成就定义
export const ACHIEVEMENTS = [
  {
    id: 'first_step',
    title: '初出茅庐',
    description: '完成第一个成长阶段',
    icon: '🌱',
    condition: (progress: Record<string, any>) => progress.stage_1?.completed,
  },
  {
    id: 'third_completed',
    title: '渐入佳境',
    description: '完成前3个成长阶段',
    icon: '🌿',
    condition: (progress: Record<string, any>) =>
      progress.stage_1?.completed && progress.stage_2?.completed && progress.stage_3?.completed,
  },
  {
    id: 'halfway',
    title: '小有成就',
    description: '完成一半成长阶段',
    icon: '🌳',
    condition: (progress: Record<string, any>) => {
      const completed = Object.values(progress).filter((p: any) => p.completed).length;
      return completed >= 6;
    },
  },
  {
    id: 'all_completed',
    title: '大功告成',
    description: '完成所有12个成长阶段',
    icon: '🏆',
    condition: (progress: Record<string, any>) => {
      const completed = Object.values(progress).filter((p: any) => p.completed).length;
      return completed === 12;
    },
  },
  {
    id: 'week_one',
    title: '坚持一周',
    description: '7天内完成3个以上阶段',
    icon: '🔥',
    condition: (progress: Record<string, any>) => {
      const now = Date.now();
      const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
      const completedInWeek = Object.values(progress).filter((p: any) => {
        if (!p.completed || !p.completedAt) return false;
        return new Date(p.completedAt).getTime() >= weekAgo;
      }).length;
      return completedInWeek >= 3;
    },
  },
];

// 检查解锁的成就
export function checkUnlockedAchievements(progress: Record<string, any>): typeof ACHIEVEMENTS {
  return ACHIEVEMENTS.filter(a => a.condition(progress));
}

// 进度Hook
export function useProgress() {
  const [progress, setProgress] = useState<Record<string, { completed: boolean; completedAt?: string }>>({});
  const [percentage, setPercentage] = useState(0);
  const [unlockedAchievements, setUnlockedAchievements] = useState<typeof ACHIEVEMENTS>([]);

  // 加载进度
  useEffect(() => {
    const loadProgress = () => {
      const savedProgress = getGrowthProgress();
      setProgress(savedProgress);
      setPercentage(getGrowthProgressPercentage());
      setUnlockedAchievements(checkUnlockedAchievements(savedProgress));
    };

    loadProgress();

    // 监听storage变化（跨标签页同步）
    const handleStorageChange = () => {
      loadProgress();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // 切换阶段状态
  const toggleStage = useCallback((stageId: string) => {
    const currentStatus = progress[stageId]?.completed || false;
    const newStatus = !currentStatus;

    saveGrowthProgress(stageId, newStatus);

    const updatedProgress = getGrowthProgress();
    setProgress(updatedProgress);
    setPercentage(getGrowthProgressPercentage());
    setUnlockedAchievements(checkUnlockedAchievements(updatedProgress));
  }, [progress]);

  // 重置所有进度
  const resetProgress = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('zenconsult_growth_progress');
      const emptyProgress: Record<string, any> = {};
      setProgress(emptyProgress);
      setPercentage(0);
      setUnlockedAchievements([]);
    }
  }, []);

  // 获取当前阶段
  const getCurrentStage = useCallback(() => {
    const completedCount = Object.values(progress).filter(p => p.completed).length;
    if (completedCount === 0) return GROWTH_STAGES[0];
    if (completedCount >= GROWTH_STAGES.length) return GROWTH_STAGES[GROWTH_STAGES.length - 1];
    return GROWTH_STAGES[completedCount];
  }, [progress]);

  // 获取下一个待完成阶段
  const getNextStage = useCallback(() => {
    for (const stage of GROWTH_STAGES) {
      if (!progress[stage.id]?.completed) {
        return stage;
      }
    }
    return null;
  }, [progress]);

  // 获取已完成阶段列表
  const getCompletedStages = useCallback(() => {
    return GROWTH_STAGES.filter(stage => progress[stage.id]?.completed);
  }, [progress]);

  // 计算预计完成时间
  const getEstimatedCompletion = useCallback(() => {
    const completedCount = Object.values(progress).filter(p => p.completed).length;
    const remaining = GROWTH_STAGES.length - completedCount;
    if (remaining === 0) return null;

    // 基于每个阶段的预计天数计算剩余时间
    const totalDays = GROWTH_STAGES.reduce((sum, stage) => sum + stage.estimatedDays, 0);
    const completedDays = GROWTH_STAGES
      .filter(stage => progress[stage.id]?.completed)
      .reduce((sum, stage) => sum + stage.estimatedDays, 0);

    return totalDays - completedDays;
  }, [progress]);

  return {
    progress,
    percentage,
    unlockedAchievements,
    toggleStage,
    resetProgress,
    getCurrentStage,
    getNextStage,
    getCompletedStages,
    getEstimatedCompletion,
    isComplete: percentage === 100,
    totalStages: GROWTH_STAGES.length,
    completedStages: Object.values(progress).filter(p => p.completed).length,
  };
}
