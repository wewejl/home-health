// 医嘱类型标签
export const getOrderTypeLabel = (type: string) => {
  const typeMap: Record<string, { label: string; className: string }> = {
    'medication': { label: '用药任务', className: 'bg-info-light text-info' },
    'monitoring': { label: '监测任务', className: 'bg-success-light text-success' },
    'behavior': { label: '行为任务', className: 'bg-warning-light text-warning' },
    'followup': { label: '复诊任务', className: 'bg-info-light text-info' },
  };
  const info = typeMap[type] || { label: type, className: 'bg-muted text-muted-foreground' };
  return { label: info.label, className: info.className };
};

// 医嘱状态标签
export const getStatusLabel = (status: string) => {
  const statusMap: Record<string, { label: string; className: string }> = {
    'draft': { label: '草稿', className: 'bg-muted text-muted-foreground' },
    'active': { label: '进行中', className: 'bg-info-light text-info' },
    'completed': { label: '已完成', className: 'bg-success-light text-success' },
    'stopped': { label: '已停用', className: 'bg-danger-light text-danger' },
  };
  const info = statusMap[status] || { label: status, className: 'bg-muted text-muted-foreground' };
  return { label: info.label, className: info.className };
};
