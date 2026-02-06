import { useState } from 'react';
import {
  QrCode,
  Apple,
  Smartphone,
  Code,
  Mail,
  Building2,
  CheckCircle2,
  Copy,
  Check,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const features = [
  'AI 智能健康咨询',
  '多科室医生分身',
  '语音交互问诊',
  '健康档案管理',
  '用药提醒监督',
  '远程查房服务',
];

const apiFeatures = [
  { title: 'RESTful API', description: '标准化的 API 接口，轻松集成' },
  { title: 'SDK 支持', description: '提供多种语言 SDK，快速接入' },
  { title: 'Webhook 回调', description: '实时获取咨询结果更新' },
  { title: '详细文档', description: '完善的 API 文档和示例代码' },
];

export default function Download() {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-16 bg-gradient-soft">
          <div className="container-custom">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 text-primary-600 text-sm font-medium mb-6">
                下载应用
              </div>
              <h1 className="text-h1 mb-6">
                开启您的<span className="text-gradient-teal">智能健康</span>之旅
              </h1>
              <p className="text-body-lg text-text-secondary">
                立即下载灵犀健康 App，体验 AI 医生分身带来的便捷健康服务
              </p>
            </div>
          </div>
        </section>

        {/* App Download */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              {/* Left: Info */}
              <div>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-600 rounded-xl mb-6">
                  <Smartphone size={20} />
                  <span className="font-medium">iOS App</span>
                </div>
                <h2 className="text-h2 mb-6">下载灵犀健康 App</h2>
                <p className="text-body-lg text-text-secondary mb-8">
                  支持 iPhone 和 iPad，要求 iOS 15.0 或更高版本
                </p>

                {/* Features */}
                <ul className="space-y-4 mb-8">
                  {features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <CheckCircle2 size={20} className="text-success flex-shrink-0" />
                      <span className="text-body text-text-secondary">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* Download Button */}
                <a
                  href="https://apps.apple.com/app/lingxi-health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-4 px-6 py-4 bg-black text-white rounded-2xl hover:bg-gray-900 transition-all duration-300 hover:scale-105"
                >
                  <Apple size={32} />
                  <div className="text-left">
                    <div className="text-xs text-gray-400">Download on the</div>
                    <div className="text-xl font-semibold">App Store</div>
                  </div>
                </a>
              </div>

              {/* Right: QR Code */}
              <div className="flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-primary rounded-3xl blur-2xl opacity-20"></div>
                  <div className="relative bg-white rounded-3xl p-8 shadow-xl">
                    <div className="w-64 h-64 bg-gray-100 rounded-2xl flex items-center justify-center mb-6">
                      <QrCode size={200} className="text-primary-500" />
                    </div>
                    <p className="text-center text-text-secondary">
                      使用相机扫描二维码下载
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* API Access */}
        <section className="py-20 bg-background">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-600 rounded-xl mb-6">
                  <Code size={20} />
                  <span className="font-medium">API 接入</span>
                </div>
                <h2 className="text-h2 mb-4">开发者接入</h2>
                <p className="text-body-lg text-text-secondary">
                  提供 API 接口，方便开发者和企业快速集成灵犀健康的 AI 能力
                </p>
              </div>

              {/* API Features */}
              <div className="grid md:grid-cols-2 gap-6 mb-12">
                {apiFeatures.map((feature, i) => (
                  <div key={i} className="bg-white rounded-xl p-6 shadow-card">
                    <h3 className="font-semibold text-text-primary mb-2">{feature.title}</h3>
                    <p className="text-body text-text-secondary">{feature.description}</p>
                  </div>
                ))}
              </div>

              {/* API Code Example */}
              <div className="bg-text-primary rounded-2xl p-6 text-white overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-text-muted">API 示例</span>
                  <button
                    onClick={() => copyToClipboard('curl -X POST https://api.lingxi.health/v1/chat \\  -H "Authorization: Bearer YOUR_API_KEY" \\  -H "Content-Type: application/json" \\  -d \'{"message": "我最近头痛怎么办？"}\'')}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
                  >
                    {copied ? <Check size={16} /> : <Copy size={16} />}
                    {copied ? '已复制' : '复制'}
                  </button>
                </div>
                <pre className="text-sm overflow-x-auto">
                  <code className="text-text-muted">
{`curl -X POST https://api.lingxi.health/v1/chat \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "我最近头痛怎么办？"}'`}
                  </code>
                </pre>
              </div>

              <div className="text-center mt-8">
                <a
                  href="https://docs.lingxi.health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary"
                >
                  查看 API 文档
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Business Cooperation */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto">
              <div className="bg-gradient-to-br from-primary-500 to-teal-500 rounded-3xl p-12 text-white">
                <div className="text-center max-w-2xl mx-auto">
                  <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <Building2 size={32} />
                  </div>
                  <h2 className="text-h2 mb-4">商务合作</h2>
                  <p className="text-white/80 mb-8">
                    欢迎养老机构、医院、企业客户与我们洽谈合作，
                    共同打造更完善的健康服务生态
                  </p>

                  <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <a
                      href="mailto:business@lingxi.health"
                      className="flex items-center gap-3 px-6 py-4 bg-white text-primary-500 rounded-xl font-semibold hover:bg-white/90 transition-all duration-300"
                    >
                      <Mail size={20} />
                      business@lingxi.health
                    </a>
                    <a
                      href="tel:400-888-8888"
                      className="flex items-center gap-3 px-6 py-4 bg-white/10 text-white rounded-xl font-semibold hover:bg-white/20 transition-all duration-300 border border-white/20"
                    >
                      400-888-8888
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-20 bg-background">
          <div className="container-custom">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-12">
                <h2 className="text-h2 mb-4">常见问题</h2>
              </div>

              <div className="space-y-4">
                {[
                  {
                    q: 'App 是否免费？',
                    a: '基础功能免费使用，高级功能需要订阅会员服务。',
                  },
                  {
                    q: '支持哪些设备？',
                    a: '目前支持 iPhone 和 iPad（iOS 15.0+），Android 版本正在开发中。',
                  },
                  {
                    q: 'AI 咨询是否准确？',
                    a: '我们的 AI 系统基于专业医学知识库训练，但仅供参考，不能替代医生诊断。',
                  },
                  {
                    q: '如何保证隐私安全？',
                    a: '我们采用端到端加密技术，严格遵守医疗数据隐私保护法规。',
                  },
                ].map((faq, i) => (
                  <details
                    key={i}
                    className="group bg-white rounded-xl shadow-card overflow-hidden"
                  >
                    <summary className="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50 transition-colors">
                      <span className="font-medium text-text-primary">{faq.q}</span>
                      <span className="text-primary-500 transform group-open:rotate-180 transition-transform">
                        ▼
                      </span>
                    </summary>
                    <div className="px-6 pb-6 text-text-secondary">
                      {faq.a}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
