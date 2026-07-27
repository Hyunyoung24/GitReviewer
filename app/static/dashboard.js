// 현재 페이지, 페이지당 갯수
let currentPage = 1;
const perPage = 10;
let allReviews = [];
let currentRepo = '';

// fetch('/dashboard')
/* Railway 배포용 절대경로 API */
function loadDashboard(page = 1) {
    /* Railway 배포용 절대경로 API */
    fetch(`https://gitreviewer-production-c6da.up.railway.app/dashboard?page=${page}&per_page=${perPage}&repo=${encodeURIComponent(currentRepo)}`)
        .then(res => res.json())
        .then(data => {
            const reviews = data.reviews;
            const categories = data.categories;
            const modal = document.getElementById('modal');
            allReviews = reviews;

            /* 통계 카드 채우기 (첫 페이지에서만) */
            if (page === 1) {
                document.getElementById('totalReviews').textContent = data.total;
                document.getElementById('totalBugs').textContent = categories['bug'] || 0;
                document.getElementById('totalSecurity').textContent = categories['security'] || 0;
                const repos = new Set(reviews.map(r => r.repo));
                document.getElementById('totalRepos').textContent = repos.size;
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
                    <td style="color: #8c959f;">${r.id}</td>
                    <td>
                        <a href="https://github.com/${r.repo}" target="_blank"
                           style="color: #0969da; text-decoration: none;"
                           onclick="event.stopPropagation()">
                            ${r.repo}
                        </a>
                    </td>
                    <td><span class="pr-badge">#${r.pr_number}</span></td>
                    <td>
                        <a href="https://github.com/${r.repo}/pull/${r.pr_number}" target="_blank"
                           style="color: #24292f; text-decoration: none;"
                           onclick="event.stopPropagation()">
                            ${r.title}
                        </a>
                    </td>
                    <td><span class="status-completed">${r.status === 'completed' ? '완료' : r.status}</span></td>
                    <td style="color: #57606a;">${date}</td>
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

function renderCharts(reviews, categories, repoCounts) {
    new Chart(document.getElementById('reviewChart'), {
        type: 'bar',
        data: {
            labels: Object.keys(repoCounts),
            datasets: [{
                label: '리뷰 횟수',
                data: Object.values(repoCounts),
                backgroundColor: '#3b82f6',
                borderRadius: 4,
                barThickness: 80,
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
    });

    /* 카테고리별 도넛 차트 */
    new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                data: Object.values(categories),
                backgroundColor: ['#cf222e', '#0969da', '#8250df', '#1a7f37', '#bf8700'],
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { position: 'right' } }
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

loadDashboard(1);

/* 30초마다 자동 새로고침 */
setInterval(() => loadDashboard(currentPage), 30000);