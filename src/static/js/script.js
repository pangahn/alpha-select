// 全局变量
let currentFundCode = '013594'; // 默认基金代码
const investmentAmount = 100000; // 默认投资金额：10万元

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签页切换
    initTabs();

    // 初始化历史数据标签页切换
    initHistoricalTabs();

    // 初始化搜索按钮
    initSearchButton();

    // 更新脚注的投资金额
    updateInvestmentFootnote();

    // 加载默认基金数据
    loadFundData(currentFundCode);
});

// 初始化标签页切换
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // 添加当前活动状态
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// 初始化历史数据标签页切换
function initHistoricalTabs() {
    const tabBtns = document.querySelectorAll('.historical-tab-btn');
    const tabContents = document.querySelectorAll('.historical-tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // 添加当前活动状态
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// 初始化搜索按钮
function initSearchButton() {
    const searchBtn = document.getElementById('searchBtn');
    const fundCodeInput = document.getElementById('fundCode');

    searchBtn.addEventListener('click', function() {
        const fundCode = fundCodeInput.value.trim();
        if (fundCode && fundCode.length >= 4) {
            currentFundCode = fundCode;
            loadFundData(fundCode);
        } else {
            alert('请输入有效的基金代码');
        }
    });

    // 回车键触发搜索
    fundCodeInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });
}

