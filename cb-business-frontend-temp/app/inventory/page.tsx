'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { ASSESSMENTS, type AssessmentResult } from '@/lib/assessment';

export default function InventoryAssessmentPage() {
  const assessment = ASSESSMENTS.inventory;
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);

  const questions = assessment.questions;
  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;
  const canProceed = !!answers[currentQuestion.id];

  const handleAnswer = (questionId: string, value: any) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleNext = () => {
    if (isLastStep) {
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
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
        <nav className="bg-white border-b">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
              ← 返回首页
            </Link>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto px-4 py-12">
          <Card className="p-8 mb-8 border-t-4" style={{ borderTopColor: '#3b82f6' }}>
            <div className="text-center mb-8">
              <div className="text-6xl mb-4">📦</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                你的资源盘点结果
              </h1>
              <p className="text-gray-600">
                资源评分: <span className="font-bold text-blue-600">{result.score}</span> / {result.maxScore}
              </p>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl p-6 text-white text-center mb-8">
              <div className="text-sm opacity-90 mb-1">资源类型</div>
              <div className="text-3xl font-bold mb-2">{result.levelName}</div>
              <div className="text-sm opacity-90">
                {result.level === 'beginner' && '轻装上阵，选择轻资产模式'}
                {result.level === 'intermediate' && '资源适中，稳健发展策略'}
                {result.level === 'advanced' && '资源充足，可快速扩张'}
              </div>
            </div>

            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4">为你推荐的策略</h2>
              <div className="grid md:grid-cols-2 gap-3">
                {result.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-l-4 ${
                      rec.priority === 'high' ? 'bg-blue-50 border-blue-500' : 'bg-gray-50 border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{rec.icon || '💡'}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-1">{rec.title}</h3>
                        <p className="text-sm text-gray-600">{rec.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <div className="flex gap-3 justify-center">
            <button onClick={handleRestart} className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
              重新评估
            </button>
            <Link href="/interests" className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              下一步: 兴趣探索 →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 问题页面
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
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
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
              style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

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
          </div>

          {/* 选项 */}
          <div className="space-y-3">
            {currentQuestion.options?.map((option) => {
              const isSelected = answers[currentQuestion.id]?.value === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(currentQuestion.id, { ...option, score: option.score || 0 })}
                  className={`
                    w-full p-4 rounded-lg border text-left transition-all
                    ${isSelected
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`
                        w-5 h-5 rounded-full border-2 flex items-center justify-center
                        ${isSelected ? 'border-blue-500' : 'border-gray-300'}
                      `}>
                        {isSelected && <div className="w-3 h-3 rounded-full bg-blue-500" />}
                      </div>
                      <span className="font-medium text-gray-900">{option.label}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

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
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:from-blue-600 hover:to-cyan-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLastStep ? '查看结果 →' : '下一题 →'}
          </button>
        </div>
      </div>
    </div>
  );
}
