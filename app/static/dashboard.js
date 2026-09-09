// CONFIG_TOKEN: 서버에서 주입된 인증 토큰
const CONFIG_TOKEN = window.__CONFIG_TOKEN__ || "";

function authHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (CONFIG_TOKEN) headers["Authorization"] = "Bearer " + CONFIG_TOKEN;
    return headers;
}

// 현재 페이지, 페이지당 갯수
let currentPage = 1;
const perPage = 10;
let allReviews = [];
let currentRepo = '';

// 차트 인스턴스
let reviewChartInstance = null;
let categoryChartInstance = null;

// 대시보드 테마
let lastCategories = {};
let lastRepoCounts = {};
const themeToggle = document.getElementById('themeToggle');

// BASE_URL 선언
// Railway, 로컬 양쪽에 대응
const BASE_URL = window.location.origin;

// fetch('/dashboard')
/* Railway 배포용 절대경로 API */
function loadDashboard(page = 1) {
    /* Railway 배포용 절대경로 API */
    fetch(`${BASE_URL}/dashboard?page=${page}&per_page=${perPage}&repo=${encodeURIComponent(currentRepo)}`)
        .then(res => {
            if (!res.ok) throw new Error("서버 오류");
            return res.json();
        })
        .then(data => {
            lastCategories = data.categories;
            lastRepoCounts = data.repo_counts;
            const reviews = data.reviews;
            const categories = data.categories;
            const modal = document.getElementById('modal');
            allReviews = reviews;

            /* 통계 카드 채우기 (첫 페이지에서만) */
            if (page === 1) {
                document.getElementById('totalReviews').textContent = data.total;
                document.getElementById('totalBugs').textContent = categories['bug'] || 0;
                document.getElementById('totalSecurity').textContent = categories['security'] || 0;
                /* 현재 페이지(reviews)가 아니라 전체 데이터 기준인 repo_counts로 집계해야
                   저장소가 여러 개여도 1페이지 리뷰가 한 저장소에 몰려있을 때 개수가 안 틀어짐 */
                document.getElementById('totalRepos').textContent = Object.keys(data.repo_counts).length;
            }

            /* 저장소 드롭다운 옵션 채우기 */
            const repoFilter = document.getElementById('repoFilter');
            if (page === 1) {
                repoFilter.innerHTML = '<option value="">전체 저장소</option>';
                Object.keys(data.repo_counts).forEach(repo => {
                    const option = document.createElement('option');
                    option.value = repo;
                    option.textContent = repo;
                    repoFilter.appendChild(option);
                });
                repoFilter.value = currentRepo;  // 선택값 복원
            }

            /* 테이블에 리뷰 이력 채우기 */
            const tbody = document.getElementById('reviewTable');
            tbody.innerHTML = '';
            reviews.forEach(r => {
                const tr = document.createElement('tr');
                const date = new Date(r.created_at + 'Z').toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' });
                tr.dataset.repo = r.repo;
                tr.dataset.title = r.title;
                tr.innerHTML = `
                    <td class="td-muted">${r.id}</td>
                    <td>
                        <a href="https://github.com/${r.repo}" target="_blank"
                           class="repo-link" 
                           onclick="event.stopPropagation()">
                            ${r.repo}
                        </a>
                    </td>
                    <td><span class="pr-badge">#${r.pr_number}</span></td>
                    <td>
                        <a href="https://github.com/${r.repo}/pull/${r.pr_number}" target="_blank"
                           class="title-link"
                           onclick="event.stopPropagation()">
                            ${r.title}
                        </a>
                    </td>
                    <td><span class="status-completed">${r.status === 'completed' ? '완료' : r.status}</span></td>
                    <td class="td-sub">${date}</td>
                `;
                tr.addEventListener('click', () => {
                    document.getElementById('modal-body').innerHTML = marked.parse(r.summary || '');
                    modal.style.display = 'block';
                });
                tbody.appendChild(tr);
            });

            /* 모달 닫기 */
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.style.display = 'none';
            });

            /* 페이지네이션 렌더링 */
            renderPagination(data.total_pages, page);

            /* 차트는 첫 페이지에서만 */
            if (page === 1) {
                renderCharts(reviews, categories, data.repo_counts);
            }
        })
        .catch(error =>{
            if (error.message === '서버 오류' || error instanceof TypeError) {
                document.querySelector('.table-card')
                .innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 40px;">서버가 실행 중이 아닙니다.</p>';
            } else {
                console.error('대시보드 로드 오류:', error);
            }
        });
}

function renderPagination(totalPages, currentPage) {
    const container = document.getElementById('pagination');
    if (!container) return;
    container.innerHTML = '';
    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
        btn.addEventListener('click', () => {
            currentPage = i;
            loadDashboard(i);
        });
        container.appendChild(btn);
    }
}

// 라이트모드, 다크모드 차트 색상 지정
function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        bar: isDark ? '#e85d04' : '#3b82f6',
        doughnut: isDark
            ? ['#f85149', '#58a6ff', '#bc8cff', '#3fb950', '#d29922']
            : ['#cf222e', '#0969da', '#8250df', '#1a7f37', '#bf8700'],
        text: isDark ? '#e6edf3' : '#24292f',
        grid: isDark ? '#30363d' : '#e1e4e8',
    };
}

