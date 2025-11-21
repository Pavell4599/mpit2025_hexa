/* ======= Particles (lightweight) ======= */
const canvas = document.getElementById('particles');
const ctx = canvas.getContext('2d');
let W = canvas.width = innerWidth;
let H = canvas.height = innerHeight;
let particles = [];

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

class P {
  constructor() {
    this.x = rand(0, W);
    this.y = rand(0, H);
    this.r = rand(0.6, 2.2);
    this.ax = rand(-0.3, 0.3);
    this.ay = rand(-0.3, 0.3);
    this.alpha = rand(0.06, 0.28);
  }

  step() {
    this.x += this.ax;
    this.y += this.ay;
    if (this.x < 0 || this.x > W) this.ax *= -1;
    if (this.y < 0 || this.y > H) this.ay *= -1;
  }

  draw() {
    ctx.beginPath();
    ctx.fillStyle = 'rgba(255,255,255,' + this.alpha + ')';
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function init() {
  particles = [];
  for (let i = 0; i < 110; i++) particles.push(new P());
}

function loop() {
  ctx.clearRect(0, 0, W, H);
  particles.forEach(p => {
    p.step();
    p.draw();
  });
  requestAnimationFrame(loop);
}

init();
loop();

onresize = () => {
  W = canvas.width = innerWidth;
  H = canvas.height = innerHeight;
  init();
};

/* reveal hero text on load */
window.addEventListener('load', () => {
  document.querySelectorAll('.hero-text > *').forEach((el, i) => {
    el.style.opacity = 0;
    el.style.transform = 'translateY(8px)';
    setTimeout(() => {
      el.style.transition = 'opacity .45s, transform .45s';
      el.style.opacity = 1;
      el.style.transform = 'translateY(0)';
    }, 160 * i);
  });
});

/* ======= DESKTOP DROPDOWNS ======= */
document.querySelectorAll('.nav-item .nav-trigger').forEach(btn => {
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const item = btn.closest('.nav-item');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.nav-item.open').forEach(i => i.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

document.addEventListener('click', () => {
  document.querySelectorAll('.nav-item.open').forEach(i => i.classList.remove('open'));
});

/* ======= BURGER / MOBILE PANEL ======= */
const burger = document.getElementById('burger');
const mobilePanel = document.getElementById('mobilePanel');

function toggleBurger() {
  burger.classList.toggle('open');
  mobilePanel.classList.toggle('active');
}

burger.addEventListener('click', (e) => {
  e.stopPropagation();
  toggleBurger();
});

// закрывать при клике вне меню
document.addEventListener('click', (e) => {
  if (mobilePanel.classList.contains('active')
    && !mobilePanel.contains(e.target)
    && !burger.contains(e.target)) {
    burger.classList.remove('open');
    mobilePanel.classList.remove('active');
  }
});

// закрывать при выборе пункта
mobilePanel.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    burger.classList.remove('open');
    mobilePanel.classList.remove('active');
  });
});

// Esc закрывает всё
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.nav-item.open').forEach(i => i.classList.remove('open'));
    burger.classList.remove('open');
    mobilePanel.classList.remove('active');
  }
});

/* ======= ANIMATION FOR CARDS USING INTERSECTION OBSERVER ======= */

// Настройки для IntersectionObserver
const options = {
  threshold: 0.5, // Появление карточки, когда она на 50% видна
};

// Создаем наблюдатель
const observer = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible'); // Добавляем класс видимости
      observer.unobserve(entry.target); // Останавливаем отслеживание после появления
    }
  });
}, options);

// Добавляем наблюдатель для всех карточек
document.querySelectorAll('.features .card').forEach(card => {
  observer.observe(card);
});

/* ======= DOWNLOAD PDF AND CSV ======= */
