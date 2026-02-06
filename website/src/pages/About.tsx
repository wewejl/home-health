import { Link } from 'react-router-dom';
import {
  HeartPulse,
  Target,
  Eye,
  Mail,
  MapPin,
  ArrowRight,
  Calendar,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const values = [
  {
    icon: HeartPulse,
    title: '以人为本',
    description: '始终将用户健康和体验放在首位，用技术温暖人心。',
  },
  {
    icon: Target,
    title: '追求卓越',
    description: '不断迭代优化产品，提供最优质的健康服务体验。',
  },
  {
    icon: Eye,
    title: '诚实透明',
    description: '保护用户隐私，明确服务边界，建立可信赖的品牌形象。',
  },
];

const milestones = [
  { year: '2023', title: '项目启动', description: '灵犀健康项目正式立项，组建核心团队' },
  { year: '2024', title: '产品发布', description: 'iOS App 正式上线，开启智能健康服务' },
  { year: '2025', title: '功能拓展', description: '推出医生分身系统、远程查房等功能' },
  { year: '2026', title: '生态建设', description: '构建完整的健康管理生态体系' },
];

const team = [
  {
    name: '技术团队',
    description: '来自国内外顶尖科技公司的 AI 和医疗信息化专家',
    icon: '👨‍💻',
  },
  {
    name: '医疗团队',
    description: '拥有丰富临床经验的主任医师组成专家顾问团',
    icon: '👨‍⚕️',
  },
  {
    name: '运营团队',
    description: '深耕医疗健康行业多年的产品运营专家',
    icon: '👩‍💼',
  },
];

export default function About() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        {/* Hero Section */}
        <section className="pt-32 pb-16 bg-gradient-soft">
          <div className="container-custom">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-50 text-purple-600 text-sm font-medium mb-6">
                关于我们
              </div>
              <h1 className="text-h1 mb-6">
                用<span className="text-gradient-teal"> AI 技术</span> 守护健康
              </h1>
              <p className="text-body-lg text-text-secondary">
                灵犀健康致力于通过人工智能技术，让每个人都能享受到
                专业、便捷的健康咨询服务，让健康管理触手可及。
              </p>
            </div>
          </div>
        </section>

        {/* Mission */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-h2 mb-8">我们的使命</h2>
              <p className="text-body-lg text-text-secondary leading-relaxed mb-8">
                通过先进的 AI 技术，打破医疗资源分布不均的壁垒，
                让优质健康服务普惠每一个人，构建更健康的中国。
              </p>
              <div className="grid grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary-500 mb-2">100万+</div>
                  <div className="text-text-secondary">服务用户</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-teal-500 mb-2">24/7</div>
                  <div className="text-text-secondary">全天候服务</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-500 mb-2">99.9%</div>
                  <div className="text-text-secondary">用户满意度</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Values */}
        <section className="py-20 bg-background">
          <div className="container-custom">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-h2 mb-4">核心价值</h2>
              <p className="text-body text-text-secondary">
                我们的价值观指引着每一个决策和行动
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              {values.map((value) => (
                <div
                  key={value.title}
                  className="card-gradient text-center group hover:shadow-glow transition-all duration-500"
                >
                  <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center text-white mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                    <value.icon size={32} />
                  </div>
                  <h3 className="text-h4 mb-3 text-text-primary">{value.title}</h3>
                  <p className="text-body text-text-secondary">{value.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Timeline */}
        <section className="py-20 bg-white">
          <div className="container-custom">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-h2 mb-4">发展历程</h2>
              <p className="text-body text-text-secondary">
                从理念到现实，我们不断前行
              </p>
            </div>
            <div className="max-w-3xl mx-auto">
              <div className="relative">
                {/* Timeline Line */}
                <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary-500 to-teal-500"></div>

                {milestones.map((milestone) => (
                  <div key={milestone.year} className="relative flex gap-8 pb-12">
                    <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center text-white font-bold z-10 flex-shrink-0">
                      {milestone.year.slice(-2)}
                    </div>
                    <div className="flex-1 pt-2">
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 text-primary-600 rounded-full text-sm font-medium mb-2">
                        <Calendar size={14} />
                        {milestone.year}
                      </div>
                      <h3 className="text-h4 mb-2">{milestone.title}</h3>
                      <p className="text-body text-text-secondary">{milestone.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Team */}
        <section id="team" className="py-20 bg-background">
          <div className="container-custom">
            <div className="text-center max-w-2xl mx-auto mb-16">
              <h2 className="text-h2 mb-4">核心团队</h2>
              <p className="text-body text-text-secondary">
                汇聚行业顶尖人才，打造专业产品
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              {team.map((member) => (
                <div
                  key={member.name}
                  className="bg-white rounded-2xl p-8 text-center shadow-card hover:shadow-card-hover transition-all duration-300"
                >
                  <div className="text-6xl mb-4">{member.icon}</div>
                  <h3 className="text-h4 mb-3 text-text-primary">{member.name}</h3>
                  <p className="text-body text-text-secondary">{member.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Contact */}
        <section id="contact" className="py-20 bg-white">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto">
              <div className="bg-gradient-to-br from-primary-500 to-teal-500 rounded-3xl p-12 text-white text-center">
                <h2 className="text-h2 mb-4">加入我们</h2>
                <p className="text-white/80 mb-8 max-w-xl mx-auto">
                  我们正在寻找志同道合的伙伴，一起用 AI 技术改变健康服务
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-8">
                  <a
                    href="mailto:1024344053@qq.com"
                    className="flex items-center gap-3 px-6 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-all duration-300"
                  >
                    <Mail size={20} />
                    1024344053@qq.com
                  </a>
                  <div className="flex items-center gap-3 px-6 py-3 bg-white/10 rounded-xl">
                    <MapPin size={20} />
                    湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室
                  </div>
                </div>

                <Link
                  to="/download"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-500 rounded-xl font-semibold hover:bg-white/90 transition-all duration-300"
                >
                  查看开放职位
                  <ArrowRight size={20} />
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Business Contact */}
        <section id="business" className="py-20 bg-background">
          <div className="container-custom">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-h2 mb-4">商务合作</h2>
              <p className="text-body-lg text-text-secondary mb-8">
                欢迎养老机构、医院、企业客户与我们洽谈合作
              </p>
              <div className="inline-flex flex-col sm:flex-row items-center gap-6">
                <a
                  href="mailto:1024344053@qq.com"
                  className="btn btn-primary"
                >
                  <Mail size={20} />
                  1024344053@qq.com
                </a>
                <a href="tel:18107300167" className="flex items-center gap-2 text-text-secondary hover:text-primary-500 transition-colors">
                  18107300167
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
