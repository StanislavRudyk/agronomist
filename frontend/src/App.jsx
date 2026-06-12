import React, { useEffect, useState, useCallback } from 'react';
import {
  CloudRain,
  Tractor,
  Warehouse,
  Leaf,
  ArrowLeft,
  FileBarChart,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  User,
  Lock,
  Mail,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const TRANSLATIONS = {
  uk: {
    navLogin: "Вхід",
    navRegister: "Реєстрація",
    heroTitle: "Інтелект вашого поля",
    heroLead: "Платформа точного землеробства для тих, хто приймає рішення на основі даних. Метеорологія, техніка та складський облік в єдиній екосистемі.",
    btnOpen: "Відкрити платформу",
    btnFeatures: "Можливості",
    sections: [
      {
        id: "weather",
        badge: "01 // ПОГОДА",
        icon: <CloudRain size={28} className="card-icon" />,
        title: "Гіперлокальна погода",
        desc: "Забудьте про регіональні прогнози з точністю плюс-мінус 50 км. Наш алгоритм збирає дані з власних метеостанцій і супутників, аналізує 15+ параметрів атмосфери та будує прогноз окремо для кожного поля. Ви отримуєте точку роси, ймовірність приморозків, швидкість вітру та індекс ультрафіолету на 10 днів наперед.",
        extraDesc: "Система автоматично попереджає про ризики та блокує планові операції, якщо погодні умови є небезпечними, зберігаючи ваші ресурси та час. Наша метеомодель адаптується під мікроклімат вашого регіону з часом.",
        primaryBtn: "Підключити метеостанцію",
        secondaryBtn: "Дивитись карту опадів",
        video: "/14626085_3840_2160_25fps.mp4"
      },
      {
        id: "machinery",
        badge: "02 // ТЕХНІКА",
        icon: <Tractor size={28} className="card-icon" />,
        title: "Моніторинг техніки",
        desc: "Повний цифровий двійник вашого автопарку в режимі реального часу. Трактори, комбайни та обприскувачі передають телеметрію кожні 5 секунд: GPS-координати з точністю RTK, оберти двигуна, витрату пального та стан гідравліки.",
        extraDesc: "Система автоматично фіксує простої, перекриття при обробці поля та відхилення від заданого маршруту. Повний звіт по кожній операції формується без участі оператора, що гарантує 100% прозорість витрат.",
        primaryBtn: "Додати техніку",
        secondaryBtn: "Аналіз маршрутів",
        video: "/12093651_3840_2160_60fps.mp4"
      },
      {
        id: "warehouse",
        badge: "03 // СКЛАД",
        icon: <Warehouse size={28} className="card-icon" />,
        title: "Розумний склад",
        desc: "Від воріт елеватора до кожного гектара поля  повний ланцюг руху матеріалів під вашим контролем. Мережа IoT-датчиків цілодобово вимірює температуру та вологість у кожній комірці зерносховища.",
        extraDesc: "При перевищенні норми система миттєво надсилає сповіщення та пропонує план вентиляції. Залишки насіння, добрив та ЗЗР автоматично списуються при кожній польовій операції, уникаючи людського фактору.",
        primaryBtn: "Провести інвентаризацію",
        secondaryBtn: "Залишки на складах",
        video: "/12747865_1920_1080_60fps.mp4"
      },
      {
        id: "reports",
        badge: "04 // ЗВІТИ",
        icon: <FileBarChart size={28} className="card-icon" />,
        title: "Цифрова історія",
        desc: "Єдина хронологія всіх подій вашого господарства. Кожна обробка поля, кожна доза добрив та кожен намолот зберігаються автоматично і формують карту врожайності з прив'язкою до GPS.",
        extraDesc: "Звіти для банків, страхових компаній та держструктур генеруються в один клік. Застосунок повністю працює офлайн: всі дані синхронізуються при появі зв'язку, навіть якщо агроном весь день був у полі.",
        primaryBtn: "Згенерувати звіт",
        secondaryBtn: "Експорт даних",
        video: "/9130276-hd_1920_1080_25fps.mp4"
      }
    ],
    footerTitle: "Готові перейти на новий рівень?",
    footerLead: "Приєднуйтесь до лідерів агробізнесу сьогодні. Залиште рутину алгоритмам, а собі контроль та прибуток.",
    btnAccount: "Створити акаунт",
    rights: "Всі права захищені."
  },
  en: {
    navLogin: "Login",
    navRegister: "Sign Up",
    heroTitle: "Intelligence of your field",
    heroLead: "Precision farming platform for data-driven decisions. Meteorology, machinery and warehouse management in a single ecosystem.",
    btnOpen: "Open Platform",
    btnFeatures: "Features",
    sections: [
      {
        id: "weather",
        badge: "01 // WEATHER",
        icon: <CloudRain size={28} className="card-icon" />,
        title: "Hyperlocal Weather",
        desc: "Forget regional forecasts with 50 km accuracy gaps. Our algorithm collects data from proprietary weather stations and satellites, analyzing 15+ atmospheric parameters and building a separate forecast for each field.",
        extraDesc: "The system automatically warns of risks and blocks planned operations when weather conditions are dangerous, saving your resources and time. Our meteorological model adapts to your microclimate over time.",
        primaryBtn: "Connect weather station",
        secondaryBtn: "View precipitation map",
        video: "/14626085_3840_2160_25fps.mp4"
      },
      {
        id: "machinery",
        badge: "02 // MACHINERY",
        icon: <Tractor size={28} className="card-icon" />,
        title: "Machinery Monitoring",
        desc: "A complete real-time digital twin of your entire fleet. Tractors, combines and sprayers transmit telemetry every 5 seconds: RTK-accurate GPS coordinates, engine RPM, fuel consumption and hydraulics status.",
        extraDesc: "The system automatically detects idle time, field overlap during treatment and route deviations. A full report for each operation is generated without operator input, ensuring 100% cost transparency.",
        primaryBtn: "Add machinery",
        secondaryBtn: "Route analysis",
        video: "/12093651_3840_2160_60fps.mp4"
      },
      {
        id: "warehouse",
        badge: "03 // WAREHOUSE",
        icon: <Warehouse size={28} className="card-icon" />,
        title: "Smart Warehouse",
        desc: "From the elevator gate to every field hectare  complete material flow under your control. A network of IoT sensors monitors temperature and humidity in every grain bin cell around the clock.",
        extraDesc: "When thresholds are exceeded, the system instantly sends alerts and suggests a ventilation plan. Seeds, fertilizers and crop protection inventory is automatically written off with each field operation, preventing human error.",
        primaryBtn: "Run inventory",
        secondaryBtn: "Warehouse balance",
        video: "/12747865_1920_1080_60fps.mp4"
      },
      {
        id: "reports",
        badge: "04 // REPORTS",
        icon: <FileBarChart size={28} className="card-icon" />,
        title: "Digital History",
        desc: "A single timeline of all events across your farm. Every field treatment, every dose of fertilizer and every harvest yield is stored automatically and forms a GPS-linked yield map.",
        extraDesc: "Reports for banks, insurance companies and government agencies are generated in one click. The app works fully offline: all data syncs when connectivity returns, even if the agronomist spent the entire day in the field.",
        primaryBtn: "Generate report",
        secondaryBtn: "Export data",
        video: "/9130276-hd_1920_1080_25fps.mp4"
      }
    ],
    footerTitle: "Ready to step up?",
    footerLead: "Join agribusiness leaders today. Leave the routine to algorithms, keep control and profit for yourself.",
    btnAccount: "Create account",
    rights: "All rights reserved.",
    auth: {
      loginTitle: "Log In",
      registerTitle: "Create Account",
      loginSub: "Enter your details to access the platform",
      registerSub: "Get full control over your agribusiness",
      fullName: "Full Name",
      email: "Email",
      password: "Password",
      btnWait: "Please wait...",
      btnLogin: "Log In",
      btnRegister: "Sign Up",
      noAccount: "Don't have an account?",
      hasAccount: "Already have an account?",
      google: "Continue with Google",
      apple: "Continue with Apple",
      or: "OR",
      welcomeBack: "Welcome Back",
      startNow: "Start Right Now",
      brandDesc: "Precision farming platform. Meteorology, machinery and warehouse management in a single ecosystem."
    }
  }
};

TRANSLATIONS.uk.auth = {
  loginTitle: "Вхід в систему",
  registerTitle: "Створити акаунт",
  loginSub: "Введіть ваші дані для доступу до платформи",
  registerSub: "Отримайте повний контроль над вашим агробізнесом",
  fullName: "Ім'я і Прізвище",
  email: "Email",
  password: "Пароль",
  btnWait: "Зачекайте...",
  btnLogin: "Увійти",
  btnRegister: "Зареєструватись",
  noAccount: "Немає акаунту?",
  hasAccount: "Вже є акаунт?",
  google: "Продовжити з Google",
  apple: "Продовжити з Apple",
  or: "АБО",
  welcomeBack: "З поверненням",
  startNow: "Починайте прямо зараз",
  brandDesc: "Платформа точного землеробства. Метеорологія, техніка та складський облік в єдиній екосистемі."
};

function LandingPage() {
  const [lang, setLang] = useState('uk');
  const [activeIndex, setActiveIndex] = useState(0);
  const t = TRANSLATIONS[lang];
  const isLoggedIn = !!localStorage.getItem('access_token');

  // Animate on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            if (entry.target.dataset.index !== undefined) {
              setActiveIndex(Number(entry.target.dataset.index));
            }
          }
        });
      },
      { threshold: 0.5 }
    );
    document.querySelectorAll('.animate-on-scroll, .split-text-block').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [lang]);

  return (
    <div className="landing-container">

      {/* ── NAVBAR ── */}
      <nav className="top-nav">
        <div className="logo-area">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 17L12 22L22 17" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M2 12L12 17L22 12" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="logo-text">АГРОКОНТРОЛЬ</span>
        </div>
        <div className="nav-right">
          <div className="lang-switcher">
            <button onClick={() => setLang('uk')} className={lang === 'uk' ? 'lang-btn active' : 'lang-btn'}>UK</button>
            <span className="lang-sep">|</span>
            <button onClick={() => setLang('en')} className={lang === 'en' ? 'lang-btn active' : 'lang-btn'}>EN</button>
          </div>
          {isLoggedIn ? (
            <a href="/dashboard" className="btn btn-primary btn-sm">Дашборд</a>
          ) : (
            <>
              <a href="/login" className="btn btn-outline btn-sm">{t.navLogin}</a>
              <a href="/register" className="btn btn-primary btn-sm">{t.navRegister}</a>
            </>
          )}
        </div>
      </nav>

      <main className="content-wrapper">

        {/* ── HERO ── */}
        <section className="hero-section">
          <video autoPlay loop muted playsInline className="hero-bg-video" src="/hero-video.mp4" />
          <div className="hero-bg-overlay" />
          <div className="hero-content">
            <h1 className="massive-title">{t.heroTitle}</h1>
            <p className="hero-lead">{t.heroLead}</p>
            <div className="hero-actions">
              {isLoggedIn ? (
                <a href="/dashboard" className="btn btn-primary btn-large">Дашборд</a>
              ) : (
                <a href="/register" className="btn btn-primary btn-large">{t.btnOpen}</a>
              )}
              <a href="#features" className="btn btn-outline btn-large">{t.btnFeatures}</a>
            </div>
          </div>
        </section>

        {/* ── SPLIT-SCREEN FEATURES ── */}
        <section id="features" className="split-features-container">

          <div className="split-content-side">
            {t.sections.map((sec, index) => (
              <div key={sec.id} className="split-text-block" data-index={index}>
                <div className="split-icon-wrapper">{sec.icon}</div>
                <div className="split-badge">{sec.badge}</div>
                <h2 className="split-title">{sec.title}</h2>
                <p className="split-desc">{sec.desc}</p>
                <p className="split-desc" style={{ marginTop: '1rem', color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>
                  {sec.extraDesc}
                </p>
                <div className="split-actions" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <a href="/register" className="btn btn-primary">{sec.primaryBtn}</a>
                  <a href="/login" className="btn-text-link">{sec.secondaryBtn} &rarr;</a>
                </div>
              </div>
            ))}
          </div>

          <div className="split-video-side">
            <div className="split-video-sticky">
              {t.sections.map((sec, index) => (
                <video
                  key={sec.id}
                  autoPlay loop muted playsInline
                  className={`split-video${activeIndex === index ? ' active' : ''}`}
                  src={sec.video}
                />
              ))}
              <div className="split-video-overlay" />
            </div>
          </div>

        </section>

        {/* ── FOOTER ── */}
        <section className="footer-cta">
          <div className="animate-on-scroll footer-cta-inner">
            <h2 className="massive-title footer-cta-title">{t.footerTitle}</h2>
            <p className="hero-lead footer-cta-lead">{t.footerLead}</p>
            {isLoggedIn ? (
              <a href="/dashboard" className="btn btn-primary btn-large footer-cta-btn">Дашборд</a>
            ) : (
              <a href="/register" className="btn btn-primary btn-large footer-cta-btn">{t.btnAccount}</a>
            )}
            <p className="copyright">&copy; {new Date().getFullYear()}  АГРОКОНТРОЛЬ. {t.rights}</p>
          </div>
        </section>

      </main>
    </div>
  );
}



// ─── Password Strength Helper ────────────────────────────────────
function getPasswordStrength(pwd) {
  let score = 0;
  const checks = {
    length: pwd.length >= 8,
    upper: /[A-Z]/.test(pwd),
    lower: /[a-z]/.test(pwd),
    digit: /\d/.test(pwd),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(pwd),
  };
  score = Object.values(checks).filter(Boolean).length;
  if (score <= 2) return { level: 'weak', label: 'Слабкий', color: '#ef4444', width: '25%' };
  if (score === 3) return { level: 'fair', label: 'Середній', color: '#f59e0b', width: '50%' };
  if (score === 4) return { level: 'good', label: 'Хороший', color: '#3b82f6', width: '75%' };
  return { level: 'strong', label: 'Сильний', color: '#22c55e', width: '100%' };
}

// ─── Auth Page Component ─────────────────────────────────────────
function AuthPage({ isLogin }) {
  const [lang, setLang] = useState('uk');
  const t = TRANSLATIONS[lang].auth;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const pwdStrength = !isLogin && password.length > 0 ? getPasswordStrength(password) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (isLogin) {
        const res = await fetch(`${API_BASE}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Помилка входу');
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        setSuccess('Вхід успішний! Переходимо...');
        setTimeout(() => {
          window.history.pushState({}, '', '/dashboard');
          window.dispatchEvent(new PopStateEvent('popstate'));
        }, 800);
      } else {
        const res = await fetch(`${API_BASE}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
          const msg = Array.isArray(data.detail)
            ? data.detail.map(e => e.msg).join('; ')
            : (data.detail || 'Помилка реєстрації');
          throw new Error(msg);
        }
        setSuccess('Акаунт створено! Переходимо до входу...');
        setTimeout(() => {
          window.history.pushState({}, '', '/login');
          window.dispatchEvent(new PopStateEvent('popstate'));
        }, 1200);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="premium-site auth-page">
      <div className="global-bg-container">
        <video className="global-bg-video" autoPlay muted loop playsInline>
          <source src="/15684083_3840_2160_60fps.mp4" type="video/mp4" />
        </video>
        <div className="global-bg-overlay auth-video-overlay"></div>
      </div>

      <a href="/" className="auth-back">
        <ArrowLeft size={18} />
        <span>На головну</span>
      </a>

      <div className="auth-wrapper">
        {/* Left brand panel */}
        <div className="auth-brand-panel">
          <div className="auth-brand-logo">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="auth-brand-name"> АГРОКОНТРОЛЬ</span>
          </div>
          <h1 className="auth-brand-title">
            {isLogin ? t.welcomeBack : t.startNow}
          </h1>
          <p className="auth-brand-desc" style={{ maxWidth: '400px' }}>
            {t.brandDesc}
          </p>
        </div>

        {/* Right form panel */}
        <div className="auth-form-panel glass-card">
          <div className="auth-form-header">
            <h2 className="auth-form-title">
              {isLogin ? t.loginTitle : t.registerTitle}
            </h2>
            <p className="auth-form-subtitle">
              {isLogin ? t.loginSub : t.registerSub}
            </p>
          </div>

          <div className="auth-social-buttons" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
            <button
              type="button"
              onClick={() => {
                window.location.href = `${API_BASE}/auth/google/login`;
              }}
              className="btn btn-outline"
              style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#fff" d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z" /></svg>
              {t.google}
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', color: 'rgba(255,255,255,0.2)', fontSize: '0.8rem', fontWeight: 600 }}>
            <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
            {t.or}
            <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }} />
          </div>

          {error && (
            <div className="auth-alert auth-alert-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="auth-alert auth-alert-success">
              <CheckCircle size={16} />
              <span>{success}</span>
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            {!isLogin && (
              <div className="auth-field">
                <label className="auth-label">{t.fullName}</label>
                <div className="auth-input-wrap">
                  <User size={16} className="auth-input-icon" />
                  <input
                    id="auth-fullname"
                    type="text"
                    className="auth-input"
                    placeholder="Іван Петренко"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <div className="auth-field">
              <label className="auth-label">{t.email}</label>
              <div className="auth-input-wrap">
                <Mail size={16} className="auth-input-icon" />
                <input
                  id="auth-email"
                  type="email"
                  className="auth-input"
                  placeholder="agro@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-label">{t.password}</label>
              <div className="auth-input-wrap">
                <Lock size={16} className="auth-input-icon" />
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder={isLogin ? '••••••••' : 'Мін. 8 символів, A-z, 0-9, !@#'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="auth-pwd-toggle"
                  onClick={() => setShowPassword(v => !v)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Сховати пароль' : 'Показати пароль'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {pwdStrength && (
                <div className="pwd-strength">
                  <div className="pwd-strength-bar">
                    <div
                      className="pwd-strength-fill"
                      style={{ width: pwdStrength.width, background: pwdStrength.color }}
                    />
                  </div>
                  <span className="pwd-strength-label" style={{ color: pwdStrength.color }}>
                    {pwdStrength.label}
                  </span>
                </div>
              )}
            </div>

            <button
              id="auth-submit-btn"
              type="submit"
              className="btn btn-primary auth-submit"
              disabled={loading}
            >
              {loading
                ? <><Loader2 size={18} className="spin" /> {t.btnWait}</>
                : (isLogin ? t.btnLogin : t.btnRegister)}
            </button>
          </form>

          <div className="auth-links">
            {isLogin ? (
              <>{t.noAccount} <a href="/register">{t.btnRegister}</a></>
            ) : (
              <>{t.hasAccount} <a href="/login">{t.btnLogin}</a></>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main App Router ─────────────────────────────────────────────
export default function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);

    const handleClick = (e) => {
      const target = e.target.closest('a');
      if (target && target.getAttribute('href')?.startsWith('/')) {
        const href = target.getAttribute('href');
        if (href.startsWith('#')) {
          e.preventDefault();
          document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
          return;
        }

        e.preventDefault();
        window.history.pushState({}, '', href);
        setCurrentPath(href);
        window.scrollTo(0, 0);
      }
    };
    document.addEventListener('click', handleClick);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      document.removeEventListener('click', handleClick);
    };
  }, []);

  if (currentPath === '/login') return <AuthPage isLogin={true} />;
  if (currentPath === '/register') return <AuthPage isLogin={false} />;


  return <LandingPage />;
}
