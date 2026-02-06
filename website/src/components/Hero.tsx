import { Link } from 'react-router-dom';
import { ArrowRight, Play, Shield, Clock, Users } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

const stats = [
  { icon: Users, value: '100万+', label: '服务用户' },
  { icon: Clock, value: '24/7', label: '在线服务' },
  { icon: Shield, value: '99.9%', label: '准确率' },
];

const ctaButtons = [
  { text: '下载 App', href: '/download', primary: true },
  { text: '了解功能', href: '/features', primary: false },
];

export default function Hero() {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 bg-gradient-mesh"></div>
      <div className="absolute inset-0 bg-pattern"></div>

      {/* 流动光晕效果 */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>

      <div ref={ref} className="container-custom relative z-10 pt-32 pb-20">
        <div className="max-w-4xl mx-auto text-center">
          {/* 标签 */}
          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 text-primary-600 text-sm font-medium mb-8 ${
              inView ? 'animate-fade-in' : 'opacity-0'
            }`}
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
            </span>
            AI 驱动的智能健康管家
          </div>

          {/* 主标题 */}
          <h1
            className={`text-display font-display text-text-primary mb-6 ${
              inView ? 'animate-slide-up' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.1s' }}
          >
            灵犀健康
            <span className="block text-gradient-teal mt-2">您的 24/7 AI 医生</span>
          </h1>

          {/* 副标题 */}
          <p
            className={`text-body-lg text-text-secondary max-w-2xl mx-auto mb-10 ${
              inView ? 'animate-slide-up' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.2s' }}
          >
            通过先进的 AI 技术，为您提供专业、便捷的健康咨询服务。
            多科室医生分身，智能健康分析，让健康管理触手可及。
          </p>

          {/* CTA 按钮 */}
          <div
            className={`flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 ${
              inView ? 'animate-slide-up' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.3s' }}
          >
            {ctaButtons.map((btn) => (
              <Link
                key={btn.text}
                to={btn.href}
                className={`btn ${btn.primary ? 'btn-primary' : 'btn-secondary'} group`}
              >
                {btn.text}
                <ArrowRight
                  size={18}
                  className="group-hover:translate-x-1 transition-transform duration-300"
                />
              </Link>
            ))}
            <button className="flex items-center gap-2 px-6 py-3 rounded-lg text-text-secondary hover:text-primary-500 transition-colors duration-300">
              <div className="w-10 h-10 rounded-full bg-primary-50 flex items-center justify-center">
                <Play size={18} className="text-primary-500 ml-0.5" />
              </div>
              观看演示
            </button>
          </div>

          {/* 统计数据 */}
          <div
            className={`grid grid-cols-3 gap-8 max-w-2xl mx-auto ${
              inView ? 'animate-slide-up' : 'opacity-0'
            }`}
            style={{ animationDelay: '0.4s' }}
          >
            {stats.map((stat, index) => (
              <div
                key={stat.label}
                className="text-center"
                style={{ animationDelay: `${0.4 + index * 0.1}s` }}
              >
                <div className="flex items-center justify-center gap-2 text-primary-500 mb-2">
                  <stat.icon size={20} />
                </div>
                <div className="text-3xl font-bold text-text-primary mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-text-secondary">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 底部渐变 */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent"></div>
    </section>
  );
}
