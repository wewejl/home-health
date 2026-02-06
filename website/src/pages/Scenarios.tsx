import { Link } from 'react-router-dom';
import {
  Home,
  Building,
  Activity,
  Users,
  TrendingUp,
  ArrowRight,
  Check,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const scenarios = [
  {
    id: 'family',
    icon: Home,
    title: '家庭健康管理',
    color: 'blue',
    description: '为每个家庭成员提供专属的健康守护，让关爱触手可及。',
    image: 'family',
    features: [
      '支持多人账号管理，全家共享',
      '儿童健康咨询，育儿问题随时问',
      '老人健康管理，子女更放心',
      '家庭健康报告，一目了然',
    ],
    benefits: ['24/7 在线响应', '多成员管理', '健康数据共享', '用药提醒'],
  },
  {
    id: 'elderly',
    icon: Building,
    title: '养老机构服务',
    color: 'teal',
    description: '提升养老服务质量，降低运营成本，让老人获得更好的照护。',
    image: 'elderly',
    features: [
      '远程查房，提高医生工作效率',
      '智能健康监测，异常情况及时预警',
      '老人友好的语音交互界面',
      '与院内系统无缝对接',
    ],
    benefits: ['降低人力成本', '提升服务质量', '减少医疗风险', '家属更放心'],
  },
  {
    id: 'hospital',
    icon: Activity,
    title: '医院辅助诊疗',
    color: 'purple',
    description: '辅助医生进行初步问诊和分诊，提升诊疗效率。',
    image: 'hospital',
    features: [
      '智能分诊建议，优化就诊流程',
      '医生分身减轻医生工作负担',
      '患者教育，提高治疗依从性',
      '随访管理，改善患者预后',
    ],
    benefits: ['提高诊疗效率', '优化资源配置', '提升患者满意度', '降低误诊风险'],
  },
];

type ColorType = 'blue' | 'teal' | 'purple';

const colorClasses: Record<ColorType, { bg: string; iconBg: string; text: string; lightBg: string }> = {
  blue: {
    bg: 'bg-primary-50',
    iconBg: 'bg-gradient-primary',
    text: 'text-primary-500',
    lightBg: 'bg-blue-50',
  },
  teal: {
    bg: 'bg-teal-50',
    iconBg: 'bg-gradient-to-br from-teal-400 to-teal-500',
    text: 'text-teal-500',
    lightBg: 'bg-teal-50',
  },
  purple: {
    bg: 'bg-purple-50',
    iconBg: 'bg-gradient-to-br from-purple-400 to-purple-500',
    text: 'text-purple-500',
    lightBg: 'bg-purple-50',
  },
};

export default function Scenarios() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-16 bg-gradient-soft">
          <div className="container-custom">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-teal-50 text-teal-600 text-sm font-medium mb-6">
                应用场景
              </div>
              <h1 className="text-h1 mb-6">
                适用于<span className="text-gradient-teal">多种场景</span>
              </h1>
              <p className="text-body-lg text-text-secondary">
                无论是家庭健康管理、养老机构服务，还是医院辅助诊疗，
                灵犀健康都能为您提供专业的解决方案。
              </p>
            </div>
          </div>
        </section>

        {/* Scenarios */}
        {scenarios.map((scenario, index) => {
          const colors = colorClasses[scenario.color as ColorType];

          return (
            <section
              key={scenario.id}
              id={scenario.id}
              className="py-20 bg-white"
            >
              <div className="container-custom">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                  {/* Content */}
                  <div className={index % 2 === 1 ? 'lg:order-2' : ''}>
                    <div className={`w-20 h-20 ${colors.iconBg} rounded-3xl flex items-center justify-center text-white mb-8 shadow-lg`}>
                      <scenario.icon size={40} />
                    </div>
                    <h2 className={`text-h2 mb-4 ${colors.text}`}>{scenario.title}</h2>
                    <p className="text-body-lg text-text-secondary mb-8">
                      {scenario.description}
                    </p>

                    {/* Features */}
                    <div className="mb-8">
                      <h3 className="font-semibold text-text-primary mb-4">核心功能</h3>
                      <ul className="space-y-3">
                        {scenario.features.map((feature, i) => (
                          <li key={i} className="flex items-start gap-3">
                            <div className={`w-6 h-6 ${colors.iconBg} rounded-full flex items-center justify-center flex-shrink-0 mt-0.5`}>
                              <Check size={14} className="text-white" />
                            </div>
                            <span className="text-body text-text-secondary">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Benefits */}
                    <div className={`flex flex-wrap gap-3`}>
                      {scenario.benefits.map((benefit, i) => (
                        <span
                          key={i}
                          className={`px-4 py-2 ${colors.lightBg} ${colors.text} rounded-full text-sm font-medium`}
                        >
                          {benefit}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Visual */}
                  <div className={index % 2 === 1 ? 'lg:order-1' : ''}>
                    <div className={`${colors.bg} rounded-3xl p-8`}>
                      {/* Mock Interface */}
                      <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                        <div className={`${colors.iconBg} p-4`}>
                          <div className="flex items-center gap-3 text-white">
                            <scenario.icon size={24} />
                            <span className="font-semibold">{scenario.title}</span>
                          </div>
                        </div>
                        <div className="p-6 space-y-4">
                          {scenario.features.slice(0, 3).map((_feature, i) => (
                            <div key={i} className="flex items-center gap-4">
                              <div className={`w-12 h-12 ${colors.lightBg} rounded-xl flex items-center justify-center ${colors.text}`}>
                                <scenario.icon size={24} />
                              </div>
                              <div className="flex-1">
                                <div className="h-3 bg-gray-100 rounded mb-2 w-3/4"></div>
                                <div className="h-2 bg-gray-50 rounded w-1/2"></div>
                              </div>
                            </div>
                          ))}
                          <div className="pt-4 border-t border-gray-100">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-text-secondary">服务状态</span>
                              <span className="flex items-center gap-2 text-sm font-medium text-success-dark">
                                <span className="w-2 h-2 bg-success rounded-full animate-pulse"></span>
                                运行中
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          );
        })}

        {/* Stats Section */}
        <section className="py-20 bg-gradient-soft">
          <div className="container-custom">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { value: '100万+', label: '家庭用户', icon: Users },
                { value: '500+', label: '养老机构', icon: Building },
                { value: '50+', label: '合作医院', icon: Activity },
                { value: '98%', label: '满意度', icon: TrendingUp },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center text-white mx-auto mb-4">
                    <stat.icon size={32} />
                  </div>
                  <div className="text-3xl font-bold text-text-primary mb-2">{stat.value}</div>
                  <div className="text-text-secondary">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="bg-gradient-to-br from-primary-500 to-teal-500 rounded-3xl p-12 text-center text-white">
              <h2 className="text-h2 mb-4">探索灵犀健康的无限可能</h2>
              <p className="text-white/80 mb-8 max-w-xl mx-auto">
                无论您是个人用户还是机构客户，我们都有适合您的解决方案
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link to="/download" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-500 rounded-xl font-semibold hover:bg-white/90 transition-all duration-300">
                  个人用户下载
                  <ArrowRight size={20} />
                </Link>
                <a
                  href="mailto:business@lingxi.health"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 text-white rounded-xl font-semibold hover:bg-white/20 transition-all duration-300 border border-white/20"
                >
                  机构商务合作
                  <ArrowRight size={20} />
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
