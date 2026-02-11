/**
 * 类型定义统一导出
 */

// 认证相关
export type {
  CurrentUser,
  LoginRequest,
  LoginResponse,
} from './auth';

// 患者相关
export type {
  Patient,
  AssignablePatient,
} from './patient';

// 医嘱相关
export type {
  OrderType,
  ScheduleType,
  OrderStatus,
  TaskStatus,
  MedicalOrder,
  TaskInstance,
  CompletionRecord,
  ComplianceStats,
  WeeklyCompliance,
  TaskListResponse,
  FamilyBond,
  ActivateOrderRequest,
  CompletionRecordRequest,
} from './medical-order';

// 咨询/会话相关
export type {
  SenderType,
  ConsultationMessage,
  Attachment,
  ConsultationSession,
  ConsultationDetailResponse,
  MessageListResponse,
  SessionCreateRequest,
  MessageCreateRequest,
  EnhancedMessageCreateRequest,
  EnhancedSessionCreateRequest,
} from './consultation';

// 医生相关
export type {
  ManagedDoctorInfo,
  DoctorInfo,
  DoctorAttributes,
  PatientStats,
  PatientAssignRequest,
  PatientAssignResponse,
} from './doctor';

// 科室相关
export type {
  Department,
  DepartmentListItem,
  DepartmentDetail,
  DepartmentDoctor,
  DepartmentCreateRequest,
  DepartmentUpdateRequest,
} from './department';
