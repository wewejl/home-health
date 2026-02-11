import { useState, useEffect } from 'react';
import { Search, User, UserPlus, Loader2 } from 'lucide-react';
import { doctorApi } from '@/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/toast';
import { useDebounce } from '@/hooks/useDebounce';
import { type AssignablePatient } from '@/types/patient';
import { getErrorMessage } from '@/utils/error-handler';

interface AssignPatientDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AssignPatientDialog = ({ open, onClose, onSuccess }: AssignPatientDialogProps) => {
  const toast = useToast();
  const [searchText, setSearchText] = useState('');
  const debouncedSearch = useDebounce(searchText, 300);
  const [patients, setPatients] = useState<AssignablePatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [assigning, setAssigning] = useState<number | null>(null);

  useEffect(() => {
    if (open) {
      fetchAssignablePatients();
    }
  }, [open, debouncedSearch]);

  const fetchAssignablePatients = async () => {
    setLoading(true);
    try {
      const response = await doctorApi.getAssignablePatients(debouncedSearch, 50);
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch assignable patients:', error);
      toast.error(`获取患者列表失败: ${getErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignPatient = async (patientId: number) => {
    setAssigning(patientId);
    try {
      await doctorApi.assignPatient(patientId, 'primary');
      toast.success('患者分配成功');
      // 更新列表中的分配状态
      setPatients(prev => prev.map(p =>
        p.id === patientId ? { ...p, is_assigned: true, assigned_at: new Date().toISOString() } : p
      ));
      onSuccess();
    } catch (error) {
      console.error('Failed to assign patient:', error);
      toast.error(`分配失败: ${getErrorMessage(error)}`);
    } finally {
      setAssigning(null);
    }
  };

  const handleUnassignPatient = async (patientId: number) => {
    setAssigning(patientId);
    try {
      await doctorApi.unassignPatient(patientId);
      toast.success('已解除患者关联');
      // 更新列表中的分配状态
      setPatients(prev => prev.map(p =>
        p.id === patientId ? { ...p, is_assigned: false, assigned_at: undefined } : p
      ));
      onSuccess();
    } catch (error) {
      console.error('Failed to unassign patient:', error);
      toast.error(`解除关联失败: ${getErrorMessage(error)}`);
    } finally {
      setAssigning(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>添加患者</DialogTitle>
        </DialogHeader>

        {/* 搜索框 */}
        <div className="relative">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            type="text"
            placeholder="搜索患者姓名或手机号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* 患者列表 */}
        <ScrollArea className="flex-1 -mx-6 px-6">
          <div className="space-y-2 py-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            ) : patients.length === 0 ? (
              <div className="text-center py-8">
                <User className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">
                  {searchText ? '未找到匹配的患者' : '暂无可分配的患者'}
                </p>
              </div>
            ) : (
              patients.map((patient) => (
                <div
                  key={patient.id}
                  className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <User className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{patient.nickname || '未设置姓名'}</span>
                        {patient.is_assigned && (
                          <Badge variant="secondary" className="text-xs">已分配</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{patient.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right text-sm text-muted-foreground">
                      {patient.gender && <span>{patient.gender} </span>}
                      {patient.age && <span>{patient.age}岁</span>}
                    </div>
                    {patient.is_assigned ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUnassignPatient(patient.id)}
                        disabled={assigning === patient.id}
                      >
                        {assigning === patient.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          '解除关联'
                        )}
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleAssignPatient(patient.id)}
                        disabled={assigning === patient.id}
                      >
                        {assigning === patient.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            <UserPlus className="w-4 h-4 mr-1" />
                            添加
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
