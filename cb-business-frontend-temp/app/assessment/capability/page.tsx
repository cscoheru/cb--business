'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { ASSESSMENTS, type AssessmentResult } from '@/lib/assessment';

export default function CapabilityAssessmentPage() {
  const router = useRouter();
  const assessment = ASSESSMENTS.capability;
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);

  const questions = assessment.questions;
  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;
  const canProceed = currentQuestion.required
    ? currentQuestion.type === 'multiple'
      ? answers[currentQuestion.id]?.length > 0
      : !!answers[currentQuestion.id]
    : true;

  const handleAnswer = (questionId: string, value: any) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleMultipleAnswer = (questionId: string, option: any) => {
    setAnswers((prev) => {
      const current = prev[questionId] || [];
      const exists = current.some((a: any) => a.value === option.value);
      if (exists) {
        return { ...prev, [questionId]: current.filter((a: any) => a.value !== option.value) };
      } else {
        return { ...prev, [questionId]: [...current, option] };
      }
    });
  };

  const handleNext = () => {
    if (isLastStep) {
      // 计算结果
      const assessmentResult = assessment.calculateScore(answers);
      setResult(assessmentResult);
      setShowResult(true);
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleRestart = () => {
    setCurrentStep(0);
    setAnswers({});
    setShowResult(false);
    setResult(null);
  };

  // 结果页面
  if (showResult && result) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
        {/* 导航栏 */}
        <nav className="bg-white border-b">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
              ← 返回首页
            </Link>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto px-4 py-12">
          {/* 结果卡片 */}
          <Card className="p-8 mb-8 border-t-4" style={{ borderTopColor: '#a855f7' }}>
            <div className="text-center mb-8">
              <div className="text-6xl mb-4">🪞</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                你的跨境电商能力画像
              </h1>
              <p className="text-gray-600">
                评估得分: <span className="font-bold text-purple-600">{result.score}</span> / {result.maxScore}
              </p>
            </div>

            {/* 等级展示 */}
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl p-6 text-white text-center mb-8">
              <div className="text-sm opacity-90 mb-1">你的等级</div>
              <div className="text-3xl font-bold mb-2">{result.levelName}</div>
              <div className="text-sm opacity-90">
                {result.level === 'beginner' && '适合从东南亚市场新手入门'}
                {result.level === 'intermediate' && '已具备进阶运营能力，可考虑扩张'}
                {result.level === 'advanced' && '专业运营者，可挑战欧美市场'}
                {result.level === 'expert' && '跨境电商专家，具备全局视野'}
              </div>
            </div>

            {/* 推荐列表 */}
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4">为你定制的行动建议</h2>
              <div className="space-y-3">
                {result.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-l-4 ${
                      rec.priority === 'high' ? 'bg-purple-50 border-purple-500' : 'bg-gray-50 border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{rec.icon || '💡'}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                          {rec.priority === 'high' && (
                            <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">优先</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{rec.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* 操作按钮 */}
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleRestart}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
            >
              重新评估
            </button>
            <Link
              href="/inventory"
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              下一步: 资源盘点 →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 问题页面
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
      {/* 导航栏 */}
      <nav className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
            ← 返回首页
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* 进度条 */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>问题 {currentStep + 1} / {questions.length}</span>
            <span>{assessment.estimatedTime}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
              style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* 问题卡片 */}
        <Card className="p-8 mb-6">
          <div className="text-center mb-8">
            <span className="text-5xl">{assessment.emoji}</span>
            <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-2">
              {assessment.title}
            </h1>
            <p className="text-gray-600">{assessment.description}</p>
          </div>

          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {currentQuestion.question}
            </h2>
            {currentQuestion.description && (
              <p className="text-sm text-gray-500">{currentQuestion.description}</p>
            )}
          </div>

          {/* 选项 */}
          <div className="space-y-3">
            {currentQuestion.options?.map((option) => {
              const isSelected =
                currentQuestion.type === 'multiple'
                  ? answers[currentQuestion.id]?.some((a: any) => a.value === option.value)
                  : answers[currentQuestion.id]?.value === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => {
                    if (currentQuestion.type === 'multiple') {
                      handleMultipleAnswer(currentQuestion.id, option);
                    } else {
                      handleAnswer(currentQuestion.id, { ...option, score: option.score || 0 });
                    }
                  }}
                  className={`
                    w-full p-4 rounded-lg border text-left transition-all
                    ${isSelected
                      ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                      : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`
                        w-5 h-5 rounded-full border-2 flex items-center justify-center
                        ${isSelected ? 'border-purple-500' : 'border-gray-300'}
                      `}>
                        {isSelected && (
                          <div className="w-3 h-3 rounded-full bg-purple-500" />
                        )}
                      </div>
                      <span className="font-medium text-gray-900">{option.label}</span>
                    </div>
                    {currentQuestion.type !== 'multiple' && (
                      <span className="text-sm text-gray-400">{option.description}</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {/* 导航按钮 */}
        <div className="flex justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 上一题
          </button>
          <button
            onClick={handleNext}
            disabled={!canProceed}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLastStep ? '查看结果 →' : '下一题 →'}
          </button>
        </div>
      </div>
    </div>
  );
}
