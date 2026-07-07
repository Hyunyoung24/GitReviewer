fetch('/dashboard')
    .then(res => res.json())
    .then(data => {
        const reviews = data.reviews;
        const modal = document.getElementById('modal');

        /* 테이블에 리뷰 이력 채우기 */
        const tbody = document.getElementById('reviewTable');
        reviews.forEach(r => {
            const tr = document.createElement('tr');
            const date = new Date(r.created_at).toLocaleString('ko-KR');
            tr.innerHTML = `
                <td>${r.id}</td>
                <td>
                    <a href="https://github.com/${r.repo}" target="_blank">
                        ${r.repo}
                    </a>
                </td>
                <td>#${r.pr_number}</td>
                <td>
                    <a href="https://github.com/${r.repo}/pull/${r.pr_number}" target="_blank">
                        ${r.title}
                    </a>
                </td>
                <td class="status-completed">${r.status}</td>
                <td>${date}</td>
            `;

            tr.addEventListener('click', () => {
                document.getElementById('modal-body').innerHTML = marked.parse(r.summary);
                modal.style.display = 'block';
            });
            tbody.appendChild(tr);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        })

        /* Chart.js로 저장소별 리뷰 횟수 집계 */
        const repoCounts = {};
        reviews.forEach(r => {
            repoCounts[r.repo] = (repoCounts[r.repo] || 0) + 1;
        });

        new Chart(document.getElementById('reviewChart'), {
            type: 'bar',
            data: {
                labels: Object.keys(repoCounts),
                datasets: [{
                    label: '리뷰 횟수',
                    data: Object.values(repoCounts),
                    backgroundColor: '#0969da',
                    borderRadius: 4,
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
            }
        });
    });

setInterval(() => location.reload(), 30000);