// 加载基金数据
async function loadFundData(fundCode) {
    try {
        // 显示加载状态
        document.getElementById('weeklyReturnsContainer').innerHTML = '<div class="loading">加载中...</div>';
        document.getElementById('fundName').textContent = '加载中...';
        document.getElementById('netvalue-data-container').innerHTML = '<div class="loading">加载中...</div>';

        // 调用API获取数据
        const response = await fetch(`/api/fund/${fundCode}?investment_amount=${investmentAmount}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        // 更新基金信息
        updateFundInfo(data);

        // 更新周收益数据
        updateWeeklyReturns(data.weekly_data);

        // 更新周收益率图
        updateWeeklyReturnsChart(data);

        // 更新单位净值图
        updateNetWorthChart(data);

        // 更新历史业绩数据
        updateHistoricalPerformance(data.historical_performance);

        // 更新历史净值数据
        updateNetValueData(data.net_worth_data);

    } catch (error) {
        console.error('获取基金数据失败:', error);
        alert('获取基金数据失败，请稍后再试');
    }
}

// 更新基金信息
function updateFundInfo(data) {
    document.getElementById('fundName').textContent = data.fund_name;
    document.getElementById('fundType').textContent = `${data.fund_code} | ${data.fund_type}`;

    // 设置天天基金网链接
    const eastmoneyLink = document.getElementById('eastmoneyLink');
    if (eastmoneyLink) {
        eastmoneyLink.href = `https://fund.eastmoney.com/${data.fund_code}.html`;
    }

    // 更新年化收益率
    const annualizedRate = data.annualized_returns['since'].toFixed(2);
    document.getElementById('yieldRate').textContent = annualizedRate + '%';

    // 更新正收益周数
    document.getElementById('weekCount').textContent = data.positive_weeks_count;

    // 更新平均周收益
    document.getElementById('avgWeeklyReturn').textContent = data.avg_weekly_return.toFixed(2);

    // 更新周期文本
    document.getElementById('periodText').textContent = data.period_text;
}

// 更新周收益数据
function updateWeeklyReturns(weeklyData) {
    const container = document.getElementById('weeklyReturnsContainer');
    container.innerHTML = '';

    weeklyData.forEach(week => {
        const weekItem = document.createElement('div');
        weekItem.className = 'weekly-return-item';

        // 判断收益是正还是负
        const isPositive = week.return_amount > 0;
        const returnColor = isPositive ? 'red' : 'green';
        const signPrefix = isPositive ? '+' : '';

        weekItem.innerHTML = `
            <div class="weekly-return-date">${week.date_range}</div>
            <div class="weekly-return-value" style="color: ${returnColor}">${signPrefix}${week.return_amount.toFixed(2)}</div>
        `;

        container.appendChild(weekItem);
    });
}

// 更新周收益率图
function updateWeeklyReturnsChart(data) {
    const trendCtx = document.getElementById('weeklyReturnsChart').getContext('2d');
    const trendLabels = data.weekly_data.map(week => week.date_range);
    const trendData = data.weekly_data.map(week => week.return_amount);

    // Check if weeklyReturnsChart exists and is a valid Chart.js instance
    if (window.weeklyReturnsChart && typeof window.weeklyReturnsChart.destroy === 'function') {
        window.weeklyReturnsChart.destroy();
    }

    window.weeklyReturnsChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: trendLabels,
            datasets: [{
                data: trendData,
                backgroundColor: 'rgba(30, 136, 229, 0.2)',
                borderColor: 'rgba(30, 136, 229, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(30, 136, 229, 1)',
                tension: 0.4,
                pointRadius: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// 更新单位净值图
function updateNetWorthChart(data) {
    const unitCtx = document.getElementById('netWorthChart').getContext('2d');
    const unitLabels = data.net_worth_data.map(item => item.date);
    const unitValues = data.net_worth_data.map(item => item.value);

    if (window.unitChart && typeof window.unitChart.destroy === 'function') {
        window.unitChart.destroy();
    }

    window.unitChart = new Chart(unitCtx, {
        type: 'line',
        data: {
            labels: unitLabels,
            datasets: [{
                data: unitValues,
                backgroundColor: 'rgba(229, 57, 53, 0.2)',
                borderColor: 'rgba(229, 57, 53, 1)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
            }
        }
    });
}

// 更新历史业绩数据
function updateHistoricalPerformance(performanceData) {
    if (!performanceData) return;

    // 定义时间区间配置
    const timeIntervals = [
        { id: '1week', key: '1week', label: '近1周' },
        { id: '1month', key: '1month', label: '近1月' },
        { id: '3months', key: '3months', label: '近3月' },
        { id: '6months', key: '6months', label: '近6月' },
        { id: '1year', key: '1year', label: '近1年' },
    ];

    // 动态更新每个时间区间的数据
    timeIntervals.forEach(interval => {
        const cellId = `perf-${interval.id}`;
        const value = performanceData[interval.key];
        const cell = document.getElementById(cellId);
        if (!cell) return;

        const isPositive = value > 0;
        const colorClass = isPositive ? 'positive' : 'negative';
        const signPrefix = isPositive ? '+' : '';

        cell.className = `performance-cell ${colorClass}`;
        cell.textContent = `${signPrefix}${value.toFixed(2)}%`;
    });
}

// 更新历史净值数据
function updateNetValueData(netValueData) {
    if (!netValueData || netValueData.length === 0) return;

    const container = document.getElementById('netvalue-data-container');
    container.innerHTML = '';

    const reversedData = [...netValueData].reverse();

    reversedData.forEach(item => {
        const row = document.createElement('div');
        row.className = 'netvalue-row';

        const isPositive = item.growth_rate > 0;
        const growthClass = isPositive ? 'positive' : 'negative';
        const signPrefix = isPositive ? '+' : '';

        row.innerHTML = `
            <div class="netvalue-cell">${item.date}</div>
            <div class="netvalue-cell">${item.value}</div>
            <div class="netvalue-cell ${growthClass}">${signPrefix}${item.growth_rate.toFixed(2)}%</div>
        `;

        container.appendChild(row);
    });
}

// 更新脚注的投资金额
function updateInvestmentFootnote() {
    const footnoteElement = document.getElementById('investment-footnote');
    if (footnoteElement) {
        // 将投资金额格式化为万元单位
        const amountInWan = investmentAmount / 10000;
        footnoteElement.textContent = `图示为持有${amountInWan}万元在近3个月的收益情况(单位:元)`;
    }
}