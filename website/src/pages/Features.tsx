import { Link } from 'react-router-dom';
import {
  Brain,
  Stethoscope,
  FileText,
  Mic,
  Pill,
  Video,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const features = [
  {
    id: 'ai',
    icon: Brain,
    title: 'AI 智能咨询',
    color: 'blue',
    description: '基于先进的自然语言处理技术，理解您的健康问题，提供专业的医疗建议和解答。',
    details: [
      '智能语义理解，准确识别用户意图',
      '多轮对话能力，深入挖掘病情信息',
      '专业医疗知识库支撑，确保建议准确性',
      '秒级响应，随时等待您的咨询',
    ],
  },
  {
    id: 'avatar',
    icon: Stethoscope,
    title: '医生分身系统',
    color: 'teal',
    description: '多科室专家 AI 分身，模拟真实问诊体验，提供精准的专科健康咨询服务。',
    details: [
      '覆盖内科、外科、皮肤科等多个科室',
      '模拟真实医生问诊风格和逻辑',
      '持续学习最新医学进展',
      '支持个性化诊断偏好设置',
    ],
  },
  {
    id: 'records',
    icon: FileText,
    title: '健康档案管理',
    color: 'purple',
    description: '自动记录和管理您的健康数据，生成完整的健康档案，方便随时查看和分享。',
    details: [
      '自动整理每次咨询记录',
      '生成结构化健康报告',
      '支持导出 PDF 分享给家人医生',
      '长期健康趋势分析',
    ],
  },
  {
    id: 'voice',
    icon: Mic,
    title: '语音交互',
    color: 'orange',
    description: '支持自然语音对话，像与真人医生交流一样自然，使用更加便捷友好。',
    details: [
      '支持普通话及多种方言',
      '智能语音识别，准确率高',
      '自然语音合成，亲切自然',
      '手势控制，老人也能轻松使用',
    ],
  },
  {
    id: 'medication',
    icon: Pill,
    title: '医嘱监督',
    color: 'green',
    description: '智能用药提醒和执行跟踪，确保按时按量服药，守护您的健康每一刻。',
    details: [
      '精准用药时间提醒',
      '支持多种服药周期设置',
      '家属可远程查看服药记录',
      '漏服自动提醒家人',
    ],
  },
  {
    id: 'rounding',
    icon: Video,
    title: '远程查房',
    color: 'blue',
    description: '为养老机构提供远程查房服务，医生可远程了解患者情况，提高工作效率。',
    details: [
      '支持多患者同时查房',
      '实时查看患者健康数据',
      '远程生成查房记录',
      '与院内系统无缝对接',
    ],
  },
];

type ColorType = 'blue' | 'teal' | 'purple' | 'orange' | 'green';

const colorClasses: Record<
  ColorType,
  { bg: string; iconBg: string; text: string; border: string }
> = {
  blue: {
    bg: 'bg-primary-50',
    iconBg: 'bg-gradient-primary',
    text: 'text-primary-500',
    border: 'border-primary-200',
  },
  teal: {
    bg: 'bg-teal-50',
    iconBg: 'bg-gradient-to-br from-teal-400 to-teal-500',
    text: 'text-teal-500',
    border: 'border-teal-200',
  },
  purple: {
    bg: 'bg-purple-50',
    iconBg: 'bg-gradient-to-br from-purple-400 to-purple-500',
    text: 'text-purple-500',
    border: 'border-purple-200',
  },
  orange: {
    bg: 'bg-orange-50',
    iconBg: 'bg-gradient-to-br from-orange-400 to-orange-500',
    text: 'text-orange-500',
    border: 'border-orange-200',
  },
  green: {
    bg: 'bg-success/20',
    iconBg: 'bg-gradient-to-br from-success-light to-success',
    text: 'text-success-dark',
    border: 'border-success/40',
  },
};

export default function Features() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-16 bg-gradient-soft">
          <div className="container-custom">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 text-primary-600 text-sm font-medium mb-6">
                功能介绍
              </div>
              <h1 className="text-h1 mb-6">
                <span className="text-gradient-teal">强大功能</span> 全面守护
              </h1>
              <p className="text-body-lg text-text-secondary">
                灵犀健康集成了智能咨询、健康档案、医嘱监督等多项功能，
                为您提供一站式健康管理解决方案。
              </p>
            </div>
          </div>
        </section>

        {/* Features List */}
        {features.map((feature, index) => {
          const colors = colorClasses[feature.color as ColorType];
          const isEven = index % 2 === 0;

          return (
            <section
              key={feature.id}
              id={feature.id}
              className={`py-20 ${isEven ? 'bg-white' : 'bg-background'}`}
            >
              <div className="container-custom">
                <div className={`grid lg:grid-cols-2 gap-12 items-center ${!isEven ? 'lg:flex-row-reverse' : ''}`}>
                  {/* Icon and Title */}
                  <div>
                    <div className={`w-20 h-20 ${colors.iconBg} rounded-3xl flex items-center justify-center text-white mb-8 shadow-lg`}>
                      <feature.icon size={40} />
                    </div>
                    <h2 className={`text-h2 mb-4 ${colors.text}`}>{feature.title}</h2>
                    <p className="text-body-lg text-text-secondary mb-8">
                      {feature.description}
                    </p>

                    {/* Features List */}
                    <ul className="space-y-4">
                      {feature.details.map((detail, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <CheckCircle2 size={20} className={colors.text + ' mt-0.5 flex-shrink-0'} />
                          <span className="text-body text-text-secondary">{detail}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Demo Card */}
                  <div className="relative">
                    <div className={`${colors.bg} rounded-3xl p-8 border ${colors.border}`}>
                      <div className="bg-white rounded-2xl p-6 shadow-lg">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100">
                          <div className={`w-10 h-10 ${colors.iconBg} rounded-xl flex items-center justify-center text-white`}>
                            <feature.icon size={20} />
                          </div>
                          <div>
                            <div className="font-semibold text-text-primary">{feature.title}</div>
                            <div className="text-sm text-text-secondary">智能服务</div>
                          </div>
                        </div>
                        <div className="space-y-3">
                          <div className="flex items-start gap-3">
                            <div className={`w-8 h-8 ${colors.bg} rounded-lg flex items-center justify-center ${colors.text}`}>
                              <feature.icon size={16} />
                            </div>
                            <div className="flex-1">
                              <div className="bg-gray-50 rounded-xl p-3 text-sm text-text-secondary">
                                {feature.details[0]}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-start gap-3 justify-end">
                            <div className="flex-1 flex justify-end">
                              <div className={`bg-gradient-primary text-white rounded-xl p-3 text-sm max-w-[80%]`}>
                                {feature.details[1]}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    {/* 装饰 */}
                    <div className={`absolute -bottom-4 -right-4 w-full h-full ${colors.bg} rounded-3xl -z-10`} />
                  </div>
                </div>
              </div>
            </section>
          );
        })}

        {/* CTA */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="bg-gradient-primary rounded-3xl p-12 text-center text-white">
              <h2 className="text-h2 mb-4">准备好体验了吗？</h2>
              <p className="text-white/80 mb-8 max-w-xl mx-auto">
                立即下载灵犀健康 App，开启您的智能健康之旅
              </p>
              <Link to="/download" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-500 rounded-xl font-semibold hover:bg-white/90 transition-all duration-300 hover:scale-105">
                免费下载 App
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
