fetch('/dashboard')
    .then(res => res.json())
    .then(data => {
        const reviews = data.reviews;

        /* 테이블에 리뷰 이력 채우기 */
        const tbody = document.getElementById('reviewTable');
        reviews.forEach(r => {
            const date = new Date(r.created_at).toLocaleString('ko-KR');
            tbody.innerHTML += `
                <tr>
                    <td>${r.id}</td>
                    <td>${r.repo}</td>
                    <td>#${r.pr_number}</td>
                    <td>${r.title}</td>
                    <td class="status-completed">${r.status}</td>
                    <td>${date}</td>
                </tr>
            `;
        });

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