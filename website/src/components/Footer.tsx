import { Link } from 'react-router-dom';
import {
  HeartPulse,
  Mail,
  Phone,
  MapPin,
  MessageCircle,
  Github,
  Twitter,
} from 'lucide-react';

const footerLinks = {
  product: {
    title: '产品',
    links: [
      { name: 'AI 智能咨询', path: '/features#ai' },
      { name: '医生分身', path: '/features#avatar' },
      { name: '健康档案', path: '/features#records' },
      { name: '语音交互', path: '/features#voice' },
    ],
  },
  scenarios: {
    title: '场景',
    links: [
      { name: '家庭健康', path: '/scenarios#family' },
      { name: '养老机构', path: '/scenarios#elderly' },
      { name: '医院辅助', path: '/scenarios#hospital' },
    ],
  },
  company: {
    title: '公司',
    links: [
      { name: '公司介绍', path: '/company' },
      { name: '关于我们', path: '/about' },
      { name: '联系我们', path: '/about#contact' },
      { name: '加入我们', path: '/about#careers' },
    ],
  },
  support: {
    title: '支持',
    links: [
      { name: '帮助中心', path: '/help' },
      { name: '隐私政策', path: '/privacy' },
      { name: '服务条款', path: '/terms' },
    ],
  },
};

const socialLinks = [
  { icon: MessageCircle, name: '微信', href: '#' },
  { icon: Github, name: 'GitHub', href: '#' },
  { icon: Twitter, name: 'Twitter', href: '#' },
];

const contactInfo = [
  { icon: Mail, value: '1024344053@qq.com', href: 'mailto:1024344053@qq.com' },
  { icon: Phone, value: '18107300167', href: 'tel:18107300167' },
  { icon: MapPin, value: '湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室', href: '#' },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-text-primary text-white">
      {/* 主要内容区 */}
      <div className="container-custom py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-12">
          {/* Logo 和简介 */}
          <div className="lg:col-span-2">
            <Link to="/" className="inline-flex items-center gap-2 mb-4">
              <div className="bg-gradient-primary text-white p-2 rounded-xl">
                <HeartPulse size={24} />
              </div>
              <span className="text-xl font-semibold">
                灵犀<span className="text-primary-400">健康</span>
              </span>
            </Link>
            <p className="text-text-muted mb-6 max-w-sm">
              灵犀健康由岳阳琳烨网络科技有限公司运营，致力于通过 AI 技术让每个人都能享受到专业、便捷的健康咨询服务。
            </p>
            {/* 社交链接 */}
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center hover:bg-primary-500 transition-colors duration-300"
                  aria-label={social.name}
                >
                  <social.icon size={18} />
                </a>
              ))}
            </div>
          </div>

          {/* 链接组 */}
          {Object.entries(footerLinks).map(([key, section]) => (
            <div key={key}>
              <h4 className="font-semibold mb-4">{section.title}</h4>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.path}>
                    <Link
                      to={link.path}
                      className="text-text-muted hover:text-primary-400 transition-colors duration-300"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* 联系方式 */}
        <div className="mt-12 pt-8 border-t border-white/10">
          <div className="flex flex-wrap items-center gap-6 text-sm text-text-muted">
            {contactInfo.map((info, index) => (
              <a
                key={index}
                href={info.href}
                className="flex items-center gap-2 hover:text-white transition-colors duration-300"
              >
                <info.icon size={16} />
                <span>{info.value}</span>
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* 版权信息 */}
      <div className="border-t border-white/10">
        <div className="container-custom py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-text-muted">
            <p>
              © {currentYear} 岳阳琳烨网络科技有限公司. 保留所有权利.
            </p>
            <p>
              湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
