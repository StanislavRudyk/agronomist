import React, { useEffect, useRef, useState } from 'react';
import { CloudRain, MapPin, Truck, Package, ArrowRight, Play, Leaf, BarChart3, Thermometer, Bell, Droplets, Sun, AlertTriangle } from 'lucide-react';

function useScrollReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
      { threshold: 0.15 }
    );
    if (ref.current) ref.current.querySelectorAll('.reveal').forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
  return ref;
}

function AnimatedCounter({ end, suffix = '' }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = end / 60;
        const timer = setInterval(() => {
          start += step;
          if (start >= end) { setCount(end); clearInterval(timer); }
          else setCount(Math.floor(start));
        }, 16);
        obs.disconnect();
      }
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [end]);
  return <span ref={ref} className="stat-num">{count}{suffix}</span>;
}

function MouseGlowCard({ children, className }) {
  const cardRef = useRef(null);
  const glowRef = useRef(null);
  const handleMove = (e) => {
    if (!cardRef.current || !glowRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    glowRef.current.style.left = (e.clientX - rect.left) + 'px';
    glowRef.current.style.top = (e.clientY - rect.top) + 'px';
  };
  return (
    <div className={`bento-card ${className}`} ref={cardRef} onMouseMove={handleMove}>
      <div className="mouse-glow" ref={glowRef}></div>
      {children}
    </div>
  );
}

const FEED_DATA = [
  { icon: 'green', Icon: Thermometer, text: 'Температура в норме', sub: 'Поле "Южное" — 22°C' },
  { icon: 'amber', Icon: AlertTriangle, text: 'Возможен дождь через 6ч', sub: 'Рекомендация: отложить опрыскивание' },
  { icon: 'blue', Icon: Truck, text: 'Трактор JD-8400 — ТО пройдено', sub: 'Следующее ТО через 200 моточасов' },
  { icon: 'green', Icon: Droplets, text: 'Влажность почвы: 68%', sub: 'Поле "Центральное" — оптимально' },
  { icon: 'red', Icon: AlertTriangle, text: 'Запасы NPK ниже 40%', sub: 'Склад №2 — требуется пополнение' },
  { icon: 'green', Icon: Sun, text: 'Прогноз: ясно 3 дня', sub: 'Идеальные условия для уборки' },
  { icon: 'blue', Icon: Bell, text: 'Новый отчёт готов', sub: 'Аналитика за июнь 2026' },
];

function LiveFeed() {
  const [feed, setFeed] = useState([
    { ...FEED_DATA[0], time: '1 мин назад' },
    { ...FEED_DATA[1], time: '3 мин назад' },
    { ...FEED_DATA[2], time: '7 мин назад' },
    { ...FEED_DATA[3], time: '12 мин назад' }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setFeed((prev) => {
        const randomEvent = FEED_DATA[Math.floor(Math.random() * FEED_DATA.length)];
        const newEvent = { ...randomEvent, time: 'Только что' };
        
        // Push older ones down
        const updatedPrev = prev.map(item => {
          if (item.time === 'Только что') return { ...item, time: '1 мин назад' };
          if (item.time.includes('мин')) {
            const mins = parseInt(item.time) + 1;
            return { ...item, time: `${mins} мин назад` };
          }
          return item;
        });

        return [newEvent, ...updatedPrev].slice(0, 4);
      });
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="feed-list">
      {feed.map((item, i) => (
        <div key={i} className="feed-item" style={{ animation: 'slideIn 0.4s ease both' }}>
          <div className={`feed-icon fi-${item.icon}`}><item.Icon size={18} /></div>
          <div className="feed-info">
            <p>{item.text}</p>
            <span>{item.sub} · {item.time}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RoiCalculator() {
  const [area, setArea] = useState(250);
  const [yieldVal, setYieldVal] = useState(4.5);

  const fuelSaved = area * 12; // 12 liters per hectare
  const extraYield = (area * yieldVal * 0.085).toFixed(1); // 8.5% yield increase
  const extraProfit = Math.floor(Number(extraYield) * 280); // $280 per ton of crop avg

  return (
    <section className="calculator-section reveal">
      <div className="section-label" style={{ display: 'block', width: 'fit-content', margin: '0 auto 16px' }}>Калькулятор ROI</div>
      <h2 className="section-title" style={{ textAlign: 'center', marginBottom: '16px' }}>Рассчитайте выгоду внедрения</h2>
      <p className="section-desc" style={{ textAlign: 'center', margin: '0 auto 60px' }}>Узнайте, сколько ресурсов сэкономит и сколько дополнительной прибыли принесет ваша ферма с технологиями Agronomist.</p>

      <div className="calc-container">
        <div className="calc-inputs">
          <div className="input-group">
            <label>Площадь полей: <span>{area} га</span></label>
            <input 
              type="range" 
              min="10" 
              max="5000" 
              step="10"
              value={area} 
              onChange={(e) => setArea(Number(e.target.value))} 
              className="input-range"
            />
          </div>
          <div className="input-group">
            <label>Средняя урожайность: <span>{yieldVal} т/га</span></label>
            <input 
              type="range" 
              min="1.0" 
              max="15.0" 
              step="0.1"
              value={yieldVal} 
              onChange={(e) => setYieldVal(Number(e.target.value))} 
              className="input-range"
            />
          </div>
        </div>

        <div className="calc-results">
          <div className="result-card">
            <div className="result-info">
              <h4>Экономия топлива</h4>
              <p><span>{fuelSaved.toLocaleString()}</span> л/год</p>
            </div>
            <div className="result-badge">-${Math.floor(fuelSaved * 1.3).toLocaleString()}</div>
          </div>
          <div className="result-card">
            <div className="result-info">
              <h4>Прибавка к урожаю</h4>
              <p><span>+{extraYield}</span> тонн</p>
            </div>
            <div className="result-badge">+8.5% КПД</div>
          </div>
          <div className="result-card" style={{ borderColor: 'var(--g4)' }}>
            <div className="result-info">
              <h4>Чистая доп. прибыль</h4>
              <p><span style={{ color: 'var(--g4)', background: 'none', WebkitTextFillColor: 'initial' }}>+${extraProfit.toLocaleString()}</span> / год</p>
            </div>
            <div className="result-badge" style={{ background: 'var(--g4)', color: '#000' }}>ROI 340%</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function App() {
  const mainRef = useScrollReveal();
  const particles = Array.from({ length: 30 }, (_, i) => ({
    left: Math.random() * 100,
    delay: Math.random() * 8,
    duration: 6 + Math.random() * 6,
    size: 1 + Math.random() * 2,
  }));

  return (
    <div ref={mainRef}>
      <nav className="navbar">
        <div className="nav-logo">
          <div className="logo-icon"><Leaf size={18} color="#fff" /></div>
          Agronomist
        </div>
        <ul className="nav-links">
          <li><a href="#features">Модули</a></li>
          <li><a href="#live">Мониторинг</a></li>
          <li><a href="#how">Как работает</a></li>
        </ul>
        <button className="nav-cta">Войти в систему</button>
      </nav>

      <section className="hero">
        <div className="hero-video-bg">
          <video autoPlay loop muted playsInline>
            <source src="/hero-video.mp4" type="video/mp4" />
          </video>
        </div>
        <div className="hero-gradient"></div>
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
        <div className="particles">
          {particles.map((p, i) => (
            <div key={i} className="particle" style={{
              left: p.left + '%',
              width: p.size + 'px', height: p.size + 'px',
              animationDelay: p.delay + 's',
              animationDuration: p.duration + 's',
            }} />
          ))}
        </div>
        <div className="hero-inner">
          <div className="hero-badge"><span className="pulse-dot"></span> Платформа нового поколения</div>
          <h1>Полный контроль<br />над <span className="gradient-text">агробизнесом</span></h1>
          <p className="hero-desc">Единая система управления: погода, поля, техника и склады. Принимайте решения на основе данных, а не интуиции.</p>
          <div className="hero-buttons">
            <button className="btn-main">Начать бесплатно <ArrowRight size={18} /></button>
            <button className="btn-ghost"><Play size={18} /> Смотреть демо</button>
          </div>
        </div>
        <div className="hero-float left">
          <div className="float-icon green"><Thermometer size={20} /></div>
          <div className="float-text"><p>AgroAnalyzer</p><span>Риск заморозков: 0%</span></div>
        </div>
        <div className="hero-float right">
          <div className="float-icon amber"><BarChart3 size={20} /></div>
          <div className="float-text"><p>Урожайность</p><span>+12% к прогнозу</span></div>
        </div>
      </section>

      <div className="stats-bar">
        <div className="stat-item"><AnimatedCounter end={50} suffix="K+" /><div className="stat-label">Гектаров под контролем</div></div>
        <div className="stat-item"><AnimatedCounter end={99} suffix=".9%" /><div className="stat-label">Uptime системы</div></div>
        <div className="stat-item"><span className="stat-num">24/7</span><div className="stat-label">Мониторинг реального времени</div></div>
        <div className="stat-item"><AnimatedCounter end={30} suffix="%" /><div className="stat-label">Снижение затрат на ГСМ</div></div>
      </div>

      <section className="features" id="features">
        <div className="reveal"><div className="section-label">Модули</div></div>
        <h2 className="section-title reveal reveal-delay-1">Всё что нужно.<br />В одном месте.</h2>
        <p className="section-desc reveal reveal-delay-2">Четыре мощных модуля, которые покрывают каждый аспект управления сельскохозяйственным предприятием.</p>

        <div className="bento">
          <MouseGlowCard className="span-7 reveal reveal-delay-1">
            <div className="card-icon"><CloudRain size={24} /></div>
            <h3>Погода и AgroAnalyzer</h3>
            <p>Высокоточный прогноз Open-Meteo с AI-анализом рисков. Заморозки, засуха, осадки — система предупредит заранее.</p>
            <div className="card-visual">
              <div className="mini-chart">
                {[35,55,45,25,70,60,80,50,90,65,40,75].map((h,i) => (
                  <div key={i} className={`cbar${h===25?' danger':''}`} style={{height:h+'%'}} />
                ))}
              </div>
            </div>
          </MouseGlowCard>

          <MouseGlowCard className="span-5 reveal reveal-delay-2">
            <div className="card-icon"><MapPin size={24} /></div>
            <h3>Управление полями</h3>
            <p>Кадастр, севооборот и геозоны.</p>
            <div className="card-visual">
              <div className="dot-map">
                <div className="map-dot d1"></div>
                <div className="map-dot d2"></div>
                <div className="map-dot d3"></div>
                <div className="map-dot d4"></div>
                <div className="map-label l1">Пшеница — 120 га</div>
                <div className="map-label l2">Кукуруза — 85 га</div>
                <div className="map-label l3">Подсолнух — 60 га</div>
              </div>
            </div>
          </MouseGlowCard>

          <MouseGlowCard className="span-5b reveal reveal-delay-3">
            <div className="card-icon"><Truck size={24} /></div>
            <h3>Техника</h3>
            <p>Контроль моточасов, ТО и статуса каждой единицы в парке.</p>
            <div className="card-visual">
              <div className="gauge-wrap">
                <div className="gauge"><span>70%</span></div>
                <div className="gauge-stats">
                  <div className="gauge-stat"><div className="gauge-dot" style={{background:'var(--g4)'}}></div>Активно <b>14</b></div>
                  <div className="gauge-stat"><div className="gauge-dot" style={{background:'#f59e0b'}}></div>На ТО <b>4</b></div>
                  <div className="gauge-stat"><div className="gauge-dot" style={{background:'#ef4444'}}></div>Простой <b>2</b></div>
                </div>
              </div>
            </div>
          </MouseGlowCard>

          <MouseGlowCard className="span-7b reveal reveal-delay-4">
            <div className="card-icon"><Package size={24} /></div>
            <h3>Склады и Учёт</h3>
            <p>Многоуровневый складской учёт: партии, сроки, семена, удобрения и ГСМ.</p>
            <div className="card-visual">
              <div className="progress-list">
                <div className="progress-item"><label><span>Семена (пшеница)</span><span>85%</span></label><div className="progress-track"><div className="progress-fill green" style={{width:'85%'}}></div></div></div>
                <div className="progress-item"><label><span>Удобрения NPK</span><span>42%</span></label><div className="progress-track"><div className="progress-fill amber" style={{width:'42%'}}></div></div></div>
                <div className="progress-item"><label><span>ГСМ (Дизель)</span><span>67%</span></label><div className="progress-track"><div className="progress-fill green" style={{width:'67%'}}></div></div></div>
                <div className="progress-item"><label><span>Гербициды</span><span>18%</span></label><div className="progress-track"><div className="progress-fill red" style={{width:'18%'}}></div></div></div>
              </div>
            </div>
          </MouseGlowCard>
        </div>
      </section>

      <section className="live-section" id="live">
        <div className="live-container">
          <div className="live-text">
            <div className="reveal"><div className="section-label">Мониторинг</div></div>
            <h2 className="section-title reveal reveal-delay-1">Всё происходит<br />прямо сейчас</h2>
            <p className="section-desc reveal reveal-delay-2">Система собирает данные 24/7. Каждое изменение температуры, каждый выезд техники, каждое движение на складе — всё фиксируется и анализируется в реальном времени.</p>
          </div>
          <div className="live-feed reveal reveal-delay-3">
            <div className="feed-header"><span className="live-dot"></span> Live Feed</div>
            <LiveFeed />
          </div>
        </div>
      </section>

      <RoiCalculator />

      <section className="how-section" id="how">
        <div className="how-inner">
          <div className="reveal"><div className="section-label">Процесс</div></div>
          <h2 className="section-title reveal reveal-delay-1">Три шага к результату</h2>
          <p className="section-desc reveal reveal-delay-2" style={{marginLeft:'auto',marginRight:'auto'}}>От регистрации до полного контроля — за один рабочий день.</p>
          <div className="steps">
            <div className="step reveal reveal-delay-1"><div className="step-num">01</div><h3>Подключите данные</h3><p>Добавьте ваши поля, технику и склады. Импорт из Excel или ручной ввод.</p></div>
            <div className="step reveal reveal-delay-2"><div className="step-num">02</div><h3>Настройте аналитику</h3><p>AgroAnalyzer привяжет прогноз к каждому полю и начнёт анализ рисков автоматически.</p></div>
            <div className="step reveal reveal-delay-3"><div className="step-num">03</div><h3>Управляйте и растите</h3><p>Получайте уведомления, оптимизируйте расходы, увеличивайте урожайность.</p></div>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-box reveal">
          <h2>Готовы к точному<br />земледелию?</h2>
          <p>Присоединяйтесь к фермерам, которые уже управляют тысячами гектаров с помощью Agronomist.</p>
          <button className="btn-main">Начать бесплатно <ArrowRight size={18} /></button>
        </div>
      </section>

      <footer className="site-footer">
        <div className="footer-grid">
          <div className="footer-brand"><h3>Agronomist 2.0</h3><p>Интеллектуальная платформа для управления сельскохозяйственным предприятием.</p></div>
          <div className="footer-col"><h4>Продукт</h4><a href="#">Погода</a><a href="#">Поля</a><a href="#">Техника</a><a href="#">Склады</a></div>
          <div className="footer-col"><h4>Компания</h4><a href="#">О нас</a><a href="#">Документация</a><a href="#">API</a></div>
          <div className="footer-col"><h4>Поддержка</h4><a href="#">Telegram</a><a href="#">Email</a><a href="#">FAQ</a></div>
        </div>
        <div className="footer-bottom"><span>© 2026 Agronomist. Все права защищены.</span><span>Сделано с ❤️ для агробизнеса</span></div>
      </footer>
    </div>
  );
}

export default App;
