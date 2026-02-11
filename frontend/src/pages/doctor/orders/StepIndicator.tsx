interface StepIndicatorProps {
  currentStep: number;
}

export const StepIndicator = ({ currentStep }: StepIndicatorProps) => {
  return (
    <>
      {/* 数字步骤指示器 */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
          currentStep >= 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
        }`}>1</div>
        <div className={`w-16 h-0.5 ${currentStep >= 1 ? 'bg-primary' : 'bg-muted'}`} />
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
          currentStep >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
        }`}>2</div>
        <div className={`w-16 h-0.5 ${currentStep >= 2 ? 'bg-primary' : 'bg-muted'}`} />
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
          currentStep >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
        }`}>3</div>
      </div>
      {/* 文字步骤指示器 */}
      <div className="flex justify-center gap-8 mb-6 text-sm">
        <span className={currentStep === 0 ? 'text-foreground font-medium' : 'text-muted-foreground'}>基础信息</span>
        <span className={currentStep === 1 ? 'text-foreground font-medium' : 'text-muted-foreground'}>调度配置</span>
        <span className={currentStep === 2 ? 'text-foreground font-medium' : 'text-muted-foreground'}>确认</span>
      </div>
    </>
  );
};
