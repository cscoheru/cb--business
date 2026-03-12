'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { ASSESSMENTS, type AssessmentResult } from '@/lib/assessment';

export default function InterestsAssessmentPage() {
  const assessment = ASSESSMENTS.interest;
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);

  const questions = assessment.questions;
  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;
  const canProceed = currentQuestion.type === 'multiple'
    ? answers[currentQuestion.id]?.length > 0
    : !!answers[currentQuestion.id];

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
      <div className="min-h-screen bg-gradient-to-b from-green-50 to-white">
        <nav className="bg-white border-b">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
              ← 返回首页
            </Link>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto px-4 py-12">
          <Card className="p-8 mb-8 border-t-4" style={{ borderTopColor: '#22c55e' }}>
            <div className="text-center mb-8">
              <div className="text-6xl mb-4">🧭</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                根据你的兴趣，为你推荐
              </h1>
              <p className="text-gray-600">
                匹配度: <span className="font-bold text-green-600">{result.score}分</span>
              </p>
            </div>

            <div className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl p-6 text-white text-center mb-8">
              <div className="text-sm opacity-90 mb-1">探索类型</div>
              <div className="text-3xl font-bold mb-2">{result.levelName}</div>
              <div className="text-sm opacity-90">
                跟随兴趣，发现最适合你的跨境电商方向
              </div>
            </div>

            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4">
                品类与市场推荐
              </h2>
              <div className="grid md:grid-cols-2 gap-3">
                {result.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-l-4 ${
                      rec.priority === 'high' ? 'bg-green-50 border-green-500' : 'bg-gray-50 border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{rec.icon || '💡'}</span>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded uppercase">
                            {rec.type}
                          </span>
                        </div>
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
              重新选择
            </button>
            <Link href="/growth-path" className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
              下一步: 成长路径 →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // 问题页面
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white">
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
            <span>步骤 {currentStep + 1} / {questions.length}</span>
            <span>{assessment.estimatedTime}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-300"
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

          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {currentQuestion.question}
            </h2>
            {currentQuestion.description && (
              <p className="text-sm text-gray-500 mb-4">{currentQuestion.description}</p>
            )}
          </div>

          {/* 多选选项 */}
          {currentQuestion.type === 'multiple' ? (
            <div className="grid md:grid-cols-2 gap-3">
              {currentQuestion.options?.map((option) => {
                const isSelected = answers[currentQuestion.id]?.some((a: any) => a.value === option.value);

                return (
                  <button
                    key={option.value}
                    onClick={() => handleMultipleAnswer(currentQuestion.id, option)}
                    className={`
                      p-4 rounded-lg border text-left transition-all
                      ${isSelected
                        ? 'border-green-500 bg-green-50 ring-2 ring-green-200'
                        : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`
                        w-5 h-5 rounded border-2 flex items-center justify-center
                        ${isSelected ? 'border-green-500 bg-green-500' : 'border-gray-300'}
                      `}>
                        {isSelected && <span className="text-white text-xs">✓</span>}
                      </div>
                      <span className="text-2xl">{option.icon}</span>
                      <span className="font-medium text-gray-900">{option.label}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            /* 单选选项 */
            <div className="space-y-3">
              {currentQuestion.options?.map((option) => {
                const isSelected = answers[currentQuestion.id]?.value === option.value;

                return (
                  <button
                    key={option.value}
                    onClick={() => handleAnswer(currentQuestion.id, option)}
                    className={`
                      w-full p-4 rounded-lg border text-left transition-all
                      ${isSelected
                        ? 'border-green-500 bg-green-50 ring-2 ring-green-200'
                        : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`
                          w-5 h-5 rounded-full border-2 flex items-center justify-center
                          ${isSelected ? 'border-green-500' : 'border-gray-300'}
                        `}>
                          {isSelected && <div className="w-3 h-3 rounded-full bg-green-500" />}
                        </div>
                        <span className="text-2xl">{option.icon}</span>
                        <div>
                          <span className="font-medium text-gray-900">{option.label}</span>
                          {option.description && (
                            <p className="text-sm text-gray-500">{option.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </Card>

        <div className="flex justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 上一步
          </button>
          <button
            onClick={handleNext}
            disabled={!canProceed}
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:from-green-600 hover:to-emerald-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLastStep ? '查看推荐 →' : '下一步 →'}
          </button>
        </div>
      </div>
    </div>
  );
}