function renderCharts(reviews, categories, repoCounts) {
    const colors = getChartColors();
    if (reviewChartInstance) reviewChartInstance.destroy();
    if (categoryChartInstance) categoryChartInstance.destroy();

    reviewChartInstance = new Chart(document.getElementById('reviewChart'), {
        type: 'bar',
        data: {
            labels: Object.keys(repoCounts),
            datasets: [{
                label: '리뷰 횟수',
                data: Object.values(repoCounts),
                backgroundColor: colors.bar,
                borderRadius: 4,
                barThickness: 80,
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1, color: colors.text }, grid: { color: colors.grid } },
                x: { ticks: { color: colors.text }, grid: { display: false } }
            }
        }
    });

    /* 카테고리별 도넛 차트 */
    categoryChartInstance = new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                data: Object.values(categories),
                backgroundColor: colors.doughnut,
                borderColor: getComputedStyle(document.documentElement).getPropertyValue('--card-bg').trim(),
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { color: colors.text } } }
        }
    });
}

/* 필터링 함수 */
function filterTable() {
    const repoVal = document.getElementById('repoFilter').value;
    const searchVal = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#reviewTable tr');
    rows.forEach(tr => {
        const repo = tr.dataset.repo || '';
        const title = tr.dataset.title || '';
        const repoMatch = !repoVal || repo === repoVal;
        const searchMatch = !searchVal || title.toLowerCase().includes(searchVal) || repo.toLowerCase().includes(searchVal);
        tr.style.display = repoMatch && searchMatch ? '' : 'none';
    });
}

document.getElementById('repoFilter').addEventListener('change', (e) => {
    currentRepo = e.target.value;
    loadDashboard(1);
});
document.getElementById('searchInput').addEventListener('input', filterTable);

/* 설정 패널 토글 */
document.getElementById('configToggle').addEventListener('click', () => {
    const body = document.getElementById('configBody');
    const arrow = document.querySelector('.config-arrow');
    const isOpen = body.style.display !== 'none';
    body.style.display = isOpen ? 'none' : 'block';
    arrow.classList.toggle('open', !isOpen);
});


/* 프롬프트 미리보기 자동 업데이트 */
function updatePreview(style) {
    const previewWrapper = document.getElementById('previewWrapper');
    const previewBox = document.getElementById('promptPreviewBox');
    const isCustom = style === 'custom';
    
    document.getElementById('customPromptWrapper').style.display = isCustom ? 'flex' : 'none';
    previewWrapper.style.display = isCustom ? 'none' : 'flex';
    
    if (!isCustom) {
        previewBox.textContent = window.stylePreview[style] || '';
    }
}

document.getElementById('promptStyle').addEventListener('change', (e) => {
    updatePreview(e.target.value);
});


/* 페이지 로드 시 현재 설정 불러오기 */
fetch(`${BASE_URL}/config`, { headers: authHeaders() })
    .then(res => res.json())
    .then(config => {
        document.getElementById('promptStyle').value = config.prompt_style;
        document.getElementById('maxTokens').value = config.max_tokens;
        // 커스텀 프롬프트 복원
        if (config.custom_prompt) {
            document.getElementById('customPrompt').value = config.custom_prompt;
        }
        window.stylePreview = config.style_instructions;
        updatePreview(config.prompt_style);
    });

loadDashboard(1);

/* 토스트 알림 */
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

/* 설정 저장 */
document.getElementById('saveConfig').addEventListener('click', () => {
    const promptStyle = document.getElementById('promptStyle').value;
    const maxTokens = parseInt(document.getElementById('maxTokens').value);
    const styleNames = {
        "general": "일반 (전반적 리뷰)",
        "security": "보안 중점",
        "performance": "성능 중점",
        "beginner": "초보자 친화적",
        "custom": "사용자 지정"
    };
    const customPrompt = document.getElementById('customPrompt').value;

    fetch(`${BASE_URL}/config`, {
        method: 'POST',
        headers: authHeaders(),
       body: JSON.stringify({ 
            prompt_style: promptStyle, 
            max_tokens: maxTokens,
            custom_prompt: promptStyle === 'custom' ? customPrompt : ""
        })
    })
    .then(res => res.json())
    .then(data => {
        showToast(`설정 저장됨: ${styleNames[promptStyle]} / ${maxTokens} 토큰`);
        console.log('설정:', data);
    })
    .catch(err => console.error('설정 저장 실패:', err));
});

// 다크모드 <-> 라이트모드 전환
themeToggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.setAttribute('data-theme', isDark ? '' : 'dark');
    themeToggle.innerHTML = isDark ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
    themeToggle.title = isDark ? '다크 모드로 전환' : '라이트 모드로 전환';
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    
    if (reviewChartInstance) reviewChartInstance.destroy();
    if (categoryChartInstance) categoryChartInstance.destroy();
    renderCharts(allReviews, lastCategories, lastRepoCounts);
});

// 페이지 로드 시 저장된 테마 복원
const saved = localStorage.getItem('theme');
if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
    themeToggle.title = '라이트 모드로 전환';
}

/* 30초마다 자동 새로고침 */
setInterval(() => loadDashboard(currentPage), 30000);