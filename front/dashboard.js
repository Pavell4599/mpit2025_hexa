const results = document.getElementById('results');
const searchInput = document.getElementById('searchInput');
const sidebar = document.getElementById('sidebar');
const menuToggle = document.querySelector('.menu-toggle');

let currentFilter = 'all';

function render(list) {
  if (!list || list.length === 0) {
    results.innerHTML = '<p style="text-align:center;color:#aaa;padding:80px;font-size:18px">Ничего не найдено</p>';
    return;
  }
  results.innerHTML = list.map(c => `
    <div class="card">
      <h3>${c.name}</h3>
      <p>ИНН: ${c.inn} • ${c.city}</p>
      <p>Выручка 2024: ${c.revenue} • ${c.employees} чел.</p>
      <span class="tag ${c.accredited ? 'acc' : 'no'}">
        ${c.accredited ? 'Аккредитована' : 'Не аккредитована'}
      </span>
    </div>
  `).join('');
}

function parseRevenue(str) {
  const num = parseFloat(str.replace(/[^\d.]/g, ''));
  return str.includes('млрд') ? num * 1000 : num;
}

function updateStats() {
  const total = companies.length;
  const accredited = companies.filter(c => c.accredited).length;
  const revenue = companies.reduce((s, c) => s + parseRevenue(c.revenue), 0);
  const employees = companies.reduce((s, c) => s + c.employees, 0);

  document.getElementById('totalCompanies').textContent = total;
  document.getElementById('accreditedCount').textContent = accredited;
  document.getElementById('totalRevenue').textContent = revenue >= 1000 
    ? (revenue/1000).toFixed(1) + ' млрд ₽' 
    : revenue.toFixed(0) + ' млн ₽';
  document.getElementById('totalEmployees').textContent = employees > 999 ? (employees/1000).toFixed(1)+' тыс.' : employees;

  document.getElementById('countAll').textContent = total + ' компаний';
  document.getElementById('countAcc').textContent = accredited + ' компаний';
  document.getElementById('countNo').textContent = (total - accredited) + ' компаний';
}

function applyFilter() {
  let filtered = companies;
  if (currentFilter === 'acc') filtered = filtered.filter(c => c.accredited);
  if (currentFilter === 'no') filtered = filtered.filter(c => !c.accredited);

  const term = searchInput.value.trim().toLowerCase();
  if (term) {
    filtered = filtered.filter(c =>
      c.name.toLowerCase().includes(term) ||
      c.inn.includes(term) ||
      c.city.toLowerCase().includes(term)
    );
  }
  render(filtered);
}

document.addEventListener('DOMContentLoaded', () => {
  updateStats();
  render(companies); // ← ВОТ ЭТО ВЕРНУЛО ТВОИ КОМПАНИИ СРАЗУ!

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      applyFilter();
      sidebar.classList.remove('open');
    });
  });

  searchInput.addEventListener('input', applyFilter);

  menuToggle.addEventListener('click', e => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
  });

  document.querySelector('.close-sidebar').addEventListener('click', () => {
    sidebar.classList.remove('open');
  });

  document.addEventListener('click', e => {
    if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuToggle) {
      sidebar.classList.remove('open');
    }
  });
});