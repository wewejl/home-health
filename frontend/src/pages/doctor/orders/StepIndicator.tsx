interface StepIndicatorProps {
  currentStep: number;
  steps?: Array<{
    id: number;
    title: string;
    type?: string;
  }>;
}

export const StepIndicator = ({ currentStep, steps = [
  { id: 0, title: '基础信息' },
  { id: 1, title: '调度配置' },
  { id: 2, title: '确认' },
] }: StepIndicatorProps) => {
  // 默认步骤（如果没有传入）
  const defaultSteps = steps.length > 0 ? steps : [
    { id: 0, title: '基础信息' },
    { id: 1, title: '调度配置' },
    { id: 2, title: '确认' },
  ];

  return (
    <>
      {/* 数字步骤指示器 */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {defaultSteps.map((step, index) => (
          <div
            key={step.id}
            className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
              currentStep >= index ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
            }`}
          >
            {index + 1}
          </div>
        ))}
        {defaultSteps.map((_, index) => (
          <div
            key={`line-${index}`}
            className={`w-16 h-0.5 ${index < defaultSteps.length - 1 && currentStep >= index ? 'bg-primary' : 'bg-muted'}`}
          />
        ))}
      </div>
      {/* 文字步骤指示器 */}
      <div className="flex justify-center gap-8 mb-6 text-sm">
        {defaultSteps.map((step) => (
          <span
            key={step.id}
            className={`cursor-pointer ${
              currentStep === step.id ? 'text-foreground font-medium' : 'text-muted-foreground'
            }`}
            onClick={() => {
              // 可选：允许点击步骤跳转
            }}
          >
            {step.title}
          </span>
        ))}
      </div>
    </>
  );
};
