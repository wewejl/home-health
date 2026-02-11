import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { doctorApi } from '@/api';
import type { MedicalOrder, BasicInfoData, ScheduleData, ScheduleType, FormErrors } from './types';
import { StepIndicator } from './StepIndicator';
import { BasicInfoStep } from './steps/BasicInfoStep';
import { ScheduleStep } from './steps/ScheduleStep';
import { ConfirmStep } from './steps/ConfirmStep';

interface CreateOrderDialogProps {
  open: boolean;
  editingOrder: MedicalOrder | null;
  onClose: () => void;
  onSuccess: () => void;
  patientId: number;
  initialBasicInfo?: BasicInfoData;
  initialSchedule?: ScheduleData;
  initialScheduleType?: ScheduleType;
}

export const CreateOrderDialog = ({
  open,
  editingOrder,
  onClose,
  onSuccess,
  patientId,
  initialBasicInfo,
  initialSchedule,
  initialScheduleType = 'once',
}: CreateOrderDialogProps) => {
  const toast = useToast();
  const [currentStep, setCurrentStep] = useState(0);
  const [scheduleType, setScheduleType] = useState<ScheduleType>(initialScheduleType);
  const [basicInfoData, setBasicInfoData] = useState<BasicInfoData>(initialBasicInfo || {});
  const [scheduleData, setScheduleData] = useState<ScheduleData>(initialSchedule || {});
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // 当对话框打开或编辑数据改变时，重置表单状态
  useEffect(() => {
    if (open) {
      setCurrentStep(0);
      setScheduleType(initialScheduleType);
      setBasicInfoData(initialBasicInfo || {});
      setScheduleData(initialSchedule || {});
      setFormErrors({});
    }
  }, [open, initialBasicInfo, initialSchedule, initialScheduleType]);

  // 编辑模式：只有一步，直接编辑基础信息和结束日期
  const isEditMode = !!editingOrder;

  const validateStep = (step: number): boolean => {
    const errors: FormErrors = {};

    if (step === 0) {
      // 编辑模式只需要验证标题
      if (!basicInfoData.title) errors.title = '请输入医嘱标题';
    }

    if (!isEditMode && step === 1) {
      if (!scheduleData.schedule_type) errors.schedule_type = '请选择调度类型';
      if (!scheduleData.start_date) errors.start_date = '请选择开始日期';
      if (!scheduleData.reminder_times || scheduleData.reminder_times.length === 0) {
        errors.reminder_times = '请选择提醒时间';
      }
      if (scheduleData.schedule_type === 'weekly' && (!scheduleData.weekdays || scheduleData.weekdays.length === 0)) {
        errors.weekdays = '请至少选择一天';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) return;

    // 编辑模式：直接提交
    if (isEditMode) {
      handleSubmit();
      return;
    }

    // 创建模式：继续下一步
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    } else {
      onClose();
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingOrder) {
        await doctorApi.updateOrder(editingOrder.id, {
          title: basicInfoData.title,
          description: basicInfoData.description,
          end_date: scheduleData.end_date,
        });
        toast.success('医嘱更新成功');
      } else {
        await doctorApi.createOrder({
          ...basicInfoData,
          ...scheduleData,
          patient_id: patientId,
          status: 'draft',
        } as Parameters<typeof doctorApi.createOrder>[0]);
        toast.success('医嘱创建成功');
      }

      onSuccess();
    } catch (error) {
      console.error('操作失败', error);
      toast.error('操作失败，请稍后重试');
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => {
      if (!open && currentStep === 0) {
        onClose();
      }
    }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editingOrder ? '编辑医嘱' : '创建医嘱'}</DialogTitle>
        </DialogHeader>

        <StepIndicator currentStep={currentStep} />

        {/* 步骤1：基础信息 */}
        {currentStep === 0 && (
          <BasicInfoStep
            data={basicInfoData}
            onChange={setBasicInfoData}
            errors={formErrors}
            isEditing={!!editingOrder}
          />
        )}

        {/* 步骤2：调度配置 */}
        {currentStep === 1 && (
          <ScheduleStep
            data={scheduleData}
            scheduleType={scheduleType}
            onScheduleTypeChange={setScheduleType}
            onChange={setScheduleData}
            errors={formErrors}
          />
        )}

        {/* 步骤3：确认 */}
        {currentStep === 2 && (
          <ConfirmStep
            basicInfo={basicInfoData}
            scheduleData={scheduleData}
          />
        )}

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={handleBack}>
            {isEditMode || currentStep === 0 ? '取消' : '上一步'}
          </Button>
          <Button onClick={isEditMode ? handleSubmit : (currentStep === 2 ? handleSubmit : handleNext)}>
            {isEditMode ? '保存' : (currentStep === 2 ? '创建' : '下一步')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
