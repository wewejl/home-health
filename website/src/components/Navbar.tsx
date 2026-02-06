import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, HeartPulse } from 'lucide-react';

const navItems = [
  { name: '首页', path: '/' },
  { name: '产品功能', path: '/features' },
  { name: '使用场景', path: '/scenarios' },
  { name: '公司介绍', path: '/company' },
  { name: '关于我们', path: '/about' },
  { name: '下载应用', path: '/download' },
];

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location]);

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'glass shadow-md py-3'
            : 'bg-transparent py-5'
        }`}
      >
        <div className="container-custom">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
              <div className="relative">
                <div className="absolute inset-0 bg-primary-500/20 rounded-full blur-xl group-hover:bg-primary-500/30 transition-all duration-500"></div>
                <div className="relative bg-gradient-primary text-white p-2 rounded-xl">
                  <HeartPulse size={28} />
                </div>
              </div>
              <span className="text-xl font-semibold text-text-primary">
                灵犀<span className="text-primary-500">健康</span>
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-link font-medium ${
                    location.pathname === item.path
                      ? 'text-primary-500 after:w-full'
                      : ''
                  }`}
                >
                  {item.name}
                </Link>
              ))}
            </div>

            {/* CTA Button - Desktop */}
            <div className="hidden lg:block">
              <Link to="/download" className="btn btn-primary">
                立即体验
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-primary-50 transition-colors"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <div
        className={`fixed inset-0 z-40 lg:hidden mobile-menu ${
          isMobileMenuOpen ? 'open' : 'closed'
        }`}
      >
        <div className="absolute inset-0 bg-background/95 backdrop-blur-lg">
          <div className="container-custom pt-24 pb-8">
            <div className="flex flex-col gap-2">
              {navItems.map((item, index) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-3 rounded-lg text-lg font-medium transition-all duration-300 ${
                    location.pathname === item.path
                      ? 'bg-primary-500 text-white'
                      : 'hover:bg-primary-50'
                  }`}
                  style={{
                    animation: `slideUp 0.3s ease-out ${index * 0.05}s both`,
                  }}
                >
                  {item.name}
                </Link>
              ))}
            </div>
            <div className="mt-8 px-4">
              <Link to="/download" className="btn btn-primary w-full">
                立即体验
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
